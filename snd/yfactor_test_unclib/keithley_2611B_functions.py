import pyvisa
import time

class SMU_K2611B():
    #GPIB address 16 by default
    def __init__(self, address=16):
        """
        SMU 2611B Object parameters

        Returns
        -------
        None.

        """
        rm = pyvisa.ResourceManager()
        gpib_address = f'GPIB0::{address}::INSTR'

        self.inst = rm.open_resource(gpib_address)
        
        self.default_delay_command = "smua.measure.delay = smua.DELAY_AUTO" #default delay on
        self.integration_time_command = "smua.measure.nplc = 1" #default integration time: medium
        self.filter_readings_command =  "smua.measure.filter.count = 8" #default filter readings '8'
        self.compliance_voltage_command = "smua.source.limitv = 1.2" #default compliance voltage = 1.2V
        self.sign = '' #default polarity positive
        self.points = 5 * 6 #default 5 points per decade, 6 decades
        self.user_sweep_delay_command = "smua.source.delay = smua.DELAY_AUTO" #default user sweep delay 0ms
        self.Imin = '100E-9'
        self.Imax = '1E-3'
        self.start_current = self.sign+self.Imin #default start current 0.1uA
        self.end_current = self.sign+self.Imax #default end current 1mA
        self.configure_sweep_command = f"smua.trigger.source.logi({self.start_current}, {self.end_current}, {self.points}, 0)"

    def reset(self):
        """
        Resets the SMU

        Returns
        -------
        None.

        """
        self.inst.write('smua.reset()')
        
    def filter_on(self):
        """
        Turns the measurement filter on

        Returns
        -------
        None.

        """
        self.inst.write('smua.measure.filter.enable = smua.FILTER_ON')
        
    def filter_off(self):
        """
        Turns the measurement filter off

        Returns
        -------
        None.

        """
        self.inst.write('smua.measure.filter.enable = smua.FILTER_OFF')

    def sourceOn(self):
        """
        Turns the SMU output ON

        Returns
        -------
        None.

        """
        self.inst.write('smua.source.output = smua.OUTPUT_ON')
        
    def sourceOff(self):
        """
        Turns the SMU output OFF

        Returns
        -------
        None.

        """
        self.inst.write('smua.source.output = smua.OUTPUT_OFF')

    def set_default_delay(self, toggle):
        """
        Toggles SMU 236 default delay: on , off
        Controls the enabling/ disabling of a fixed delay used to compensate for the instrument settling time when measuring resistive loads

        Returns
        -------
        None.
        """
        if toggle == 'on':
            self.default_delay_command = "smua.measure.delay = smua.DELAY_AUTO"
        elif toggle == 'off':
            self.default_delay_command = "smua.measure.delay = smua.DELAY_OFF"

    def set_filter(self, count, method='FILTER_REPEAT_AVG'):
        """
        Configures the filter to be used during the measurement acquisition.

        Parameters
        ----------
        count : TYPE integer
            DESCRIPTION. The number of measurements that should be grouped in the filter. To ensure analagous functionality to the K236, choices are 2, 4, 8, 16, 32.

        Returns
        -------
        None.
        """
        if count == 'off':
            self.filter_readings_command = ""
        elif count == '2':
            self.filter_readings_command = "smua.measure.filter.count = 2"
        elif count == '4':
            self.filter_readings_command = "smua.measure.filter.count = 4"
        elif count == '8':
            self.filter_readings_command = "smua.measure.filter.count = 8"
        elif count == '16':
            self.filter_readings_command = "smua.measure.filter.count = 16"
        elif count == '32':
            self.filter_readings_command = "smua.measure.filter.count = 32"

    def set_polarity(self, polarity):
        """
        Set source current positive (+) or negative (-).

        Returns
        -------
        None.
        """
        if polarity == '+':
            self.sign = ''
            self.start_current = self.sign+self.Imin
            self.end_current = self.sign+self.Imax
            self.configure_sweep_command = f"smua.trigger.source.logi({self.start_current}, {self.end_current}, {self.points}, 0)"

        elif polarity == '-':
            self.sign = '-'
            self.start_current = self.sign+self.Imin
            self.end_current = self.sign+self.Imax
            self.configure_sweep_command = f"smua.trigger.source.logi({self.start_current}, {self.end_current}, {self.points}, 0)"

    def set_compliance_voltage(self, Vmax):
        """
        Set compliance voltage. I believe MicroA does not exceed Vmax = 4, but the limit can be set to whatever the correct value is.
        Compliance voltage changes in 0.1V increments, so compliance voltage value truncates to a minimum of 0.1 and to a max of 4.0 if out of range.

        Returns
        -------
        None.
        """
        if 0.1 <= Vmax <= 4.0:
            self.compliance_voltage_command = f"smua.source.limitv = {Vmax}"
        elif Vmax < 0.1:
            self.compliance_voltage_command = "smua.source.limitv = 0.1"
        elif Vmax > 4.0:
            self.compliance_voltage_command = "smua.source.limitv = 4.0"

    def set_integration_time(self, option):
        """
        Set integration time: 60Hz, Medium, Fast
        The ADC integrates the input signal over a time window equal to integration_time = number_of_power_line_cycles / line_frequency

        Since the line_frequency is 60Hz on US mains, an NPLC of 1 gives integration _time = 1 / 60 = 16.67ms

        Returns
        -------
        None.
        """
        if option == '60Hz':
            self.integration_time_command = "smua.measure.nplc = 1" #16.67ms
        elif option == 'Medium':
            self.integration_time_command = "smua.measure.nplc = 0.5" #8.35ms
        elif option == 'Fast':
            self.integration_time_command = "smua.measure.nplc = 0.1" #1.67ms

    def set_user_sweep_delay(self, sweep_delay):
        """
        Set sweep delay, lower limit 0ms, upper limit 1s? (change if needed)

        Returns
        -------
        None.
        """
        if 0 <= sweep_delay <= 1000:
            self.user_sweep_delay_command = f"smua.source.delay = {sweep_delay/1000}"
        elif sweep_delay < 0:
            self.user_sweep_delay_command = "smua.source.delay = 0"
        elif sweep_delay > 1000:
            self.user_sweep_delay_command = "smua.source.delay = 1"

    def set_points_per_decade(self, points_per_decade):
        """
        Set points per decade: 5, 10, 25, or 50 points per decade
        Since there are always 6 decades in the IV labview program and the smu 2611B needs the total number of points,
        self.points takes the multiple of points per decade and 6 decades.

        Returns
        -------
        None.
        """
        if points_per_decade == '5':
            self.points = 5 * 6
            self.configure_sweep_command = f"smua.trigger.source.logi({self.start_current}, {self.end_current}, {self.points}, 0)"
        elif points_per_decade == '10':
            self.points = 10 * 6
            self.configure_sweep_command = f"smua.trigger.source.logi({self.start_current}, {self.end_current}, {self.points}, 0)"
        elif points_per_decade == '25':
            self.points = 25 * 6
            self.configure_sweep_command = f"smua.trigger.source.logi({self.start_current}, {self.end_current}, {self.points}, 0)"
        elif points_per_decade == '50':
            self.points = 50 * 6
            self.configure_sweep_command = f"smua.trigger.source.logi({self.start_current}, {self.end_current}, {self.points}, 0)"

    def set_maximum_current(self, current):
        """
        Set current range based on maximum current: 1mA, 2mA, 3mA, 4mA, 5mA

        Returns
        -------
        None.
        """
        if current == '1mA':
            self.Imin = '100E-9'
            self.Imax = '1E-3'
            self.start_current = self.sign+self.Imin
            self.end_current = self.sign+self.Imax
            self.configure_sweep_command = f"smua.trigger.source.logi({self.start_current}, {self.end_current}, {self.points}, 0)"
        elif current == '2mA':
            self.Imin = '200E-9'
            self.Imax = '2E-3'
            self.start_current = self.sign+self.Imin
            self.end_current = self.sign+self.Imax
            self.configure_sweep_command = f"smua.trigger.source.logi({self.start_current}, {self.end_current}, {self.points}, 0)"
        elif current == '3mA':
            self.Imin = '300E-9'
            self.Imax = '3E-3'
            self.start_current = self.sign+self.Imin
            self.end_current = self.sign+self.Imax
            self.configure_sweep_command = f"smua.trigger.source.logi({self.start_current}, {self.end_current}, {self.points}, 0)"
        elif current == '4mA':
            self.Imin = '400E-9'
            self.Imax = '4E-3'
            self.start_current = self.sign+self.Imin
            self.end_current = self.sign+self.Imax
            self.configure_sweep_command = f"smua.trigger.source.logi({self.start_current}, {self.end_current}, {self.points}, 0)"
        elif current == '5mA':
            self.Imin = '500E-9'
            self.Imax = '5E-3'
            self.start_current = self.sign+self.Imin
            self.end_current = self.sign+self.Imax
            self.configure_sweep_command = f"smua.trigger.source.logi({self.start_current}, {self.end_current}, {self.points}, 0)"
   
    def takeIV(self):
        """
        SMU IV Sequence
        
        Returns
        -------
        source_values: a list of current values fed to the diode.
        voltage_values: a list of voltage values measured across the diode.

        """
        self.reset()

        self.inst.write('display.screen = display.SMUA') #Switches the front-panel display to show Channel A (SMUA) This affects only the UI, not measurements or sourcing.
        self.inst.write('display.smua.measure.func = display.MEASURE_DCVOLTS') #Sets the displayed measurement function for SMUA to DC volts. 
    
        self.inst.write('format.data = format.ASCII') #Sets output data format to ASCII text so the returned values will not be binary.
        self.inst.write('smua.nvbuffer1.clear()') #Clears nonvolatile buffer 1. Removes old stored readings so new data starts clean.
        self.inst.write('smua.nvbuffer1.appendmode = 1') #Enables append mode. New readings are added to the buffer, old readings are preserved until cleared.
        self.inst.write('smua.nvbuffer1.collectsourcevalues = 1') #Tells the buffer to also store source values with each measurement so each record can include the measured value and the source level at that moment.
        self.inst.write('smua.measure.count = 1') #Take one measurement per trigger/reading request. So each measurement command returns a single reading (not an average or burst).

        self.inst.write('smua.source.func = smua.OUTPUT_DCAMPS') #Sets SMUA to source current mode so that the SMU will force current: Current Source / Voltage Measure mode.

        self.inst.write(self.default_delay_command)

        self.inst.write(self.integration_time_command)

        if self.filter_readings_command:
            self.inst.write(self.filter_readings_command)
            self.inst.write('smua.measure.filter.type = smua.FILTER_REPEAT_AVG')
            self.filter_on()
        else:
            self.filter_off()

        self.inst.write(self.compliance_voltage_command)
        
        self.inst.write(self.configure_sweep_command)

        self.sourceOn()

        self.inst.write('smua.trigger.measure.action = smua.ENABLE')

        self.inst.write('smua.trigger.initiate()')
        time.sleep(3)

        source_values = self.inst.query_ascii_values('printbuffer(1, smua.nvbuffer1.n, smua.nvbuffer1.sourcevalues)')
        measure_values = self.inst.query_ascii_values('printbuffer(1, smua.nvbuffer1.n, smua.nvbuffer1.readings)')

        print(source_values) #current values
        print(measure_values) #voltage values

        return source_values, measure_values
        