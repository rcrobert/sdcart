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


# class PWM(threading.Thread):
#     ADD_CHANNEL = 'pwm_cls_add_channel'
#     REMOVE_CHANNEL = 'pwm_cls_remove_channel'
#     CHANGE_DC = 'pwm_cls_change_dc'
#
#     class Command(object):
#         def __init__(self, command, *args):
#             self.type = command
#             self.args_list = args
#
#     class Channel(object):
#         def __init__(self, pin):
#             self.pin = pin
#             self.duty_cycle = 5
#             self.state = True
#
#     def __init__(self, frequency):
#         super(PWM, self).__init__()
#
#         self._period = 1.0 / frequency / 10.0
#         self._channels = []
#
#         self._term_event = threading.Event()
#
#         self._command_queue = Queue(maxsize=10)
#
#         GPIO.setmode(GPIO.BOARD)
#
#     def run(self):
#         count = 0
#         while True:
#             if self._term_event.is_set():
#                 # Cleanup
#                 break
#
#             try:
#                 # Pop and handle one command
#                 command = self._command_queue.get_nowait()
#
#                 if command.type == self.ADD_CHANNEL:
#                     # print 'Adding channels', command.args_list[0]
#
#                     for each in command.args_list[0]:
#                         GPIO.setup(each, GPIO.OUT, initial=GPIO.HIGH)
#                         self._channels.append(self.Channel(each))
#
#                 elif command.type == self.REMOVE_CHANNEL:
#                     # print 'Removing channels', command.args_list[0]
#
#                     for index, channel in enumerate(self._channels):
#                         if channel.pin == command.args_list[0]:
#                             self._channels.pop(index)
#                             break
#
#                 elif command.type == self.CHANGE_DC:
#                     # print 'Changing duty cycle of channel', command.args_list[0], 'to', command.args_list[1]
#
#                     for index, channel in enumerate(self._channels):
#                         if channel.pin == command.args_list[0]:
#                             self._channels[index].duty_cycle = command.args_list[1]
#                             break
#
#             except Empty:
#                 # Handle Empty exception and continue on
#                 pass
#
#             for each in self._channels:
#                 if count < each.duty_cycle and not each.state:
#                     # Turn on the channel
#                     # print 'Turning ON pin', each.pin
#                     GPIO.output(each.pin, 1)
#                     each.state = True
#                 elif count >= each.duty_cycle and each.state:
#                     # Turn off that channel
#                     # print 'Turning OFF pin', each.pin
#                     GPIO.output(each.pin, 0)
#                     each.state = False
#
#             # Increment and delay
#             count = (count + 1) % 10
#             time.sleep(self._period)
#
#     def add_channel(self, *pins):
#         self._command_queue.put_nowait(self.Command(self.ADD_CHANNEL, pins))
#
#     def remove_channel(self, pin):
#         self._command_queue.put_nowait(self.Command(self.REMOVE_CHANNEL, pin))
#
#     def set_duty_cycle(self, channel, dc):
#         self._command_queue.put_nowait(self.Command(self.CHANGE_DC, channel, dc))
#
#
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