#!/usr/bin/env python
import time
import os
import RPi.GPIO as GPIO
import MySQLdb

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
DEBUG = 1

# read SPI data from MCP3008 chip, 8 possible adc's (0 thru 7)
def readadc(adcnum, clockpin, mosipin, misopin, cspin):
        if ((adcnum > 7) or (adcnum < 0)):
                return -1
        GPIO.output(cspin, True)

        GPIO.output(clockpin, False)  # start clock low
        GPIO.output(cspin, False)     # bring CS low

        commandout = adcnum
        commandout |= 0x18  # start bit + single-ended bit
        commandout <<= 3    # we only need to send 5 bits here
        for i in range(5):
                if (commandout & 0x80):
                        GPIO.output(mosipin, True)
                else:
                        GPIO.output(mosipin, False)
                commandout <<= 1
                GPIO.output(clockpin, True)
                GPIO.output(clockpin, False)

        adcout = 0
        # read in one empty bit, one null bit and 10 ADC bits
        for i in range(12):
                GPIO.output(clockpin, True)
                GPIO.output(clockpin, False)
                adcout <<= 1
                if (GPIO.input(misopin)):
                        adcout |= 0x1

        GPIO.output(cspin, True)
        
        adcout >>= 1       # first bit is 'null' so drop it
        return adcout

# change these as desired - they're the pins connected from the
# SPI port on the ADC to the Cobbler
SPICLK = 18
SPIMISO = 23
SPIMOSI = 24
SPICS = 25

# set up the SPI interface pins
GPIO.setup(SPIMOSI, GPIO.OUT)
GPIO.setup(SPIMISO, GPIO.IN)
GPIO.setup(SPICLK, GPIO.OUT)
GPIO.setup(SPICS, GPIO.OUT)
GPIO.setwarnings(False)


# 10k trim pot connected to adc #0
potentiometer_adc = 0;
led_adc = 1;

led_o_adc = 2;


#last_read = 0       # this keeps track of the last potentiometer value
#tolerance = 5       # to keep from being jittery we'll only change
                    # volume when the pot has moved more than 5 'counts'


def ConvertVolts(data,places):
  volts = (data * 3.3) / float(1023)
  volts = round(volts,places)
  return volts

def ConvertTemp(data,places):
 
  # ADC Value
  # (approx)  Temp  Volts
  #    0      -50    0.00
  #   78      -25    0.25
  #  155        0    0.50
  #  233       25    0.75
  #  310       50    1.00
  #  465      100    1.50
  #  775      200    2.50
  # 1023      280    3.30
 
  temp = ((data * 330)/float(1023))-50
  temp = round(temp,places)
  return temp

elements_p = []
for i in range(0, 10):
    led = readadc(led_adc, SPICLK, SPIMOSI, SPIMISO, SPICS)
    #p = sensor.read_pressure()
    #p = p / 100.00
    #print "Adding %s to the list." % led
    # append is a function that lists understand
    # time.sleep(1)
    # print p
    elements_p.append(led)

elements_q = []
for i in range(0, 10):
    led_o = readadc(led_o_adc, SPICLK, SPIMOSI, SPIMISO, SPICS)
    #p = sensor.read_pressure()
    #p = p / 100.00
    #print "Adding %s to the list." % led
    # append is a function that lists understand
    # time.sleep(1)
    # print p
    elements_q.append(led_o)



#trim_pot = readadc(potentiometer_adc, SPICLK, SPIMOSI, SPIMISO, SPICS)
#led = readadc(led_adc, SPICLK, SPIMOSI, SPIMISO, SPICS)

#print trim_pot

elements_t = []
for i in range(0, 10):
    trim_pot = readadc(potentiometer_adc, SPICLK, SPIMOSI, SPIMISO, SPICS)
    temp_level = trim_pot
    temp = ConvertTemp(temp_level,2)
    #print "Adding %s to the list." % temp
    # append is a function that lists understand
    # time.sleep(1)
    # print p
    elements_t.append(temp)

temp_sql = round(sum(elements_t) / float(len(elements_t)),2)
led_sql = round(sum(elements_p) / float(len(elements_p)),0)
led_o_sql = round(sum(elements_q) / float(len(elements_q)),0)

#print temp_sql
#print led_sql

#temp_level = trim_pot
#temp       = ConvertTemp(temp_level,2)




# Open database connection
db = MySQLdb.connect("localhost","weather","weather","mcp3008" )
# prepare a cursor object using cursor() method
cursor = db.cursor()
# Prepare SQL query to INSERT a record into the database.
sql = "INSERT INTO data (temp, light, light_o) \
       VALUES ('%s', '%s', '%s')" % \
       (temp_sql,led_sql,led_o_sql)
try:
   # Execute the SQL command
   cursor.execute(sql)
   # Commit your changes in the database
   db.commit()
except:
   # Rollback in case there is any error
   db.rollback()
# disconnect from server
db.close()

