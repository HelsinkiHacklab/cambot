import utils, hmac, hashlib, time


from twisted.internet import protocol
from twisted.protocols import basic
from twisted.internet import reactor

import dbus.service


class camprotocol(basic.LineReceiver):
    delimiter = "\n"
    last_activity = 0.0
    keepalive_timeout = 5

    def connectionMade(self):
        self.factory.bus.add_signal_receiver(self.dbus_signal_received, dbus_interface = "com.example.TestService")
        self.session_key = utils.create_session_key()
        self.send_signed("HELLO\t%s" % (utils.hex_encode(self.session_key)))
        reactor.callLater(self.keepalive_timeout, self.keepalive_callback)

    def send_signed(self, message):
        h = hmac.new(self.session_key, message, hashlib.sha1)
        raw = message + "\t" + h.hexdigest() + "\n"
        print "Sending: %s" % raw
        self.transport.write(raw)
        self.last_activity = time.time()

    def dbus_signal_received(self, *args, **kwargs):
         self.transport.write("Got signal, args: %s\n   kwargs: %s\n" % (repr(args), repr(kwargs)))

    def verify_data(self, data):
        sent_hash = utils.hex_decode(data[-40:])
        message = data[:-40]
        h = hmac.new(self.session_key, message, hashlib.sha1)
        if sent_hash != h.digest():
            return False
        return message

    def keepalive_callback(self):
        # Immediately register another callback for a later time
        reactor.callLater(self.keepalive_timeout, self.keepalive_callback)
        if (time.time() - self.last_activity < self.keepalive_timeout):
            # We're good
            return
        self.send_signed("KEEPALIVE %s" % time.strftime('%Y-%m-%d %H:%M:%S'))

    def lineReceived(self, data):
        print "got data: %s" % data
        message = self.verify_data(data)
        if message == False:
            self.send_signed("ERROR\tHash mismatch")
            self.transport.loseConnection()
            return
        
        #Echo service for debugging
        self.send_signed(message.upper())

        self.last_activity = time.time()
        self.parse_message(message)

    def parse_message(self, message):
        if message == "BYE":
            self.send_signed("Good bye")
            self.transport.loseConnection()
            return

class camfactory(protocol.ServerFactory, dbus.service.Object):
    protocol = camprotocol
    
    def __init__(self, config, bus,  object_path='/com/example/TestService/object'):
        dbus.service.Object.__init__(self, bus, object_path)
        self.bus = bus
        self.config = config


    @dbus.service.signal('com.example.TestService')
    def HelloSignal(self, message):
        # The signal is emitted when this method exits
        # You can have code here if you wish
        pass
