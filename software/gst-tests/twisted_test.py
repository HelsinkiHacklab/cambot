from twisted.internet import glib2reactor
glib2reactor.install()

from twisted.internet import protocol, reactor
from twisted.protocols import basic
import dbus
import dbus.mainloop.glib
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)


import dbus.service


class camprotocol(basic.LineReceiver):
    def connectionMade(self):
        self.factory.bus.add_signal_receiver(self.dbus_signal_received, dbus_interface = "com.example.TestService")

    def dbus_signal_received(self, *args, **kwargs):
         self.transport.write("Got signal, args: %s\n   kwargs: %s\n" % (repr(args), repr(kwargs)))

    def lineReceived(self, data):
        #print "got data: %s" % data
        self.transport.write(data.upper() + "\n")
        self.factory.HelloSignal(data)
        if (data == "BYE"):
            self.transport.loseConnection()

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


reactor.listenTCP(6969, camfactory(dbus.SystemBus()))
reactor.run()