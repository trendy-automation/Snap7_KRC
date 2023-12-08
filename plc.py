import logging
import snap7  # pip install python-snap7
import traceback
import threading
import numpy as np  # pip install numpy
from queue import Queue
import time
import copy
from data_io import Data_IO, Tag


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
        # объект логинга
        self.logger = logging.getLogger("_plc_   ")

        # Создание очереди
        self.inputs_queue = Queue()
        self.outputs_queue = Queue()

        # KUKA IN SIGNALS
        self.kuka_db_in = Data_IO(plc_config['data_io']['kuka_db_in'])

        # KUKA OUT SIGNALS
        self.kuka_db_out = Data_IO(plc_config['data_io']['kuka_db_out'])

        # RDK IN SIGNALS
        self.rdk_db_out = Data_IO(plc_config['data_io']['rdk_db_out'])

        # RDK OUT SIGNALS
        self.rdk_db_in = Data_IO(plc_config['data_io']['rdk_db_in'])

        # Добавление в очередь
        self.inputs_queue.put(dict(kuka_inputs=copy.deepcopy(self.kuka_db_in),
                                   rdk_inputs=copy.deepcopy(self.rdk_db_in)))
        self.outputs_queue.put(dict(kuka_outputs=copy.deepcopy(self.kuka_db_out),
                                    rdk_outputs=copy.deepcopy(self.rdk_db_out)))

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

    def get_bool(self, tag: Tag) -> int:
        tag_data = self.snap7client.db_read(self.db_num, tag.offsetbyte, 1)
        return snap7.util.get_bool(tag_data, 0, tag.offsetbit)
    
    def get_real(self, tag: Tag) -> float:
        tag_data = self.snap7client.db_read(self.db_num, tag.offsetbyte, 4)
        return snap7.util.get_real(tag_data, 0)
    
    def get_usint(self, tag: Tag) -> int:
        byte_array_read = self.snap7client.db_read(self.db_num, tag.offsetbyte, 1)
        return snap7.util.get_usint(byte_array_read, 0)
    
    def get_int(self, tag: Tag) -> int:
        tag_data = self.snap7client.db_read(self.db_num, tag.offsetbyte, self.massa[tag.value_type])
        return snap7.util.get_int(tag_data, 0)
    
    def get_char(self, tag: Tag) -> str:
        return self.snap7client.db_read(self.db_num, tag.offsetbyte, 1).decode()

    def get_string(self, tag: Tag) -> int:
        len_arr = 254 if tag.value_type == 'String' else tag.value_type[7:-1]
        byte_array_read = self.snap7client.db_read(self.db_num, tag.offsetbyte, len_arr)
        return snap7.util.get_string(byte_array_read, 0)

    def get_db_value(self, tag: Tag) -> Tag:
        tag.value = None
        if tag.value_type == 'Bool':
            tag.value = self.get_bool(tag)
        elif tag.value_type == "Real":
            tag.value = self.get_real(tag)
        elif tag.value_type == "USInt":
            tag.value = self.get_usint(tag)
        elif "Int" in tag.value_type and tag.value_type in self.massa:
            tag.value = self.get_int(tag)
        elif tag.value_type == 'Char':
            tag.value = self.get_char(tag)
        elif tag.value_type.startswith('String'):
            tag.value = self.get_string(tag)
        return tag

    def set_bool(self, tag: Tag) -> int:
        tag_data = self.snap7client.db_read(self.db_num, tag.offsetbyte, 1)
        snap7.util.set_bool(tag_data, 0, tag.offsetbit, bool(tag.value))
        return self.snap7client.db_write(self.db_num, tag.offsetbyte, tag_data)

    def set_real(self, tag: Tag) -> int:
        tag_data = bytearray(4)
        snap7.util.set_real(tag_data, 0, tag.value)
        return self.snap7client.db_write(self.db_num, tag.offsetbyte, tag_data)

    def set_usint(self, tag: Tag) -> int:
        tag_data = bytearray(1)
        snap7.util.set_usint(tag_data, 0, tag.value)
        return self.snap7client.db_write(self.db_num, tag.offsetbyte, tag_data)

    def set_int(self, tag) -> int:
        tag_data = bytearray(self.massa[tag.value_type])
        snap7.util.set_int(tag_data, 0, tag.value)
        return self.snap7client.db_write(self.db_num, tag.offsetbyte, tag_data)

    def set_char(self, tag: Tag) -> int:
        tag_data = bytearray(1)
        if tag.value:
            tag_data = bytes(tag.value, "ascii")
        return self.snap7client.db_write(self.db_num, tag.offsetbyte, tag_data)

    def set_string(self, tag) -> int:
        len_arr = 254 if tag.value_type == 'String' else tag.value_type[7:-1]
        # print(f'{tag.value_type=} , {len_arr=}')
        tag.value = f"%.{len_arr}s" % tag.value
        tag_data = bytearray(len_arr + 2)
        snap7.util.set_string(tag_data, 0, tag.value, len_arr)
        tag_data[0] = np.uint8(len_arr)  # np.uint8(len(tag_data)-2)
        tag_data[1] = np.uint8(len(tag.value))
        return self.snap7client.db_write(self.db_num, tag.offsetbyte, tag_data)

    def set_db_value(self, tag: Tag) -> int:
        assert tag.value_type[0] != 'U' or tag.value >= 0, f"Запись отрицательного значения в тип {tag.value_type}"
        if tag.value_type == 'Bool':
            return self.set_bool(tag)
        if tag.value_type == "Real":
            return self.set_real(tag)
        if tag.value_type == "USInt":
            return self.set_usint(tag)
        if "Int" in tag.value_type and tag.value_type in self.massa:
            return self.set_int(tag)
        if tag.value_type == 'Char':
            return self.set_char(tag)
        if tag.value_type.startswith('String'):
            return self.set_string(tag)
        return 0

    def set_signals(self, db: Data_IO):
        for output_signal in db:
            self.set_db_value(output_signal)

    def get_signals(self, db: Data_IO):
        for input_signal in db:
            input_signal = self.get_db_value(input_signal)

    def run(self):
        self.logger.info(f"Connection with PLC {self.plc_ip} started")
        cur_thread = threading.current_thread()

        # Основной цикл
        do_run = getattr(cur_thread, "do_run", True)
        if not do_run:
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
                            self.get_signals(self.kuka_db_in)
                            self.get_signals(self.rdk_db_in)

                        self.process_io()

            except Exception as error:
                self.logger.error(f"Не удалось обработать цикл класса plc\n"
                                  f"Ошибка {str(error)} {traceback.format_exc()}")
            time.sleep(self.refresh_time)

    def process_io(self):
        try:
            # Считывание входных сигналов
            self.get_signals(self.kuka_db_out)
            self.get_signals(self.rdk_db_out)

            self.outputs_queue.queue[0] = dict(kuka_outputs=copy.deepcopy(self.kuka_db_out),
                                               rdk_outputs=copy.deepcopy(self.rdk_db_out))

            inputs = self.inputs_queue.queue[0]
            # self.logger.info(f': {self.kuka_db_out=}')
            # self.logger.info(f': {self.rdk_db_out=}')

            # Сравнение предыдущих значений с текущими (не тратим время на перезапись)
            kuka_inputs = inputs['kuka_inputs']
            if self.kuka_db_in != kuka_inputs:
                self.set_signals(kuka_inputs)
                self.kuka_db_in = copy.deepcopy(kuka_inputs)

            rdk_inputs = inputs['rdk_inputs']
            if self.rdk_db_in != rdk_inputs:
                self.set_signals(rdk_inputs)
                self.rdk_db_in = copy.deepcopy(rdk_inputs)

        except Exception as error:
            self.logger.error(f"Не удалось обработать данные из DB{self.db_num}\n"
                              f"Ошибка {str(error)} {traceback.format_exc()}")
            self.snap7client.disconnect()
