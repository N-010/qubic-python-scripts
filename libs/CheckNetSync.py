import asyncio
import re
from tabnanny import check

import aiofiles


def getAllSecondFromTime(date: str):
    from datetime import datetime

    fullDate = "20" + date
    print(datetime.strptime(
        fullDate, '%Y%m%d%H%M%S'))


def getNumber(str: str) -> int:
    numberRe = re.compile("\d")
    return int("".join(numberRe.findall(str)))


def checkNetworkSync(log: str, lineNumber: int = 300) -> bool:
    netSyncRe = re.compile("(\d{12}) .*\(\+(.*) -(.*) \.\.\.(.*)\)")
    foundAll = netSyncRe.findall(log)
    lastData = foundAll[-lineNumber:]

    # Not enough data
    if(lineNumber > lastData.__len__()):
        return True

    for netData in lastData:
        data = netData[0]
        rx = getNumber(netData[1])
        tx = getNumber(netData[2])
        wx = getNumber(netData[3])

        if rx != 0 or tx != 0 or wx != 0:
            return True

    return False


# async def main():
#     async with aiofiles.open("test.log", "r") as logFile:
#         logStr = await logFile.read()
#         print(checkNetworkSync(logStr))

# if __name__ == "__main__":
#     asyncio.run(main())
