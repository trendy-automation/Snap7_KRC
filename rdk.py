import threading

from robodk.robodialogs import *
from robodk.robolink import *  # API to communicate with RoboDK
from queue import Queue
from obj import Obj


class RDK(threading.Thread):
    def __init__(self, rdk_config):
        print("rdk.py")

        # Наследование потока
        threading.Thread.__init__(self, args=(), name=rdk_config['robotname'] , kwargs=None)

        self.robotname = rdk_config['robotname']
        self.cnt = rdk_config['cnt']
        self.speed = rdk_config['speed']

        self.inputs_queue = rdk_config['inputs_queue']
        self.outputs_queue = rdk_config['outputs_queue']

    def run(self):

        # Any interaction with RoboDK must be done through RDK:
        RDK = Robolink()

        robot = RDK.Item(self.robotname)

        # Get the current position of the TCP with respect to the reference frame:
        target_ref = robot.Pose()

        # Move the robot to the first point:
        robot.MoveJ(target_ref)

        # It is important to provide the reference frame and the tool frames when generating programs offline
        robot.setPoseFrame(robot.PoseFrame())
        robot.setPoseTool(robot.PoseTool())
        robot.setRounding(self.cnt)  # Set the rounding parameter (Also known as: CNT, APO/C_DIS, ZoneData, Blending radius, cornering, ...)
        robot.setSpeed(self.speed)  # Set linear speed in mm/s

        # Чтение rdk_inputs
        rdk_inputs = self.inputs_queue.queue[0]['rdk_inputs']
        # Чтение outputs
        kuka_outputs = self.outputs_queue.queue[0]['kuka_outputs']
        rdk_outputs = self.outputs_queue.queue[0]['rdk_outputs']
        # Изменение

        rdk_outputs.RDK_IO_OUT1 = True

        # Запись rdk_outputs
        self.outputs_queue.queue[0] = dict(kuka_outputs=kuka_outputs, rdk_inputs=rdk_outputs)

        '''
        print(self.robotname)
        print(self.cnt)
        print(self.speed)

        '''
        
        # Communication with controller (OfficeLite)
        #while True:
            #robot.setJoints(rob_axis_act) #rob_axis_act стримит krcrpc.py
            