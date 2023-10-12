import threading
from robodk.robolink import *  # API to communicate with RoboDK
import logging


class RDK(threading.Thread):
    def __init__(self, rdk_config):
        print("rdk.py")

        # Наследование потока
        threading.Thread.__init__(self, args=(), name=rdk_config['robotname'] , kwargs=None)

        self.robotname = rdk_config['robotname']
        self.cnt = rdk_config['CNT']
        self.speed = rdk_config['speed']
        self.refresh_time = rdk_config['refresh_time']

        self.inputs_queue = rdk_config['inputs_queue']
        self.outputs_queue = rdk_config['outputs_queue']
        self.axis_act_queue = rdk_config['axis_act_queue']

        # объект логинга
        self.logger = logging.getLogger("_rdk_   ")

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

        self.logger.info(f"CNT {self.cnt}")
        self.logger.info(f"Speed {self.speed}")

        # Communication with controller (OfficeLite)
        while True:
            # rob_axis_act записывается в очередь в krcrpc.py
            robot.setJoints(self.axis_act_queue.queue[0])

            # Чтение входов OL и RoboDK из очереди
            kuka_inputs = self.inputs_queue.queue[0]['kuka_inputs']

            # Write values to RDK
            rdk_outputs = self.outputs_queue.queue[0]['rdk_outputs']
            for output_signal_name, _ in rdk_outputs:
                # print('rdk.py: ' + f'{output_signal_name=} {rdk_outputs.get(output_signal_name)=}')
                RDK.setParam(output_signal_name, int(rdk_outputs.get(output_signal_name)))
                # RDK.setParam('IO_1', 'True')

            # Read values from RDK
            rdk_inputs = self.inputs_queue.queue[0]['rdk_inputs']
            for input_signal_name, _ in rdk_inputs:
                # print('rdk.py: ' + f'{rdk_inputs.get(input_signal_name)=}')
                rdk_inputs.set(input_signal_name, bool(RDK.getParam(input_signal_name)))

            # Запись rdk_outputs
            self.inputs_queue.queue[0] = dict(kuka_inputs=kuka_inputs, rdk_inputs=rdk_inputs)

            time.sleep(self.refresh_time)
