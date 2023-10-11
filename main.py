from plc import PLC
from krcrpc import KRCRPC
from rdk import RDK
import yaml #pip install PyYAML
import os
from queue import Queue

if __name__ == '__main__':
    csd = os.path.dirname(os.path.abspath(__file__))
    config = yaml.safe_load(open(csd + "/config.yaml"))
    
    # PLC thread
    plc_config = config['plc']

    my_plc = PLC(plc_config)
    my_plc.start()

    # KRC RPC thread
    krc_rpc_config = config['krc_rpc']

    krc_rpc = KRCRPC(krc_rpc_config)
    krc_rpc.start()

    # RoboDK thread
    robotname = config['robodk']['robotname']
    cnt = config['robodk']['CNT']
    speed = config['robodk']['speed']

    rdk = RDK(robotname, cnt, speed)
    rdk.start()
