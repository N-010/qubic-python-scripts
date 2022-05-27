from genericpath import exists
import json
import re
import aiofiles


class JsonSettings(object):
    def __init__(self: str,
                 seed: str,
                 computerId: str,
                 operatorId: str,
                 tick: str,
                 region: str,
                 cpuNum: str,
                 is_enable: str,
                 is_computer: str,
                 knownPublicPeers: list[str]):
        self.seed = seed
        self.computerId = computerId
        self.operatorId = operatorId
        self.tick = tick
        self.region = region
        self.cpuNum = cpuNum
        # self.ownAddress = ownAddress
        # self.ownMask = ownMask
        self.is_enable: bool = is_enable.lower() == "true".lower()
        self.is_computer: bool = is_computer.lower() == "true".lower()
        self.knownPublicPeers = knownPublicPeers


async def getSettings(jsonFile) -> list[JsonSettings]:
    if exists(jsonFile) == False:
        print(F"{jsonFile} is not exist")
        return [JsonSettings()]

    async with aiofiles.open(jsonFile, "r") as jsonFile:
        jsonFileContent = await jsonFile.read()

    jsonData = json.loads(jsonFileContent)
    jsonSettingsList = jsonData["InstanceSettings"]
    operatorId = jsonData["operatorId"]
    knownPublicPeers = jsonData["known_public_peers"]

    instanceSettingsList: list[JsonSettings] = []
    flavorRe = re.compile(".*-.*-.*")
    for Settings in jsonSettingsList:
        try:
            flavor_name = Settings["flavor_name"]
            if flavorRe.findall(flavor_name).__len__() > 0:
                cpuNum = str(Settings["flavor_name"]).split('-')[-1]
            else:
                raise KeyError
        except KeyError:
            try:
                cpuNum = str(Settings["cpu_num"])
            except KeyError:
                cpuNum = str(0)

        try:
            tick = str(Settings["tick"])
        except KeyError:
            tick = str(2500000)

        try:
            region = Settings["region"]
        except KeyError:
            region = ""

        try:
            is_computer = Settings["computer"]
        except:
            is_computer = str("false")

        instanceSettingsList.append(JsonSettings(
            Settings["seed"], Settings["computerId"],
            operatorId, tick, region,
            cpuNum, Settings["enable"], is_computer, knownPublicPeers))

    return instanceSettingsList
