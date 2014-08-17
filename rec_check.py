#!/usr/bin/python2.6
import pyaudio
import wave
import sys

chunk = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 5
WAVE_OUTPUT_FILENAME = "output.wav"

p = pyaudio.PyAudio()


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

print "* recording"
all = []
for i in range(0, RATE / chunk * RECORD_SECONDS):
	try:
		data = stream.read(chunk)
		all.append(data)
	except:
		print "lost chunk"
print "* done recording"

stream.close()
p.terminate()

# write data to WAVE file
data = ''.join(all)
wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
wf.setnchannels(CHANNELS)
wf.setsampwidth(p.get_sample_size(FORMAT))
wf.setframerate(RATE)
wf.writeframes(data)
wf.close()
