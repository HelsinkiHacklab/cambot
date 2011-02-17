#!/usr/bin/env python -i
import sys,os
import ConfigParser
import socket, threading
from datetime import datetime, timedelta

local_module_dir = os.path.join(os.path.dirname( os.path.realpath( __file__ ) ),  'libs')
if os.path.isdir(local_module_dir):                                       
    sys.path.append(local_module_dir)
import utils


class testclient:
    def __init__(self, address_tuple, config):
        self.config = config
        print self.config.get('auth', 'shared_secret')
        self.socket = socket.create_connection(address_tuple)

        self.receiver_thread = threading.Thread(target=self.tcp_reader)
        self.receiver_thread.setDaemon(1)
        self.receiver_thread.start()
        

    def lineReceived(self, data):
        print "Client: got data %s" % data
        # Check for HELLO first as it defines our session key....
        if data[0:6] == "HELLO\t":
            self.session_key = utils.hex_decode(data.split("\t")[1])
            self.hmac_wrapper = utils.hmac_wrapper(self.session_key + self.config.get('auth', 'shared_secret'))
        message = self.verify_data(data)
        #print "Client: Got message %s\n" % message
        #print "Client: self.session_key=%s" % utils.hex_encode(self.session_key)
        if message == False:
            print "ERROR Hash mismatch"
            return

        self.parse_message(message)

    def parse_message(self, message):
        command, tab, cmd_args = message.partition("\t")
        func = getattr(self, command, None)
        if callable(func):
            return func(cmd_args)
        else:
            print "Don't know how to handle %s" % repr(message)


    def ping(self):
        self.send_signed("PING\t%s" % utils.utcstamp().strftime('%Y-%m-%d %H:%M:%S.%f'))
        self.pinged = utils.utcstamp()

    def PONG(self, timestamp_str):
        # Safety, make sure we adjust latency only if we called the ping method
        if self.pinged:
            self.latency = utils.utcstamp() - self.pinged
        self.pinged = None

        # Calculate delta to server time
        if self.latency:
            parsed_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S.%f')
            self.server_timedelta = utils.utcstamp() - parsed_time

    def HELLO(self, *args):
        # Automagically ping after HELLO
        self.ping()
        return

    def KEEPALIVE(self, *args):
        return

    def verify_data(self, data):
        return self.hmac_wrapper.verify_data(data)

    def send_signed(self, message):
        raw = self.hmac_wrapper.sign(message) + "\n";
        self.socket.sendall(raw)
        print "Sent: %s" % raw

    def tcp_reader(self):
        alive = True
        charbuffer = ''
        try:
            while alive:
                data = self.socket.recv(4096)
                if data == '':
                    continue

                # TODO: hex-encode unprintable characters (but keep newlines)
                sys.stdout.write(data)

                charbuffer += data
                # Partition the charbuffer at newlines and parse the command until we have no newlines left
                while charbuffer.find("\n") != -1:
                    part = charbuffer.partition("\n")
                    charbuffer = part[2]
                    self.lineReceived(part[0])

        except Exception, e:
            print e
            self.alive = False



if __name__ == '__main__':
    config = ConfigParser.SafeConfigParser()
    config.read('tcpserver.conf')
    c = testclient(('127.0.0.1', '8080'), config)

