import argparse
import asyncio
import atexit
import os
import pathlib
import re
import subprocess

import aiofiles
from genericpath import exists


def checkFile(filePath):
    if not exists(filePath):
        print(f"{filePath} is not exists")
        return False
    return True


def convertIps(ips: list[str]) -> list[str]:
    formatedIp = []
    for ip in ips:
        ip = ip.replace('.', ',')
        ip = '{' + ip + '},'
        formatedIp.append(ip)

    return formatedIp


cppContent: str = ""
cppFilePath: str = ""


def restoreCppFile():
    if cppContent.__len__() > 0:
        with open(cppFilePath, "w") as cppFile:
            cppFile.write(cppContent)


async def main():
    from libs.FSMode import applyFSMode
    from libs.JsonSettings import getSettings
    from libs.Terminal import style

    parser = argparse.ArgumentParser(description=(
        "Building qubic from source code"))
    parser.add_argument("--settingsJsonFilePath", type=pathlib.Path,
                        help="Path to json file with settings",
                        default="")
    parser.add_argument("--slnFilePath", type=pathlib.Path,
                        help="Path to sln file",
                        default="")
    parser.add_argument("--cppFilePath", type=pathlib.Path,
                        help="Path to cpp file with qubic source",
                        default="")
    parser.add_argument("--msBuildFilePath", type=pathlib.Path,
                        help="Path to MsBuild.exe",
                        default="")
    parser.add_argument("--outDir", type=pathlib.Path,
                        help="The folder in which the efi files will be written to",
                        default="")
    parser.add_argument("--freeCpuNum", type=int,
                        help="The number of cores that will not take part in mining",
                        default=2)
    parser.add_argument("--saveCppFile", help="",
                        action="store_true", default=False)
    parser.add_argument("--fsMode", help="Apply the code that allows you to select FS with .data files",
                        action="store_true", default=False)
    args = parser.parse_args()

    global cppContent
    global cppFilePath

    settingsFilePath = str(args.settingsJsonFilePath)
    slnFilePath = str(args.slnFilePath)
    cppFilePath = str(args.cppFilePath)
    msBuildFilePath = str(args.msBuildFilePath)
    freeCpuNum: int = args.freeCpuNum
    computingCpuNum: int = 1
    outDir = str(os.path.abspath(args.outDir))
    saveCppFile = args.saveCppFile
    fsMode = args.fsMode

    # Checking
    exists = os.path.exists(settingsFilePath)
    currentStyle = style.GREEN if exists else style.RED
    print( currentStyle +  f"Json File: {settingsFilePath}" + style.WHITE)

    exists = os.path.exists(slnFilePath)
    currentStyle = style.GREEN if exists else style.RED
    print(currentStyle + f"sln File: {slnFilePath}" + style.WHITE)

    exists = os.path.exists(cppFilePath)
    currentStyle = style.GREEN if exists else style.RED
    print(currentStyle + f"cpp File: {cppFilePath}" + style.WHITE)

    exists = os.path.exists(msBuildFilePath)
    currentStyle = style.GREEN if exists else style.RED
    print(currentStyle + f"ms Build File: {msBuildFilePath}" + style.WHITE)

    exists = os.path.exists(outDir)
    currentStyle = style.GREEN if exists else style.RED
    print(currentStyle + f"Out Dir: {outDir}" + style.WHITE)

    print(f"Save cpp File: {saveCppFile}")
    print(f"FS Mode: {fsMode}")

    atexit.register(restoreCppFile)

    if not checkFile(settingsFilePath)\
            or not checkFile(slnFilePath)\
            or not checkFile(cppFilePath)\
            or not checkFile(msBuildFilePath):
        return

    # Re
    seedsRegex = re.compile(
        '(static unsigned char ownSeeds[ ]*.*=[ ]*\{\n+)(.*)(\n+\};)')
    operatorRegex = re.compile('(define[ ]*OPERATOR[ ]*\")(.*)(\")')
    computerIdRegex = re.compile('(define[ ]*COMPUTOR[ ]*\")(.*)(\")')
    numberOfMiningProcessorsRegex = re.compile(
        '(define[ ]*NUMBER_OF_MINING_PROCESSORS)([ ]*[0-9]+)')
    numberOfComputingProcessorsRegex = re.compile(
        '(define[ ]*NUMBER_OF_COMPUTING_PROCESSORS)([ ]*[0-9]+)')
    knownPublicRegex = re.compile(
        '(static const unsigned char knownPublicPeers.* *= *{\n)((.*\{.*\},{0,1}\n)*)(\};)')
    tickRe = re.compile('(define TICK )(\w*)')
    # Network Re
    ownAddressRe = re.compile(
        '(static const unsigned char ownAddress\[4\] = \{)(.*)(\})')
    ownMaskRe = re.compile(
        '(static const unsigned char ownMask\[4\] = \{)(.*)(\})')
    defaultRouteGatewayRe = re.compile(
        '(static const unsigned char defaultRouteGateway\[4\] = \{)(.*)(\})')
    ownPublicAddressRe = re.compile(
        '(static const unsigned char ownPublicAddress\[4\] = \{)(.*)(\})')

    taskSettings = asyncio.create_task(getSettings(settingsFilePath))

    async with aiofiles.open(cppFilePath, "r+") as cppFile:
        cppContent = await cppFile.read()

    settingList = await asyncio.gather(taskSettings)
    savedCppFileTasks = []
    for settings in settingList[0]:
        # Skip disabled instances
        if not settings.is_enable:
            continue

        seeds = settings.seeds
        seeds_str = str(seeds).replace(r"'", r'"').replace(r'[', '').replace(r']', '')
        # Seed
        newCppContent = seedsRegex.sub(rf"\1{seeds_str}\3", cppContent)
        # Operator
        newCppContent = operatorRegex.sub(
            rf"\1{settings.operatorId}\3", newCppContent)
        # ComputerId
        newCppContent = computerIdRegex.sub(
            rf"\1{settings.computerId}\3", newCppContent)
        # Tick
        newCppContent = tickRe.sub(rf"\g<1>{settings.tick}", newCppContent)
        # Cpu Number
        cpuNumber = str(max(
            0, int(settings.cpuNum) - freeCpuNum))

        # Network
        ownAddress = settings.ownAddress.replace(r".", r",")
        newCppContent = ownAddressRe.sub(rf"\g<1>{ownAddress}\g<3>", newCppContent)
        ownMask = settings.ownMask.replace(r".", r",")
        newCppContent = ownMaskRe.sub(rf"\g<1>{ownMask}\g<3>", newCppContent)
        defaultRouteGateway = settings.defaultRouteGateway.replace(r".", r",")
        newCppContent = defaultRouteGatewayRe.sub(rf"\g<1>{defaultRouteGateway}\g<3>", newCppContent)
        ownPublicAddress = settings.ownPublicAddress.replace(r".", r",")
        newCppContent = ownPublicAddressRe.sub(rf"\g<1>{ownPublicAddress}\g<3>", newCppContent)

        # Only Computer Settings
        if settings.is_computer:
            cpuNumber = str(max(0, int(cpuNumber) - computingCpuNum))
            newCppContent = numberOfComputingProcessorsRegex.sub(
                rf"\1 {computingCpuNum}", newCppContent)

        newCppContent = numberOfMiningProcessorsRegex.sub(
            rf"\1 {cpuNumber}", newCppContent)
        # Known Public IPs
        knownPublicPeers = '\t' + '\n\t'.join(
            convertIps(settings.knownPublicPeers)) + '\n'
        newCppContent = knownPublicRegex.sub(
            rf"\1{knownPublicPeers}\4", newCppContent)

        # FS Mode
        if fsMode:
            newCppContent = applyFSMode(newCppContent)

        filename_sufix = seeds[0][-2:]

        if saveCppFile:
            saveCppFile = await aiofiles.open(f"Qubic_{filename_sufix}.txt", "w").__aenter__()
            savedCppFileTasks.append(asyncio.create_task(
                saveCppFile.write(newCppContent)))

        async with aiofiles.open(cppFilePath, "w") as cppFile:
            await cppFile.write(newCppContent)

        if not saveCppFile:
            msBuildCmd = fr""""{msBuildFilePath}" "{slnFilePath}" -m /t:build /p:DebugSymbols=false /p:DebugType=None /p:Configuration=Release,OutDir={outDir},TargetName=Qubic_{filename_sufix}"""
            subprocess.call(msBuildCmd)

    await asyncio.gather(*savedCppFileTasks)


if __name__ == "__main__":
    asyncio.run(main())
