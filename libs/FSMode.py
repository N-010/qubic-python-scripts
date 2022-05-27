import re


fsCode = r"""
////////// Volume \\\\\\\\\\

static constexpr int FS_INDEX = 1;
static volatile EFI_HANDLE* handleBuffer = NULL;

EFI_STATUS getVolumeByIndex(EFI_FILE_PROTOCOL*& root)
{
    EFI_GUID simpleFileSystemProtocolGuid = EFI_SIMPLE_FILE_SYSTEM_PROTOCOL_GUID;

    EFI_STATUS status;
    if (handleBuffer == NULL)
    {
        unsigned long long handleNumber = 0;
        status = bs->LocateHandleBuffer(ByProtocol, &simpleFileSystemProtocolGuid, NULL, &handleNumber, (EFI_HANDLE**)&handleBuffer);
        if (status)
        {
            logStatus(L"EFI_BOOT_SERVICES.LocateHandleBuffer() fails ", status);
            return status;
        }

        CHAR16  Log[256];
        setText(Log, L"handleNumber = ");
        appendNumber(Log, handleNumber, false);
        log(Log);

        if (FS_INDEX >= handleNumber)
        {
            bs->SetMem(Log, sizeof(Log), 0);
            setText(Log, L"FS_INDEX is not valid.");
            appendText(Log, L"FS_INDEX: ");
            appendNumber(Log, FS_INDEX, false);
            appendText(Log, L". Number of disks found: ");
            appendNumber(Log, handleNumber, false);
            log(Log);

            if (handleBuffer)
            {
                bs->FreePool((void*)handleBuffer);
                handleBuffer = NULL;
            }

            return EFI_INVALID_PARAMETER;
        }
    }

    EFI_SIMPLE_FILE_SYSTEM_PROTOCOL* simpleFs = NULL;

    // Get protocol pointer for current volume
    status = bs->HandleProtocol(handleBuffer[FS_INDEX], &simpleFileSystemProtocolGuid, (void**)&simpleFs);
    if (status)
    {
        logStatus(L"EFI_BOOT_SERVICES.HandleProtocol() fails", status);

        return status;
    }

    // Open the volume
    status = simpleFs->OpenVolume(simpleFs, (void**)&root);
    if (status)
    {
        logStatus(L"EFI_SIMPLE_FILE_SYSTEM_PROTOCOL.OpenVolume() fails", status);

        return status;

    }

    return EFI_SUCCESS;
}"""

fsCodeDeinit = r"""
    if (handleBuffer)
    {
        bs->FreePool((void*)handleBuffer);
    }
"""

deinitPointInsert = r"""if (dejavu0)
    {
        bs->FreePool((void*)dejavu0);
    }
"""

fsCodeGetVolume = r"if (status = getVolumeByIndex(root))"


def applyFSMode(cppCode: str) -> str:
    if cppCode.find("getVolumeByIndex") > 0:
        return cppCode

    fsModeReg = re.compile("(endif\n)(\n)*(static BOOLEAN initialize())")
    appliedMode = fsModeReg.sub(rf"\1\n\n{fsCode}\n\n\3", cppCode)

    getVolumeReg = re.compile(
        "if \(status = simpleFileSystemProtocol->OpenVolume\(simpleFileSystemProtocol, \(void\*\*\)\&root\)\)")
    appliedMode = getVolumeReg.sub(fr"{fsCodeGetVolume}", appliedMode)

    pos = appliedMode.find(deinitPointInsert)
    if pos > 0:
        appliedMode = appliedMode[:pos] + \
            f"\n{fsCodeDeinit}\n" + appliedMode[pos:]

    appliedMode = appliedMode.replace(
        r"bs->LocateProtocol(&simpleFileSystemProtocolGuid, NULL, (void**)&simpleFileSystemProtocol);", "")

    return appliedMode
