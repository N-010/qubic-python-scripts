import asyncio
from io import TextIOWrapper
import re
import string
import subprocess
from .Terminal import runAsyncCmd


######## Async ########

async def getServerNamesAsync():
    stdout = await runAsyncCmd("openstack server list")
    serverNameRe = re.compile("(Qubic_\w{2})")
    return serverNameRe.findall(stdout.decode())


async def getConsoleLogAsync(serverName: string):
    return await runAsyncCmd(F"openstack console log show {serverName}")


async def rebootComputerAsync(serverName: string):
    print(f"Rebooting {serverName}")
    await runAsyncCmd(f"openstack server reboot {serverName}")

async def getVolumeList():
    stdout = await runAsyncCmd("openstack volume list")
    imageRe = re.compile("\| (.*) \| .*(Qubic_Data_\w{2})")
    return imageRe.findall(stdout.decode())

async def createImageFromVolume(volumeName: str, imageName: str):
    stdout = await runAsyncCmd(f"cinder.exe upload-to-image {volumeName} {imageName} --force True")
    return imageName


async def downloadImage(imageName: str):
    stdout = await runAsyncCmd(f"openstack image save --file {imageName}.iso {imageName}")
    print(f"Downloaded: {imageName}")

async def deleteImages(imageNamesList: list[str]):
    imageNamesStr = " ".join(imageNamesList)
    await runAsyncCmd(f"openstack image delete {imageNamesStr}")

async def waitSaving(imageName: str, checkTime: int = 5):
    print(f"imageName: {imageName}")
    while True:
        stdout = await runAsyncCmd("openstack image list")
        statutsRe = re.compile(f"{imageName}.* \| (\w*)") 
        try:
            statusAll = statutsRe.findall(stdout.decode())
            print(statusAll)
            status = statusAll[0]
        except:
            print(f"Failed to get status for {imageName}")
            return
        
        print(f"{imageName}: {status}")
        if status != "active":
            await asyncio.sleep(checkTime)
        else:
            return



######## Withot async ########

def getConsoleLog(serverName: string,
                  stdOut: TextIOWrapper = ...):
    subprocess.call(
        f"openstack console log show {serverName}", stdout=stdOut, shell=True)


def rebootComputer(serverName: string):
    subprocess.call(
        f"openstack server reboot {serverName}", shell=True)


def getServerNames():
    serverListOutput = str(subprocess.check_output(
        "openstack server list", shell=True))
    serverNameRe = re.compile("(Qubic_\w{2})")
    return serverNameRe.findall(serverListOutput)
