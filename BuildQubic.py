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
    seedRegex = re.compile(
        '(static unsigned char ownSeed[ ]*.*=[ ]*\")(.*)(\";)')
    operatorRegex = re.compile('(define[ ]*OPERATOR[ ]*\")(.*)(\")')
    computerIdRegex = re.compile('(define[ ]*COMPUTOR[ ]*\")(.*)(\")')
    numberOfMiningProcessorsRegex = re.compile(
        '(define[ ]*NUMBER_OF_MINING_PROCESSORS)([ ]*[0-9]+)')
    numberOfComputingProcessorsRegex = re.compile(
        '(define[ ]*NUMBER_OF_COMPUTING_PROCESSORS)([ ]*[0-9]+)')
    knownPublicRegex = re.compile(
        '(static const unsigned char knownPublicPeers.* *= *{\n)((.*\{.*\},{0,1}\n)*)(\};)')
    tickRe = re.compile('(define TICK )(\w*)')

    taskSettings = asyncio.create_task(getSettings(settingsFilePath))

    async with aiofiles.open(cppFilePath, "r+") as cppFile:
        cppContent = await cppFile.read()

    settingList = await asyncio.gather(taskSettings)
    savedCppFileTasks = []
    for settings in settingList[0]:
        # Skip disabled instances
        if not settings.is_enable:
            continue

        seed = settings.seed
        # Seed
        newCppContent = seedRegex.sub(rf"\1{seed}\3", cppContent)
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

        if saveCppFile:
            saveCppFile = await aiofiles.open(f"Qubic_{seed[-2:]}.txt", "w").__aenter__()
            savedCppFileTasks.append(asyncio.create_task(
                saveCppFile.write(newCppContent)))

        async with aiofiles.open(cppFilePath, "w") as cppFile:
            await cppFile.write(newCppContent)

        msBuildCmd = fr""""{msBuildFilePath}" "{slnFilePath}" -m /t:build /p:DebugSymbols=false /p:DebugType=None /p:Configuration=Release,OutDir={outDir},TargetName=Qubic_{seed[-2:]}"""
        subprocess.call(msBuildCmd)

    await asyncio.gather(*savedCppFileTasks)


if __name__ == "__main__":
    asyncio.run(main())
