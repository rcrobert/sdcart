import RPi.GPIO as GPIO
import time

class LEDcontroller(object):

    RED = 35
    GREEN = 36
    BLUE = 33

    on = False

    @classmethod
    def init(cls):
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(cls.RED, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(cls.GREEN, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(cls.BLUE, GPIO.OUT, initial=GPIO.LOW)

    @classmethod
    def toggle(cls):
        if cls.on:
            GPIO.output(cls.RED, GPIO.LOW)
            GPIO.output(cls.GREEN, GPIO.LOW)
            print("off")
            cls.on = False
        else:
            GPIO.output(cls.RED, GPIO.HIGH)
            GPIO.output(cls.GREEN, GPIO.HIGH)
            print("on")
            cls.on = True

l = LEDcontroller()
l.init()

b = GPIO.PWM(l.BLUE, 40000)
r = GPIO.PWM(l.RED, 40000)
g = GPIO.PWM(l.GREEN, 40000)
# b.start(0)
# r.start(0)
# g.start(0)

while True:
    try:

        n = raw_input("led y or n?\n")
        if n == 'y':
            l.toggle()
        if n == 'b':
            b.start(100)
        if n == '3':
            GPIO.output(l.RED, GPIO.HIGH)
            GPIO.output(l.GREEN, GPIO.HIGH)
        if n == 'r':
            b.start(75)
            r.start(75)
        if n == 'o':
            b.stop()
            r.stop()
            g.stop()
        if n == 'x':

            for x in range(0, 101, 5):
                g.ChangeDutyCycle(x)
                r.ChangeDutyCycle(100 - x)
                time.sleep(0.5)
            for x in range(100, -1, -5):
                g.ChangeDutyCycle(x)
                r.ChangeDutyCycle(100 - x)
                time.sleep(0.5)

        # if n == 'y':
        #     g.ChangeDutyCycle(5)
        #     r.ChangeDutyCycle(100)


        else:
            pass




    except KeyboardInterrupt:
        GPIO.cleanup()
        break

