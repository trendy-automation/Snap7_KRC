import threading
import logging
import traceback
import socket
import time
import json
import re
from queue import Queue
#from obj import Obj


class KRCRPC(threading.Thread):
    def __init__(self, krc_rpc_config):
        print("krcrpc.py")

        # Наследование потока
        threading.Thread.__init__(self, args=(), name=krc_rpc_config['hostname'], kwargs=None)

        # Hostname компа с OfficeLite
        self.krc_hostname = krc_rpc_config['hostname']
        # Порт OfficeLite
        self.krc_port = krc_rpc_config['port']
        # Аутентификация по ключу
        self.krc_authkey = krc_rpc_config['authkey']
        # Время переподключения
        self.reconnect_timeout = krc_rpc_config['reconnect_timeout']
        # Время обновления
        self.refresh_time = krc_rpc_config['refresh_time']

        self.inputs_queue = krc_rpc_config['inputs_queue']
        self.outputs_queue = krc_rpc_config['outputs_queue']
        self.axis_act_queue = Queue()
        self.axis_act_queue.put([0**8])

        # объект логинга
        self.logger = logging.getLogger("_krcrpc_")
        # logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

        # Статус подключения к KRC RPC
        self.connection_ok = False
        # Время, в течении которого KRC RPC был недоступен
        self.unreachable_time = 0

    def run(self):
        self.logger.info(f"Connection with KRC RPC {self.krc_hostname} started")
        cur_thread = threading.current_thread()
        # Основной цикл
        do_run = getattr(cur_thread, "do_run", True)
        if not do_run:
            self.socketclient.close()
            self.connection_ok = False

        while do_run:
            try:
                if self.unreachable_time == 0 or (time.time() - self.unreachable_time) > self.reconnect_timeout:
                    if not self.connection_ok:
                        # Подключение к KRC RPC ...
                        try:
                            #self.connection_ok = False
                            self.logger.info(f"Подключение к KRC RPC {self.krc_hostname}...")
                            # Сокет для связи с KRC RPC
                            self.socketclient = socket.socket(socket.AF_INET,
                                                              socket.SOCK_STREAM)  # , socket.SO_REUSEADDR
                            self.socketclient.connect((self.krc_hostname, self.krc_port))

                            self.connection_ok = True
                            self.unreachable_time = 0
                            self.logger.info(f"Соединение открыто {self.krc_hostname}")

                            # Authentication
                            message = ("{'method':'auth','params':['" + self.krc_authkey + "'],'id':1}\n").encode()
                            self.socketclient.send(message)
                            self.logger.info(f"Auth {self.socketclient.recv(1024)}")

                            # Robot name
                            message = "{'method':'Var_ShowVar','params':['$TRAFONAME[]'],'id':2}\n".encode()
                            self.socketclient.send(message)
                            self.logger.info(f"Robot name: {self.socketclient.recv(1024)}")

                        except Exception as error:
                            self.logger.error(f"Не удалось подключиться к KRC RPC: {self.krc_hostname}\n"
                                              f"Ошибка {str(error)} {traceback.format_exc()}")

                            self.connection_ok = False
                            self.unreachable_time = time.time()
                    else:
                        self.process_krc_rpc()

            except Exception as error:
                self.logger.error(f"Не удалось обработать цикл класса KRCRPC\n"
                                  f"Ошибка {str(error)} {traceback.format_exc()}")
                self.socketclient.close()
                self.connection_ok = False

            time.sleep(self.refresh_time)

    # Communication with KRC RPC (OfficeLite)
    def process_krc_rpc(self):
        try:
            # ----------------------------------------------------------
            # VARIABLES
            # ----------------------------------------------------------
            
            # Чтение kuka_outputs
            kuka_outputs = self.outputs_queue.queue[0]['kuka_outputs']

            # Чтение inputs
            kuka_inputs = self.inputs_queue.queue[0]['kuka_inputs']
            rdk_inputs = self.inputs_queue.queue[0]['rdk_inputs']

            # Write values to OfficeLite
            # for output_signal in kuka_outputs:
            #     OL.setParam(output_signal.name, int(output_signal.value))

            # Read values from OfficeLite
            # for input_signal in kuka_inputs:
            #     input_signal.value = OL.getParam(input_signal.name)

            # -------
            # BOOL
            # -------

            # Write BOOL OfficeLite --> DB [261] //DECL GLOBAL BOOL someBool_OUT = FALSE
            if "someBool" in kuka_inputs.signals():
                kuka_inputs.someBool = self.Bool_ShowVar('someBool_OUT')
                self.logger.info(f"someBool_OUT OL --> DB {kuka_inputs.someBool=}...")

            # Write BOOL DB ->> OfficeLite [527] //DECL GLOBAL BOOL someBool_IN = FALSE
            if "someBool" in kuka_outputs.signals():
                self.Bool_SetVar('someBool_IN', str(kuka_outputs.someBool[0]))
                self.logger.info(f"someBool_IN DB --> OL {kuka_outputs.someBool=}...")

            # -------
            # INT
            # -------

            # Write INT to DB
            # DECL GLOBAL INT someUInt = 0
            if "someUInt" in kuka_inputs.signals():
                # print('krcrpc.py: ' + f'{kuka_inputs.someUInt=}')
                kuka_inputs.someUInt = 223  # must be value from OfficeLite

            self.inputs_queue.queue[0] = dict(kuka_inputs=kuka_inputs, rdk_inputs=rdk_inputs)

            '''
            # WRITE LaserTrigg var to TRUE
            message = ("{'method':'Var_SetVar','params':['LaserTrigg','false'],'id':2}\n").encode()
            print('krcrpc.py: ' + ">>>\t", message)
            self.socketclient.send(message)
            response_bytes = self.socketclient.recv(1024)
            print('krcrpc.py: ' + "<<<\t", response_bytes)
            '''

            # ----------------------------------------------------------
            # MOTION VISUALIZATION VIA $AXIS_ACT
            # ----------------------------------------------------------

            # response from socket client (bytes)
            message = "{'method':'Var_ShowVar','params':['$AXIS_ACT'],'id':3}\n".encode()
            # print('krcrpc.py: ' + ">>>\t", message)
            self.socketclient.send(message)
            response_bytes = self.socketclient.recv(1024)
            # print('krcrpc.py: ' + "<<<\t", response_bytes)

            # RESPONSE PARSING
            # convert bytes to str
            response_str = response_bytes.decode('UTF-8')
            # convert str to json
            response_json = json.loads(response_str)
            # split only axis value by <:>
            raw_axis_act = re.split(': A1 |, A\d |, E\d ', response_json['result'])
            # cut and convert string to float
            rob_axis_act = [float(axis) for axis in raw_axis_act[1:9]]

            # Запись rob_axis_act в очередь
            self.axis_act_queue.queue[0] = rob_axis_act
            # print(f'{rob_axis_act=}')

        except Exception as error:
            self.logger.error(f"Не удалось получить данные из KRC RPC\n"
                              f"Ошибка {str(error)} {traceback.format_exc()}")
            self.socketclient.close()
            self.connection_ok = False
            # self.unreachable_time = time.time()

    def Bool_SetVar(self, var_name, var_value):
        message = ("{'method':'Var_SetVar','params':['" + var_name + "','" + var_value + "'],'id':3}\n").encode()
        self.socketclient.send(message)
        response_bytes = self.socketclient.recv(1024)
        # print('krcrpc.py: ' + "<<<\t", response_bytes)

    def Bool_ShowVar(self, var_name):
        message = ("{'method':'Var_ShowVar','params':['" + var_name + "'],'id':3}\n").encode()
        self.socketclient.send(message)
        response_bytes = self.socketclient.recv(1024)
        # print('krcrpc.py: ' + "<<<\t", response_bytes)

        # RESPONSE PARSING
        # convert bytes to str
        response_str = response_bytes.decode('UTF-8')
        # convert str to json
        response_json = json.loads(response_str)
        # split only axis value by <:>
        var_value = response_json['result']
        if var_value == 'FALSE':
            var_value = False
        if var_value == 'TRUE':
            var_value = True
        return var_value
