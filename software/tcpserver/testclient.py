#!/usr/bin/env python -i
import sys,os
local_module_dir = os.path.join(os.path.dirname( os.path.realpath( __file__ ) ),  'libs')
if os.path.isdir(local_module_dir):                                       
    sys.path.append(local_module_dir)
import utils, hmac, hashlib
import ConfigParser
import socket, threading


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
        if data[0:6] == "HELLO\t":
            self.session_key = utils.hex_decode(data.split("\t")[1])
            self.hmac_key = self.session_key + self.config.get('auth', 'shared_secret')
        message = self.verify_data(data)
        #print "Client: Got message %s\n" % message
        #print "Client: self.session_key=%s" % utils.hex_encode(self.session_key)
        if message == False:
            print "ERROR Hash mismatch"
            return

    def verify_data(self, data):
        sent_hash = utils.hex_decode(data[-40:])
        #print "got hash %s" % utils.hex_encode(sent_hash)
        message = data[:-41]
        #print "got message %s" % repr(message)
        h = hmac.new(self.hmac_key, message, hashlib.sha1)
        if sent_hash != h.digest():
            return False
        return message

    def send_signed(self, message):
        h = hmac.new(self.hmac_key, message, hashlib.sha1)
        #print "session key %s" % utils.hex_encode(self.session_key)
        #print "hmac key %s" % repr(self.hmac_key)
        self.socket.sendall(message + "\t" + h.hexdigest() + "\n")

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

