try:
	import ftd2xx as d2xx
except:
	print('pip install ftd2xx to control vdi daq')

class RFDAQ():

	byteorder = [15,0,14,1,13,2,12,3,11,4,10,5,9,6,8,7]

	def __init__(self):

		device_ids = []
		device_list = d2xx.listDevices()

		for k in device_list:
			string = k.decode('utf-8')
			if 'RFDAQ' in string:
				device_ids.append(device_list.index(k))

		self.devices = {}
		self.calfactors = {}

		for k in device_ids:
			sn = device_list[k].decode('utf-8')
			dev = d2xx.open(k)

			self.devices[sn] = dev
			self.calfactors[sn] = self.get_all_cal_factors(sn)

	def __del__(self):
		try:	self.cleanup()
		except:	pass

	def cleanup(self):
		print("closing devices")
		for k in self.devices:
			self.devices[k].close()

	def get_cal_byte(self, sn, channel, byte):
		#channel 0 through 15
		#byte 0-6
		address = self.byteorder.index(channel) * 7 + byte

		dev = self.devices[sn]
		command = [3, 170, 1, address, 3^170^1^address]
		dev.write(bytes(command))

		out = list(dev.read(2))
		#print(out)
		return out[1]

	def get_cal_factor(self, sn, channel):
		#channel 0 through 15

		calbytes = []

		for k in range(7):
			byte = self.get_cal_byte(sn, channel, k)
			calbytes.append(byte)

		calfactor = (calbytes[0]*2**24 + calbytes[1] * 2**16 + calbytes[2] * 2**8 + calbytes[3]) * 10**(calbytes[4]-127)
		zerofactor = calbytes[5]*2**8 + calbytes[6]
		if zerofactor > 32768:
			zerofactor = zerofactor-2**16
		zerofactor = (zerofactor/2**15)*2.5

		return calfactor, zerofactor

	def get_all_cal_factors(self, sn):

		out = {}

		for k in range(16):
			calfactor, zerofactor = self.get_cal_factor(sn, k)
			out[k] = (calfactor, zerofactor)

		return out

	def get_raw_data(self, sn, scale):
		#scale is 1 through 3
		#corresponding to 2.5, 5, 10
		#returns (inner conductor voltage, outer conductor voltage)
		command = [2,6,scale,2^6^scale]
		dev = self.devices[sn]

		dev.write(bytes(command))

		out = list(dev.read(33))
		print(out)
		out = out[1:]

		

		data = {}

		#byteorder = [15,0,14,1,13,2,12,3,11,4,10,5,9,6,8,7]

		for k in range(8):
			#start index for each channel
			inner_index = self.byteorder.index(k*2)
			outer_index = self.byteorder.index(k*2+1)

			data[k] = ((out[inner_index*2] * 2**8 + out[inner_index*2+1]), (out[outer_index*2] * 2**8 + out[outer_index*2+1]))

		return data

	def get_caled_data(self, sn, scale):

		raw_data = self.get_raw_data(sn,scale)
		ranges = {1:2.5,2:5,3:10}

		caled_data = {}

		for k in raw_data:

			vinner = raw_data[k][0]
			vouter = raw_data[k][1]

			if vinner>2**15:
				vinner = vinner-2**16

			if vouter>2**15:
				vouter = vouter-2**16

			inner_caled = ((vinner*ranges[scale]/-32768)-self.calfactors[sn][k*2][1])*self.calfactors[sn][k*2][0]
			outer_caled = ((vouter*ranges[scale]/-32768)-self.calfactors[sn][k*2+1][1])*self.calfactors[sn][k*2+1][0]

			caled_data[k] = (inner_caled, outer_caled)

		return caled_data


class VDAQ():

	def __init__(self, sn):

		self.sn = sn

		device_list = d2xx.listDevices()
		device_id = -1

		for k in device_list:
			string = k.decode('utf-8')
			if sn in string:
				device_id = device_list.index(k)

		self.dev = d2xx.open(device_id)
		self.calfactors, self.zerofactors = self.get_cal_factors()

	def cleanup(self):
		self.dev.close()
		print(f"{self.sn} disconnected")
	
	def __del__(self):
		try:	self.cleanup()
		except:	pass

	def write_voltage(self, channel, voltage):
		#this can be programmed to have a delay in us but I don't see the point of that
		#so I didn't bother coding / testing it

		#alisa wanted some safety features
		if abs(voltage) <= 10:
			vscaled = int(((voltage/10)+1)*2**15)
			v_lsb = vscaled & 0xff
			v_msb = (vscaled >> 8) & 0xff
			command = [9, 0, 1, channel, 0, 0, v_msb, v_lsb]

			self.dev.write(bytes(command))
		else:
			print('voltage out of range')

	def get_cal_byte(self, address):
		#address 0 through 112
		command = [0xaa, 0x01, address]
		self.dev.write(bytes(command))

		out = list(self.dev.read(1))[0]
		#print(out)
		return out

	def get_cal_factors(self):
		#channel 0 through 15

		calbytes = []

		#read in all 112 cal bytes
		for k in range(112):
			byte = self.get_cal_byte(k)
			calbytes.append(byte)

		#split into the two different cal factors, 56 bytes each
		calbytes1 = calbytes[0:56]
		calbytes2 = calbytes[56:]

		cf1, zero1 = self.chunkmath(calbytes1, 2.5)
		cf2, zero2 = self.chunkmath(calbytes2, 10)

		#index the cal factors by range, maybe this will make something easier later
		cfs_out = {1:cf1, 2:cf2, 3:cf2}
		zeros_out = {1:zero1, 2:zero2, 3:zero2}

		return cfs_out, zeros_out

	def chunkmath(self, calbytes, scale):

		#split into chunks of 7 bytes each
		chunks = [calbytes[k:k+7] for k in range(0,56,7)]

		cal_out = {}
		zero_out = {}

		count = 0

		for k in chunks:
			calfactor = ( (k[0] << 24) + (k[1] << 16) + (k[2] << 8) + k[3]) * (10 ** (k[4]-127))
			zerofactor = (k[5] << 8) + k[6]

			if zerofactor > 32768:
				zerofactor = zerofactor - 2**16
			zerofactor = zerofactor / 2**15 * scale

			cal_out[count] = calfactor
			zero_out[count] = zerofactor
			count = count+1

		return cal_out, zero_out

	def get_data(self, channel, scale):
		#channel 0-7
		#scale 1: +/-2.5V
		#scale 2: +/-5V
		#scale 3: +/-10V

		scalefactors = {1:2.5,2:5,3:10}

		self.dev.write(bytes([0x08,0x00,0x01,0x01,channel,scale]))
		#this returns four bytes
		#first two bytes are the MSB data from ch4-7, next two bytes are MSB from ch0-3

		out = list(self.dev.read(4))

		if channel > 3:
			data = out[0:2]
		else:
			data = out[2:]

		#now parse and calibrate the data
		v_raw = (data[0] << 8) + data[1]
		if v_raw > 2**15:
			v_raw = v_raw - 2**16

		vout = ((v_raw*scalefactors[scale]/-32768) - self.zerofactors[scale][channel]) * self.calfactors[scale][channel]

		return vout