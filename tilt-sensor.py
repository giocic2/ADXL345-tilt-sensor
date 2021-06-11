import time
import adafruit_adxl34x
import busio
import board
from struct import unpack
import numpy

i2c = busio.I2C(board.SCL, board.SDA, frequency=100e3)
accelerometer = adafruit_adxl34x.ADXL345(i2c)
accelerometer.range = adafruit_adxl34x.Range.RANGE_16_G # Range

# Offset compensation (MANUAL CALIBRATION)
# OFSX = 0x2A # X-axis offset in LSBs (sensore amazon #1)
# OFSY = 0x26 # Y-axis offset in LSBs (sensore amazon #1)
# OFSZ = 0x80 # Z-axis offset in LSBs (sensore amazon #1)
OFSX = 0x00 # X-axis offset in LSBs (sensore adafruit #1)
OFSY = 0x00 # Y-axis offset in LSBs (sensore adafruit #1)
OFSZ = 0x00 # Z-axis offset in LSBs (sensore adafruit #1)
accelerometer._write_register_byte(adafruit_adxl34x._REG_OFSX, OFSX)
accelerometer._write_register_byte(adafruit_adxl34x._REG_OFSY, OFSY) 
accelerometer._write_register_byte(adafruit_adxl34x._REG_OFSZ, OFSZ)

# Data rate and power mode control
# bit5: low power (disabled)
# bit4-1: output data rate (100 Hz)
accelerometer._write_register_byte(adafruit_adxl34x._REG_BW_RATE, 0b00001010)

# Power-saving feature control
# bit6: link (disabled)
# bit5: auto sleep (disabled)
# bit4: measure (disabled --> enabled)
# bit3: sleep (disabled)
# bit2-1: wakeup bits (8 Hz) 
accelerometer._write_register_byte(adafruit_adxl34x._REG_BW_RATE, 0b00000000)
accelerometer._write_register_byte(adafruit_adxl34x._REG_BW_RATE, 0b00001000)

# Data format control
# bit8: self test (disabled)
# bit7: SPI mode (4 wire)
# bit6: interrupt active level (active high)
# bit4: full resolution bit (enabled)
# bit3: justify (right)
# bit2-1: range (16g)
accelerometer._write_register_byte(adafruit_adxl34x._REG_DATA_FORMAT, 0b00001011)

# FIFO control
# bit8-7: FIFO mode (stream)
# bit6: trigger (INT1, but unuseful)
# bit5-1: samples needed to trigger watermark interrupt (immediately)  
accelerometer._write_register_byte(adafruit_adxl34x._REG_FIFO_CTL, 0b10000000)

# Edit 'offset' and 'calibrated full-scale' sections after "calibration.py" test.
# Sensor: Adafruit #1
x_min = -249
x_max = 260
delta_x = 509
y_min = -244
y_max = 261
delta_y = 505
z_min = -258
z_max = 242
delta_z = 500

# Offset expressed in LSB.
# We use this instead of OFS registers for finer tuning.
# These numbers depends on calibration.py results for a specific sensor.
x_offset = round((x_min + x_max) / 2)
y_offset = round((y_min + y_max) / 2)
z_offset = round((z_min + z_max) / 2)

# Calibrated full-scale factor, for rescaling.
# We assume that LSB:g relation in linear after rescaling.
# These numbers depends on calibration.py results for a specific sensor.
x_cfs = numpy.ceil(delta_x / 2)
y_cfs = numpy.ceil(delta_y / 2)
z_cfs = numpy.ceil(delta_z / 2)

time.sleep(1)

averages = 10
x_g_avg = 0
y_g_avg = 0
z_g_avg = 0
tiltAngle_1st_avg = 0
tiltAngle_2nd_avg = 0

while True:
	for index in range(averages):
		DATA_XYZ = accelerometer._read_register(adafruit_adxl34x._REG_DATAX0, 6)
		time.sleep(0.1)
		x, y, z = unpack("<hhh",DATA_XYZ)
		x_g = x - x_offset
		y_g = y - y_offset
		z_g = z - z_offset
		x_g_avg = x_g_avg + x_g/averages
		y_g_avg = y_g_avg + y_g/averages
		z_g_avg = z_g_avg + z_g/averages
		# Two formulas to evaluate the same tilt angle
		tiltAngle_1st = numpy.arcsin(- y_g_avg / y_cfs)
		tiltAngle_2nd = numpy.arccos(+ z_g_avg / z_cfs)
		tiltAngle_1st_avg = tiltAngle_1st_avg + tiltAngle_1st/averages
		tiltAngle_2nd_avg = tiltAngle_2nd_avg + tiltAngle_2nd/averages
	print("x y z [LSB]:", round(x_g_avg), round(y_g_avg), round(z_g_avg))
	print("Tilt angle [deg] (two values that should be equal): {0:.2f} {1:.2f}".format(numpy.rad2deg(tiltAngle_1st_avg), numpy.rad2deg(tiltAngle_2nd_avg)))
	accelerometer._write_register_byte(adafruit_adxl34x._REG_BW_RATE, 0b00000000)
	accelerometer._write_register_byte(adafruit_adxl34x._REG_BW_RATE, 0b00001000)
	step=input("Enter something to repeat...")
	x_g_avg = 0
	y_g_avg = 0
	z_g_avg = 0
	tiltAngle_1st_avg = 0
	tiltAngle_2nd_avg = 0