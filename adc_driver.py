import spidev
import sys
import time

import threading
import RPi.GPIO as GPIO


class ADC(object):

    ###############################################################
    # CLASS CONSTANTS AND PORTED MACROS
    ###############################################################

    # Defaults
    DEFAULT_FREQ = 5000
    DEFAULT_MODE = 0b11

    RESET_BITS = [0xFF for _ in xrange(50)]

    # COMM REGISTER
    AD7192_COMM_WEN = (1 << 7)
    COMM_WRITE = (0 << 6)
    COMM_READ = (1 << 6)
    COMM_CREAD = (1 << 2)

    @staticmethod
    def COMM_ADDR(x):
        return (x & 0x07) << 3

    # COMM REGISTER ADDRESSES
    COMM_REG = 0x0
    STATUS_REG = 0x0
    MODE_REG = 0x1
    CONFIG_REG = 0x2
    DATA_REG = 0x3
    ID_REG = 0x4
    GPOCON_REG = 0x5
    OFFSET_REG = 0x6
    FULLSCALE_REG = 0x7

    # MODE REGISTER
    MODE_SEL_MASK = (0x7 << 21)             # Operation Mode Select Mask
    MODE_DAT_STA = (1 << 20)                # Status Register transmission
    MODE_SINC3 = (1 << 15)                  # SINC3 Filter Select
    MODE_ACX = (1 << 14)                    # AC excitation enable(AD7195 only)
    MODE_ENPAR = (1 << 13)                  # Parity Enable
    MODE_CLKDIV = (1 << 12)                 # Clock divide by 2 (AD7190/2 only)
    MODE_SCYCLE = (1 << 11)                 # Single cycle conversion
    MODE_REJ60 = (1 << 10)                  # 50/60Hz notch filter

    @staticmethod
    def MODE_SEL(x):
        return (x & 0x7) << 21              # Operation Mode Select

    @staticmethod
    def MODE_CLKSRC(x):
        return (x & 0x3) << 18              # Clock Source Select

    @staticmethod
    def MODE_RATE(x):
        return x & 0x3FF                    # Filter Update Rate Select

    # MODE_SEL Options
    MODE_CONT = 0                           # Continuous Conversion Mode
    MODE_SINGLE = 1                         # Single Conversion Mode
    MODE_IDLE = 2                           # Idle Mode
    MODE_PWRDN = 3                          # Power-Down Mode
    MODE_CAL_INT_ZERO = 4                   # Internal Zero-Scale Calibration
    MODE_CAL_INT_FULL = 5                   # Internal Full-Scale Calibration
    MODE_CAL_SYS_ZERO = 6                  # System Zero-Scale Calibration
    MODE_CAL_SYS_FULL = 7                   # System Full-Scale Calibration

    # STATUS REGISTER BIT DESIGNATIONS
    STAT_RDY = (1 << 7)                     # Ready
    STAT_ERR = (1 << 6)                     # Error (Overrange, Underrange)
    STAT_NOREF = (1 << 5)                   # Error no external reference
    STAT_PARITY = (1 << 4)                  # Parity
    STAT_CH3 = (1 << 2)                     # Channel 3
    STAT_CH2 = (1 << 1)                     # Channel 2
    STAT_CH1 = (1 << 0)                     # Channel 1

    ###############################################################
    # PUBLIC METHODS
    ###############################################################

    def __init__(self, port, chip, cs_pin):
        self.spi = spidev.SpiDev()
        self.spi.open(port, chip)
        self.spi.cshigh = False
        self.spi.max_speed_hz = 1000000
        self.spi.mode = 0b11

        # Use GPIO for chip select, not the built-in
        self.cs = cs_pin
        GPIO.setup(cs_pin, GPIO.OUT, initial=GPIO.HIGH)

        self._bridgePower = False

    def close(self):
        self.spi.close()

    def reset(self):
        self.spi.writebytes(self.RESET_BITS)

    def bridge_power(self):
        return self._bridgePower

    def writebytes(self, byte_list):
        """Simplify scoping for writing bytes to the ADC.

        :param byte_list: Byte list to send to ADC.
        :return: None.
        """
        self.spi.writebytes(byte_list)

    def readbytes(self, num):
        """Simplify scoping for reading bytes from the ADC.

        :param num: Number of bytes to read
        :return: Byte list returned from ADC.
        """
        return self.spi.readbytes(num)

    # Configuration Functions
    def ConfigurePseudoGain1(self):
        self.spi.writebytes([self.COMM_WRITE | self.COMM_ADDR(self.CONFIG_REG)])
        self.spi.writebytes([0x00])
        self.spi.writebytes([0x10])
        self.spi.writebytes([0x58])
        self.spi.writebytes([self.COMM_READ | self.COMM_ADDR(self.CONFIG_REG)])

    def ConfigureGain128Ch1(self):  #CHANNEL 1
        self.spi.writebytes([self.COMM_WRITE | self.COMM_ADDR(self.CONFIG_REG)])
        self.spi.writebytes([0x00])
        self.spi.writebytes([0x01])  #differential Channel AN1-AN2
        self.spi.writebytes([0x57])  #Reference detect on, buffered inputs, gain 128

    def ConfigureGain128Ch2(self):  #CHANNEL 2
        self.spi.writebytes([self.COMM_WRITE | self.COMM_ADDR(self.CONFIG_REG)])
        self.spi.writebytes([0x00])
        self.spi.writebytes([0x02])  #differential Channel AN3-AN4
        self.spi.writebytes([0x57])  #Reference detect on, buffered inputs, gain 128

    def ConfigureGain128Ch1CHOP(self):
        self.spi.writebytes([self.COMM_WRITE | self.COMM_ADDR(self.CONFIG_REG)])
        self.spi.writebytes([0x80])  #Chop Enabled
        self.spi.writebytes([0x01])  #differential Channel AN1-AN2
        self.spi.writebytes([0x5F])  #Reference detect on, buffered inputs, gain 128

    POLARITY_UNIPOLAR = 1
    POLARITY_BIPOLAR = 2

    def MultiChannelEnable(self, polarity):
        self.spi.writebytes([self.COMM_WRITE | self.COMM_ADDR(self.CONFIG_REG)])
        self.spi.writebytes([0x00])
        self.spi.writebytes([0x03])  #Auto sequences between differential channels 1 & 2
        if polarity == 1:
            self.spi.writebytes([0x5F])  #Reference detect on, buffered inputs, gain 128, unipolar
            print("Both Channels Enabled in Unipolar Mode")
        elif polarity == 2:
            self.spi.writebytes([0x57])  #Reference detect on, buffered inputs, gain 128, bipolar
            print("Both Channels Enabled in Bipolar Mode")

    def FullScaleCalibration(self):
        complete = False
        self.spi.writebytes([self.COMM_WRITE | self.COMM_ADDR(self.MODE_REG)])
        self.spi.writebytes([0xB8])
        self.spi.writebytes([0x08])
        self.spi.writebytes([0xFF])
        while not complete:
            status = self.ReadStatusReg()
            if not status[0] >> 7:
                complete = True

    def ZeroScaleCalibration(self):
        complete = False
        self.spi.writebytes([self.COMM_WRITE | self.COMM_ADDR(self.MODE_REG)])
        self.spi.writebytes([0x98])
        self.spi.writebytes([0x08])
        self.spi.writebytes([0xFF])
        while not complete:
            status = self.ReadStatusReg()
            if not status[0] >> 7:
                complete = True

    # Mode Functions
    def SetModeZL9Hz(self):  #9.4Hz Zero Latency
        self.spi.writebytes([self.COMM_WRITE | self.COMM_ADDR(self.MODE_REG)])
        self.spi.writebytes([0x18])  #continuous conversion mode, appends status register to data output, internal 4.92 MHz clock, MCLK2 is tristated
        self.spi.writebytes([0x09])  #sinc4 filter is used, parity disabled, zero latency. output rate falls over to next
        self.spi.writebytes([0xFF])  #9.4Hz output rate

    def SetMode10Hz(self):  #10Hz
        self.spi.writebytes([self.COMM_WRITE | self.COMM_ADDR(self.MODE_REG)])
        self.spi.writebytes([0x18])  #continuous conversion mode, appends status register to data output, internal 4.92 MHz clock, MCLK2 is tristated
        self.spi.writebytes([0x09])  #sinc4 filter is used, parity disabled, zero latency. output rate falls over to next
        self.spi.writebytes([0xE0])

    def SetMode50Hz(self):  #50Hz
        self.spi.writebytes([self.COMM_WRITE | self.COMM_ADDR(self.MODE_REG)])
        self.spi.writebytes([0x18])  #continuous conversion mode, appends status register to data output, internal 4.92 MHz clock, MCLK2 is tristated
        self.spi.writebytes([0x08])  #sinc4 filter is used, parity disabled, zero latency. output rate falls over to next
        self.spi.writebytes([0x60])

    def SetMode5Hz(self):  #4.7Hz
        self.spi.writebytes([self.COMM_WRITE | self.COMM_ADDR(self.MODE_REG)])
        self.spi.writebytes([0x18])  #continuous conversion mode, appends status register to data output, internal 4.92 MHz clock, MCLK2 is tristated
        self.spi.writebytes([0x03])  #sinc4 filter is used, parity disabled, zero latency. output rate falls over to next
        self.spi.writebytes([0xFF])

    def SetMode5HzZL(self):  #4.7Hz
        self.spi.writebytes([self.COMM_WRITE | self.COMM_ADDR(self.MODE_REG)])
        self.spi.writebytes([0x18])  #continuous conversion mode, appends status register to data output, internal 4.92 MHz clock, MCLK2 is tristated
        self.spi.writebytes([0x03])  #sinc4 filter is used, parity disabled, zero latency. output rate falls over to next
        self.spi.writebytes([0xFF])

    def SetMode25Hz(self):  #25Hz
        self.spi.writebytes([self.COMM_WRITE | self.COMM_ADDR(self.MODE_REG)])
        self.spi.writebytes([0x18])  #continuous conversion mode, appends status register to data output, internal 4.92 MHz clock, MCLK2 is tristated
        self.spi.writebytes([0x08])  #sinc4 filter is used, parity disabled, zero latency. output rate falls over to next
        self.spi.writebytes([0xC0])

    def SetMode300Hz(self):  #300Hz
        self.spi.writebytes([self.COMM_WRITE | self.COMM_ADDR(self.MODE_REG)])
        self.spi.writebytes([0x18])  #continuous conversion mode, appends status register to data output, internal 4.92 MHz clock, MCLK2 is tristated
        self.spi.writebytes([0x08])  #sinc4 filter is used, parity disabled, zero latency. output rate falls over to next
        self.spi.writebytes([0x10])

    def SetMode960Hz(self):  #960Hz
        self.spi.writebytes([self.COMM_WRITE | self.COMM_ADDR(self.MODE_REG)])
        self.spi.writebytes([0x18])  #continuous conversion mode, appends status register to data output, internal 4.92 MHz clock, MCLK2 is tristated
        self.spi.writebytes([0x08])  #sinc4 filter is used, parity disabled, zero latency. output rate falls over to next
        self.spi.writebytes([0x05])

    def SetMode2400Hz(self):  #2400Hz
        self.spi.writebytes([self.COMM_WRITE | self.COMM_ADDR(self.MODE_REG)])
        self.spi.writebytes([0x18])  #continuous conversion mode, appends status register to data output, internal 4.92 MHz clock, MCLK2 is tristated
        self.spi.writebytes([0x08])  #sinc4 filter is used, parity disabled, zero latency. output rate falls over to next
        self.spi.writebytes([0x02])

    def SetMode4800Hz(self):  #4800Hz
        self.spi.writebytes([self.COMM_WRITE | self.COMM_ADDR(self.MODE_REG)])
        self.spi.writebytes([0x18])  #continuous conversion mode, appends status register to data output, internal 4.92 MHz clock, MCLK2 is tristated
        self.spi.writebytes([0x08])  #sinc4 filter is used, parity disabled, zero latency. output rate falls over to next
        self.spi.writebytes([0x01])

    def ToggleBridgePower(self):
        if not self._bridgePower:
            self.spi.writebytes([self.COMM_WRITE | self.COMM_ADDR(self.GPOCON_REG)])
            self.spi.writebytes([0x40])
            self.spi.writebytes([self.COMM_READ | self.COMM_ADDR(self.GPOCON_REG)])
            read = self.spi.readbytes(1)
            if read[0] & 0x40:
                self._bridgePower = True
        elif self._bridgePower:
            self.spi.writebytes([self.COMM_WRITE | self.COMM_ADDR(self.GPOCON_REG)])
            self.spi.writebytes([0x00])
            self.spi.writebytes([self.COMM_READ | self.COMM_ADDR(self.GPOCON_REG)])
            read = self.spi.readbytes(1)
            if not read[0] & 0x40:
                self._bridgePower = False

    def BridgePowerOn(self):
        self.spi.writebytes([self.COMM_WRITE | self.COMM_ADDR(self.GPOCON_REG)])
        self.spi.writebytes([0x40])
        self.spi.writebytes([self.COMM_READ | self.COMM_ADDR(self.GPOCON_REG)])
        read = self.spi.readbytes(1)
        if read[0] & 0x40:
            self._bridgePower = True
            print('Bridge Power On')
        else:
            print('***********************Bridge Power Off, Check Power to AD7192***********************')

    # Read Functions
    def ReadModeReg(self):
        self.spi.writebytes([self.COMM_READ | self.COMM_ADDR(self.MODE_REG)])
        response = self.spi.readbytes(3)
        return response

    def ReadStatusReg(self):
        self.spi.writebytes([self.COMM_READ | self.COMM_ADDR(self.STATUS_REG)])
        response = self.spi.readbytes(1)
        return response

    def ReadConfigReg(self):
        self.spi.writebytes([self.COMM_READ | self.COMM_ADDR(self.CONFIG_REG)])
        response = self.spi.readbytes(3)
        return response

    def ReadDataRegCH1(self):
        self.spi.writebytes([self.COMM_READ | self.COMM_ADDR(self.DATA_REG)])
        data = self.spi.readbytes(4)
        result = (data[0] << 16) + (data[1] << 8) + data[2]
        return [result, data[3]]

    def ReadDataRegCH2(self):
        self.ConfigureGain128Ch2()
        self.spi.writebytes([self.COMM_READ | self.COMM_ADDR(self.DATA_REG)])
        data = self.spi.readbytes(4)
        result = (data[0] << 16) + (data[1] << 8) + data[2]
        return [result, data[3]]

    def ReadDataReg(self):
        self.spi.writebytes([self.COMM_READ | self.COMM_ADDR(self.DATA_REG)])
        data = self.spi.readbytes(4)
        result = (data[0] << 16) + (data[1] << 8) + data[2]
        return [result, data[3]]


class ADCError(Exception):
    def __init__(self, args):
        self.args = args


class ADCController(threading.Thread):
    CHIP_1 = 0
    CHIP_2 = 1

    LOAD_CELL_1 = 0
    LOAD_CELL_2 = 1
    LOAD_CELL_3 = 2
    LOAD_CELL_4 = 3

    LC1_OFFSET = 130220
    LC2_OFFSET = 132756
    LC3_OFFSET = 129746
    LC4_OFFSET = 129713

    def __init__(self):
        super(ADCController, self).__init__()
        self._adc_list = []
        self._initialized = False

        # Handles for ADCs
        self._ADC1 = None
        self._ADC2 = None

        # Initialize GPIO
        GPIO.setmode(GPIO.BOARD)

        # Initialize lock for sharing weight
        self.weight_lock = threading.Lock()

        # Store total weight
        self.weight = 0.0

        # Create threading Events for control
        self.term_event = threading.Event()

        # Configurable settings
        self.average_count = 60.0
        self.shift = 6
        self.threshold = 20
        self.deviation_limit = 1.0
        self.steady_count = 5

        # Variables used in run()
        self._last_weight = 0

    def run(self):
        # Initialize the ADCs
        self.initialize()

        # Check if its initialized, raise an error, THIS SHOULD NEVER HAPPEN WITH INITIALIZE() CALL IN RUN
        if not self._initialized:
            raise ADCError('ADCs must be initialized before running')

        TARE_OFFSET_1 = 0
        TARE_OFFSET_2 = 0
        TARE_OFFSET_3 = 0
        TARE_OFFSET_4 = 0
        oldAvg1 = 0
        oldAvg2 = 0
        oldAvg1_A2 = 0
        oldAvg2_A2 = 0
        lastVal = 0
        lastVal2 = 0
        lastVal_A2 = 0
        lastVal2_A2 = 0
        tare_1_ready = False
        tare_2_ready = False
        tare_3_ready = False
        tare_4_ready = False
        gramLimit = 0

        read_LC1 = False
        read_LC2 = False
        read_LC3 = False
        read_LC4 = False

        totalChange_grams = 0


        # Arrays for checking for stable values
        array1 = []
        array2 = []
        array3 = []
        array4 = []

        for i in range(self.steady_count):
            array1.append(0)
            array2.append(0)
            array3.append(0)
            array4.append(0)

        steadyVal_1 = 0
        steadyVal_2 = 0
        steadyVal_3 = 0
        steadyVal_4 = 0

        steady1 = True
        steady2 = True
        steady3 = True
        steady4 = True

        ch1_ADC1 = {
            'values': [],
            'average': 0,
            'lbs': 0
        }
        ch2_ADC1 = {
            'values': [],
            'average': 0,
            'lbs': 0
        }
        ch1_ADC2 = {
            'values': [],
            'average': 0,
            'lbs': 0
        }
        ch2_ADC2 = {
            'values': [],
            'average': 0,
            'lbs': 0
        }

        while True:
            # Check termination signal for safely ending thread
            if self.term_event.is_set():
                # Perform any necessary cleanup steps
                self.select_chip(self.CHIP_1)
                self._ADC1.close()

                self.select_chip(self.CHIP_2)
                self._ADC2.close()

                GPIO.cleanup()
                break



            # Get Data
            # print 'Reading ADC1'
            self.select_chip(self.CHIP_1)
            data = self._ADC1.ReadDataReg()

            # print 'Reading ADC2'
            self.select_chip(self.CHIP_2)
            data2 = self._ADC2.ReadDataReg()


            deltaGrams_LC1 = 0
            deltaGrams_LC2 = 0
            deltaGrams_LC3 = 0
            deltaGrams_LC4 = 0


            # ADC 1 DATA
            if not data[1] >> 7:

                if (data[1] << 7) == 0x00:     #channel 1 --- LOAD CELL #1
                    read_LC1 = True

                    if data[1] == 0x40:
                        print("Channel 1 error")

                    if abs((data[0] >> self.shift) - lastVal) > self.threshold:
                        ch1_ADC1['values'] = []
                    if len(ch1_ADC1['values']) != self.average_count:
                        ch1_ADC1['values'].append(data[0] >> self.shift)
                        lastVal = data[0] >> self.shift
                    else:
                        ch1_ADC1['values'].pop(0)
                        ch1_ADC1['values'].append(data[0] >> self.shift)
                        lastVal = data[0] >> self.shift

                        # compute average
                        avg_sum = 0
                        for val in ch1_ADC1['values']:
                            avg_sum += val
                        ch1_ADC1['average'] = (avg_sum / self.average_count)

                        # delta1 = ch1_ADC1['average'] - oldAvg1
                        # deltaLB = self.delta_to_lbs(delta1, self.LOAD_CELL_1)
                        # print(ch1_ADC1['average'])
                        if not steady1:
                            # print('Not steady')
                            #shift in value
                            if len(array1) == self.steady_count:
                                array1.pop(0)
                            array1.append(ch1_ADC1['average'])

                        if abs((max(array1) - min(array1))) > self.deviation_limit:
                            # print('Out of bounds')
                            steady1 = False
                            array1 = []
                            #shift in value
                            array1.append(ch1_ADC1['average'])

                        elif len(array1) == self.steady_count and not steady1:
                            #average
                            new_steady1 = sum(array1) / len(array1)
                            deltaWeight1 = new_steady1 - steadyVal_1
                            if self.to_grams(deltaWeight1, self.LOAD_CELL_1) < 20000:   # protects from start up spike reading
                                deltaGrams_LC1 = self.to_grams(deltaWeight1, self.LOAD_CELL_1)
                                # print("deltaWeight1: " + repr(round(deltaWeight1, 1)))
                                # print("LC1 grams: " + repr(self.to_grams(deltaWeight1, self.LOAD_CELL_1)))
                            steadyVal_1 = new_steady1
                            steady1 = True

                        if abs(steadyVal_1 - ch1_ADC1['average']) > self.deviation_limit:
                            steady1 = False
                            #shift in value
                            if len(array1) == self.steady_count:
                                array1.pop(0)
                            array1.append(ch1_ADC1['average'])

                elif data[1] & 0x01:       #channel 2 ---- LOAD CELL #2
                    read_LC2 = True

                    if data[1] == 0x41:
                        print("Channel 2 error")

                    if abs((data[0] >> self.shift) - lastVal2) > self.threshold:
                        ch2_ADC1['values'] = []

                    if len(ch2_ADC1['values']) != self.average_count:

                        ch2_ADC1['values'].append(data[0] >> self.shift)
                        lastVal2 = data[0] >> self.shift
                    else:
                        ch2_ADC1['values'].pop(0)
                        ch2_ADC1['values'].append(data[0] >> self.shift)
                        lastVal2 = data[0] >> self.shift



                        # compute average
                        avg_sum = 0
                        for val in ch2_ADC1['values']:
                            avg_sum += val
                        ch2_ADC1['average'] = (avg_sum / self.average_count)

                        # delta2 = ch2_ADC1['average'] - oldAvg2
                        # deltaLB2 = self.delta_to_lbs(delta2, self.LOAD_CELL_2)

                        if not steady2:
                            # print('Not steady')
                            #shift in value
                            if len(array2) == self.steady_count:
                                array2.pop(0)
                            array2.append(ch2_ADC1['average'])

                        if abs((max(array2) - min(array2))) > self.deviation_limit:
                            # print('Out of bounds')
                            steady2 = False
                            array2 = []
                            #shift in value
                            array2.append(ch2_ADC1['average'])

                        elif len(array2) == self.steady_count and not steady2:
                            #average
                            new_steady2 = sum(array2) / len(array2)
                            deltaWeight2 = new_steady2 - steadyVal_2
                            if self.to_grams(deltaWeight2, self.LOAD_CELL_2) < 20000:   # protects from start up spike reading
                                deltaGrams_LC2 = self.to_grams(deltaWeight2, self.LOAD_CELL_2)
                                # print("steady val: " + repr(steadyVal_2))
                                # print("LC2 grams: " + repr(self.to_grams(deltaWeight2, self.LOAD_CELL_2)))
                            steadyVal_2 = new_steady2
                            read_LC2 = True
                            steady2 = True

                        if abs(steadyVal_2 - ch2_ADC1['average']) > self.deviation_limit:
                            # print('Away from steady')
                            steady2 = False
                            #shift in value
                            if len(array2) == self.steady_count:
                                array2.pop(0)
                            array2.append(ch2_ADC1['average'])

            # ADC 2 DATA
            if not data2[1] >> 7:

                if (data2[1] << 7) == 0x00:     #channel 1              LOAD CELL #3

                    if data2[1] == 0x40:
                        print("Channel 1 - ADC 2 error")

                    if abs((data2[0] >> self.shift) - lastVal_A2) > self.threshold:   # if value changes by a lot, reset moving average filter
                        ch1_ADC2['values'] = []
                    if len(ch1_ADC2['values']) != self.average_count:
                        ch1_ADC2['values'].append(data2[0] >> self.shift)
                        lastVal_A2 = data2[0] >> self.shift
                    else:
                        ch1_ADC2['values'].pop(0)
                        ch1_ADC2['values'].append(data2[0] >> self.shift)
                        lastVal_A2 = data2[0] >> self.shift

                        # compute average
                        avg_sum = 0
                        for val in ch1_ADC2['values']:
                            avg_sum += val
                        ch1_ADC2['average'] = (avg_sum / self.average_count)

                        delta1 = ch1_ADC2['average'] - oldAvg1_A2
                        deltaLB = self.delta_to_lbs(delta1, self.LOAD_CELL_3)

                        if abs(delta1) > .2:
                            ch1_ADC2['lbs'] = self.to_lbs(ch1_ADC2['average'], self.LOAD_CELL_3)
                            read_LC3 = True
                            # print([round(delta1, 1), round(ch1_ADC2['average'] - LC3_OFFSET, 1), 'Load Cell 3'])
                            # print(repr(self.toGrams(ch1_ADC2['average'], self.LOAD_CELL_3)) + ' grams LC3')
                            # print(repr(ch1_ADC2['lbs']) + ' pounds')
                            oldAvg1_A2 = ch1_ADC2['average']

                elif data2[1] & 0x01:       #channel 2          LOAD CELL #4
                    # print("data: " + repr(hex(data2[0] >> self.shift)))
                    if data2[1] == 0x41:
                        print("Channel 2-ADC 2 error")

                    if abs((data2[0] >> self.shift) - lastVal2_A2) > self.threshold:
                        ch2_ADC2['values'] = []

                    if len(ch2_ADC2['values']) != self.average_count:
                        ch2_ADC2['values'].append(data2[0] >> self.shift)
                        lastVal2_A2 = data2[0] >> self.shift

                    else:
                        ch2_ADC2['values'].pop(0)
                        ch2_ADC2['values'].append(data2[0] >> self.shift)
                        lastVal2_A2 = data2[0] >> self.shift


                        # compute average
                        avg_sum = 0
                        for val in ch2_ADC2['values']:
                            avg_sum += val
                        ch2_ADC2['average'] = (avg_sum / self.average_count)



                        # display
                        delta2 = ch2_ADC2['average'] - oldAvg2_A2
                        deltaLB2 = self.delta_to_lbs(delta2, self.LOAD_CELL_4)

                        if abs(deltaLB2) > .0021:
                        # elif not tare and abs(delta2) > .2:
                            ch2_ADC2['lbs'] = self.to_lbs(ch2_ADC2['average'], self.LOAD_CELL_4)
                            read_LC4 = True
                            # print([round(delta2, 1), round(ch2_ADC2['average'] - LC4_OFFSET, 1), 'Load Cell 4'])
                            # print(repr(self.toGrams(ch2_ADC2['average'], self.LOAD_CELL_4)) + ' grams LC4')
                            # print(repr(ch2_ADC2['lbs']) + ' pounds')
                            oldAvg2_A2 = ch2_ADC2['average']


            if steady1 and steady2:
                # print("got here")
                totalChange_grams += deltaGrams_LC1 + deltaGrams_LC2 + deltaGrams_LC3 + deltaGrams_LC4
                if abs(totalChange_grams) * 0.00220462 > .009:   # change in total weight has to change by .01 lbs
                    if self.weight_lock.acquire():
                        self.weight += totalChange_grams
                        # Release when done
                        self.weight_lock.release()
                    self._last_weight = self.weight
                    print("total weight: " + repr(self.weight) + " grams")
                    print(repr(round(self.weight * 0.00220462, 3)) + " lbs")
                    totalChange_grams = 0




                # readCount += 1


    def initialize(self):
        # Instantiate ADCs
        self._adc_list.append(ADC(0, 0, 16))
        self._adc_list.append(ADC(0, 1, 18))
        self._ADC1 = self._adc_list[0]
        self._ADC2 = self._adc_list[1]

        # Iterate through all indices and ADC objects
        for chip, adc in enumerate(self._adc_list):
            print 'Initializing ADC: ', chip



            # Select the ADC we are working with
            self.select_chip(chip)

            # Send reset signal
            adc.writebytes(ADC.RESET_BITS)
            time.sleep(0.0005)

            # Configure
            adc.ConfigureGain128Ch1()
            adc.MultiChannelEnable(ADC.POLARITY_BIPOLAR)
            adc.BridgePowerOn()
            adc.ZeroScaleCalibration()
            adc.FullScaleCalibration()
            adc.SetMode2400Hz()
            time.sleep(0.001)

        # Flag as initialized
        self._initialized = True

    def select_chip(self, chip):
        """Select an ADC to communicate with.

        :param chip: Channel from one of the class member variables.
        :return: None
        """
        # Deselect all chips
        for adc in self._adc_list:
            GPIO.output(adc.cs, 1)

        # Delay 20us for safety
        time.sleep(0.00002)

        # Select the chip we want
        GPIO.output(self._adc_list[chip].cs, 0)

    def enable_continuous_read(self, chip):
        # Select the ADC
        self.select_chip(chip)

        # Enable continuous read
        self._adc_list[chip].writebytes([0x5C])

    def disable_continuous_read(self, chip):
        # Select the ADC
        self.select_chip(chip)

        # Disable continuous read
        self._adc_list[chip].writebytes([0x58])

    @classmethod
    def to_lbs(cls, val, load_cell):
        if load_cell == cls.LOAD_CELL_1:
            return round(((val - cls.LC1_OFFSET) * 0.8049 - 0.1281) * .00220462, 4)
        elif load_cell == cls.LOAD_CELL_2:
            return round(((val - cls.LC2_OFFSET) * 0.8153 + 0.1841) * .00220462, 4)
        elif load_cell == cls.LOAD_CELL_3:
            return round(((val - cls.LC3_OFFSET) * 0.8677 - 0.0041) * .00220462, 4)
        elif load_cell == cls.LOAD_CELL_4:
            return round(((val - cls.LC4_OFFSET) * 0.8732 - 0.0613) * .00220462, 4)

    @classmethod
    def delta_to_lbs(cls, val, load_cell):
        # All values are for 7V
        if load_cell == cls.LOAD_CELL_1:
            return round((val * 0.8049 - 0.1281) * .00220462, 4)
        elif load_cell == cls.LOAD_CELL_2:
            return round((val * 0.8153 + 0.1841) * .00220462, 4)
        elif load_cell == cls.LOAD_CELL_3:
            return round((val * 0.8677 - 0.0041) * .00220462, 4)
        elif load_cell == cls.LOAD_CELL_4:
            return round((val * 0.8732 - 0.0613) * .00220462, 4)

    @classmethod
    def to_grams(cls, val, load_cell):
            if load_cell == cls.LOAD_CELL_1:
                return round(val * 0.805 - 0.1295, 1)
                # if abs(val) < 501:
                #     return round(val * 0.8016 - 0.0495, 1)
                # else:
                #     if val > 0:
                #         return round(val * 0.8042 - 4.9331, 1)
                #     if val < 0:
                #         return round(val * 0.8042 + 4.9331, 1)
                #     # return round(val * 0.805 - 0.0695, 1)

                #
            elif load_cell == cls.LOAD_CELL_2:
                return round(val * 0.8153 + 0.1841, 1)
            elif load_cell == cls.LOAD_CELL_3:
                return round((val - cls.LC3_OFFSET) * 0.8677 - 0.0041, 1)
            elif load_cell == cls.LOAD_CELL_4:
                return round((val - cls.LC4_OFFSET) * 0.8733 - 0.0834, 1)


def main():
    adc_control = ADCController()
    adc_control.daemon = False

    print 'Starting...'

    try:
        adc_control.start()
        while True:
            pass
    except KeyboardInterrupt:
        # Send exit command
        adc_control.term_event.set()

        print 'Waiting for thread to end...'
        adc_control.join()

        print 'closing...'
        sys.exit(0)

if __name__ == '__main__':
    main()