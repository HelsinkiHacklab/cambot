#!/usr/bin/env python

#adapted from https://code.fluendo.com/flumotion/trac/browser/flumotion/trunk/flumotion/component/converters/overlay/overlay.py and http://pygstdocs.berlios.de/pygst-tutorial/capabilities.html

import sys, os
import pygtk, gtk, gobject
import pygst
pygst.require("0.10")
import gst

import cairo
from cairo import ImageSurface
from cairo import Context
import pango
import pangocairo

import dbus
from dbus.mainloop.glib import DBusGMainLoop
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

class GTK_Main():
    CAPS_TEMPLATE = "video/x-raw-rgb,bpp=32,depth=32,width=%d,height=%d," \
            "red_mask=-16777216,green_mask=16711680,blue_mask=65280," \
            "alpha_mask=255,endianness=4321,framerate=0/1"    

    def __init__(self):
        self.overlay_buffer = None
        self.overlay_text = "Foo Bar Baz 123"
        
        self.bus = dbus.SystemBus()
        #self.bus = dbus.SessionBus()
        #textsignal = self.bus.add_signal_receiver(self.overlay_text_changed, 'textchanged', 'com.example')
        textsignal = self.bus.add_signal_receiver(self.overlay_text_changed, dbus_interface = "com.example.TestService", signal_name = "HelloSignal")
    
    
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_title("Mpeg2-Player")
        window.set_default_size(500, 400)
        window.connect("destroy", gtk.main_quit, "WM destroy")
        vbox = gtk.VBox()
        window.add(vbox)
        hbox = gtk.HBox()
        vbox.pack_start(hbox, False)
        #self.entry = gtk.Entry()
        #hbox.add(self.entry)
        self.button = gtk.Button("Start")
        hbox.pack_start(self.button, False)
        self.button.connect("clicked", self.start_stop)
        self.movie_window = gtk.DrawingArea()
        vbox.add(self.movie_window)
        window.show_all()       


        #self.player = gst.parse_launch('videotestsrc name=source ! video/x-raw-yuv,format=(fourcc)AYUV ! videomixer name=mix ! ffmpegcolorspace ! autovideosink name=videosink')
        # PONDER: How to get the resolution from the videosink ?
        #self.player = gst.parse_launch('videotestsrc name=source ! video/x-raw-yuv,format=(fourcc)AYUV ! videomixer name=mix ! ffmpegcolorspace ! videoscale ! autovideosink name=videosink')
        #self.player = gst.parse_launch('videotestsrc name=source ! videoscale ! video/x-raw-yuv,format=(fourcc)AYUV ! videomixer name=mix ! ffmpegcolorspace !  autovideosink name=videosink')
        # This hardcoded resolution works.
        #self.player = gst.parse_launch('videotestsrc name=source ! video/x-raw-yuv,format=(fourcc)AYUV,width=500,height=400 ! videomixer name=mix ! ffmpegcolorspace !  autovideosink name=videosink')
        self.player = gst.parse_launch('videotestsrc name=source ! tee name=player')
        self.bin1 = gst.gst_parse_bin_from_description('queue ! video/x-raw-yuv,format=(fourcc)AYUV,width=500,height=400 ! videomixer name=mix ! ffmpegcolorspace !  autovideosink name=videosink', True)
        self.player.add(self.bin1)
        #self.bin2 = gst.gst_parse_bin_from_description('queue ! video/x-raw-yuv,format=(fourcc)AYUV,width=500,height=400 ! videomixer name=mix ! ffmpegcolorspace !  tcpserversink name=videosink', True)
        #self.player.add(self.bin2)
        self.tee = self.player.get_by_name("player")
        self.tee.link(self.bin1)

        # adapted from https://code.fluendo.com/flumotion/trac/browser/flumotion/trunk/flumotion/component/converters/overlay/overlay.py
        self.videomixer = self.bin1.get_by_name("mix")
        self.converter = self.bin1.get_by_name("conv")
        self.videomixer.get_pad('sink_0').connect('notify::caps', self._notify_caps_cb)
        self.sourceBin = gst.Bin()
        self.overlay = gst.element_factory_make('appsrc', 'overlay')
        self.overlay.set_property('do-timestamp', True)
        self.overlay.connect('need-data', self.push_buffer)
        self.sourceBin.add(self.overlay)
        self.alphacolor = gst.element_factory_make('alphacolor')
        self.sourceBin.add(self.alphacolor)
        self.overlay.link(self.alphacolor)
        self.sourceBin.add_pad(gst.GhostPad('src', self.alphacolor.get_pad('src')))
        self.sourceBin.set_locked_state(True)
        self.player.add(self.sourceBin)

        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.enable_sync_message_emission()
        bus.connect("message", self.on_message)
        bus.connect("sync-message::element", self.on_sync_message)

        self.start_stop(None)

    def overlay_text_changed(self, new_text, *args, **kwargs):
        print "Got args: %s" % repr(args)
        print "Got kwargs: %s" % repr(kwargs)
        self.overlay_text = new_text
        self.renegerate_overlay_buffer()

    def resolution_changed(self):
        self.renegerate_overlay_buffer()
        self.capsStr = self.CAPS_TEMPLATE % (self.video_width, self.video_height)
        caps = gst.caps_from_string(self.capsStr)
        self.overlay.set_property('caps', caps)
        print "overlay caps"
        print caps.to_string()
        print "* overlay sink_pads and caps"
        for i in self.overlay.sink_pads():
            for i2 in i.get_caps():
                print "** pad %s caps: %s" % (i2.get_name(), i2.to_string())
        print "* overlay src_pads and caps"
        for i in self.overlay.src_pads():
            for i2 in i.get_caps():
                print "** pad %s caps: %s" % (i2.get_name(), i2.to_string())
        print "* alphacolor sink_pads and caps"
        for i in self.alphacolor.sink_pads():
            for i2 in i.get_caps():
                print "** pad %s caps: %s" % (i2.get_name(), i2.to_string())
        print "* alphacolor src_pads and caps"
        for i in self.alphacolor.src_pads():
            for i2 in i.get_caps():
                print "** pad %s caps: %s" % (i2.get_name(), i2.to_string())

    def _notify_caps_cb(self, pad, param):
        caps = pad.get_negotiated_caps()
        print "_notify_caps_cb got caps: %s" % caps
        if caps is None:
            return

        struct = pad.get_negotiated_caps().get_structure(0)
        self.video_height = struct['height']
        self.video_width = struct['width']
        self.video_framerate = struct['framerate']
        self.duration = float(self.video_framerate.denom) / self.video_framerate.num
        print "Width:%s, Height:%s, Framerate=%s, Duration=%s" %(self.video_width, self.video_height, self.video_framerate, self.duration)

        self.resolution_changed()

        if not self.sourceBin.get_pad("src").is_linked():
            #self.sourceBin.link_filtered(self.videomixer, gst.Caps("video/x-raw-yuv, format=(fourcc)AYUV"))
            print "* sourceBin src_pads and caps"
            for i in self.sourceBin.src_pads():
                for i2 in i.get_caps():
                    print "** pad %s caps: %s" % (i2.get_name(), i2.to_string())
            print "* videomixer sink_pads and caps"
            for i in self.videomixer.sink_pads():
                for i2 in i.get_caps():
                    print "** pad %s caps: %s" % (i2.get_name(), i2.to_string())
            self.sourceBin.link(self.videomixer)
            self.sourceBin.set_locked_state(False)
            self.sourceBin.set_state(gst.STATE_PLAYING)

    def push_buffer(self, source, arg0):
        #print "push_buffer called"
        if self.overlay_buffer == None:
            self.renegerate_overlay_buffer()
        #print "overlay_buffer size: %d" % len(self.overlay_buffer)
        gstBuf = gst.Buffer(self.overlay_buffer)
        padcaps = gst.caps_from_string(self.capsStr)
        gstBuf.set_caps(padcaps)
        gstBuf.duration = int(self.duration * gst.SECOND)
        source.emit('push-buffer', gstBuf)


    def renegerate_overlay_buffer(self):
        image = ImageSurface(cairo.FORMAT_ARGB32, self.video_width, self.video_height)
        context = Context(image)
        text = self.overlay_text
        font = pango.FontDescription('sans normal 22')
        text_offset = [6, 6]

        textOverflowed = False
        if text:
            pcContext = pangocairo.CairoContext(context)
            pangoLayout = pcContext.create_layout()
            font = pango.FontDescription('sans normal 22')
            pangoLayout.set_font_description(font)
    
            context.move_to(text_offset[0]+2, text_offset[1]+2)
            pangoLayout.set_markup('<span foreground="black" >%s</span>' % text)
            pcContext.show_layout(pangoLayout)
            context.move_to(text_offset[0], text_offset[1])
            pangoLayout.set_markup('<span foreground="white" >%s</span>' % text)
            pcContext.show_layout(pangoLayout)
    
            textWidth, textHeight = pangoLayout.get_pixel_size()
        
        self.overlay_buffer = image.get_data()
        print "overlay_buffer size: %d" % len(self.overlay_buffer)

    def start_stop(self, w):
        if self.button.get_label() == "Start":
                self.button.set_label("Stop")
                self.player.set_state(gst.STATE_PLAYING)
        else:
            self.player.set_state(gst.STATE_NULL)
            self.button.set_label("Start")
                        
    def on_message(self, bus, message):
        t = message.type
        if t == gst.MESSAGE_EOS:
            self.player.set_state(gst.STATE_NULL)
            self.button.set_label("Start")
        elif t == gst.MESSAGE_ERROR:
            self.player.set_state(gst.STATE_NULL)
            self.button.set_label("Start")
            err, debug = message.parse_error()
            print "Error: %s" % err, debug


    def foreach_test(self, *data):
        print data

    def on_sync_message(self, bus, message):
        if message.structure is None:
            return
        message_name = message.structure.get_name()
        if message_name == "prepare-xwindow-id":
            imagesink = message.src
            imagesink.set_property("force-aspect-ratio", True)
            gtk.gdk.threads_enter()
            imagesink.set_xwindow_id(self.movie_window.window.xid)
            gtk.gdk.threads_leave()




            
GTK_Main()
gtk.gdk.threads_init()
gtk.main()