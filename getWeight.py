__author__ = 'asacharn'

import spidev
import sys
import time

try:
    import RPi.GPIO as GPIO
except RuntimeError:
    print("Error importing RPi.GPIO!  This is probably because you need superuser privileges.  You can achieve this by using 'sudo' to run your script")



#COMM REGISTER
AD7192_COMM_WEN = (1 << 7)      # Write Enable */
COMM_WRITE = (0 << 6)           # Write Operation */
COMM_READ = (1 << 6)            # Read Operation */
def COMM_ADDR(x):               # Register Address */
    return (((x) & 0x7) << 3)
COMM_CREAD = (1 << 2)           # Continuous Read of Data Register */



#COMM REGISTER ADRESSES

COMM_REG = 0x0
STATUS_REG = 0x0
MODE_REG = 0x1
CONFIG_REG = 0x2
DATA_REG = 0x3
ID_REG = 0x4
GPOCON_REG = 0x5
OFFSET_REG = 0x6
FULLSCALE_REG = 0x7






def to_hex(byte_list):
    return ', '.join([hex(i) for i in byte_list])


class ADCVars:
    bridgePower = False



def main():
    ADC1 = spidev.SpiDev()
    ADC2 = spidev.SpiDev()
    ADC1.open(0, 0)
    ADC2.open(0, 1)
    ADC1.cshigh = False
    ADC2.cshigh = False

    ADC1.max_speed_hz = 250000
    print("speed1: " + repr(ADC1.max_speed_hz))
    ADC1.mode = 0b11
    ADC2.max_speed_hz = 250000
    print("speed2: " + repr(ADC2.max_speed_hz))
    ADC2.mode = 0b11

    GPIO.setmode(GPIO.BOARD)
    CS_Ch1 = 16
    CS_Ch2 = 18
    DoutRDY = 15
    GPIO.setup(CS_Ch1, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(CS_Ch2, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(DoutRDY, GPIO.IN)

    GPIO.output(CS_Ch1, 1)
    GPIO.output(CS_Ch2, 1)
    time.sleep(1)



    #LOAD CELL OFFSETS
    global LC1_OFFSET
    LC1_OFFSET = 130220
    global LC2_OFFSET
    LC2_OFFSET = 132756
    global LC3_OFFSET
    LC3_OFFSET = 129746
    global LC4_OFFSET
    LC4_OFFSET = 129713

    RESET_BITS = [0xFF for i in range(0, 50)]


    def Select_CH_1():
        GPIO.output(CS_Ch2, 1)
        GPIO.output(CS_Ch1, 1)
        time.sleep(.00002)      #wait 20 micro seconds
        GPIO.output(CS_Ch1, 0)

    def Select_CH_2():
        GPIO.output(CS_Ch1, 1)
        GPIO.output(CS_Ch2, 1)
        time.sleep(.00002)      #wait 20 micro seconds
        GPIO.output(CS_Ch2, 0)

    def EnableContRead(ADC):
        if ADC == ADC1:
            Select_CH_1()
        elif ADC == ADC2:
            Select_CH_2()
        ADC.writebytes([0x5C])  #enable continuous read

    def DisableContRead(ADC):
        if ADC == ADC1:
            Select_CH_1()
        elif ADC == ADC2:
            Select_CH_2()
        ADC.writebytes([0x58])  #disable continuous read

    def ReadContData(ADC):  #waits for falling edge of Dout/RDY pin and reads data once it is detected
        if ADC == ADC1:
            Select_CH_1()
        elif ADC == ADC2:
            Select_CH_2()
        dataNotReady = True
        while dataNotReady:
            if not GPIO.input(DoutRDY):
                print('data ready')
                dataNotReady = False
        data = ADC.readbytes(4)
        result = (data[0] << 16) + (data[1] << 8) + data[2]
        return result
        # GPIO.wait_for_edge(DoutRDY, GPIO.FALLING)





    def ConfigurePseudoGain1(ADC):
        if ADC == ADC1:
            Select_CH_1()
        elif ADC == ADC2:
            Select_CH_2()
        ADC.writebytes([COMM_WRITE | COMM_ADDR(CONFIG_REG)])
        ADC.writebytes([0x00])
        ADC.writebytes([0x10])  #pseudo ain1
        ADC.writebytes([0x58])
        ADC.writebytes([COMM_READ | COMM_ADDR(CONFIG_REG)])
        response = ADC.readbytes(3)
        print(to_hex(response))

    def ConfigureGain128Ch1(ADC):  #CHANNEL 1
        if ADC == ADC1:
            Select_CH_1()
        elif ADC == ADC2:
            Select_CH_2()
        ADC.writebytes([COMM_WRITE | COMM_ADDR(CONFIG_REG)])
        ADC.writebytes([0x00])
        ADC.writebytes([0x01])  #differential Channel AN1-AN2
        ADC.writebytes([0x57])  #Reference detect on, buffered inputs, gain 128

    def ConfigureGain128Ch2(ADC):  #CHANNEL 2
        if ADC == ADC1:
            Select_CH_1()
        elif ADC == ADC2:
            Select_CH_2()
        ADC.writebytes([COMM_WRITE | COMM_ADDR(CONFIG_REG)])
        ADC.writebytes([0x00])
        ADC.writebytes([0x02])  #differential Channel AN3-AN4
        ADC.writebytes([0x57])  #Reference detect on, buffered inputs, gain 128
        

    def ConfigureGain128Ch1CHOP(ADC):
        if ADC == ADC1:
            Select_CH_1()
        elif ADC == ADC2:
            Select_CH_2()
        ADC.writebytes([COMM_WRITE | COMM_ADDR(CONFIG_REG)])
        ADC.writebytes([0x80])  #Chop Enabled
        ADC.writebytes([0x01])  #differential Channel AN1-AN2
        ADC.writebytes([0x5F])  #Reference detect on, buffered inputs, gain 128
        ADC.writebytes([COMM_READ | COMM_ADDR(CONFIG_REG)])
        print("chop enabled")

    def MultiChannelEnable(ADC, polarity):
        if ADC == ADC1:
            Select_CH_1()
        elif ADC == ADC2:
            Select_CH_2()
        ADC.writebytes([COMM_WRITE | COMM_ADDR(CONFIG_REG)])
        ADC.writebytes([0x00])
        ADC.writebytes([0x03])  #Auto sequences between differential channels 1 & 2
        if polarity == 1:
            ADC.writebytes([0x5F])  #Reference detect on, buffered inputs, gain 128, unipolar
            print("Both Channels Enabled in Unipolar Mode")
        elif polarity == 2:
            ADC.writebytes([0x57])  #Reference detect on, buffered inputs, gain 128, bipolar
            # print("GAIN IS CURRENTLY AT 32!!!~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*************")
            print("Both Channels Enabled in Bipolar Mode")


    def FullScaleCalibration(ADC):
        if ADC == ADC1:
            Select_CH_1()
        elif ADC == ADC2:
            Select_CH_2()
        complete = False
        ADC.writebytes([COMM_WRITE | COMM_ADDR(MODE_REG)])
        ADC.writebytes([0xB8])
        ADC.writebytes([0x08])
        ADC.writebytes([0xFF])
        # ADC.writebytes([COMM_READ | COMM_ADDR(MODE_REG)])
        # response = ADC.readbytes(3)
        # print(to_hex(response))
        while not complete:
            status = ReadStatusReg(ADC)
            if not status[0] >> 7:
                complete = True
                print("Full Scale Calibration Complete!")
                # ADC.writebytes([COMM_READ | COMM_ADDR(MODE_REG)])
                # response = ADC.readbytes(3)
                # print(to_hex(response))

    def ZeroScaleCalibration(ADC):
        if ADC == ADC1:
            Select_CH_1()
        elif ADC == ADC2:
            Select_CH_2()
        complete = False
        ADC.writebytes([COMM_WRITE | COMM_ADDR(MODE_REG)])
        ADC.writebytes([0x98])
        ADC.writebytes([0x08])
        ADC.writebytes([0xFF])
        while not complete:
            status = ReadStatusReg(ADC)
            if not status[0] >> 7:
                complete = True
                print("Zero Scale Calibration Complete!")

#MODE FUNCTIONS

    def SetModeZL9Hz(ADC):  #9.4Hz Zero Latency
        if ADC == ADC1:
            Select_CH_1()
        elif ADC == ADC2:
            Select_CH_2()
        ADC.writebytes([COMM_WRITE | COMM_ADDR(MODE_REG)])
        ADC.writebytes([0x18])  #continuous conversion mode, appends status register to data output, internal 4.92 MHz clock, MCLK2 is tristated
        ADC.writebytes([0x09])  #sinc4 filter is used, parity disabled, zero latency. output rate falls over to next
        ADC.writebytes([0xFF])  #9.4Hz output rate
        # ADC.writebytes([COMM_READ | COMM_ADDR(MODE_REG)])
        # response = ADC.readbytes(3)
        # print(to_hex(response))
        print("Output rate set at 9.4 Hz, zero latency enabled")

    def SetMode10Hz(ADC):  #10Hz
        if ADC == ADC1:
            Select_CH_1()
        elif ADC == ADC2:
            Select_CH_2()
        ADC.writebytes([COMM_WRITE | COMM_ADDR(MODE_REG)])
        ADC.writebytes([0x18])  #continuous conversion mode, appends status register to data output, internal 4.92 MHz clock, MCLK2 is tristated
        ADC.writebytes([0x09])  #sinc4 filter is used, parity disabled, zero latency. output rate falls over to next
        ADC.writebytes([0xE0])
        ADC.writebytes([COMM_READ | COMM_ADDR(MODE_REG)])
        response = ADC.readbytes(3)
        print(to_hex(response))
        print("Output rate set at 10 Hz, zero latency enabled")

    def SetMode50Hz(ADC):  #50Hz
        if ADC == ADC1:
            Select_CH_1()
        elif ADC == ADC2:
            Select_CH_2()
        ADC.writebytes([COMM_WRITE | COMM_ADDR(MODE_REG)])
        ADC.writebytes([0x18])  #continuous conversion mode, appends status register to data output, internal 4.92 MHz clock, MCLK2 is tristated
        ADC.writebytes([0x08])  #sinc4 filter is used, parity disabled, zero latency. output rate falls over to next
        ADC.writebytes([0x60])
        # ADC.writebytes([COMM_READ | COMM_ADDR(MODE_REG)])
        # response = ADC.readbytes(3)
        # print(to_hex(response))
        print("Output rate set at 50 Hz, zero latency enabled")

    def SetMode5Hz(ADC):  #4.7Hz
        if ADC == ADC1:
            Select_CH_1()
        elif ADC == ADC2:
            Select_CH_2()
        ADC.writebytes([COMM_WRITE | COMM_ADDR(MODE_REG)])
        ADC.writebytes([0x18])  #continuous conversion mode, appends status register to data output, internal 4.92 MHz clock, MCLK2 is tristated
        ADC.writebytes([0x03])  #sinc4 filter is used, parity disabled, zero latency. output rate falls over to next
        ADC.writebytes([0xFF])
        # ADC.writebytes([COMM_READ | COMM_ADDR(MODE_REG)])
        # response = ADC.readbytes(3)
        # print(to_hex(response))
        print("Output rate set at 4.7 Hz, zero latency disabled")

    def SetMode5HzZL(ADC):  #4.7Hz
        if ADC == ADC1:
            Select_CH_1()
        elif ADC == ADC2:
            Select_CH_2()
        ADC.writebytes([COMM_WRITE | COMM_ADDR(MODE_REG)])
        ADC.writebytes([0x18])  #continuous conversion mode, appends status register to data output, internal 4.92 MHz clock, MCLK2 is tristated
        ADC.writebytes([0x03])  #sinc4 filter is used, parity disabled, zero latency. output rate falls over to next
        ADC.writebytes([0xFF])
        # ADC.writebytes([COMM_READ | COMM_ADDR(MODE_REG)])
        # response = ADC.readbytes(3)
        # print(to_hex(response))
        print("Output rate set at 4.7 Hz, zero latency enabled")

    def SetMode25Hz(ADC):  #25Hz
        if ADC == ADC1:
            Select_CH_1()
        elif ADC == ADC2:
            Select_CH_2()
        ADC.writebytes([COMM_WRITE | COMM_ADDR(MODE_REG)])
        ADC.writebytes([0x18])  #continuous conversion mode, appends status register to data output, internal 4.92 MHz clock, MCLK2 is tristated
        ADC.writebytes([0x08])  #sinc4 filter is used, parity disabled, zero latency. output rate falls over to next
        ADC.writebytes([0xC0])
        ADC.writebytes([COMM_READ | COMM_ADDR(MODE_REG)])
        response = ADC.readbytes(3)
        print(to_hex(response))
        print("Output rate set at 25 Hz, zero latency enabled")

    def SetMode300Hz(ADC):  #300Hz
        if ADC == ADC1:
            Select_CH_1()
        elif ADC == ADC2:
            Select_CH_2()
        ADC.writebytes([COMM_WRITE | COMM_ADDR(MODE_REG)])
        ADC.writebytes([0x18])  #continuous conversion mode, appends status register to data output, internal 4.92 MHz clock, MCLK2 is tristated
        ADC.writebytes([0x08])  #sinc4 filter is used, parity disabled, zero latency. output rate falls over to next
        ADC.writebytes([0x10])
        # ADC.writebytes([COMM_READ | COMM_ADDR(MODE_REG)])
        # response = ADC.readbytes(3)
        # print(to_hex(response))
        print("Output rate set at 300 Hz, zero latency enabled")

    def SetMode960Hz(ADC):  #960Hz
        if ADC == ADC1:
            Select_CH_1()
        elif ADC == ADC2:
            Select_CH_2()
        ADC.writebytes([COMM_WRITE | COMM_ADDR(MODE_REG)])
        ADC.writebytes([0x18])  #continuous conversion mode, appends status register to data output, internal 4.92 MHz clock, MCLK2 is tristated
        ADC.writebytes([0x08])  #sinc4 filter is used, parity disabled, zero latency. output rate falls over to next
        ADC.writebytes([0x05])
        print("Output rate set at 960 Hz, zero latency enabled")

    def SetMode2400Hz(ADC):  #2400Hz
        if ADC == ADC1:
            Select_CH_1()
        elif ADC == ADC2:
            Select_CH_2()
        ADC.writebytes([COMM_WRITE | COMM_ADDR(MODE_REG)])
        ADC.writebytes([0x18])  #continuous conversion mode, appends status register to data output, internal 4.92 MHz clock, MCLK2 is tristated
        ADC.writebytes([0x08])  #sinc4 filter is used, parity disabled, zero latency. output rate falls over to next
        ADC.writebytes([0x02])
        print("Output rate set at 2400 Hz, zero latency enabled")

    def SetMode4800Hz(ADC):  #4800Hz
        if ADC == ADC1:
            Select_CH_1()
        elif ADC == ADC2:
            Select_CH_2()
        ADC.writebytes([COMM_WRITE | COMM_ADDR(MODE_REG)])
        ADC.writebytes([0x18])  #continuous conversion mode, appends status register to data output, internal 4.92 MHz clock, MCLK2 is tristated
        ADC.writebytes([0x08])  #sinc4 filter is used, parity disabled, zero latency. output rate falls over to next
        ADC.writebytes([0x01])
        print("Output rate set at 4800 Hz, zero latency enabled")

    def ToggleBridgePower(ADC):
        if ADC == ADC1:
            Select_CH_1()
        elif ADC == ADC2:
            Select_CH_2()
        if not ADCVars.bridgePower:
            ADC.writebytes([COMM_WRITE | COMM_ADDR(GPOCON_REG)])
            ADC.writebytes([0x40])
            ADC.writebytes([COMM_READ | COMM_ADDR(GPOCON_REG)])
            read = ADC.readbytes(1)
            if read[0] & 0x40:
                ADCVars.bridgePower = True
                print('Bridge Power On')
            else:
                print('Bridge Power Off')
        elif ADCVars.bridgePower:
            ADC.writebytes([COMM_WRITE | COMM_ADDR(GPOCON_REG)])
            ADC.writebytes([0x00])
            ADC.writebytes([COMM_READ | COMM_ADDR(GPOCON_REG)])
            read = ADC.readbytes(1)
            if not read[0] & 0x40:
                ADCVars.bridgePower = False
                print('Bridge Power Off')
            else:
                print('Bridge Power On')

    def BridgePowerOn(ADC):
        if ADC == ADC1:
            Select_CH_1()
        elif ADC == ADC2:
            Select_CH_2()
        ADC.writebytes([COMM_WRITE | COMM_ADDR(GPOCON_REG)])
        ADC.writebytes([0x40])
        ADC.writebytes([COMM_READ | COMM_ADDR(GPOCON_REG)])
        read = ADC.readbytes(1)
        if read[0] & 0x40:
            ADCVars.bridgePower = True
            print('Bridge Power On')
        else:
            print('***********************Bridge Power Off, Check Power to AD7192***********************')

#READ FUNCTIONS

    def ReadModeReg(ADC):
        if ADC == ADC1:
            Select_CH_1()
        elif ADC == ADC2:
            Select_CH_2()
        ADC.writebytes([COMM_READ | COMM_ADDR(MODE_REG)])
        response = ADC.readbytes(3)
        print(to_hex(response))

    def ReadStatusReg(ADC):
        if ADC == ADC1:
            Select_CH_1()
        elif ADC == ADC2:
            Select_CH_2()
        ADC.writebytes([COMM_READ | COMM_ADDR(STATUS_REG)])
        response = ADC.readbytes(1)
        return response
        #print(to_hex(response))

    def ReadConfigReg(ADC):
        if ADC == ADC1:
            Select_CH_1()
        elif ADC == ADC2:
            Select_CH_2()
        ADC.writebytes([COMM_READ | COMM_ADDR(CONFIG_REG)])
        response = ADC.readbytes(3)
        print(to_hex(response))

    def ReadDataRegCH1(ADC):
        if ADC == ADC1:
            Select_CH_1()
        elif ADC == ADC2:
            Select_CH_2()
        #ConfigureGain128Ch1(ADC)
        ADC.writebytes([COMM_READ | COMM_ADDR(DATA_REG)])
        data = ADC.readbytes(4)
        result = (data[0] << 16) + (data[1] << 8) + data[2]
        return [result, data[3]]

    def ReadDataRegCH2(ADC):
        if ADC == ADC1:
            Select_CH_1()
        elif ADC == ADC2:
            Select_CH_2()
        ConfigureGain128Ch2(ADC)
        ADC.writebytes([COMM_READ | COMM_ADDR(DATA_REG)])
        data = ADC.readbytes(4)
        result = (data[0] << 16) + (data[1] << 8) + data[2]
        return [result, data[3]]

    def ReadDataReg(ADC):
        if ADC == ADC1:
            Select_CH_1()
        elif ADC == ADC2:
            Select_CH_2()
        ADC.writebytes([COMM_READ | COMM_ADDR(DATA_REG)])
        data = ADC.readbytes(4)
        result = (data[0] << 16) + (data[1] << 8) + data[2]
        return [result, data[3]]

    class scale:
            totalWeight = 0
            lastWeight = 0
            LC1_g = 0
            LC2_g = 0
            LC3_g = 0
            LC4_g = 0



    def getWeight(totalReads, tare):
        TARE_OFFSET_1 = 0
        TARE_OFFSET_2 = 0
        TARE_OFFSET_3 = 0
        TARE_OFFSET_4 = 0
        readCount = 0
        SHIFT = 6
        THRESHOLD = 20
        oldAvg1 = 0
        oldAvg2 = 0
        oldAvg1_A2 = 0
        oldAvg2_A2 = 0
        AVERAGE_COUNT = 200.0       # how many values to average
        lastVal = 0
        lastVal2 = 0
        lastVal_A2 = 0
        lastVal2_A2 = 0
        lastWeight = 0
        totalWeight = 0
        tare_1_ready = False
        tare_2_ready = False
        tare_3_ready = False
        tare_4_ready = False
        read_LC1 = False
        read_LC2 = False
        read_LC3 = False
        read_LC4 = False
        gramLimit = 0
        lastGrams2 = 0


        steadyCount = 10

        array1 = []
        array2 = []
        array3 = []
        array4 = []

        for i in range(steadyCount):
            array1.append(0)
            array2.append(0)
            array3.append(0)
            array4.append(0)

        deviationLimit = 1.0

        steadyVal_1 = 0
        steadyVal_2 = 0
        steadyVal_3 = 0
        steadyVal_4 = 0

        steady1 = True
        steady2 = True
        steady3 = True
        steady4 = True



        def toLbs(val, loadCellNum):
            if loadCellNum == 1:
                return round(((val - LC1_OFFSET) * 0.8049 - 0.1281) * .00220462, 4)    #7V
            elif loadCellNum == 2:
                # return round(((val - LC2_OFFSET) * 1.3338 - 0.2541) * .00220462, 2)    #5V
                # return round(((val - LC2_OFFSET) * 0.9487 - 0.7804) * .00220462, 2)    #7V
                return round(((val - LC2_OFFSET) * 0.8153 + 0.1841) * .00220462, 4)    #7V_updated
                # return round(((val - LC2_OFFSET) * 0.6657 - 0.9161) * .00220462, 2)    #10V
            elif loadCellNum == 3:
                return round(((val - LC3_OFFSET) * 0.8677 - 0.0041) * .00220462, 4)    #7V
                # return round(((val - OFFSET1) * 1.2335 - 0.4163) * .00220462, 2)    #5V
            elif loadCellNum == 4:
                # return round(((val - LC4_OFFSET) * 1.2402 - 1.3237) * .00220462, 2)    #5V
                return round(((val - LC4_OFFSET) * 0.8732 - 0.0613) * .00220462, 4)    #7V


        def deltaToLbs(val, loadCellNum):
            if loadCellNum == 1:
                return round((val * 0.8049 - 0.1281) * .00220462, 4)    #7V
            elif loadCellNum == 2:
                # return round((val * 1.3338 - 0.2541) * .00220462, 2)    #5V
                return round((val * 0.8153 + 0.1841) * .00220462, 4)    #7V
                # return round((val * 0.6657 - 0.9161) * .00220462, 4)    #10V
            elif loadCellNum == 3:
                return round((val * 0.8677 - 0.0041) * .00220462, 4)    #7V
                # return round((val * 1.2335 - 0.4163) * .00220462, 4)    #5V
            elif loadCellNum == 4:
                # return round((val * 1.2402 - 1.3237) * .00220462, 4)    #5V
                return round((val * 0.8732 - 0.0613) * .00220462, 4)    #7V


        def toGrams(val, loadCellNum):
            if loadCellNum == 1:
                # return round((val - LC1_OFFSET) * 0.805 - 0.1295, 1)
                return round(val * 0.805 - 0.1295, 1)
            elif loadCellNum == 2:
                return round(val * 0.8153 + 0.1841, 1)
            elif loadCellNum == 3:
                return round((val - LC3_OFFSET) * 0.8677 - 0.0041, 1)
            elif loadCellNum == 4:
                return round((val - LC4_OFFSET) * 0.8733 - 0.0834, 1)

        # print(repr(24 - SHIFT) + " bits of resolution")
        # print("Moving average count = " + repr(AVERAGE_COUNT))

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




        def sumWeights():
            # total = round(ch1_ADC1['lbs'] + ch2_ADC1['lbs'] + ch1_ADC2['lbs'] + ch2_ADC2['lbs'], 2)
            total = round(ch1_ADC1['lbs'] + ch2_ADC1['lbs'], 3)
            # print("total weight: " + repr(total) + " lbs")
            # total = deltaWeight1 + deltaWeight2
            return total

        # EnableContRead(ADC2)
        if tare:
            totalReads = 200
        while readCount < totalReads:

            # Select_CH_1()
            data = ReadDataReg(ADC1)
            # data = [0x00, 0x00]
            data2 = ReadDataReg(ADC2)
            # data2 = ReadContData(ADC2)
            # data2 = [0x00, 0x00]

            # ADC 1 DATA
            if not data[1] >> 7:

                if (data[1] << 7) == 0x00:     #channel 1 --- LOAD CELL #1

                    if data[1] == 0x40:
                        print("Channel 1 error")

                    # print((data[0] >> SHIFT) - lastVal)
                    if abs((data[0] >> SHIFT) - lastVal) > THRESHOLD:
                        ch1_ADC1['values'] = []
                    if len(ch1_ADC1['values']) != AVERAGE_COUNT:
                        ch1_ADC1['values'].append(data[0] >> SHIFT)
                        lastVal = data[0] >> SHIFT
                        # print("length: " + repr(len(ch1_ADC1['values'])))
                        # time.sleep(.01)
                    else:
                        ch1_ADC1['values'].pop(0)
                        ch1_ADC1['values'].append(data[0] >> SHIFT)
                        lastVal = data[0] >> SHIFT

                        # compute average
                        avg_sum = 0
                        for val in ch1_ADC1['values']:
                            avg_sum += val
                        ch1_ADC1['average'] = (avg_sum / AVERAGE_COUNT)

                        delta1 = ch1_ADC1['average'] - oldAvg1
                        deltaLB = deltaToLbs(delta1, 1)
                        # print(ch1_ADC1['average'])
                        if tare:
                            TARE_OFFSET_1 = ch1_ADC1['average']
                            tare_1_ready = True
                        else:
                            if not steady1:
                                # print('Not steady')
                                #shift in value
                                if len(array1) == steadyCount:
                                    array1.pop(0)
                                array1.append(ch1_ADC1['average'])

                            if abs((max(array1) - min(array1))) > deviationLimit:
                                # print('Out of bounds')
                                steady1 = False
                                array1 = []
                                #shift in value
                                array1.append(ch1_ADC1['average'])

                            elif len(array1) == steadyCount and not steady1:
                                #average
                                new_steady1 = sum(array1) / len(array1)
                                deltaWeight1 = new_steady1 - steadyVal_1
                                if toGrams(deltaWeight1, 1) < 20000:
                                    scale.totalWeight += toGrams(deltaWeight1, 1)
                                    print("steady val: " + repr(steadyVal_1))
                                    print("LC1 grams: " + repr(toGrams(deltaWeight1, 1)))
                                steadyVal_1 = new_steady1
                                read_LC1 = True
                                steady1 = True

                            if abs(steadyVal_1 - ch1_ADC1['average']) > deviationLimit:
                                # print('Away from steady')
                                steady1 = False
                                #shift in value
                                if len(array1) == steadyCount:
                                    array1.pop(0)
                                array1.append(ch1_ADC1['average'])


                elif data[1] & 0x01:       #channel 2 ---- LOAD CELL #2
                    # print('data: ' + repr(data))
                    # time.sleep(.2)
                    if data[1] == 0x41:
                        print("Channel 2 error")

                    if abs((data[0] >> SHIFT) - lastVal2) > THRESHOLD:
                        ch2_ADC1['values'] = []

                    if len(ch2_ADC1['values']) != AVERAGE_COUNT:

                        ch2_ADC1['values'].append(data[0] >> SHIFT)
                        lastVal2 = data[0] >> SHIFT
                    else:
                        ch2_ADC1['values'].pop(0)
                        ch2_ADC1['values'].append(data[0] >> SHIFT)
                        lastVal2 = data[0] >> SHIFT



                        # compute average
                        avg_sum = 0
                        for val in ch2_ADC1['values']:
                            avg_sum += val
                        ch2_ADC1['average'] = (avg_sum / AVERAGE_COUNT)

                        delta2 = ch2_ADC1['average'] - oldAvg2
                        deltaLB2 = deltaToLbs(delta2, 2)


                        if tare:
                            TARE_OFFSET_2 = ch2_ADC1['average']
                            tare_2_ready = True
                        else:
                            if not steady2:
                                # print('Not steady')
                                #shift in value
                                if len(array2) == steadyCount:
                                    array2.pop(0)
                                array2.append(ch2_ADC1['average'])

                            if abs((max(array2) - min(array2))) > deviationLimit:
                                # print('Out of bounds')
                                steady2 = False
                                array2 = []
                                #shift in value
                                array2.append(ch2_ADC1['average'])

                            elif len(array2) == steadyCount and not steady2:
                                #average
                                new_steady2 = sum(array2) / len(array2)
                                deltaWeight2 = new_steady2 - steadyVal_2
                                if toGrams(deltaWeight2, 2) < 20000:
                                    scale.totalWeight += toGrams(deltaWeight2, 2)
                                    # print("steady val: " + repr(steadyVal_2))
                                    print("LC2 grams: " + repr(toGrams(deltaWeight2, 2)))
                                steadyVal_2 = new_steady2
                                read_LC2 = True
                                steady2 = True

                            if abs(steadyVal_2 - ch2_ADC1['average']) > deviationLimit:
                                # print('Away from steady')
                                steady2 = False
                                #shift in value
                                if len(array2) == steadyCount:
                                    array2.pop(0)
                                array2.append(ch2_ADC1['average'])



            # ADC 2 DATA
            if not data2[1] >> 7:

                if (data2[1] << 7) == 0x00:     #channel 1              LOAD CELL #3

                    if data2[1] == 0x40:
                        print("Channel 1 - ADC 2 error")

                    if abs((data2[0] >> SHIFT) - lastVal_A2) > THRESHOLD:   # if value changes by a lot, reset moving average filter
                        ch1_ADC2['values'] = []
                    if len(ch1_ADC2['values']) != AVERAGE_COUNT:
                        ch1_ADC2['values'].append(data2[0] >> SHIFT)
                        lastVal_A2 = data2[0] >> SHIFT
                    else:
                        ch1_ADC2['values'].pop(0)
                        ch1_ADC2['values'].append(data2[0] >> SHIFT)
                        lastVal_A2 = data2[0] >> SHIFT

                        # compute average
                        avg_sum = 0
                        for val in ch1_ADC2['values']:
                            avg_sum += val
                        ch1_ADC2['average'] = (avg_sum / AVERAGE_COUNT)

                        delta1 = ch1_ADC2['average'] - oldAvg1_A2
                        deltaLB = deltaToLbs(delta1, 3)

                        if tare:
                            TARE_OFFSET_3 = ch1_ADC2['average']
                            tare_3_ready = True
                        # elif not tare and abs(deltaLB) > .0021:
                        elif not tare and abs(delta1) > .2:
                            ch1_ADC2['lbs'] = toLbs(ch1_ADC2['average'], 3)
                            read_LC3 = True
                            # print([round(delta1, 1), round(ch1_ADC2['average'] - LC3_OFFSET, 1), 'Load Cell 3'])
                            # print(repr(toGrams(ch1_ADC2['average'], 3)) + ' grams LC3')
                            # print(repr(ch1_ADC2['lbs']) + ' pounds')
                            oldAvg1_A2 = ch1_ADC2['average']
                            # readCount += 1
                            # sumWeights()
                            # readCount += 1

                elif data2[1] & 0x01:       #channel 2          LOAD CELL #4
                    # print("data: " + repr(hex(data2[0] >> SHIFT)))
                    if data2[1] == 0x41:
                        print("Channel 2-ADC 2 error")

                    if abs((data2[0] >> SHIFT) - lastVal2_A2) > THRESHOLD:
                        ch2_ADC2['values'] = []

                    if len(ch2_ADC2['values']) != AVERAGE_COUNT:
                        ch2_ADC2['values'].append(data2[0] >> SHIFT)
                        lastVal2_A2 = data2[0] >> SHIFT

                    else:
                        ch2_ADC2['values'].pop(0)
                        ch2_ADC2['values'].append(data2[0] >> SHIFT)
                        lastVal2_A2 = data2[0] >> SHIFT


                        # compute average
                        avg_sum = 0
                        for val in ch2_ADC2['values']:
                            avg_sum += val
                        ch2_ADC2['average'] = (avg_sum / AVERAGE_COUNT)



                        # display
                        delta2 = ch2_ADC2['average'] - oldAvg2_A2
                        deltaLB2 = deltaToLbs(delta2, 4)
                        if tare:
                            TARE_OFFSET_4 = ch2_ADC2['average']
                            tare_4_ready = True
                        elif not tare and abs(deltaLB2) > .0021:
                        # elif not tare and abs(delta2) > .2:
                            ch2_ADC2['lbs'] = toLbs(ch2_ADC2['average'], 4)
                            read_LC4 = True
                            # print([round(delta2, 1), round(ch2_ADC2['average'] - LC4_OFFSET, 1), 'Load Cell 4'])
                            # print(repr(toGrams(ch2_ADC2['average'], 4)) + ' grams LC4')
                            # print(repr(ch2_ADC2['lbs']) + ' pounds')
                            oldAvg2_A2 = ch2_ADC2['average']
                            # readCount += 1


            # if read_LC1 and read_LC2 and read_LC3 and read_LC4:
            # if read_LC1 and read_LC2:
            # currentWeight = deltaWeight1 + deltaWeight2
            read_LC1 = False
            read_LC2 = False
            read_LC3 = False
            read_LC4 = False
            if abs(scale.totalWeight - scale.lastWeight) > .5:
                # print("total weight: " + repr(currentWeight) + " lbs")
                # print("grams: " + repr(round(currentWeight * 453.592, 1)) + " g")
                print("total weight: " + repr(scale.totalWeight) + " grams")
                print(repr(round(scale.totalWeight * 0.00220462, 3)) + " lbs")
                # readCount += 1
                scale.lastWeight = scale.totalWeight


            # if tare_1_ready and tare_2_ready and tare_3_ready and tare_4_ready:
            # if tare_3_ready and tare_4_ready:
            if tare_1_ready and tare_2_ready:
                global LC1_OFFSET
                print("before lc1: " + repr(LC1_OFFSET))
                LC1_OFFSET = TARE_OFFSET_1
                print("after lc1: " + repr(LC1_OFFSET))
                global LC2_OFFSET
                print("before lc2: " + repr(LC2_OFFSET))
                LC2_OFFSET = TARE_OFFSET_2
                print("after lc2: " + repr(LC2_OFFSET))
                global LC3_OFFSET
                LC3_OFFSET = TARE_OFFSET_3
                global LC4_OFFSET
                LC4_OFFSET = TARE_OFFSET_4
                return



    def initializeADC(ADC):
        if ADC == ADC1:
            Select_CH_1()
            print("***** ADC 1 *****")
        elif ADC == ADC2:
            Select_CH_2()
            print("***** ADC 2 *****")



        # print("resetting")
        # time.sleep(4)
        ADC.writebytes(RESET_BITS)
        time.sleep(.0005)
        ConfigureGain128Ch1(ADC)
        # print("multi channel enable")
        # time.sleep(4)
        MultiChannelEnable(ADC, 2)       # 1 = unipolar, 2 = bipolar
        # print("bridge power")
        # time.sleep(4)
        BridgePowerOn(ADC)
        #ConfigureGain128Ch1CHOP(ADC)
        ZeroScaleCalibration(ADC)
        FullScaleCalibration(ADC)
        #SetMode5Hz(ADC)
        #SetMode10Hz(ADC)
        #SetModeZL9Hz(ADC)
        #SetMode5HzZL(ADC)
        # SetMode50Hz(ADC)
        # SetMode300Hz(ADC)
        # SetMode960Hz(ADC)
        SetMode2400Hz(ADC)
        # SetMode4800Hz(ADC)
        #SetMode25Hz(ADC)
        time.sleep(.001)




    try:

        # time.sleep(2)
        initializeADC(ADC1)
        initializeADC(ADC2)
        #ADC.writebytes(ox80)

        while True:
            n = raw_input('type e to end, d to read data from load cells\n')
            if n.strip() == 'e':
                break

            elif n == 'bp':
                ToggleBridgePower(ADC1)

            elif n == 'f':
                ReadModeReg(ADC1)

            elif n == '6':
                ReadModeReg(ADC2)

            elif n == 're':
                Select_CH_1()
                ADC1.writebytes(RESET_BITS)
                Select_CH_2()
                ADC2.writebytes(RESET_BITS)
            elif n == 'm':
                print(repr(ADC1.mode) + " - ch1")
                print(repr(ADC2.mode) + " - ch2")

            elif n == 't':
                print("tare enabled")
                getWeight(1, True)

            elif n == 'w':
                getWeight(50, False)

            elif n == 'g':
                 Select_CH_1()
                 print("Channel 1 = " + repr(GPIO.input(CS_Ch1)))
                 print("Channe 2 = " + repr(GPIO.input(CS_Ch2)))
            elif n == 'h':
                 Select_CH_2()
                 print("Channel 1 = " + repr(GPIO.input(CS_Ch1)))
                 print("Channe 2 = " + repr(GPIO.input(CS_Ch2)))
            elif n == 'y':
                 Select_CH_1()
                 Select_CH_2()
                 print("Channel 1 = " + repr(GPIO.input(CS_Ch1)))
                 print("Channe 2 = " + repr(GPIO.input(CS_Ch2)))

            elif n == 'k':
                EnableContRead(ADC2)
                # while 1:
                #     data = ReadContData(ADC2)
                #     print(data[0] >> 7)
                # DisableContRead(ADC2)
            elif n == '#':
                DisableContRead(ADC2)

            elif n == 'd':
                readCount = 0
                SHIFT = 6

                #LOAD CELL 1
                # LC1_OFFSET = 129747     #offset of loadcell 1 (ch1, adc 2) at 7 volts

                #LOAD CELL 2
                # LC2_OFFSET = 132258     #offset of loadcell 2 (ch2, adc 2) at 5 volts
                # LC2_OFFSET = 132746     #offset of loadcell 2 (ch2, adc 2) at 7 volts
                # LC2_OFFSET = 133479     #offset of loadcell 2 (ch2, adc 2) at 10 volts

                #LOAD CELL 3
                OFFSET1 = 130159        #offset of loadcell 3 (ch1, adc 1) at 5 volts
                # LC3_OFFSET = 129746     #offset of loadcell 3 (ch1, adc 1) at 7 volts

                #LOAD CELL 4
                # OFFSET2 = 130064        #offset of loadcell 4 (ch2, adc 1) at 5 volts
                # LC4_OFFSET = 129713            #CHANGE WHEN HOOKED UP BACK TO LOADCELL 4

                THRESHOLD = 50
                oldAvg1 = 0
                oldAvg2 = 0
                oldAvg1_A2 = 0
                oldAvg2_A2 = 0
                AVERAGE_COUNT = 400.0       # how many values to average
                lastVal = 0
                lastVal2 = 0
                lastVal_A2 = 0
                lastVal2_A2 = 0
                lastWeight = 0
                platformWeight = 5.15

                def toLbs(val, loadCellNum):
                    if loadCellNum == 1:
                        return round(((val - LC1_OFFSET) * 0.9421 - 0.7887) * .00220462, 3)    #7V
                    elif loadCellNum == 2:
                        # return round(((val - LC2_OFFSET) * 1.3338 - 0.2541) * .00220462, 2)    #5V
                        # return round(((val - LC2_OFFSET) * 0.9487 - 0.7804) * .00220462, 2)    #7V
                        return round(((val - LC2_OFFSET) * 0.9534 - 0.9534) * .00220462, 3)    #7V_updated
                        # return round(((val - LC2_OFFSET) * 0.6657 - 0.9161) * .00220462, 2)    #10V
                    elif loadCellNum == 3:
                        return round(((val - LC3_OFFSET) * 0.8802 - 0.0494) * .00220462, 3)    #7V
                        # return round(((val - OFFSET1) * 1.2335 - 0.4163) * .00220462, 2)    #5V
                    elif loadCellNum == 4:
                        # return round(((val - LC4_OFFSET) * 1.2402 - 1.3237) * .00220462, 2)    #5V
                        return round(((val - LC4_OFFSET) * 0.8896 - 0.049) * .00220462, 3)    #7V


                def deltaToLbs(val, loadCellNum):
                    if loadCellNum == 1:
                        return round((val * 0.9421 - 0.7887) * .00220462, 3)    #7V
                    elif loadCellNum == 2:
                        # return round((val * 1.3338 - 0.2541) * .00220462, 2)    #5V
                        return round((val * 0.9534 - 0.9534) * .00220462, 3)    #7V
                        # return round((val * 0.6657 - 0.9161) * .00220462, 4)    #10V
                    elif loadCellNum == 3:
                        return round((val * 0.8802 - 0.0494) * .00220462, 3)    #7V
                        # return round((val * 1.2335 - 0.4163) * .00220462, 4)    #5V
                    elif loadCellNum == 4:
                        # return round((val * 1.2402 - 1.3237) * .00220462, 4)    #5V
                        return round((val * 0.8896 - 0.049) * .00220462, 3)    #7V


                def toGrams(val, loadCellNum):
                    if loadCellNum == 1:
                        return round((val - LC1_OFFSET) * 0.9421 - 0.7887)    #7V
                    elif loadCellNum == 2:
                        # return round((val - LC2_OFFSET) * 1.3338 - 0.2541)    #5V
                        # return round((val - LC2_OFFSET) * 0.9534 - 0.9534)    #7V
                        return round(val * 0.5043 + 0.1361, 1)
                        # return round((val - LC2_OFFSET) * 0.6657 - 0.9161)    #10V
                    elif loadCellNum == 3:
                        return round((val - LC3_OFFSET) * 0.8802 - 0.0494)    #7V
                        # return round((val - OFFSET1) * 1.2335 - 0.4163)     #5V
                    elif loadCellNum == 4:
                        # return round((val - LC4_OFFSET) * 1.2402 - 1.3237)     #5V
                        return round((val - LC4_OFFSET) * 0.8896 - 0.049)     #7V

                print(repr(24 - SHIFT) + " bits of resolution")
                print("Moving average count = " + repr(AVERAGE_COUNT))

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

                def sumWeights():
                    total = round(ch1_ADC1['lbs'] + ch2_ADC1['lbs'] + ch1_ADC2['lbs'] + ch2_ADC2['lbs'] - platformWeight, 2)
                    # print("total weight: " + repr(total) + " lbs")
                    return total

                # EnableContRead(ADC2)
                while readCount < 5:

                    # Select_CH_1()
                    data = ReadDataReg(ADC1)
                    # data = [0x00, 0x00]
                    data2 = ReadDataReg(ADC2)
                    # data2 = ReadContData(ADC2)
                    # data2 = [0x00, 0x00]

                    # ADC 1 DATA
                    if not data[1] >> 7:

                        if (data[1] << 7) == 0x00:     #channel 1 --- LOAD CELL #1

                            if data[1] == 0x40:
                                print("Channel 1 error")

                            # print((data[0] >> SHIFT) - lastVal)
                            if abs((data[0] >> SHIFT) - lastVal) > THRESHOLD:
                                ch1_ADC1['values'] = []
                            if len(ch1_ADC1['values']) != AVERAGE_COUNT:
                                ch1_ADC1['values'].append(data[0] >> SHIFT)
                                lastVal = data[0] >> SHIFT
                                # print("length: " + repr(len(ch1_ADC1['values'])))
                                # time.sleep(.1)
                            else:
                                ch1_ADC1['values'].pop(0)
                                ch1_ADC1['values'].append(data[0] >> SHIFT)
                                lastVal = data[0] >> SHIFT

                                # compute average
                                avg_sum = 0
                                for val in ch1_ADC1['values']:
                                    avg_sum += val
                                ch1_ADC1['average'] = (avg_sum / AVERAGE_COUNT)

                                # display
                                delta1 = ch1_ADC1['average'] - oldAvg1
                                deltaLB = deltaToLbs(delta1, 1)



                                # only display value if it's different from the last
                                if abs(delta1) > .2:
                                # if abs(deltaLB) > .0024:
                                    ch1_ADC1['lbs'] = toLbs(ch1_ADC1['average'], 1)
                                    # print([delta1, ch1_ADC1['average'] - LC1_OFFSET, 'Ch 1'])
                                    print([round(delta1, 1), round(ch1_ADC1['average'], 1), 'Ch 1: ADC 1'])
                                    # print(repr(toGrams(ch1_ADC1['average'], 1)) + ' grams')
                                    # print(repr(ch1_ADC1['lbs']) + ' pounds: Ch1')
                                    oldAvg1 = ch1_ADC1['average']
                                    # readCount += 1
                                    # print("read count: " + repr(readCount))
                                    # sumWeights()


                        elif data[1] & 0x01:       #channel 2 ---- LOAD CELL #2
                            # print('data: ' + repr(data))
                            # time.sleep(.2)
                            if data[1] == 0x41:
                                print("Channel 2 error")

                            if abs((data[0] >> SHIFT) - lastVal2) > THRESHOLD:
                                ch2_ADC1['values'] = []

                            if len(ch2_ADC1['values']) != AVERAGE_COUNT:

                                ch2_ADC1['values'].append(data[0] >> SHIFT)
                                lastVal2 = data[0] >> SHIFT
                            else:
                                ch2_ADC1['values'].pop(0)
                                ch2_ADC1['values'].append(data[0] >> SHIFT)
                                lastVal2 = data[0] >> SHIFT



                                # compute average
                                avg_sum = 0
                                for val in ch2_ADC1['values']:
                                    avg_sum += val
                                ch2_ADC1['average'] = (avg_sum / AVERAGE_COUNT)

                                # display
                                delta2 = ch2_ADC1['average'] - oldAvg2
                                deltaLB2 = deltaToLbs(delta2, 2)


                                if abs(delta2) > .2:
                                # if abs(deltaLB2) > .0024:
                                    ch2_ADC1['lbs'] = toLbs(ch2_ADC1['average'], 2)
                                    # print([delta2, ch2_ADC1['average'] - LC2_OFFSET, 'Ch 2'])
                                    # print([round(delta2, 1), round(ch2_ADC1['average'] - LC2_OFFSET, 1), 'Ch 2: ADC 1'])
                                    # print(repr(toGrams(delta2, 2)) + ' grams')
                                    # print(repr(ch2_ADC1['lbs']) + ' pounds')
                                    oldAvg2 = ch2_ADC1['average']
                                    # readCount += 1
                                    # print("read count: " + repr(readCount))
                                    # sumWeights()


                    # ADC 2 DATA
                    if not data2[1] >> 7:

                        if (data2[1] << 7) == 0x00:     #channel 1              LOAD CELL #3

                            if data2[1] == 0x40:
                                print("Channel 1 - ADC 2 error")

                            if abs((data2[0] >> SHIFT) - lastVal_A2) > THRESHOLD:   # if value changes by a lot, reset moving average filter
                                ch1_ADC2['values'] = []
                            if len(ch1_ADC2['values']) != AVERAGE_COUNT:
                                ch1_ADC2['values'].append(data2[0] >> SHIFT)
                                lastVal_A2 = data2[0] >> SHIFT
                            else:
                                ch1_ADC2['values'].pop(0)
                                ch1_ADC2['values'].append(data2[0] >> SHIFT)
                                lastVal_A2 = data2[0] >> SHIFT

                                # compute average
                                avg_sum = 0
                                for val in ch1_ADC2['values']:
                                    avg_sum += val
                                ch1_ADC2['average'] = (avg_sum / AVERAGE_COUNT)

                                # display
                                delta1 = ch1_ADC2['average'] - oldAvg1_A2
                                deltaLB = deltaToLbs(delta1, 1)

                                # only display value if it's different from the last
                                # if abs(delta1) > 0.2:
                                if abs(deltaLB) > .0024:
                                    ch1_ADC2['lbs'] = toLbs(ch1_ADC2['average'], 3)
                                    # print([round(delta1, 1), round(ch1_ADC2['average'] - LC3_OFFSET, 1), 'Ch 1: ADC 2'])
                                    # print(repr(toGrams(ch1_ADC2['average'], 3)) + ' grams')
                                    # print(repr(ch1_ADC2['lbs']) + ' pounds')
                                    oldAvg1_A2 = ch1_ADC2['average']
                                    # readCount += 1
                                    # sumWeights()

                        elif data2[1] & 0x01:       #channel 2          LOAD CELL #4
                            # print("data: " + repr(hex(data2[0] >> SHIFT)))
                            # if data2[1] == 0x41:
                                # print("Channel 2-ADC 2 error")

                            if abs((data2[0] >> SHIFT) - lastVal2_A2) > THRESHOLD:
                                ch2_ADC2['values'] = []

                            if len(ch2_ADC2['values']) != AVERAGE_COUNT:
                                ch2_ADC2['values'].append(data2[0] >> SHIFT)
                                lastVal2_A2 = data2[0] >> SHIFT

                            else:
                                ch2_ADC2['values'].pop(0)
                                ch2_ADC2['values'].append(data2[0] >> SHIFT)
                                lastVal2_A2 = data2[0] >> SHIFT


                                # compute average
                                avg_sum = 0
                                for val in ch2_ADC2['values']:
                                    avg_sum += val
                                ch2_ADC2['average'] = (avg_sum / AVERAGE_COUNT)

                                # display
                                delta2 = ch2_ADC2['average'] - oldAvg2_A2
                                deltaLB2 = deltaToLbs(delta2, 2)
                                # if abs(delta2) > 0.2:
                                # if abs(delta2) > 0.009:
                                if abs(deltaLB2) > .0024:
                                    ch2_ADC2['lbs'] = toLbs(ch2_ADC2['average'], 4)
                                    # print([round(delta2, 1), round(ch2_ADC2['average'] - LC4_OFFSET, 1), 'Ch 2: ADC 2'])
                                    # print(repr(toGrams(ch2_ADC2['average'], 4)) + ' grams')
                                    # print(repr(ch2_ADC2['lbs']) + ' pounds')
                                    # oldAvg2_A2 = ch2_ADC2['average']
                                    # readCount += 1



                    # currentWeight = sumWeights()
                    # if abs(currentWeight - lastWeight) > .009:
                    # # if not currentWeight == lastWeight:
                    #     print("total weight: " + repr(currentWeight) + " lbs")
                    #     lastWeight = currentWeight






        #spi.close(response)
        Select_CH_1()
        ADC1.close()
        Select_CH_2()
        ADC2.close()
        GPIO.cleanup()
        print('Exiting')
        sys.exit(0)
    except KeyboardInterrupt:
        Select_CH_1()
        ADC1.close()
        Select_CH_2()
        ADC2.close()
        GPIO.cleanup()
        print('Exiting')
        sys.exit(0)

if __name__ == '__main__':
    main()