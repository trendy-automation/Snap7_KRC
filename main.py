from plc import PLC
from krcrpc import KRCRPC
from rdk import RDK
import yaml  # pip install PyYAML
import os
import sys
import logging
from logging import handlers

def start_logging(logger_level, logger_debug_file, logger_format):
    # logger
    logging.basicConfig(level=logger_level,
                        handlers=[logging.StreamHandler(sys.stdout),
                                  logging.handlers.RotatingFileHandler(logger_debug_file,
                                                                       maxBytes=(1048576 * 5),
                                                                       backupCount=7)],
                        format=logger_format)


if __name__ == '__main__':
    csd = os.path.dirname(os.path.abspath(__file__))
    config = yaml.safe_load(open(csd + "/config.yaml"))

    logger_level = config['logger']['level']
    logger_debug_file = config['logger']['debug_file']
    logger_format = config['logger']['format']

    start_logging(logger_level, logger_debug_file, logger_format)

    # PLC thread
    plc_config = config['plc']
    my_plc = PLC(plc_config)
    my_plc.start()

    # KRC RPC thread
    krc_rpc_config = config['krc_rpc']
    krc_rpc_config['inputs_queue'] = my_plc.inputs_queue
    krc_rpc_config['outputs_queue'] = my_plc.outputs_queue
    krc_rpc = KRCRPC(krc_rpc_config)
    krc_rpc.start()

    # Передаем rob_axis_act между потоками через очередь
    axis_act_queue = krc_rpc.axis_act_queue

    # RoboDK thread
    # rdk_config = config['robodk']
    # rdk_config['inputs_queue'] = my_plc.inputs_queue
    # rdk_config['outputs_queue'] = my_plc.outputs_queue
    # rdk_config['axis_act_queue'] = krc_rpc.axis_act_queue
    # rdk = RDK(rdk_config)
    # rdk.start()
