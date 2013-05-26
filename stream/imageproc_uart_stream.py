from imageproc_py.stream.serial_stream import *

class ImageprocUARTStream():
    """
    Similar to a BasestationStream: receives packets and sends them to the imagerproc.
    """
    def __init__(self,
                 port='/dev/ttyUSB0',
                 baud='1000000',
                 sinks=None):

        self.serial = SerialStream(port=port,
                                   baud=baud,
                                   timeout=None,
                                   read_size=1000,#TODO 1000 is arbitrary
                                   sinks=None,
                                   autoStart=True)
        self.dispatcher=AsynchDispatch(sinks=sinks,
                                       callbacks={'packet':[self.send]})

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
            self.serial.put(Message('serial_data', toSend))

    def put(self, message):
        self.dispatcher.put(message)
