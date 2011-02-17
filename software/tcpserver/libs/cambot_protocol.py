import utils
from datetime import datetime, timedelta


from twisted.internet import protocol
from twisted.protocols import basic
from twisted.internet import reactor

import dbus.service


class camprotocol(basic.LineReceiver):
    delimiter = "\n"
    last_activity = utils.utcstamp()
    keepalive_timeout = timedelta(seconds=15)
    keepalive_timer = None

    def connectionMade(self):
        self.factory.bus.add_signal_receiver(self.dbus_signal_received, dbus_interface = "com.example.TestService")
        self.session_key = utils.create_session_key()
        self.hmac_wrapper = utils.hmac_wrapper(self.session_key + self.factory.config.get('auth', 'shared_secret'))
        self.send_signed("HELLO\t%s" % (utils.hex_encode(self.session_key)))
        self.keepalive_timer = reactor.callLater(self.keepalive_timeout.seconds, self.keepalive_callback)

    def connectionLost(self, reason):
        print "connectionLost trig, reason=%s" % repr(reason)
        if self.keepalive_timer:
            self.keepalive_timer.cancel()

    def send_signed(self, message):
        raw = self.hmac_wrapper.sign(message) + "\n";
        print "Sending: %s" % raw
        self.transport.write(raw)
        self.last_activity = utils.utcstamp()

    def dbus_signal_received(self, *args, **kwargs):
         self.transport.write("Got signal, args: %s\n   kwargs: %s\n" % (repr(args), repr(kwargs)))

    def verify_data(self, data):
        return self.hmac_wrapper.verify_data(data)

    def keepalive_callback(self):
        # Immediately register another callback for a later time
        self.keepalive_timer = reactor.callLater(self.keepalive_timeout.seconds, self.keepalive_callback)
        if (utils.utcstamp() - self.last_activity < self.keepalive_timeout):
            # We're good
            return
        self.send_signed("KEEPALIVE\t%s" % utils.utcstamp().strftime('%Y-%m-%d %H:%M:%S.%f'))

    def lineReceived(self, data):
        print "got data: %s" % data
        message = self.verify_data(data)
        if message == False:
            self.send_signed("ERROR\tHash mismatch")
            self.transport.loseConnection()
            return

        self.last_activity = utils.utcstamp()
        self.parse_message(message)

    def parse_message(self, message):
        command, tab, cmd_args = message.partition("\t")
        func = getattr(self, command, None)
        if callable(func):
            return func(cmd_args)
        else:
            self.send_signed("NACK")

    def BYE(self, *args):
        self.transport.loseConnection()
        return

    def PING(self, *args):
        self.send_signed("PONG\t%s" % utils.utcstamp().strftime('%Y-%m-%d %H:%M:%S.%f'))
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
