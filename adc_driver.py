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
        self.spi.max_speed_hz = 250000
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
        self.num_chips = 2
        self.num_load_cells = 4
        self.average_count = 60.0
        self.shift = 6
        self.threshold = 20
        self.deviation_limit = 1.0
        self.steady_count = 100

    def _initialize(self):
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

    def run(self):
        # Initialize the ADCs
        self._initialize()

        # Check if its initialized, raise an error, THIS SHOULD NEVER HAPPEN WITH INITIALIZE() CALL IN RUN
        if not self._initialized:
            raise ADCError('ADCs must be initialized before running')

        """
        Need:
        -raw ADC read
        -array for average
        -average
        -lastVal, raw ADC read data post-shift
        -array for steady values
        -steadyVal_x, last steady value
        -steadyx, boolean stability state
        """
        class ChannelValues(object):
            def __init__(self):
                # Most recent and last raw ADC reads
                self.read = 0
                self.last_read = 0

                # All values to average and the current average
                self.average_array = []
                self.average = 0.0

                # Last set of stable values, current stable level, and boolean stability
                self.stable_array = []
                self.stable = 0.0
                self.is_stable = True

        # Instantiate value holders
        channel_vals = []
        read_data = [[], []]
        delta_weight = 0.0

        for i in xrange(self.num_load_cells):
            channel_vals.append(ChannelValues())

        # Initialize stable array
        for ch in channel_vals:
            for i in xrange(self.steady_count):
                ch.stable_array.append(0)

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

            # Read data from both ADCs
            self.select_chip(self.CHIP_1)
            read_data[0] = self._ADC1.ReadDataReg()
            self.select_chip(self.CHIP_2)
            read_data[1] = self._ADC2.ReadDataReg()

            # Iterate through ADC return data
            for chip, data in enumerate(read_data):
                # Check if data ready, if not skip this reading
                if data[1] >> 7:
                    continue

                # Determine channel
                if (data[1] << 7) == 0x00:
                    channel = 0
                elif data[1] & 0x01:
                    channel = 1
                else:
                    # Raise an error if its neither channel?
                    # TODO: what do we do if it is neither channel
                    pass

                # Index calculation given an ADC and channel, maps into class constant values for load cells
                current_load_cell = chip * 2 + channel
                channel_data = channel_vals[current_load_cell]

                # TODO: fix LC4
                # if current_load_cell == self.LOAD_CELL_4:
                #     continue

                # Shift out lower bits from raw data
                shifted_data = data[0] >> self.shift

                # If the raw read delta is greater than threshold, clear the average
                if abs(shifted_data - channel_data.last_read) > self.threshold:
                    # Indexes to Channel 1 on either ADC 1 or 2
                    channel_data.average_array = []

                # Build the array until we have average_count measurements
                channel_data.average_array.append(shifted_data)
                channel_data.last_read = shifted_data

                if len(channel_data.average_array) > self.average_count:
                    # Pop one value so we have average_count values
                    channel_data.average_array.pop(0)

                    # Compute new average
                    channel_data.average = sum(channel_data.average_array) / self.average_count

                    # If not stable, build the array
                    if not channel_data.is_stable:
                        # Shift in value
                        if len(channel_data.stable_array) == self.steady_count:
                            channel_data.stable_array.pop(0)
                        channel_data.stable_array.append(channel_data.average)

                    # If the array deviates, clear it and mark as unstable
                    if abs(max(channel_data.stable_array) - min(channel_data.stable_array)) > self.deviation_limit:
                        channel_data.is_stable = False
                        channel_data.stable_array = [channel_data.average]

                    # Else if we filled the array and it was unstable
                    elif len(channel_data.stable_array) == self.steady_count and not channel_data.is_stable:
                        new_stable = sum(channel_data.stable_array) / self.steady_count
                        delta_val = new_stable - channel_data.stable

                        # Check that the change in weight is large enough
                        if self.to_grams(delta_val, current_load_cell) < 20000:
                            # Track accumulated change
                            delta_weight += self.to_grams(delta_val, current_load_cell)

                            # DEBUG
                            # print 'Stable Val: ', channel_data.stable
                            print 'LC', (current_load_cell + 1), ' grams: ', delta_weight

                        # Update the saved stable value
                        channel_data.stable = new_stable
                        channel_data.is_stable = True

                    # If we deviate far enough from the old stable value, mark as unstable
                    if abs(channel_data.stable - channel_data.average) > self.deviation_limit:
                        channel_data.is_stable = False

                        # Shift in value
                        if len(channel_data.stable_array) == self.steady_count:
                            channel_data.stable_array.pop(0)
                        channel_data.stable_array.append(channel_data.average)

            # Update only when the accumulated change is large enough
            if abs(self.grams_to_lbs(delta_weight)) > 0.01:
                # print("total weight: " + repr(currentWeight) + " lbs")
                # print("grams: " + repr(round(currentWeight * 453.592, 1)) + " g")


                # Block to acquire the lock
                if self.weight_lock.acquire():
                    # Update weight
                    self.weight += delta_weight

                    # Release when done
                    self.weight_lock.release()

                # Reset accumulated change
                delta_weight = 0.0

                print 'Total weight: ', round(self.weight, 3), ' grams'
                print round(self.grams_to_lbs(self.weight), 3), ' lbs'

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

    @staticmethod
    def grams_to_lbs(val):
        return val * 0.00220462

    @classmethod
    def to_grams(cls, val, load_cell):
            if load_cell == cls.LOAD_CELL_1:
                return round(val * 0.5043 + 0.1361, 1)
            elif load_cell == cls.LOAD_CELL_2:
                return round(val * 0.5043 + 0.1361, 1)
            elif load_cell == cls.LOAD_CELL_3:
                return round(val * 0.5043 + 0.1361, 1)
            elif load_cell == cls.LOAD_CELL_4:
                return round(val * 0.5043 + 0.1361, 1)


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