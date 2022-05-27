# BuildQubic.py

## Параметры

Параметры можно посмотреть через `help`: `python BuildQubic.py -h`

### `--freeCpuNum`

В данном параметре указывается сколько ядер освободить от майнинга. Это значение будет вычитаться из `cpu_num`, которое указано в `Settings.json`

## Пример использования

Вначале надо установить зависимости для этого скрипта: `pip3 install -r .\requirements.txt`

Запуск скрипта:
```powershell
python BuildQubic.py --settingsJsonFilePath ".\Settings.json" --slnFilePath "G:\Projects\C++\Qubic\Qubic.sln" --cppFilePath "G:\Projects\C++\Qubic\Qubic\qubic.cpp" --msBuildFilePath "C:\Program Files\Microsoft Visual Studio\2022\Community\Msbuild\Current\Bin\amd64\MSBuild.exe" --freeCpuNum 2
```
### Значения по умолчанию

Чтобы постоянно не указывать значения параметров, их значение можно задать в самом скрипте `BuildQubic.py`.\
Например `--slnFilePath`. Найдите такой код:
```python
parser.add_argument("--slnFilePath", type=pathlib.Path,
                        help="Path to sln file",
                        default=r"G:\Projects\C++\Qubic\Qubic.sln")
```
Здесь надо изменить значение в `default`

# Settings.json

В этом `json` файле указываются настройки для сборки компьютеров. Пример содержимого файла можно найти в файле `Settings.json`

### `InstanceSettings`

Этот объект содержит массив настроек, который включает поля:
1. `seed`
1. `computerId`
1. `cpu_num` - количество ядер, которые будут задействованы майнинге (без вычитания 2)
1. `enable` - если `false`, компьютер с данными настройками не будет собираться