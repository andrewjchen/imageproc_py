import threading
import serial
import time
import struct
import binascii
from imageproc_py.stream.serial_stream import *
from imageproc_py.protocol.packet import *

class SerialCommState:
        Length, ChLength, Data, Checksum = range(4)

class ImageprocUARTStream(threading.Thread):
    """
    Similar to a BasestationStream: receives packets and sends them to the imagerproc.
    """
    SerialCommState = SerialCommState.Length
    lengthToGo = 0
    data = ""
    lengthbyte = 0
    lengthCheck = 0

    def __init__(self,
                 port='/dev/ttyUSB0',
                 baud='1000000',
                 timeout=0.1,
                 sinks=None,
                 autoStart=True):

        threading.Thread.__init__(self)
        self.daemon = True

        try:
            self.serial = serial.Serial(port,baud,timeout=timeout)
            self.serial.open()
        except:
            print 'Failed to open serial port at %s' % port.__str__()
            self.serial = None

        if autoStart:
            self.start()

        self.dispatcher=AsynchDispatch(sinks=sinks,
                                       callbacks={'packet':[self.send]})


    def run(self):
        if self.serial is not None:
            while(True):
                self.poll()

    def poll(self):
        #print "polling"
        if self.SerialCommState is SerialCommState.Length:
            val = self.serial.read(1)
            if len(val) is 1:
                self.lengthByte = ord(val)
                self.SerialCommState = SerialCommState.ChLength
                #print "length=" + str(self.lengthByte)
        elif self.SerialCommState is SerialCommState.ChLength:
            self.lengthCheck = ord(self.serial.read(1))
            #print "lengthcheck=" + str(self.lengthCheck)
            if self.lengthByte + self.lengthCheck is 0xff:
                self.SerialCommState = SerialCommState.Data
                self.lengthToGo = self.lengthByte - 3
            else:
                self.SerialCommState = SerialCommState.ChLength
                self.lengthByte = self.lengthCheck
        elif self.SerialCommState is SerialCommState.Data:
            if self.lengthToGo > 0:
                self.data = self.data + self.serial.read(1)
                #print "data so far:" + self.data
                self.lengthToGo = self.lengthToGo - 1
            else:
                self.SerialCommState = SerialCommState.Checksum
        elif self.SerialCommState is SerialCommState.Checksum:
            checksum = ord(self.serial.read(1))
            sum = 0xff
            for c in self.data:
                sum = sum + ord(c)
            sum = sum & 0xff
            if checksum is sum:
                p = Packet(payload=self.data)
                #print("received packet=" + str(p))
                self.dispatcher.dispatch(Message("packet", p))
                self.data = ""
            self.SerialCommState = SerialCommState.Length

    def serial_payload(self, data):
        """length, bitwise flip length, data, checksum"""

        # + 3 for the length, ~length, and checksum
        length = len(data) + 3
        datalengthCompliment = ~length if ~length >= 0 else ~length + 256
        payload = chr(length) + chr(datalengthCompliment) + ''.join(data)
        sum = 0xff
        for c in data:
            sum = sum + ord(c)
        sum  = sum & 0xff
        return payload + chr(sum)

    def send(self, message):
        if self.serial is not None:
            toSend = self.serial_payload(message.data.payload)
            self.serial.write(toSend)
            #self.serial.put(Message('serial_data', toSend))

    def put(self, message):
        self.dispatcher.put(message)

    def register_robot(self,robot):
        self.dispatcher.add_sinks({"packet":[robot.put]})
