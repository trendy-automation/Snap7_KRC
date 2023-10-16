Snap7 is an open source, 32/64 bit, multi-platform Ethernet communication suite for interfacing natively with Siemens S7 PLCs.

Python wrapper for the snap7 PLC communication library - [GitHub](https://github.com/gijzelaerr/python-snap7).

Supported data types: String, Char, UInt, USint, Bool.

Используемые основные пакеты:
python-snap7    # pip install python-snap7
robodk 5.6.4    # pip install robodk

### Инструкция

1. Создать DB для переменных, добавить переменные поддерживаемого типа для KUKA и RoboDK.
2. В аттрибутах DB отлючить оптимизацию (Optimized block access).
3. Заполнить config.yaml, в data_io прописать корректные сдвиги (offsets) как в DB. 
4. Запустить RoboDK, PLC SIM и OfficeLite. В OfficeLite запустить KRC-RPC.
5. Запустить main.py.

![Alt text](image.png)