import sys
from subprocess import Popen, PIPE
import re



# take a webcam image
# determine if an existing image should be used, else take a new image
if len(sys.argv) == 1:
    image_name = './images/thisImage.jpg'
    Popen(['fswebcam', '-r', '500x300', '--no-banner', image_name]).communicate()
else:
    image_name = str(sys.argv[1])

# capture output of hsv program
(out, err) = Popen(['/home/pi/izot-sdk/izot/testing/cart_project/executables/hsvrun', image_name], stdout=PIPE).communicate()

# parse hsv results
vals = re.findall(r"\d*\.\d*", out)

vals[0] = float(vals[0])

# cascade_list = []

# with open('/home/pi/izot-sdk/izot/testing/cart_project/cascades/cascades.txt') as text:
#     for line in text:
#         cascade_list.append(line.rstrip())

# determine color region
if float(vals[1]) <= 55 or float(vals[1]) > 280:
    found = 1   

if 55 < float(vals[1]) <= 150:
    found = 2
   
if 150 < float(vals[1]) <= 280:
    found = 3

if vals[0] < 0.15:
    found = 0

# number of cascades passed
# cascadeTotal = 0

# using color region, determine cascade list to run
# for c in cascade_list:
#     proc = Popen(['/home/pi/izot-sdk/izot/testing/cart_project/executables/objectdetect', '--cascade=./cascades/{}'.format(c), image_name], stdout=PIPE)
#     (out, err) = proc.communicate()
#     # print 'Using {0} cascade: '.format(c.strip('.xml')), out.strip()
#     if out.strip() == '0':
#         if c.strip('.xml') == 'Round':
#             if found == 0:
#                 print 'Region0:Round;',
#             if found == 1:
#                 print 'Region1:Round;',
#             if found == 2:
#                 print 'Region2:Round;',
#             if found == 3:
#                 print 'Region3:Round;',
#         elif c.strip('.xml') == 'Long':
#             if found == 1:
#                 print 'Region1:Long;',
#             if found == 2:
#                 print 'Region2:Long;',
#             if found == 3:
#                 print 'Region3:Long;',
#         elif c.strip('.xml') == 'Bunch':
#             if found == 1:
#                 print 'Region1:Bunch;',
#             if found == 2:
#                 print 'Region2:Bunch;',
#             if found == 3:
#                 print 'Region3:Bunch;',
#         cascadeTotal += 1

# TEMP if none of above and ratios are right

if found == 0:
    print 'Region0:None;'
if found == 1:
    print 'Region1:None;'
if found == 2:
    print 'Region2:None;',
if found == 3:
    print 'Region3:None;',

# exit gracefully
sys.exit(0)
