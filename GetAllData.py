import argparse
import asyncio
import pathlib
from libs.Openstack import getVolumeList, createImageFromVolume, downloadImage, waitSaving, deleteImages
from libs.RcInit import setOsVariables


async def main():
    parser = argparse.ArgumentParser(description=(
        "Checks computers for freezes and reboots "))
    parser.add_argument("--rcFile", help="rc file",
                        default="../Login/rc.sh", type=pathlib.Path)
    parser.add_argument("--clearScreen", action="store_true", default=False)

    args = parser.parse_args()
    rcFilePath = args.rcFile

    if not setOsVariables(rcFilePath):
        return

    volumeDataList = await getVolumeList()
    if volumeDataList.__len__() <= 0:
        return

    print(volumeDataList)

# Img
    print("Creating img from volumes...")
    tasks = []
    imageNamesList = []
    for volumeData in volumeDataList:
        imageName = volumeData[1] + "_img"
        imageNamesList.append(imageName)
        tasks.append(asyncio.create_task(createImageFromVolume(volumeData[0], imageName)))

    await asyncio.gather(*tasks)
    tasks.clear()

# Waiting
    print("Waiting until img is saved...")
    for imageName in imageNamesList:
        tasks.append(asyncio.create_task(waitSaving(imageName)))

    await asyncio.gather(*tasks)
    tasks.clear()

# Downloading
    print("Downloading...")
    for imageName in imageNamesList:
        tasks.append(asyncio.create_task(downloadImage(imageName)))

    await asyncio.gather(*tasks)
    tasks.clear()

# Deleting
    print("Deleting...")
    await deleteImages(imageNamesList)

    return

if __name__ == "__main__":
    asyncio.run(main())
