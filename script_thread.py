import sys
from subprocess import Popen, PIPE, call
import subprocess
import re



# take a webcam image
# determine if an existing image should be used, else take a new image
if len(sys.argv) == 1:
    image_name = '/home/pi/izot-sdk/izot/testing/cart_project/thisImage.jpg'
    Popen(['fswebcam', '-r', '500x300', '--no-banner', image_name]).communicate()
else:
    image_name = str(sys.argv[1])

# capture output of hsv program
(out, err) = Popen(['/home/pi/izot-sdk/izot/testing/cart_project/executables/hsvrun', image_name], stdout=PIPE).communicate()

# parse hsv results
vals = re.findall(r"\d*\.\d*", out)

vals[0] = float(vals[0])

cascade_list = []

with open('/home/pi/izot-sdk/izot/testing/cart_project/cascades/cascades.txt') as text:
    for line in text:
        cascade_list.append(line.rstrip())

color_bounds = []

with open('/home/pi/izot-sdk/izot/testing/cart_project/calibration.txt') as text:
    for line in text:
        color_bounds.append(line.rstrip())

color_bounds[0] = float(color_bounds[0])
color_bounds[1] = float(color_bounds[1])
color_bounds[2] = float(color_bounds[2])

# determine color region
if float(vals[1]) <= color_bounds[0] or float(vals[1]) > 280:
    found = 1

if color_bounds[0] < float(vals[1]) <= color_bounds[1]:
    found = 2
   
if color_bounds[1] < float(vals[1]) <= color_bounds[2]:
    found = 3

if color_bounds[2] < float(vals[1]) <= 280:
    found = 4

if vals[0] < 0.15:
    found = 0


# print vals[1]
# number of cascades passed
cascadeTotal = 0

for c in cascade_list:
	proc = Popen(['/home/pi/izot-sdk/izot/testing/cart_project/executables/objectdetect', '--cascade=/home/pi/izot-sdk/izot/testing/cart_project/cascades/{}'.format(c), image_name], stdout=PIPE)
	(out, err) = proc.communicate()
    # print 'Using {0} cascade: '.format(c.strip('.xml')), out.strip()
	if out.strip() == '0':
		cascadeTotal += 1
		if c.strip('.xml') == 'Round':
			if found == 0:
				print 'Region0:Round;',
			if found == 1:
				print 'Region1:Round;',
			if found == 2:
				print 'Region2:Round;',
			if found == 3:
				print 'Region3:Round;',
			if found == 4:
				print 'Region4:Round;',
		elif c.strip('.xml') == 'Long':
			if found == 0:
				print 'Region0:Long;',
			if found == 1:
				print 'Region1:Long;',
			if found == 2:
				print 'Region2:Long;',
			if found == 3:
				print 'Region3:Long;',
			if found == 4:
				print 'Region4:Long;',
		elif c.strip('.xml') == 'Bunch':
			if found == 0:
				print 'Region0:Bunch;',
			if found == 1:
				print 'Region1:Bunch;',
			if found == 2:
				print 'Region2:Bunch;',
			if found == 3:
				print 'Region3:Bunch;',
			if found == 4:
				print 'Region4:Bunch;',

# If none of above and ratios are right
if cascadeTotal == 0:
	if found == 0:
		print 'Region0:None;',
	if found == 1:
		print 'Region1:None;',
	if found == 2:
		print 'Region2:None;',
	if found == 3:
		print 'Region3:None;',
	if found == 4:
		print 'Region4:None;',

# exit gracefully
sys.exit(0)
