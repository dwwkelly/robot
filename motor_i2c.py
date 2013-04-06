import smbus

bus = smbus.SMBus(0)
address = 15

def SetMotorSpeed(speeda, speedb, address=address, bus=bus):
	# speeds can be set from -255 to 255
	MotorSpeedSet =		0x82
	PWMFrequenceSet =	0x84
	DirectionSet =		0xaa
	MotorSetA =			0xa1
	MotorSetB =			0xa5
	Nothing =			0x01
	I2CMotorDriverAdd =	0x0f

	direction = ''
	if speeda >= 0:
		direction += '0b01'
	else:
		direction += '0b10'
	if speedb >= 0:
		direction += '10'
	else:
		direction += '01'
	direction = eval(direction)

	bus.write_i2c_block_data(address,DirectionSet,[direction])
	bus.write_i2c_block_data(address,MotorSpeedSet,[abs(speeda), abs(speedb)])