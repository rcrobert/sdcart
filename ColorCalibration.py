import sys
from subprocess import Popen, PIPE
import re

file = open("/home/pi/izot-sdk/izot/testing/cart_project/calibration.txt", "w")
image_name = '/home/pi/izot-sdk/izot/testing/cart_project/images/CalibrationImage.jpg'

raw_input('Press Enter To Calibrate for RED')
Popen(['fswebcam', '-r', '500x300', '--no-banner', image_name]).communicate()

(out, err) = Popen(['/home/pi/izot-sdk/izot/testing/cart_project/executables/hsvrun', image_name], stdout=PIPE).communicate()

color_values = []

# parse hsv results
vals = re.findall(r"\d*\.\d*", out)

print "RED Hue: ",
print vals[1]
color_values.append(vals[1])

raw_input('Press Enter To Calibrate for ORANGE')
Popen(['fswebcam', '-r', '500x300', '--no-banner', image_name]).communicate()

(out, err) = Popen(['/home/pi/izot-sdk/izot/testing/cart_project/executables/hsvrun', image_name], stdout=PIPE).communicate()

# parse hsv results
vals = re.findall(r"\d*\.\d*", out)

print "ORANGE Hue: ",
print vals[1]
color_values.append(vals[1])

raw_input('Press Enter To Calibrate for YELLOW')
Popen(['fswebcam', '-r', '500x300', '--no-banner', image_name]).communicate()

(out, err) = Popen(['/home/pi/izot-sdk/izot/testing/cart_project/executables/hsvrun', image_name], stdout=PIPE).communicate()

# parse hsv results
vals = re.findall(r"\d*\.\d*", out)

print "YELLOW Hue: ",
print vals[1]
color_values.append(vals[1])
raw_input('Press Enter To Calibrate for GREEN')
Popen(['fswebcam', '-r', '500x300', '--no-banner', image_name]).communicate()

(out, err) = Popen(['/home/pi/izot-sdk/izot/testing/cart_project/executables/hsvrun', image_name], stdout=PIPE).communicate()

# parse hsv results
vals = re.findall(r"\d*\.\d*", out)

print "GREEN Hue: ",
print vals[1]
color_values.append(vals[1])

bound1 = (float(color_values[0]) + float(color_values[1]))/2
bound2 = (float(color_values[1]) + float(color_values[2]))/2
bound3 = (float(color_values[2]) + float(color_values[3]))/2

print bound1
print bound2
print bound3

file.write(str(bound1))
file.write("\n")
file.write(str(bound2))
file.write("\n")
file.write(str(bound3))
file.write("\n")