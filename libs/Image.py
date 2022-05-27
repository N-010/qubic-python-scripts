from io import BytesIO
import os
from pathlib import Path
import pycdlib
import fs
from fs.opener import fsopendir


def list_files(startpath):
    for root, dirs, files in os.walk(startpath):
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * (level)
        print('{}{}/'.format(indent, os.path.basename(root)))
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            print('{}{}'.format(subindent, f))


def create_iso_from_folder(folder_path: Path):
    iso = pycdlib.PyCdlib()
    iso.new(udf='2.60')
    # bootstr = b'boot\n'
    # iso.add_fp(BytesIO(bootstr), len(bootstr), '/BOOT.;1')
    isolinuxstr = b'\x00'*0x40 + b'\xfb\xc0\x78\x70'
    iso.add_fp(BytesIO(isolinuxstr), len(isolinuxstr), '/BOOT.;1')
    for root, dirs, files in os.walk(folder_path):
        rootFolder = os.path.relpath(root, folder_path)
        # print(os.path.normpath(rootFolder))
        for dir in dirs:
            folder = '/' + \
                os.path.normpath(os.path.join(rootFolder, dir))
            folder = folder.replace("\\", "/")
            iso.add_directory(udf_path=folder)
        for file in files:
            iso_file_path = '/' + \
                os.path.normpath(os.path.join(rootFolder, file))
            iso_file_path = iso_file_path.replace('\\', '/')
            print(iso_file_path)
            iso.add_file(os.path.join(root, file), udf_path=iso_file_path)
            print()

    # iso.add_eltorito('/BOOT.;1', efi=True, boot_info_table=True,
    #                  platform_id=0xef, media_name="hdemul")
    iso.add_eltorito('/BOOT.;1', boot_load_size=4, media_name="noemul")
    iso.add_isohybrid()
    iso.write('test.iso')
    iso.close()


def main():
    # iso = pycdlib.PyCdlib()
    # iso.new(udf='2.60')
    # test_file = "requirements.txt"
    # print(os.stat(test_file))
    # iso.add_directory(udf_path="/dir")
    # iso.add_file("requirements.txt", udf_path=f"/{test_file.upper()}")
    # iso.write("test.iso")
    # iso.close()
    # return


    app_fs = fs.opener.open_fs("test_dir.img", create_dir=True)

    # imgFolderPath: Path = r"G:\Programs\Qubic\Vexxhost\Imgs\ha"
    # create_iso_from_folder(imgFolderPath)
    return

    foostr = b'foo\n'
    print(foostr)
    iso.add_fp(BytesIO(foostr), len(foostr), '/FOO.;1')

    iso.add_directory('/DIR1')

    iso.write('new.iso')
    iso.close()


if __name__ == "__main__":
    main()
