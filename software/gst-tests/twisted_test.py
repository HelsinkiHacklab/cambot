from twisted.internet import glib2reactor
glib2reactor.install()

from twisted.internet import protocol, reactor
from twisted.protocols import basic


import dbus
import dbus.service
import dbus.mainloop.glib
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)


class camprotocol(basic.LineReceiver):
    def lineReceived(self, data):
        print "got data: %s" % data
        self.transport.write(data.upper() + "\n")
        self.factory.HelloSignal(data)
        if (data == "BYE"):
            self.transport.loseConnection()

class camfactory(protocol.ServerFactory, dbus.service.Object):
    protocol = camprotocol
    
    def __init__(self, bus,  object_path='/com/example/TestService/object'):
        dbus.service.Object.__init__(self, bus, object_path)
        self.bus = bus


    @dbus.service.signal('com.example.TestService')
    def HelloSignal(self, message):
        # The signal is emitted when this method exits
        # You can have code here if you wish
        pass


reactor.listenTCP(6969, camfactory(dbus.SessionBus()))
reactor.run()