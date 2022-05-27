import string
from datetime import datetime

import aiofiles


async def writeToLog(computerName: string,
                     logData: string):
    async with aiofiles.open(f"log_{computerName}.log", "a") as logFile:
        await logFile.write(f"{datetime.utcnow(): }" + logData + "\n")
