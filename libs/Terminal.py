import asyncio
import os


class style():
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'


def clear():
    # check and make call for specific operating system
    _ = os.system('clear' if os.name == 'posix' else 'cls')

async def runAsyncCmd(cmd):
    proc = await asyncio.create_subprocess_shell(cmd,
                                                 stdin=asyncio.subprocess.PIPE,
                                                 stderr=asyncio.subprocess.PIPE,
                                                 stdout=asyncio.subprocess.PIPE)
    stdout, stderr = await proc.communicate()
    proc.stdout
    return stdout