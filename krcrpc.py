import threading
import logging
import traceback
import socket
import time
import json
import re
from queue import Queue
from obj import Obj

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

        # объект логинга
        self.logger = logging.getLogger("_krcrpc_.client")
        # logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

        # Сокет для связи с KRC RPC
        self.socketclient = socket.socket()
        # Статус подключения к KRC RPC
        self.connection_ok = False
        # Время, в течении которого KRC RPC был недоступен
        self.unreachable_time = 0

    def run(self):
        self.logger.info(f"Connection with KRC RPC {self.krc_hostname} started")
        cur_thread = threading.current_thread()
        # Основной цикл
        do_run = getattr(cur_thread, "do_run", True)
        if do_run==False:
            self.socketclient.close()


        # Подключение к KRC RPC ...
        try:
            self.logger.info(f"Подключение к KRC RPC {self.krc_hostname}...")
            self.socketclient.connect((self.krc_hostname, self.krc_port))
    
            # Authentication
            message = ("{'method':'auth','params':['" + self.krc_authkey + "'],'id':1}\n").encode()
            print(">>>\t", message)
            self.socketclient.send(message)
            print("<<<\t", self.socketclient.recv(1024))

            # Robot name
            message = "{'method':'Var_ShowVar','params':['$TRAFONAME[]'],'id':2}\n".encode()
            print(">>>\t", message)
            self.socketclient.send(message)
            print("<<<\t", self.socketclient.recv(1024))
            print('')

        except Exception as error:
            self.logger.error(f"Не удалось подключиться к KRC RPC: {self.krc_hostname}\n"
                                f"Ошибка {str(error)} {traceback.format_exc()}")
            #??
            #socket.client.logger.disabled = True
            self.unreachable_time = time.time()


        while do_run:
            try:
                if self.unreachable_time == 0 or (time.time() - self.unreachable_time) > self.reconnect_timeout:
                    
                    # Check if socket closed
                    #self.socketclient.close()
                    # print(self.socketclient._closed)

                    '''
                    if not self.socketclient._closed:
                        # Подключение к KRC RPC ...
                        try:
                            self.connection_ok = False
                            self.logger.info(f"Подключение к KRC RPC {self.krc_hostname}...")
                            #self.socketclient.connect((self.krc_hostname, self.krc_port))
                            self.socketclient.connect(('PCRC-2RL7HHTTRE', 3333))

                            # Authentication
                            #message = "{'method':'auth','params':['" + self.krc_authkey + "'],'id':1}\n".encode()
                            message = "{'method':'auth','params':['TOP_SECRET_KEY'],'id':1}\n".encode()
                            print(">>>\t", message)
                            self.socketclient.send(message)
                            print("<<<\t", self.socketclient.recv(1024))

                            # Robot name
                            message = "{'method':'Var_ShowVar','params':['$TRAFONAME[]'],'id':2}\n".encode()
                            print(">>>\t", message)
                            self.socketclient.send(message)
                            print("<<<\t", self.socketclient.recv(1024))

                        except Exception as error:
                            self.logger.error(f"Не удалось подключиться к KRC RPC: {self.krc_hostname}\n"
                                              f"Ошибка {str(error)} {traceback.format_exc()}")
                            #??
                            #socket.client.logger.disabled = True
                            self.unreachable_time = time.time()
                    else:
                        if not self.connection_ok:
                            self.connection_ok = True
                            self.unreachable_time = 0
                            self.logger.info(f"Соединение открыто {self.krc_hostname}")
                            #??
                            #socket.client.logger.disabled = False
                       
                        self.process_krc_rpc()
                    '''

                self.process_krc_rpc()

            except Exception as error:
                self.logger.error(f"Не удалось обработать цикл класса KRCRPC\n"
                                  f"Ошибка {str(error)} {traceback.format_exc()}")
            time.sleep(1)

    # Communication with KRC RPC (OfficeLite)
    def process_krc_rpc(self):
    
        try:
            #----------------------------------------------------------
            # VARIABLES
            #----------------------------------------------------------
            '''
            # WRITE LaserTrigg var to TRUE
            message = ("{'method':'Var_SetVar','params':['LaserTrigg','false'],'id':2}\n").encode()
            print(">>>\t", message)
            self.socketclient.send(message)
            response_bytes = self.socketclient.recv(1024)
            print("<<<\t", response_bytes)
            '''
        
            #----------------------------------------------------------
            # MOTION
            #----------------------------------------------------------
            
            # response from socket client (bytes)
            #start_time = time.time()
            message = "{'method':'Var_ShowVar','params':['$AXIS_ACT'],'id':3}\n".encode()
            #print(">>>\t", message)
            self.socketclient.send(message)
            response_bytes = self.socketclient.recv(1024)
            #print("<<<\t", response_bytes)
            #print("--- response time: %s seconds ---" % (time.time() - start_time))

            ### RESPONSE PARSING ###
            # convert bytes to str
            response_str = response_bytes.decode('UTF-8')

            # convert str to json
            response_json = json.loads(response_str)

            # split only axis value by <:>
            raw_axis_act = re.split(': A1 |, A\d |, E\d ', response_json['result'])

            #4 cut and convert string to float
            rob_axis_act = [float(axis) for axis in raw_axis_act[1:9]]
            print(f'{rob_axis_act=}')
            print(' ')

        except Exception as error:
            self.logger.error(f"Не удалось получить данные из KRC RPC\n"
                              f"Ошибка {str(error)} {traceback.format_exc()}")
            self.socketclient.close()
        