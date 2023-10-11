import logging
import queue
import time
import snap7  # pip install python-snap7
import traceback
import threading
import numpy as np  # pip install numpy
from queue import Queue
from obj import Obj

from robodk.robodialogs import *
from robodk.robolink import *  # API to communicate with RoboDK


class PLC(threading.Thread):
    def __init__(self, plc_config):
        print("plc.py")
        
        # Наследование потока
        threading.Thread.__init__(self, args=(), name=plc_config['ip'], kwargs=None)

        # IP аддрес контроллера
        self.plc_ip = plc_config['ip']
        # Номер DB блока с сигналами
        self.db_num = plc_config['db_num']
        # Время переподключения
        self.reconnect_timeout = plc_config['reconnect_timeout']
        # Время обновления
        self.refresh_time = plc_config['refresh_time']

        self.inputs_queue = Queue()
        self.outputs_queue = Queue()

        self.inputs_queue.put(dict(kuka_inputs={}, rdk_inputs={}))
        self.outputs_queue.put(dict(kuka_outputs={}, rdk_outputs={}))

        # KUKA IN SIGNALS
        self.kuka_db_in = Obj({
            # Correct offsets
            "someString": ["", "String", 0, 0],
            "someChar": ["", "Char", 256, 0],
            "someUInt": [0, "UInt", 258, 0],
            "someUSInt": [0, "USInt", 260, 0],
            "someBool": [False, "Bool", 261, 0],
        })

        # KUKA OUT SIGNALS
        self.kuka_db_out = Obj({
            # Correct offsets
            "someString": ["", "String", 0, 0],
            "someChar": ["", "Char", 256, 0],
            "someUInt": [0, "UInt", 258, 0],
            "someUSInt": [0, "USInt", 260, 0],
            "someBool": [False, "Bool", 261, 0],
        })

        # RDK IN SIGNALS
        self.rdk_db_in = Obj({
            "RDK_IO_IN1": [False, "Bool", 262, 0], 
            "RDK_IO_IN2": [False, "Bool", 262, 1],
            "RDK_IO_IN3": [False, "Bool", 262, 2],
            "RDK_IO_IN4": [False, "Bool", 262, 3],
            "RDK_IO_IN5": [False, "Bool", 262, 4],
            "RDK_IO_IN6": [False, "Bool", 262, 5],
            "RDK_IO_IN7": [False, "Bool", 262, 6],
            "RDK_IO_IN8": [False, "Bool", 262, 7],
            "RDK_IO_IN9": [False, "Bool", 263, 0],
            "RDK_IO_IN10": [False, "Bool", 263, 1],
        })

        # RDK OUT SIGNALS
        self.rdk_db_out = Obj({
            "RDK_IO_OUT1": [False, "Bool", 264, 0],
            "RDK_IO_OUT2": [False, "Bool", 264, 1],
            "RDK_IO_OUT3": [False, "Bool", 264, 2],
            "RDK_IO_OUT4": [False, "Bool", 264, 3],
            "RDK_IO_OUT5": [False, "Bool", 264, 4],
            "RDK_IO_OUT6": [False, "Bool", 264, 5],
            "RDK_IO_OUT7": [False, "Bool", 264, 6],
            "RDK_IO_OUT8": [False, "Bool", 264, 7],
            "RDK_IO_OUT9": [False, "Bool", 265, 0],
            "RDK_IO_OUT10": [False, "Bool", 265, 1]
        })

        # объект логинга
        self.logger = logging.getLogger("_plc_.client")
        # logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

        # библиотека для связи с PLC
        self.snap7client = snap7.client.Client()
        # статус подключения к контроллеру
        self.connection_ok = False
        # Время, в течении которого контроллер был недоступен
        self.unreachable_time = 0

        self.massa = {
            "UInt": 2,
            "Int": 2,
            "DInt": 4
        }

    def get_bool(self, db_number, offsetbyte, offsetbit) -> int:
        tag_data = self.snap7client.db_read(db_number, offsetbyte, 1)
        return snap7.util.get_bool(tag_data, 0, offsetbit)
    
    def get_real(self, db_number, offsetbyte) -> float:
        tag_data = self.snap7client.db_read(db_number, offsetbyte, 4)
        return snap7.util.get_real(tag_data, 0)
    
    def get_usint(self, db_number, offsetbyte) -> int:
        byte_array_read = self.snap7client.db_read(db_number, offsetbyte, 1)
        return snap7.util.get_usint(byte_array_read, 0)
    
    def get_int(self, db_number, offsetbyte, value_type) -> int:
        tag_data = self.snap7client.db_read(db_number, offsetbyte, self.massa[value_type])
        return snap7.util.get_int(tag_data, 0)
    
    def get_char(self, db_number, offsetbyte) -> str:
        return self.snap7client.db_read(db_number, offsetbyte, 1).decode()

    def get_string(self, db_number, offsetbyte, value_type) -> int:
        len_arr = 254 if value_type == 'String' else value_type[7:-1]
        byte_array_read = self.snap7client.db_read(db_number, offsetbyte, len_arr)
        return snap7.util.get_string(byte_array_read, 0)

    def get_db_value(self, tag_list: list) -> list:
        value, value_type, offsetbyte, offsetbit = tag_list
        if value_type == 'Bool':
            return [self.get_bool(self.db_num, offsetbyte, offsetbit), value_type, offsetbyte, offsetbit]
        if value_type == "USInt":
            return [self.get_usint(self.db_num, offsetbyte), value_type, offsetbyte, offsetbit]
        if "Int" in value_type and value_type in self.massa:
            return [self.get_int(self.db_num, offsetbyte, value_type), value_type, offsetbyte, offsetbit]
        if value_type == 'Char':
            return [self.get_char(self.db_num, offsetbyte), value_type, offsetbyte, offsetbit]
        if value_type.startswith('String'):
            return [self.get_string(self.db_num, offsetbyte, value_type), value_type, offsetbyte, offsetbit]
        return None

    def set_bool(self, db_number, offsetbyte, offsetbit, tag_value) -> int:
        tag_data = self.snap7client.db_read(db_number, offsetbyte, 1)
        snap7.util.set_bool(tag_data, 0, offsetbit, bool(tag_value))
        return self.snap7client.db_write(db_number, offsetbyte, tag_data)

    def set_real(self, db_number, offsetbyte, tag_value) -> int:
        tag_data = bytearray(4)
        snap7.util.set_real(tag_data, 0, tag_value)
        return self.snap7client.db_write(db_number, offsetbyte, tag_data)

    def set_usint(self, db_number, offsetbyte, tag_value) -> int:
        tag_data = bytearray(1)
        snap7.util.set_usint(tag_data, 0, tag_value)
        return self.snap7client.db_write(db_number, offsetbyte, tag_data)

    def set_int(self, db_number, offsetbyte, tag_value, value_type) -> int:
        tag_data = bytearray(self.massa[value_type])
        assert value_type[1]!='U' or tag_value>=0, f"Запись отрицательного значения в тип {value_type}"
        snap7.util.set_int(tag_data, 0, tag_value)
        return self.snap7client.db_write(db_number, offsetbyte, tag_data)

    def set_char(self, db_number, offsetbyte, tag_value) -> int:
        tag_data = bytearray(1)
        tag_data = bytes(tag_value[0], "ascii")
        return self.snap7client.db_write(db_number, offsetbyte, tag_data)

    def set_string(self, db_number, offsetbyte, tag_value, value_type) -> int:
        len_arr = 254 if value_type == 'String' else value_type[7:-1]
        tag_value = f"%.{len_arr}s" % tag_value
        tag_data = bytearray(len_arr + 2)
        snap7.util.set_string(tag_data, 0, tag_value, len_arr)
        tag_data[0] = np.uint8(len_arr) #np.uint8(len(tag_data)-2)
        tag_data[1] = np.uint8(len(tag_value))      
        return self.snap7client.db_write(db_number, offsetbyte, tag_data)

    def set_db_value(self, tag_list: list) -> int:
        tag_value, value_type, offsetbyte, offsetbit = tag_list
        if value_type == 'Bool':
            return self.set_bool(self.db_num, offsetbyte, offsetbit, tag_value)
        if value_type == "USInt":
            return self.set_usint(self.db_num, offsetbyte, tag_value)
        if "Int" in value_type and value_type in self.massa:
            return self.set_int(self.db_num, offsetbyte, tag_value, value_type)
        if value_type == 'Char':
            return self.set_char(self.db_num, offsetbyte, tag_value)
        if value_type.startswith('String'):
            return self.set_string(self.db_num, offsetbyte, tag_value, value_type)
        return 0

    def set_signals(self, db: Obj):
        for output_signal in db:
            self.set_db_value(output_signal)
        #for output_signal in db.signals():
        #    self.set_db_value(db.get(output_signal))

    def get_signals(self, db: Obj):
        for input_signal in db:
            #print(f'{input_signal=}')
            input_signal = self.get_db_value(input_signal)

    def run(self):
        self.logger.info(f"Connection with PLC {self.plc_ip} started")
        cur_thread = threading.current_thread()
        # Основной цикл
        do_run = getattr(cur_thread, "do_run", True)
        if do_run==False:
            self.snap7client.disconnect()
        while do_run:
            try:
                if self.unreachable_time == 0 or (time.time() - self.unreachable_time) > self.reconnect_timeout:
                    if not self.snap7client.get_connected():
                        # Подключение к контроллеру ...
                        try:
                            self.connection_ok = False
                            self.logger.info(f"Подключение к контроллеру {self.plc_ip}...")
                            self.snap7client.connect(self.plc_ip, 0, 1)
                        except Exception as error:
                            self.logger.error(f"Не удалось подключиться к контроллеру: {self.plc_ip}\n"
                                              f"Ошибка {str(error)} {traceback.format_exc()}")
                            snap7.client.logger.disabled = True
                            self.unreachable_time = time.time()
                    else:
                        if not self.connection_ok:
                            self.connection_ok = True
                            self.unreachable_time = 0
                            self.logger.info(f"Соединение открыто {self.plc_ip}")
                            snap7.client.logger.disabled = False

                        self.process_io()

            except Exception as error:
                self.logger.error(f"Не удалось обработать цикл класса plc\n"
                                  f"Ошибка {str(error)} {traceback.format_exc()}")
            time.sleep(self.refresh_time)

    def process_io(self):

        try:
            self.get_signals(self.kuka_db_in)
            self.get_signals(self.rdk_db_in)

            self.inputs_queue.queue[0] = dict(kuka_inputs=self.kuka_db_in, rdk_inputs=self.rdk_db_in)

            outputs = self.outputs_queue.queue[0]
            kuka_outputs = outputs['kuka_outputs']
            rdk_outputs = outputs['rdk_outputs']

            if self.kuka_db_out != kuka_outputs:
                self.set_signals(self.kuka_db_out)
            if self.rdk_db_out != rdk_outputs:
                self.set_signals(self.rdk_outputs)

        except Exception as error:
            self.logger.error(f"Не удалось обработать данные из DB{self.db_num}\n"
                              f"Ошибка {str(error)} {traceback.format_exc()}")
            self.snap7client.disconnect()

