import struct
import time
from imageproc_py.stream.asynch_dispatch import *
from imageproc_py.protocol.packet import *
from imageproc_py.protocol.protocol import *

class UARTRobotStream():

    """
    Similar to a RobotStream.
    Should be transport agnostic, but tested for UART.
    """
    def __init__(self, transport=None):
        self.transport = transport
        self.last_time = time.time()

    def send_packet(self, type, data=''):
        if self.transport is not None:
            pkt = Packet(type,data,0,0,time=(time.time()-self.last_time))
            self.transport.put(Message('packet',pkt))

    def set_thrust_open_loop(self, left, right):
        thrust = [left, right, 200] #TODO 200?
        self.send_packet('SET_THRUST_OPEN_LOOP', struct.pack("3h", *thrust))

