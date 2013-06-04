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
        self.dispatcher=AsynchDispatch(sinks={'telem_data':[self.telem_data_received]},
                                       callbacks={'packet':[self.packet_received]})

    def put(self, message):
        self.dispatcher.put(message)

    def send_packet(self, type, data=''):
        if self.transport is not None:
            pkt = Packet(type,data,0,0,time=(time.time()-self.last_time))
            self.transport.put(Message('packet',pkt))

    def set_thrust_open_loop(self, left, right):
        thrust = [left, right, 200] #TODO 200?
        self.send_packet('SET_THRUST_OPEN_LOOP', struct.pack("3h", *thrust))

    def packet_received(self, message):
        pkt = message.data
        p = Protocol()
        if pkt.pkt_type is p.find('SPECIAL_TELEMETRY').value:
            self.dispatcher.dispatch(Message('telem_data', pkt))

    def telem_data_received(self, message):
        payload = message.data.data
        pattern = '=LLll'+13*'h'
        data = struct.unpack(pattern, payload)
        print "data=" + str(data)
