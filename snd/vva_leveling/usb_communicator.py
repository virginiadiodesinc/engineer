import ftd2xx as d2xx
import power_control_functions as pcf


class usb_communicator():
	USB_NAME = b'VDIU9'
	handle = None

	def connect(self):
		device_list = d2xx.listDevices()
		usb_device_index = None

		for index, device in enumerate(device_list):
			if device == self.USB_NAME:
				usb_device_index = index

		self.handle = d2xx.open(usb_device_index)
	

	def write(self, byte_string):
		self.handle.write(byte_string)

