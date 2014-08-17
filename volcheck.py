#!/usr/bin/python2.6

import pyaudio
import struct
import sys

p = pyaudio.PyAudio()
device = int(sys.argv[1])
started = False
while not started:
	try:
		stream = p.open(format=pyaudio.paInt16, channels=1, rate=11025, input=True, frames_per_buffer=256, input_device_index=device)
		started = True
		print "Device %i open successful" % device
	except:
		print "Could not open device %i" % device
		device += 1

while True:
	try:
		data = stream.read(256)
	except IOError:
		print "Warning: frame dropped"
		continue
	d = struct.unpack("256h",data)
	vol = max(d)
	sys.stdout.write("%i " % vol)
	sys.stdout.flush()


#14
