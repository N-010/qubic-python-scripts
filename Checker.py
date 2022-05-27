import argparse
import asyncio
import os
import pathlib
import re
import string
import time
from datetime import datetime

from libs.Enums import errorType
from libs.Terminal import clear, style


def getAllRcFiles(rcFilesFolder):
    rcFileRegex = re.compile('.*rc.*\.sh')
    return [f for f in os.listdir(rcFilesFolder) if rcFileRegex.match(f)]


async def saveLog(log: str,
                  computerName: str):
    import aiofiles
    async with aiofiles.open(F"{computerName}_error_{datetime.utcnow().timestamp().__str__()}.log", "w") as logFile:
        await logFile.write(log)


async def checkComputerAsync(computerName: string,
                             downTimeSeconds: int = 5 * 60,
                             old_time_re: bool = False):
    from libs.Openstack import getConsoleLogAsync
    from libs.CheckNetSync import checkNetworkSync

    logBytes = await asyncio.create_task(getConsoleLogAsync(computerName))
    logString = logBytes.decode()

    print(style.GREEN + f"Computer: {computerName}" + style.WHITE)

    if old_time_re:
        dateReg = re.compile(
            "(\d{4}-\d{1,2}-\d{1,2} \d{1,2}:\d{1,2}:\d{1,2})")
    else:
        dateReg = re.compile(
            "(\d{12}) ")

    skip_freeze_check = False

    try:
        lastDateString: str = dateReg.findall(logString)[-1]
        if not old_time_re:
            lastDateString = "20" + lastDateString
    except IndexError:
        skip_freeze_check = True
        print(style.YELLOW + "Could not find the latest update time" + style.WHITE)

    if not skip_freeze_check:
        try:
            if not old_time_re:
                lastDateTime = datetime.strptime(
                    lastDateString, '%Y%m%d%H%M%S')
            else:
                lastDateTime = datetime.strptime(
                    lastDateString, '%Y-%m-%d %H:%M:%S')

        except ValueError:
            skip_freeze_check = True
            print(
                style.RED + f"Failed to retrieve date from string: {lastDateString}" + style.WHITE)

        if not skip_freeze_check:
            print(f"\tLast time: {lastDateTime.time()}")
            nowTime = datetime.utcnow()
            deltaDataTime = nowTime - lastDateTime
            if deltaDataTime.days >= 0 and deltaDataTime.seconds > downTimeSeconds:
                await saveLog(logString, computerName)
                return (computerName, errorType.FREEZE)

    if re.findall('Exception Type', logString).__len__() > 0:
        await saveLog(logString, computerName)
        return (computerName, errorType.EXCEPTION)

    if not checkNetworkSync(logString):
        await saveLog(logString, computerName)
        return (computerName, errorType.NET_DISCONECT)


    return (computerName, errorType.SUCCESS)


async def main():
    from libs.Log import writeToLog

    from libs.Openstack import getServerNamesAsync, rebootComputerAsync
    from libs.RcInit import setOsVariables

    parser = argparse.ArgumentParser(description=(
        "Checks computers for freezes and reboots "))
    parser.add_argument("--waitTime", type=int,
                        help="Waiting time before restarting the test", default=3 * 60, metavar='seconds')
    parser.add_argument("--oldTime", action="store_true",
                        default=False)
    parser.add_argument("--downTime", help="If the computer freezes for more than this time (seconds), it will restart",
                        default=5 * 60, type=int, metavar='seconds')
    parser.add_argument("--updateComputerNamesTime", help="How many seconds to update computer names",
                        default=10 * 60, type=int, metavar='seconds')
    parser.add_argument("--rcFilesPath", help="Path to rc files",
                        type=pathlib.Path, default="./")
    parser.add_argument("--rcFile", help="rc file",
                        default="../Login/rc.sh", type=pathlib.Path)
    parser.add_argument("--clearScreen", action="store_true", default=False)

    args = parser.parse_args()

    if args.clearScreen:
        clear()

    # Check rc file
    rcFile = args.rcFile
    if not setOsVariables(rcFile):
        return

    waitTime = args.waitTime
    downTime = args.downTime
    oldTime = args.oldTime
    updateComputerNamesTime = args.updateComputerNamesTime
    lastUpdateComputerNamesTime = 0
    tasks = []
    while True:
        currentTime = time.time()
        if currentTime - lastUpdateComputerNamesTime >= updateComputerNamesTime:
            print(style.GREEN + "Get server names..." + style.WHITE)
            serverNames = await getServerNamesAsync()
            print(f"Server Names:\n\t{serverNames}")
            lastUpdateComputerNamesTime = currentTime

        # Find errors
        for serverName in serverNames:
            tasks.append(asyncio.create_task(
                checkComputerAsync(serverName, downTime, oldTime)))

        resultTypes = await asyncio.gather(*tasks)
        tasks.clear()

        logTasks = []
        # Reboot
        for resultType in resultTypes:
            computerName = resultType[0]
            error = resultType[1]
            logTasks.append(asyncio.create_task(
                writeToLog(computerName, str(error))))
            if error != errorType.SUCCESS:
                print(style.RED +
                      f"Error {computerName}: {error}" + style.WHITE)
                tasks.append(asyncio.create_task(
                    rebootComputerAsync(computerName)))

        await asyncio.sleep(waitTime)
        # Waiting for processes to complete, if they have not had time to run
        await asyncio.gather(*logTasks)
        await asyncio.gather(*tasks)
        tasks.clear()

        print("________________________________")


if __name__ == "__main__":
    asyncio.run(main())
