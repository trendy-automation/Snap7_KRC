Snap7 is an open source, 32/64 bit, multi-platform Ethernet communication suite for interfacing natively with Siemens S7 PLCs.

Python wrapper for the snap7 PLC communication library - [GitHub](https://github.com/gijzelaerr/python-snap7).

Supported data types: String, Char, UInt, USint, Bool.

Packages:
python-snap7 #pip install python-snap7
numpy #pip install numpy
PyYAML #pip install PyYAML

### Инструкция

1. Создать DB для переменных, добавить переменные поддерживаемого типа.
2. В аттрибутах DB отлючить оптимизацию (Optimized block access).
3. В config.yaml прописать IP контроллера и номер блока DB. 
4. В plc.py - *init* прописать переменные с корректными сдвигами (Offset) как в DB.
5. В plc.py - *process_io* добавить переменные для чтения и записи.
6. Запустить main.py.
7. Profit!