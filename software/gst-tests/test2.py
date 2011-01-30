import sys, os
import pygtk, gtk, gobject
import pygst
pygst.require("0.10")
import gst


class GTK_Main():
    def __init__(self):
        self.vencoder_str = "ffmpegcolorspace ! x264enc tune=zerolatency byte-stream=true ! rtph264pay"
        # increasing the bitrate doesn't seem to improve quality...
        self.vencoder_str = "ffmpegcolorspace ! x264enc tune=zerolatency byte-stream=true bitrate=8000 ! rtph264pay"
        #self.vencoder_str = "ffenc_h263 ! rtph263ppay"
        #self.vencoder_str = "videoscale ! videorate ! video/x-raw-yuv,width=352,height=288,framerate=15/1 !  ffmpegcolorspace ! x264enc tune=zerolatency byte-stream=true bitrate=1500 ! rtph264pay"
        #self.vencoder_str = "videoscale ! videorate !  ffmpegcolorspace ! x264enc tune=zerolatency byte-stream=true  ! rtph264pay"
        #self.vencoder_str = "ffmpegcolorspace ! videoscale ! videorate !  video/x-raw-yuv,width=380,height=240 ! x264enc tune=zerolatency byte-stream=true bitrate=1500 ! rtph264pay"
        self.player = gst.parse_launch("gstrtpbin name=rtpbin \
        v4l2src ! tee name=splitter ! " + self.vencoder_str + " ! rtpbin.send_rtp_sink_0 \
                  rtpbin.send_rtp_src_0 ! udpsink port=5000 host=127.0.0.1                           \
                  rtpbin.send_rtcp_src_0 ! udpsink port=5001 host=127.0.0.1 sync=false async=false    \
                  udpsrc port=5005 ! rtpbin.recv_rtcp_sink_0                           \
        audiotestsrc ! amrnbenc ! rtpamrpay ! rtpbin.send_rtp_sink_1                   \
                  rtpbin.send_rtp_src_1 ! udpsink port=5002 host=127.0.0.1                            \
                  rtpbin.send_rtcp_src_1 ! udpsink port=5003 host=127.0.0.1 sync=false async=false    \
                  udpsrc port=5007 ! rtpbin.recv_rtcp_sink_1 \
        splitter. ! queue ! video/x-raw-yuv,format=(fourcc)YUY2,width=640,height=480 ! ffmpegcolorspace ! autovideosink"
        )


        self.player.set_state(gst.STATE_PLAYING)

# gstrtpbin name=rtpbin \
#         v4l2src ! ffmpegcolorspace ! ffenc_h263 ! rtph263ppay ! rtpbin.send_rtp_sink_0 \
#                   rtpbin.send_rtp_src_0 ! udpsink port=5000                            \
#                   rtpbin.send_rtcp_src_0 ! udpsink port=5001 sync=false async=false    \
#                   udpsrc port=5005 ! rtpbin.recv_rtcp_sink_0                           \
#         audiotestsrc ! amrnbenc ! rtpamrpay ! rtpbin.send_rtp_sink_1                   \
#                   rtpbin.send_rtp_src_1 ! udpsink port=5002                            \
#                   rtpbin.send_rtcp_src_1 ! udpsink port=5003 sync=false async=false    \
#                   udpsrc port=5007 ! rtpbin.recv_rtcp_sink_1



GTK_Main()
gtk.gdk.threads_init()
gtk.main()        