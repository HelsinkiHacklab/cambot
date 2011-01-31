#!/usr/bin/python

import sys, os

from twisted.internet import glib2reactor
glib2reactor.install()
from twisted.internet import reactor

import dbus
import dbus.mainloop.glib
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

local_module_dir = os.path.join(os.path.dirname( os.path.realpath( __file__ ) ),  'libs')
if os.path.isdir(local_module_dir):                                       
    sys.path.append(local_module_dir)
import cambot_protocol

import ConfigParser
config = ConfigParser.SafeConfigParser()
if not os.path.isfile('tcpserver.conf'):
    config.add_section('auth')
    config.set('auth', 'shared_secret', 'HackLab')
    config.add_section('socket')
    config.set('socket', 'port', '8080')
    # TODO: Other defaults
    with open('tcpserver.conf', 'wb') as configfile:
        config.write(configfile)
config.read('tcpserver.conf')

print config.get('auth', 'shared_secret')


reactor.listenTCP(config.getint('socket', 'port'), cambot_protocol.camfactory(config, dbus.SystemBus()))
reactor.run()