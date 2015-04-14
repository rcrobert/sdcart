import RPIO.PWM as PWM

import time

red = 16
green = 19
blue = 13



def initLEDs():
    PWM.setup()
    PWM.set_loglevel(PWM.LOG_LEVEL_ERRORS)
    PWM.init_channel(0, subcycle_time_us=10000)  #channel 0 for red LED
    PWM.init_channel(1, subcycle_time_us=10000)  #channel 1 for green LED
    PWM.init_channel(2, subcycle_time_us=10000)  #channel 2 for blue LED

def statusLedsRED():
    PWM.add_channel_pulse(0, 16, 0, 999)
    PWM.add_channel_pulse(1, 19, 0, 0)
    PWM.add_channel_pulse(2, 13, 0, 0)

def statusLedsGREEN():
    PWM.add_channel_pulse(0, 16, 0, 0)
    PWM.add_channel_pulse(1, 19, 0, 250)
    PWM.add_channel_pulse(2, 13, 0, 0)

def statusLedsBLUE():
    PWM.add_channel_pulse(0, 16, 0, 0)
    PWM.add_channel_pulse(1, 19, 0, 0)
    PWM.add_channel_pulse(2, 13, 0, 250)


initLEDs()

while True:

    try:
        pass
        n = raw_input("r, g, or b?\n")
        # if n == '1':
        #     PWM.add_channel_pulse(0, red, 0, 50)
        # elif n == '2':
        #     PWM.add_channel_pulse(0, red, 0, 1000)
        # elif n == '3':
        #     PWM.add_channel_pulse(1, blue, 0, 1500)
        # elif n == '4':
        #     PWM.add_channel_pulse(1, blue, 0, 400)
        if n == 'r':
            statusLedsRED()
        if n == '2':
            PWM.add_channel_pulse(0, red, 0, 500)
            PWM.add_channel_pulse(1, green, 0, 0)
            PWM.add_channel_pulse(2, blue, 0, 0)
        elif n == 'g':
            statusLedsGREEN()
        elif n == 'b':
            statusLedsBLUE()
        elif n == 's':
            d = .01
            while True:
                PWM.add_channel_pulse(0, red, 0, 200)
                PWM.add_channel_pulse(1, green, 0, 0)
                PWM.add_channel_pulse(2, blue, 0, 0)
                time.sleep(d)
                PWM.add_channel_pulse(0, red, 0, 100)
                PWM.add_channel_pulse(1, green, 0, 0)
                PWM.add_channel_pulse(2, blue, 0, 200)
                time.sleep(d)
                PWM.add_channel_pulse(0, red, 0, 0)
                PWM.add_channel_pulse(1, green, 0, 0)
                PWM.add_channel_pulse(2, blue, 0, 400)
                time.sleep(d)
                PWM.add_channel_pulse(0, red, 0, 200)
                PWM.add_channel_pulse(1, green, 0, 0)
                PWM.add_channel_pulse(2, blue, 0, 400)
                time.sleep(d)
        elif n == 'f':
            for y in range(0, 10):
                for x in range(0, 999):
                    PWM.add_channel_pulse(0, red, 0, x)
                    PWM.add_channel_pulse(1, green, 0, 0)
                    PWM.add_channel_pulse(2, blue, 0, 999 - x)
                    time.sleep(.005)
        elif n == 'p':
            PWM.add_channel_pulse(0, red, 0, 1999)
            PWM.add_channel_pulse(1, green, 0, 0)
            PWM.add_channel_pulse(2, blue, 0, 1999)
        elif n == 'y':
            PWM.add_channel_pulse(0, red, 0, 500)
            PWM.add_channel_pulse(1, green, 0, 500)
            PWM.add_channel_pulse(2, blue, 0, 0)
        elif n == 'o':
            PWM.add_channel_pulse(0, red, 0, 0)
            PWM.add_channel_pulse(1, green, 0, 0)
            PWM.add_channel_pulse(2, blue, 0, 0)
    except KeyboardInterrupt:
        PWM.cleanup()
        # rgb.stop_servo(17)
        break