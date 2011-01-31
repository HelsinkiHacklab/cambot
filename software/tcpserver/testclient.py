#!/usr/bin/env python
import sys,os
local_module_dir = os.path.join(os.path.dirname( os.path.realpath( __file__ ) ),  'libs')
if os.path.isdir(local_module_dir):                                       
    sys.path.append(local_module_dir)
import utils, hmac, hashlib

# client example from http://www.oluyede.org/blog/2008/08/31/twisted-interactive-console/

from twisted.internet import defer, stdio, protocol, reactor
from twisted.protocols import basic

class Repl(basic.LineReceiver):
    delimiter = '\n'
    prompt_string = '>>> '

    def prompt(self):
        self.transport.write(self.prompt_string)

    def connectionMade(self):
        self.sendLine('Welcome to Repl')
        # store factory and connector upon connection to the stdout
        self.factory = CFactory()
        self.connector = reactor.connectTCP('127.0.0.1', 8080, self.factory)
        self.prompt()

    def lineReceived(self, line):
        if not line:
            self.prompt()
            return

        self.issueCommand(line)

    def issueCommand(self, command):
        # write to the connector's transport, not the one writing on stdout
        #self.connector.transport.write("%s%s" % (command, self.delimiter))
        self.connector.send_signed(command)
        # register the callback on the factory's deferred
        self.factory.deferred.addCallback(self._checkResponse)

    def _checkResponse(self, message):
        self.sendLine(message)
        self.prompt()
        # recreate the deferred each time we have the response
        self.factory.deferred = defer.Deferred()

class Client(basic.LineReceiver):
    delimiter = '\n'

    def connectionMade(self):
        pass

    def lineReceived(self, data):
        print "Client: got data %s" % data
        if data[0:6] == "HELLO\t":
            self.session_key = utils.hex_decode(data.split("\t")[1])
        message = self.verify_data(data)
        print "Client: Got message %s\n" % message
        print "Client: self.session_key=%s" % utils.hex_encode(self.session_key)
        if message == False:
            self.factory.deferred.callback("ERROR Hash mismatch")
            return
        
        self.factory.deferred.callback(message)

    def verify_data(self, data):
        sent_hash = utils.hex_decode(data[-40:])
        message = data[:-41]
        h = hmac.new(self.session_key, message, hashlib.sha1)
        if sent_hash != h.digest():
            return False
        return message

    def send_signed(self, message):
        h = hmac.new(self.session_key, message, hashlib.sha1)
        self.transport.write(message + "\t" + h.hexdigest() + "\n")

    def responseFinished(self, num_lines, data):
        # just fire the callback
        self.factory.deferred.callback((
            self.cmd_success, num_lines, data))

    def connectionLost(self, reason):
        reactor.stop()


class CFactory(protocol.ClientFactory):
    protocol = Client

    def __init__(self):
        self.deferred = defer.Deferred()

if __name__ == "__main__":
    stdio.StandardIO(Repl())
    reactor.run()