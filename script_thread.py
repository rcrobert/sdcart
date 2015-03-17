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
(out, err) = Popen(['./executables/hsvrun', image_name], stdout=PIPE).communicate()

# parse hsv results
vals = re.findall(r"\d*\.\d*", out)

cascade_list = []

# determine color region
if float(vals[1]) <= 22 or float(vals[1]) > 280:
    found = 1
    with open('./cascades/test1.txt') as text:
        for line in text:
            cascade_list.append(line.rstrip())

if 22 < float(vals[1]) <= 150:
    found = 2
    with open('./cascades/test2.txt') as text:
        for line in text:
            cascade_list.append(line.rstrip())

if 150 < float(vals[1]) <= 280:
    found = 3
    with open('./cascades/test3.txt') as text:
        for line in text:
            cascade_list.append(line.rstrip())

# number of cascades passed
cascadeTotal = 0

# using color region, determine cascade list to run
for c in cascade_list:
    proc = Popen(['./executables/objectdetect', '--cascade=./cascades/{}'.format(c), image_name], stdout=PIPE)
    (out, err) = proc.communicate()
    # print 'Using {0} cascade: '.format(c.strip('.xml')), out.strip()
    if out.strip() == '0':
        if c.strip('.xml') == 'round':
            if found == 1:
                print 'Region1:Round;',
            if found == 2:
                print 'Region2:Round;',
        elif c.strip('.xml') == 'banana':
            if found == 1:
                print 'Region1:Banana;',
            if found == 2:
                print 'Region2:Banana;',
        elif c.strip('.xml') == 'asparagus':
            print 'Region2:Asparagus;',
        cascadeTotal += 1

# TEMP if none of above and ratios are right
if cascadeTotal == 0:
    if found == 2:
        if vals[0] > 0.25:
            print 'Region2:Lettuce;Region2:Kale;',

# exit gracefully
sys.exit(0)
