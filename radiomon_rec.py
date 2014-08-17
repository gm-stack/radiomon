#!/usr/bin/env python

import pyaudio
import wave
import sys
import struct
import time
import os
import subprocess
import MySQLdb, MySQLdb.cursors
import traceback
import ConfigParser

config = ConfigParser.ConfigParser()
config.read("radiomon.conf")

p = pyaudio.PyAudio()

stream = p.open(format=pyaudio.paInt16, channels=1, rate=11025, input=True, frames_per_buffer=256, input_device_index=7)

def openwav(filename):
	wf = wave.open(filename,'wb')
	wf.setnchannels(1)
	wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
	wf.setframerate(11025)
	return wf

rectimeout = 0
recdata = ""
starttime = 0
wf = None
filename = None
df = None
dfcont = ""
filetime = 0
datecode = None
timecode = None

conn = MySQLdb.connect(host=config.get("mysql","host"),
			user=config.get("mysql","user"),
			passwd=config.get("mysql","passwd"),
			db=config.get("mysql","db"), 
			cursorclass=MySQLdb.cursors.DictCursor, charset='utf8')
cursor = conn.cursor()

threshold = config.get("record","threshold")
chopfromstart = config.get("record","chopfromstart")
initialtimeout = config.get("record","initialtimeout")

try:
	while True:
		try:
			data = stream.read(256)
		except IOError:
			print "Warning: frame dropped"
			continue
		d = struct.unpack("256h",data)
		vol = max(d)
		if (vol > threshold):
			#print "vol: %i" % vol
			if (rectimeout == 0):
				recdata = ""
				print "Started recording at %s" % time.strftime("%H:%M:%S")
				if (time.time() - starttime > (60*5)):
					filetime = 0
					if (wf):
						print "closing %s" % filename
						wf.close()
						subprocess.Popen(["/usr/bin/oggenc","-b","24",filename], stdout=sys.stdout)
						try:
							conn.ping()
							cursor.execute("INSERT INTO transmissioninfo (datetime,comments,category,lastedit,txinfo) VALUES (%(datetime)s, '', 'none', 'initial', %(txinfo)s)",
										{'datetime': datecode + timecode, 'txinfo': dfcont})
						except:
							print "MySQL error"
							traceback.print_exc(file=sys.stdout)
					if (df): df.close()
					datecode = time.strftime("%Y%m%d")
					timecode = time.strftime("%H%M")
					filename = "output/%s/rec%s.wav" % (datecode,timecode)
					dfilename = "output/%s/rec%s.txt" % (datecode,timecode)
					if not os.path.exists("output/%s/" % datecode):
						os.mkdir("output/"+datecode)
					wf = openwav(filename)
					df = open(dfilename,'w')
					dfcont = ""
					print "Opening new file: %s" % filename
				starttime = time.time()
			rectimeout = initialtimeout
		if (rectimeout > 0):
			rectimeout -= 1
			recdata += data
			if (rectimeout == 0):
				if len(recdata) > chopfromstart*2:
					nowtime = time.strftime("%H:%M:%S")
					reclen = time.time() - starttime
					print "Stopped recording at %s - %.2f seconds recorded" % (nowtime, reclen)
					frames = recdata[chopfromstart*2:]
					wf.writeframes(frames)
					dfline = ("%f," % filetime)
					writelen = float(len(frames))/float(11025*2)
					filetime += writelen
					dfline += "%f,%f,%s\n" % (filetime,writelen,nowtime)
					df.write(dfline)
					dfcont += dfline
					df.flush()
					
except KeyboardInterrupt:
	print "Stopping and closing file"
	wf.close()
	if (filename):
		subprocess.Popen(["/usr/bin/oggenc","-b","24",filename], stdout=sys.stdout)
		cursor.execute("INSERT INTO transmissioninfo (datetime,comments,category,lastedit,txinfo) VALUES (%(datetime)s, '', 'none', 'initial', %(txinfo)s)",
										{'datetime': datecode + timecode, 'txinfo': dfcont})
	df.close()
