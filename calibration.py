import time
import adafruit_adxl34x
import busio
import board
from struct import unpack

i2c = busio.I2C(board.SCL, board.SDA, frequency=100e3)
accelerometer = adafruit_adxl34x.ADXL345(i2c)
accelerometer.range = adafruit_adxl34x.Range.RANGE_16_G # Range

# Offset compensation (MANUAL CALIBRATION)
OFSX = 0x2A # X-axis offset in LSBs
OFSY = 0x26 # Y-axis offset in LSBs
OFSZ = 0x80 # Z-axis offset in LSBs
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

averages = 10
x_avg = 0
y_avg = 0
z_avg = 0
x_min = 4096
y_min = 4096
z_min = 4096
x_max = -4096
y_max = -4096
z_max = -4096
time.sleep(1)

while True:
	for index in range(averages):
		DATA_XYZ = accelerometer._read_register(adafruit_adxl34x._REG_DATAX0, 6)
		x, y, z = unpack("<hhh",DATA_XYZ)
		print(x, y, z)
		time.sleep(0.1)
		x_avg = x_avg + x/averages
		y_avg = y_avg + y/averages
		z_avg = z_avg + z/averages
	x_avg = round(x_avg)
	y_avg = round(y_avg)
	z_avg = round(z_avg)
	print("Average values: ", x_avg, y_avg, z_avg)
	if x_avg < x_min:
		x_min = x_avg
	if x_avg > x_max:
		x_max = x_avg
	if y_avg < y_min:
		y_min = y_avg
	if y_avg > y_max:
		y_max = y_avg
	if z_avg < z_min:
		z_min = z_avg
	if z_avg > z_max:
		z_max = z_avg
	delta_x = x_max - x_min
	delta_y = y_max - y_min
	delta_z = z_max - z_min
	print("Minimum values (LSB): ", x_min, y_min, z_min)
	print("Maximum values (LSB): ", x_max, y_max, z_max)
	print("Excursion (LSB): ", delta_x, delta_y, delta_z)
	if delta_x > 512 or delta_y > 512 or delta_z > 512:
		print("WARNING: your sensors seems to be out of range!")
		print("Excursion should not exceed 512 LSB (+-1g).")
	step=input("Enter something to repeat...")
	x_avg = 0
	y_avg = 0
	z_avg = 0
	accelerometer._write_register_byte(adafruit_adxl34x._REG_BW_RATE, 0b00000000)
	accelerometer._write_register_byte(adafruit_adxl34x._REG_BW_RATE, 0b00001000)

