# import RPIO.PWM as PWM
import RPi.GPIO as GPIO


class LEDController(object):
    # RGB Uppers
    # 36
    # 33
    # 35

    # RGB Lowers
    # 29
    # 31
    # 32
    RED = 35
    GREEN = 36
    BLUE = 33

    @classmethod
    def init(cls):
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(cls.RED, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(cls.GREEN, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(cls.BLUE, GPIO.OUT, initial=GPIO.LOW)

    @classmethod
    def close(cls):
        pass

    @classmethod
    def toggle(cls, led, state):
        GPIO.output(led, state)


# class LED(object):
#     brightness = 500
#
#     @classmethod
#     def initLeds(cls):
#         PWM.setup()
#         PWM.set_loglevel(PWM.LOG_LEVEL_ERRORS)
#         PWM.init_channel(0, subcycle_time_us=10000)  #channel 0 for red LED
#         PWM.init_channel(1, subcycle_time_us=10000)  #channel 1 for green LED
#         PWM.init_channel(2, subcycle_time_us=10000)  #channel 2 for blue LED
#
#     @classmethod
#     def statusLedsRED(cls):
#         PWM.add_channel_pulse(0, 16, 0, cls.brightness)
#         PWM.add_channel_pulse(1, 19, 0, 0)
#         PWM.add_channel_pulse(2, 13, 0, 0)
#
#     @classmethod
#     def statusLedsGREEN(cls):
#         PWM.add_channel_pulse(0, 16, 0, 0)
#         PWM.add_channel_pulse(1, 19, 0, cls.brightness)
#         PWM.add_channel_pulse(2, 13, 0, 0)
#
#     @classmethod
#     def statusLedsBLUE(cls):
#         PWM.add_channel_pulse(0, 16, 0, 0)
#         PWM.add_channel_pulse(1, 19, 0, 0)
#         PWM.add_channel_pulse(2, 13, 0, cls.brightness)
#
#     @classmethod
#     def statusLedsOFF(cls):
#         PWM.add_channel_pulse(0, 16, 0, 0)
#         PWM.add_channel_pulse(1, 19, 0, 0)
#         PWM.add_channel_pulse(2, 13, 0, 0)


if __name__ == "__main__":

    LEDController.init()
    LEDController.toggle(LEDController.GREEN, 1)

    while True:
        try:
            pass
        except KeyboardInterrupt:
            break

    # import time
    #
    # red = 16
    # green = 19
    # blue = 13
    #
    # LED.initLEDs()
    #
    # while True:
    #
    #     try:
    #         pass
    #         n = raw_input("r, g, or b?\n")
    #         # if n == '1':
    #         #     PWM.add_channel_pulse(0, red, 0, 50)
    #         # elif n == '2':
    #         #     PWM.add_channel_pulse(0, red, 0, 1000)
    #         # elif n == '3':
    #         #     PWM.add_channel_pulse(1, blue, 0, 1500)
    #         # elif n == '4':
    #         #     PWM.add_channel_pulse(1, blue, 0, 400)
    #         if n == 'r':
    #             LED.statusLedsRED()
    #         if n == '2':
    #             PWM.add_channel_pulse(0, red, 0, 500)
    #             PWM.add_channel_pulse(1, green, 0, 0)
    #             PWM.add_channel_pulse(2, blue, 0, 0)
    #         elif n == 'g':
    #             LED.statusLedsGREEN()
    #         elif n == 'b':
    #             LED.statusLedsBLUE()
    #         elif n == 's':
    #             d = .01
    #             while True:
    #                 PWM.add_channel_pulse(0, red, 0, 200)
    #                 PWM.add_channel_pulse(1, green, 0, 0)
    #                 PWM.add_channel_pulse(2, blue, 0, 0)
    #                 time.sleep(d)
    #                 PWM.add_channel_pulse(0, red, 0, 100)
    #                 PWM.add_channel_pulse(1, green, 0, 0)
    #                 PWM.add_channel_pulse(2, blue, 0, 200)
    #                 time.sleep(d)
    #                 PWM.add_channel_pulse(0, red, 0, 0)
    #                 PWM.add_channel_pulse(1, green, 0, 0)
    #                 PWM.add_channel_pulse(2, blue, 0, 400)
    #                 time.sleep(d)
    #                 PWM.add_channel_pulse(0, red, 0, 200)
    #                 PWM.add_channel_pulse(1, green, 0, 0)
    #                 PWM.add_channel_pulse(2, blue, 0, 400)
    #                 time.sleep(d)
    #         elif n == 'f':
    #             for y in range(0, 10):
    #                 for x in range(0, 999):
    #                     PWM.add_channel_pulse(0, red, 0, x)
    #                     PWM.add_channel_pulse(1, green, 0, 0)
    #                     PWM.add_channel_pulse(2, blue, 0, 999 - x)
    #                     time.sleep(.005)
    #         elif n == 'p':
    #             PWM.add_channel_pulse(0, red, 0, 1999)
    #             PWM.add_channel_pulse(1, green, 0, 0)
    #             PWM.add_channel_pulse(2, blue, 0, 1999)
    #         elif n == 'y':
    #             PWM.add_channel_pulse(0, red, 0, 500)
    #             PWM.add_channel_pulse(1, green, 0, 500)
    #             PWM.add_channel_pulse(2, blue, 0, 0)
    #         elif n == 'o':
    #             PWM.add_channel_pulse(0, red, 0, 0)
    #             PWM.add_channel_pulse(1, green, 0, 0)
    #             PWM.add_channel_pulse(2, blue, 0, 0)
    #     except KeyboardInterrupt:
    #         PWM.cleanup()
    #         # rgb.stop_servo(17)
    #         break