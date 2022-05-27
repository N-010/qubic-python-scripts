from genericpath import exists
import os
import re


def clearLine(line):
    line = re.split('#', line)[0]
    line = re.sub('[\'\"# ]', '', line)
    return line


def getEnvVariables(rcFile) -> dict:
    envVariables = {}
    exportPattern = re.compile(
        '(.*export[ ]*)(.*)(=)(.*[ ]*)(#*)', re.MULTILINE | re.IGNORECASE)
    with open(rcFile) as rcFileWriper:
        rcFileContent = rcFileWriper.read()
        for exportLine in exportPattern.findall(rcFileContent):
            exportLineVarName = clearLine(exportLine[1])
            varValue = clearLine(exportLine[3])
            envVariables.update({exportLineVarName:  varValue})

    return envVariables


def setOsVariables(rcFile):
    if not exists(rcFile):
        print(f"File {rcFile} could not be found")
        return False

    envVars = getEnvVariables(rcFile)
    for envVar in envVars:
        os.environ[envVar] = str(envVars[envVar])

    return True