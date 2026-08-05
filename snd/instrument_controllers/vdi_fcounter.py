try:
	import ftd2xx as d2xx
except:
	print('pip install ftd2xx to control vdi f counter')
import atexit

class FC():

	def __init__(self, sn):

		self.sn = sn

		device_list = d2xx.listDevices()
		device_id = -1

		for k in device_list:
			string = k.decode('utf-8')
			if sn in string:
				device_id = device_list.index(k)

		self.dev = d2xx.open(device_id)
		self.calfactor = self.read_calfactor()

		atexit.register(self.cleanup)

	def __del__(self):
		try:	self.close()
		except:	pass

	def cleanup(self):
		self.dev.close()

	def close(self):
		self.dev.close()
		print(f"{self.sn} frequency counter disconnected")

	def read_calfactor(self):
		command = [0x03, 0xaa, 0x01, 0xcf,
				0x67,0x03,0xaa,0x01,0xd0,
				0x78,0x03,0xaa,0x01,0xd1,
				0x79,0x03,0xaa,0x01,0xd2,
				0x7a,0x03,0xaa,0x01,0xd3,
				0x7b]
		self.dev.write(bytes(command))
		out = list(self.dev.read(10))

		byte2 = out[1]
		byte4 = out[3]
		byte6 = out[5]
		byte8 = out[7]
		byte10 = out[9]

		base = byte8+(byte6<<8)+(byte4<<16)+(byte2<<24)
		exp = 10**(byte10-127)

		# print (f'cal factor bytes: {byte2}, {byte4}, {byte6}, {byte8}, {byte10}')

		# print (f'cal factor base = {base}')
		# print (f'cal factor exp = {exp}')

		calfactor = base*exp

		# print (f'cal factor = {calfactor}')
		return calfactor

	def read_frequency(self):
		#hard coded 100ms = 3.84khz resolution
		command = [0x03, 0xFC, 0x64, 0x00, 0x9b]
		self.dev.write(bytes(command))

		out = list(self.dev.read(5))

		error = out[0]
		#if error is 0x55 or 85 that's good I think

		data = (out[1])+(out[2]<<8)+(out[3]<<16)+(out[4]<<24)

		scaled = data / 1e8 * 384

		# print (f'frequency bytes = {out[1]}, {out[2]}, {out[3]}, {out[4]}')

		# print (f'freq data = {data}')
		# print (f'scale by data / 1e8 * 384')
		# print (f'scaled data = {scaled}')

		return scaled * self.calfactor