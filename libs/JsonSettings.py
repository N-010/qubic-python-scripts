from genericpath import exists
import json
import re
import aiofiles


class JsonSettings(object):
    def __init__(self: str,
                 seed: str,
                 computerId: str,
                 operatorId: str,

                 #Network
                 ownAddress: str,
                 ownMask: str,
                 defaultRouteGateway: str,
                 ownPublicAddress:str,

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
        # Network
        self.ownAddress = ownAddress
        self.ownMask = ownMask
        self.defaultRouteGateway = defaultRouteGateway 
        self.ownPublicAddress = ownPublicAddress 

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

        # Openstack
        try:
            region = Settings["region"]
        except KeyError:
            region = ""

        # Network
        try:
            ownAddress = Settings["ownAddress"]
        except KeyError:
            ownAddress = str("0.0.0.0")
        try:
            ownMask = Settings["ownMask"]
        except KeyError:
            ownMask = str("255.255.255.255")
        try:
            defaultRouteGateway = Settings["defaultRouteGateway"]
        except KeyError:
            defaultRouteGateway = str("0.0.0.0")
        try:
            ownPublicAddress = Settings["ownPublicAddress"]
        except KeyError:
            ownPublicAddress = str("0.0.0.0")

        try:
            is_computer = Settings["computer"]
        except:
            is_computer = str("false")

        instanceSettingsList.append(JsonSettings(
            seed=Settings["seed"], computerId=Settings["computerId"],
            operatorId=operatorId, ownAddress=ownAddress, ownMask=ownMask, 
            defaultRouteGateway=defaultRouteGateway, ownPublicAddress=ownPublicAddress, 
            tick=tick, region=region, cpuNum=cpuNum, is_enable=Settings["enable"], 
            is_computer=is_computer, knownPublicPeers=knownPublicPeers))

    return instanceSettingsList
