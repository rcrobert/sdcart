#!/usr/bin/python2.7
import sys, re
from subprocess import call, Popen, PIPE

def main():
	process_id = open("VLC_ID.txt", "r")
	text_file = open("cart.txt", "w")
	#Popen(['cvlc', 'v4l2:///dev/video0', '--video-filter', 'transform', '--transform-type', 'hflip', '&']).communicate()

	VLC_PID = process_id.read().rstrip()

	print VLC_PID

	#keyIn = raw_input('Press S to capture image')
	Popen(['kill', '-CONT', VLC_PID]).communicate()

	Popen(['scrot', '-s', 'thisImage.jpg']).communicate()

	Popen(['kill', '-STOP', VLC_PID]).communicate()	

	proc = Popen(['python', 'script_thread.py', 'thisImage.jpg'], stdout = PIPE)
	(out, err) = proc.communicate()
	choices = out.split(";")

	listNumbers = 1
	line_list = []

	for line in choices:
		line = line.strip(';')
		if line != '':
			print line,
		else:
			print 'Not Found',

	text_file.close()	
if __name__ == '__main__':
	main()
