# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version 4.2.1-0-g80c4cb6)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc

###########################################################################
## Class VirtualENRPanel
###########################################################################

class VirtualENRPanel ( wx.Panel ):

	def __init__( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( 770,696 ), style = wx.TAB_TRAVERSAL, name = wx.EmptyString ):
		wx.Panel.__init__ ( self, parent, id = id, pos = pos, size = size, style = style, name = name )

		bSizer5 = wx.BoxSizer( wx.HORIZONTAL )

		bSizer44 = wx.BoxSizer( wx.VERTICAL )

		self.m_panel6 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.BORDER_RAISED|wx.TAB_TRAVERSAL )
		bSizer7 = wx.BoxSizer( wx.VERTICAL )

		self.m_staticText30 = wx.StaticText( self.m_panel6, wx.ID_ANY, u"Instruments", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText30.Wrap( -1 )

		self.m_staticText30.SetFont( wx.Font( wx.NORMAL_FONT.GetPointSize(), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, wx.EmptyString ) )

		bSizer7.Add( self.m_staticText30, 0, wx.ALL, 5 )

		fgSizer1 = wx.FlexGridSizer( 0, 4, 0, 0 )
		fgSizer1.SetFlexibleDirection( wx.BOTH )
		fgSizer1.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

		self.m_staticText371 = wx.StaticText( self.m_panel6, wx.ID_ANY, u"Type", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText371.Wrap( -1 )

		fgSizer1.Add( self.m_staticText371, 0, wx.ALL, 5 )

		self.m_staticText381 = wx.StaticText( self.m_panel6, wx.ID_ANY, u"Address", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText381.Wrap( -1 )

		fgSizer1.Add( self.m_staticText381, 0, wx.ALL, 5 )

		self.m_staticText39 = wx.StaticText( self.m_panel6, wx.ID_ANY, u"Connected", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText39.Wrap( -1 )

		fgSizer1.Add( self.m_staticText39, 0, wx.ALL, 5 )

		self.m_staticText40 = wx.StaticText( self.m_panel6, wx.ID_ANY, u"Power On", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText40.Wrap( -1 )

		fgSizer1.Add( self.m_staticText40, 0, wx.ALL, 5 )

		self.m_staticText231 = wx.StaticText( self.m_panel6, wx.ID_ANY, u"MXG/PSG", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText231.Wrap( -1 )

		fgSizer1.Add( self.m_staticText231, 0, wx.ALL, 5 )

		self.m_textCtrl17 = wx.TextCtrl( self.m_panel6, wx.ID_ANY, u"20", wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer1.Add( self.m_textCtrl17, 0, wx.ALL, 5 )

		self.m_checkBox3 = wx.CheckBox( self.m_panel6, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer1.Add( self.m_checkBox3, 0, wx.ALL, 5 )

		self.m_checkBox4 = wx.CheckBox( self.m_panel6, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer1.Add( self.m_checkBox4, 0, wx.ALL, 5 )

		self.m_staticText241 = wx.StaticText( self.m_panel6, wx.ID_ANY, u"EXA/PXA", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText241.Wrap( -1 )

		fgSizer1.Add( self.m_staticText241, 0, wx.ALL, 5 )

		self.m_textCtrl18 = wx.TextCtrl( self.m_panel6, wx.ID_ANY, u"18", wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer1.Add( self.m_textCtrl18, 0, wx.ALL, 5 )

		self.m_checkBox5 = wx.CheckBox( self.m_panel6, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer1.Add( self.m_checkBox5, 0, wx.ALL, 5 )


		fgSizer1.Add( ( 0, 0), 1, wx.EXPAND, 5 )

		self.m_staticText251 = wx.StaticText( self.m_panel6, wx.ID_ANY, u"NI-DAQ", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText251.Wrap( -1 )

		fgSizer1.Add( self.m_staticText251, 0, wx.ALL, 5 )

		self.m_textCtrl19 = wx.TextCtrl( self.m_panel6, wx.ID_ANY, u"Dev1", wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer1.Add( self.m_textCtrl19, 0, wx.ALL, 5 )

		self.m_checkBox7 = wx.CheckBox( self.m_panel6, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer1.Add( self.m_checkBox7, 0, wx.ALL, 5 )


		fgSizer1.Add( ( 0, 0), 1, wx.EXPAND, 5 )

		self.m_staticText261 = wx.StaticText( self.m_panel6, wx.ID_ANY, u"HP6627", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText261.Wrap( -1 )

		fgSizer1.Add( self.m_staticText261, 0, wx.ALL, 5 )

		self.m_textCtrl20 = wx.TextCtrl( self.m_panel6, wx.ID_ANY, u"5", wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer1.Add( self.m_textCtrl20, 0, wx.ALL, 5 )

		self.m_checkBox9 = wx.CheckBox( self.m_panel6, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer1.Add( self.m_checkBox9, 0, wx.ALL, 5 )

		self.m_checkBox10 = wx.CheckBox( self.m_panel6, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer1.Add( self.m_checkBox10, 0, wx.ALL, 5 )

		self.m_staticText29 = wx.StaticText( self.m_panel6, wx.ID_ANY, u"Keithley 2600", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText29.Wrap( -1 )

		fgSizer1.Add( self.m_staticText29, 0, wx.ALL, 5 )

		self.m_textCtrl23 = wx.TextCtrl( self.m_panel6, wx.ID_ANY, u"16", wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer1.Add( self.m_textCtrl23, 0, wx.ALL, 5 )

		self.m_checkBox11 = wx.CheckBox( self.m_panel6, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer1.Add( self.m_checkBox11, 0, wx.ALL, 5 )

		self.m_checkBox12 = wx.CheckBox( self.m_panel6, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer1.Add( self.m_checkBox12, 0, wx.ALL, 5 )


		bSizer7.Add( fgSizer1, 1, wx.EXPAND, 5 )


		self.m_panel6.SetSizer( bSizer7 )
		self.m_panel6.Layout()
		bSizer7.Fit( self.m_panel6 )
		bSizer44.Add( self.m_panel6, 0, wx.EXPAND |wx.ALL, 5 )

		self.m_panel9 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.BORDER_RAISED|wx.TAB_TRAVERSAL )
		bSizer8 = wx.BoxSizer( wx.VERTICAL )

		self.m_staticText31 = wx.StaticText( self.m_panel9, wx.ID_ANY, u"Correction Factors", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText31.Wrap( -1 )

		self.m_staticText31.SetFont( wx.Font( wx.NORMAL_FONT.GetPointSize(), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, wx.EmptyString ) )

		bSizer8.Add( self.m_staticText31, 0, wx.ALL, 5 )

		gSizer7 = wx.GridSizer( 0, 2, 0, 0 )

		self.m_staticText32 = wx.StaticText( self.m_panel9, wx.ID_ANY, u"WR10-42 Taper (dB)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText32.Wrap( -1 )

		gSizer7.Add( self.m_staticText32, 0, wx.ALL, 5 )

		self.m_textCtrl24 = wx.TextCtrl( self.m_panel9, wx.ID_ANY, u"0.11", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer7.Add( self.m_textCtrl24, 0, wx.ALL, 5 )

		self.m_staticText33 = wx.StaticText( self.m_panel9, wx.ID_ANY, u"WRXX-10 Taper (dB)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText33.Wrap( -1 )

		gSizer7.Add( self.m_staticText33, 0, wx.ALL, 5 )

		self.m_textCtrl25 = wx.TextCtrl( self.m_panel9, wx.ID_ANY, u"0", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer7.Add( self.m_textCtrl25, 0, wx.ALL, 5 )

		self.m_staticText41 = wx.StaticText( self.m_panel9, wx.ID_ANY, u"Tif (K)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText41.Wrap( -1 )

		gSizer7.Add( self.m_staticText41, 0, wx.ALL, 5 )

		self.m_textCtrl281 = wx.TextCtrl( self.m_panel9, wx.ID_ANY, u"100", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer7.Add( self.m_textCtrl281, 0, wx.ALL, 5 )


		bSizer8.Add( gSizer7, 1, wx.EXPAND, 5 )


		self.m_panel9.SetSizer( bSizer8 )
		self.m_panel9.Layout()
		bSizer8.Fit( self.m_panel9 )
		bSizer44.Add( self.m_panel9, 0, wx.EXPAND |wx.ALL, 5 )

		self.m_panel71 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.BORDER_RAISED|wx.TAB_TRAVERSAL )
		bSizer91 = wx.BoxSizer( wx.VERTICAL )

		self.m_staticText35 = wx.StaticText( self.m_panel71, wx.ID_ANY, u"Noise Source Biasing", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText35.Wrap( -1 )

		self.m_staticText35.SetFont( wx.Font( wx.NORMAL_FONT.GetPointSize(), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, wx.EmptyString ) )

		bSizer91.Add( self.m_staticText35, 0, wx.ALL, 5 )

		gSizer8 = wx.GridSizer( 0, 2, 0, 0 )

		self.m_checkBox1 = wx.CheckBox( self.m_panel71, wx.ID_ANY, u"voltage bias (HP6627)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_checkBox1.SetValue(True)
		gSizer8.Add( self.m_checkBox1, 0, wx.ALL, 5 )


		gSizer8.Add( ( 0, 0), 1, wx.EXPAND, 5 )

		self.m_staticText36 = wx.StaticText( self.m_panel71, wx.ID_ANY, u"HP Channel", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText36.Wrap( -1 )

		gSizer8.Add( self.m_staticText36, 0, wx.ALL, 5 )

		self.m_textCtrl27 = wx.TextCtrl( self.m_panel71, wx.ID_ANY, u"4", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer8.Add( self.m_textCtrl27, 0, wx.ALL, 5 )

		self.m_staticText37 = wx.StaticText( self.m_panel71, wx.ID_ANY, u"Voltage (V)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText37.Wrap( -1 )

		gSizer8.Add( self.m_staticText37, 0, wx.ALL, 5 )

		self.m_textCtrl28 = wx.TextCtrl( self.m_panel71, wx.ID_ANY, u"28", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer8.Add( self.m_textCtrl28, 0, wx.ALL, 5 )

		self.m_staticText361 = wx.StaticText( self.m_panel71, wx.ID_ANY, u"Current Limit (mA)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText361.Wrap( -1 )

		gSizer8.Add( self.m_staticText361, 0, wx.ALL, 5 )

		self.m_textCtrl271 = wx.TextCtrl( self.m_panel71, wx.ID_ANY, u"100", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer8.Add( self.m_textCtrl271, 0, wx.ALL, 5 )

		self.m_checkBox2 = wx.CheckBox( self.m_panel71, wx.ID_ANY, u"current bias (Keithley)", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer8.Add( self.m_checkBox2, 0, wx.ALL, 5 )


		gSizer8.Add( ( 0, 0), 1, wx.EXPAND, 5 )

		self.m_staticText38 = wx.StaticText( self.m_panel71, wx.ID_ANY, u"Current (mA)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText38.Wrap( -1 )

		gSizer8.Add( self.m_staticText38, 0, wx.ALL, 5 )

		self.m_textCtrl29 = wx.TextCtrl( self.m_panel71, wx.ID_ANY, u"3", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer8.Add( self.m_textCtrl29, 0, wx.ALL, 5 )

		self.m_staticText351 = wx.StaticText( self.m_panel71, wx.ID_ANY, u"Voltage Limit (V)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText351.Wrap( -1 )

		gSizer8.Add( self.m_staticText351, 0, wx.ALL, 5 )

		self.m_textCtrl26 = wx.TextCtrl( self.m_panel71, wx.ID_ANY, u"20", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer8.Add( self.m_textCtrl26, 0, wx.ALL, 5 )


		bSizer91.Add( gSizer8, 1, wx.EXPAND, 5 )


		self.m_panel71.SetSizer( bSizer91 )
		self.m_panel71.Layout()
		bSizer91.Fit( self.m_panel71 )
		bSizer44.Add( self.m_panel71, 0, wx.EXPAND |wx.ALL, 5 )

		self.m_panel8 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.BORDER_RAISED|wx.TAB_TRAVERSAL )
		bSizer11 = wx.BoxSizer( wx.VERTICAL )

		self.m_staticText34 = wx.StaticText( self.m_panel8, wx.ID_ANY, u"Troubleshooting", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText34.Wrap( -1 )

		self.m_staticText34.SetFont( wx.Font( wx.NORMAL_FONT.GetPointSize(), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, wx.EmptyString ) )

		bSizer11.Add( self.m_staticText34, 0, wx.ALL, 5 )

		bSizer4 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_button91 = wx.Button( self.m_panel8, wx.ID_ANY, u"MotorCW", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer4.Add( self.m_button91, 0, wx.ALL, 5 )

		self.m_button101 = wx.Button( self.m_panel8, wx.ID_ANY, u"MotorCCW", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer4.Add( self.m_button101, 0, wx.ALL, 5 )

		self.m_button11 = wx.Button( self.m_panel8, wx.ID_ANY, u"Reconnect Instruments", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer4.Add( self.m_button11, 0, wx.ALL, 5 )


		bSizer11.Add( bSizer4, 1, wx.EXPAND, 5 )


		self.m_panel8.SetSizer( bSizer11 )
		self.m_panel8.Layout()
		bSizer11.Fit( self.m_panel8 )
		bSizer44.Add( self.m_panel8, 1, wx.EXPAND |wx.ALL, 5 )


		bSizer5.Add( bSizer44, 0, wx.EXPAND, 5 )

		bSizer7 = wx.BoxSizer( wx.VERTICAL )

		self.m_panel5 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		gSizer1 = wx.GridSizer( 0, 2, 0, 0 )

		self.m_staticText27 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"VBW (Hz)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText27.Wrap( -1 )

		gSizer1.Add( self.m_staticText27, 0, wx.ALL, 5 )

		self.vbw_hz = wx.TextCtrl( self.m_panel5, wx.ID_ANY, u"1", wx.DefaultPosition, wx.DefaultSize, wx.TE_READONLY )
		gSizer1.Add( self.vbw_hz, 0, wx.ALL, 5 )

		self.m_staticText28 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"RBW (Hz)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText28.Wrap( -1 )

		gSizer1.Add( self.m_staticText28, 0, wx.ALL, 5 )

		self.rbw_hz = wx.TextCtrl( self.m_panel5, wx.ID_ANY, u"8000000", wx.DefaultPosition, wx.DefaultSize, wx.TE_READONLY )
		gSizer1.Add( self.rbw_hz, 0, wx.ALL, 5 )

		self.m_staticText4 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"IF Center Freq (MHz)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText4.Wrap( -1 )

		gSizer1.Add( self.m_staticText4, 0, wx.ALL, 5 )

		self.ifcenter_mhz = wx.TextCtrl( self.m_panel5, wx.ID_ANY, u"70", wx.DefaultPosition, wx.DefaultSize, wx.TE_READONLY )
		gSizer1.Add( self.ifcenter_mhz, 0, wx.ALL, 5 )

		self.m_staticText5 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"Sweep Time (s)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText5.Wrap( -1 )

		gSizer1.Add( self.m_staticText5, 0, wx.ALL, 5 )

		self.ifbw_mhz = wx.TextCtrl( self.m_panel5, wx.ID_ANY, u"1", wx.DefaultPosition, wx.DefaultSize)
		gSizer1.Add( self.ifbw_mhz, 0, wx.ALL, 5 )

		self.m_staticText6 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"Start Frequency (GHz)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText6.Wrap( -1 )

		gSizer1.Add( self.m_staticText6, 0, wx.ALL, 5 )

		self.fstart_ghz = wx.TextCtrl( self.m_panel5, wx.ID_ANY, u"110", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer1.Add( self.fstart_ghz, 0, wx.ALL, 5 )

		self.m_staticText7 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"Stop Frequency (GHz)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText7.Wrap( -1 )

		gSizer1.Add( self.m_staticText7, 0, wx.ALL, 5 )

		self.fstop_ghz = wx.TextCtrl( self.m_panel5, wx.ID_ANY, u"170", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer1.Add( self.fstop_ghz, 0, wx.ALL, 5 )

		self.m_staticText25 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"Multiplier", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText25.Wrap( -1 )

		gSizer1.Add( self.m_staticText25, 0, wx.ALL, 5 )

		self.mult = wx.TextCtrl( self.m_panel5, wx.ID_ANY, u"12", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer1.Add( self.mult, 0, wx.ALL, 5 )

		self.m_staticText8 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"LO Power (dBm)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText8.Wrap( -1 )

		gSizer1.Add( self.m_staticText8, 0, wx.ALL, 5 )

		self.lopower_dbm = wx.TextCtrl( self.m_panel5, wx.ID_ANY, u"0", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer1.Add( self.lopower_dbm, 0, wx.ALL, 5 )

		self.m_staticText16 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"Number of Points", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText16.Wrap( -1 )

		gSizer1.Add( self.m_staticText16, 0, wx.ALL, 5 )

		self.num_points = wx.TextCtrl( self.m_panel5, wx.ID_ANY, u"101", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer1.Add( self.num_points, 0, wx.ALL, 5 )

		self.m_staticText26 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"Meas. Delay (s)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText26.Wrap( -1 )

		gSizer1.Add( self.m_staticText26, 0, wx.ALL, 5 )

		self.measdelay = wx.TextCtrl( self.m_panel5, wx.ID_ANY, u"1", wx.DefaultPosition, wx.DefaultSize, wx.TE_READONLY )
		gSizer1.Add( self.measdelay, 0, wx.ALL, 5 )

		self.m_button5 = wx.Button( self.m_panel5, wx.ID_ANY, u"Check Setup at Midband", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer1.Add( self.m_button5, 0, wx.ALL, 5 )

		self.verify_textbox = wx.StaticText( self.m_panel5, wx.ID_ANY, u"[measured power]", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.verify_textbox.Wrap( -1 )

		gSizer1.Add( self.verify_textbox, 0, wx.ALL, 5 )


		self.m_panel5.SetSizer( gSizer1 )
		self.m_panel5.Layout()
		gSizer1.Fit( self.m_panel5 )
		bSizer7.Add( self.m_panel5, 0, wx.EXPAND |wx.ALL, 5 )

		bSizer13 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText3 = wx.StaticText( self, wx.ID_ANY, u"Save Directory: ", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText3.Wrap( -1 )

		bSizer13.Add( self.m_staticText3, 0, wx.ALL, 5 )

		self.output_dir_picker = wx.DirPickerCtrl( self, wx.ID_ANY, wx.EmptyString, u"Select a folder", wx.DefaultPosition, wx.DefaultSize, wx.DIRP_DEFAULT_STYLE )
		bSizer13.Add( self.output_dir_picker, 1, wx.ALL, 5 )


		bSizer7.Add( bSizer13, 0, wx.EXPAND, 5 )

		bSizer15 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText19 = wx.StaticText( self, wx.ID_ANY, u"Filename:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText19.Wrap( -1 )

		bSizer15.Add( self.m_staticText19, 0, wx.ALL, 5 )

		self.output_filename = wx.TextCtrl( self, wx.ID_ANY, u"Tsys", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer15.Add( self.output_filename, 1, wx.ALL, 5 )


		bSizer7.Add( bSizer15, 0, wx.EXPAND, 5 )

		self.m_notebook4 = wx.Notebook( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_panel3 = wx.Panel( self.m_notebook4, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		bSizer13 = wx.BoxSizer( wx.VERTICAL )

		gSizer3 = wx.GridSizer( 0, 2, 0, 0 )

		self.m_staticText17 = wx.StaticText( self.m_panel3, wx.ID_ANY, u"NS Calibration File (T Hot)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText17.Wrap( -1 )

		gSizer3.Add( self.m_staticText17, 0, wx.ALL, 5 )

		self.ns_file_in = wx.FilePickerCtrl( self.m_panel3, wx.ID_ANY, wx.EmptyString, u"Select a file", u"*.*", wx.DefaultPosition, wx.DefaultSize, wx.FLP_DEFAULT_STYLE )
		gSizer3.Add( self.ns_file_in, 0, wx.ALL, 5 )

		self.m_staticText18 = wx.StaticText( self.m_panel3, wx.ID_ANY, u"Room Temp (K)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText18.Wrap( -1 )

		gSizer3.Add( self.m_staticText18, 0, wx.ALL, 5 )

		self.roomtemp_k = wx.TextCtrl( self.m_panel3, wx.ID_ANY, u"293", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer3.Add( self.roomtemp_k, 0, wx.ALL, 5 )

		self.m_button8 = wx.Button( self.m_panel3, wx.ID_ANY, u"Save Chopped Data", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer3.Add( self.m_button8, 0, wx.ALL, 5 )


		bSizer13.Add( gSizer3, 0, wx.EXPAND, 5 )


		self.m_panel3.SetSizer( bSizer13 )
		self.m_panel3.Layout()
		bSizer13.Fit( self.m_panel3 )
		self.m_notebook4.AddPage( self.m_panel3, u"Meas Tsys using NS", False )
		self.m_panel2 = wx.Panel( self.m_notebook4, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		bSizer14 = wx.BoxSizer( wx.VERTICAL )

		gSizer2 = wx.GridSizer( 0, 2, 0, 0 )

		self.m_staticText11 = wx.StaticText( self.m_panel2, wx.ID_ANY, u"T Hot (K)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText11.Wrap( -1 )

		gSizer2.Add( self.m_staticText11, 0, wx.ALL, 5 )

		self.ln2_thot = wx.TextCtrl( self.m_panel2, wx.ID_ANY, u"293", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer2.Add( self.ln2_thot, 0, wx.ALL, 5 )

		self.m_staticText12 = wx.StaticText( self.m_panel2, wx.ID_ANY, u"T Cold (K)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText12.Wrap( -1 )

		gSizer2.Add( self.m_staticText12, 0, wx.ALL, 5 )

		self.ln2_tcold = wx.TextCtrl( self.m_panel2, wx.ID_ANY, u"80", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer2.Add( self.ln2_tcold, 0, wx.ALL, 5 )

		self.m_button6 = wx.Button( self.m_panel2, wx.ID_ANY, u"Save Chopped Data", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer2.Add( self.m_button6, 0, wx.ALL, 5 )


		bSizer14.Add( gSizer2, 0, wx.EXPAND, 5 )


		self.m_panel2.SetSizer( bSizer14 )
		self.m_panel2.Layout()
		bSizer14.Fit( self.m_panel2 )
		self.m_notebook4.AddPage( self.m_panel2, u"Meas Tsys Hot/Cold", False )
		self.m_panel7 = wx.Panel( self.m_notebook4, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		bSizer15 = wx.BoxSizer( wx.VERTICAL )

		gSizer4 = wx.GridSizer( 0, 2, 0, 0 )

		self.m_staticText22 = wx.StaticText( self.m_panel7, wx.ID_ANY, u"RX Tsys File", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText22.Wrap( -1 )

		gSizer4.Add( self.m_staticText22, 0, wx.ALL, 5 )

		self.rx_tsys_in = wx.FilePickerCtrl( self.m_panel7, wx.ID_ANY, wx.EmptyString, u"Select a file", u"*.*", wx.DefaultPosition, wx.DefaultSize, wx.FLP_DEFAULT_STYLE )
		gSizer4.Add( self.rx_tsys_in, 0, wx.ALL, 5 )

		self.m_staticText23 = wx.StaticText( self.m_panel7, wx.ID_ANY, u"NS with unknown T Hot", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText23.Wrap( -1 )

		gSizer4.Add( self.m_staticText23, 0, wx.ALL, 5 )

		self.ns_unknown_in = wx.FilePickerCtrl( self.m_panel7, wx.ID_ANY, wx.EmptyString, u"Select a file", u"*.*", wx.DefaultPosition, wx.DefaultSize, wx.FLP_DEFAULT_STYLE )
		gSizer4.Add( self.ns_unknown_in, 0, wx.ALL, 5 )

		self.m_staticText24 = wx.StaticText( self.m_panel7, wx.ID_ANY, u"Filename", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText24.Wrap( -1 )

		gSizer4.Add( self.m_staticText24, 0, wx.ALL, 5 )

		self.ns_cal_filename = wx.TextCtrl( self.m_panel7, wx.ID_ANY, u"NS XX Cal File", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer4.Add( self.ns_cal_filename, 0, wx.ALL, 5 )

		self.m_button12 = wx.Button( self.m_panel7, wx.ID_ANY, u"Calculate and Save File", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer4.Add( self.m_button12, 0, wx.ALL, 5 )


		bSizer15.Add( gSizer4, 0, wx.EXPAND, 5 )


		self.m_panel7.SetSizer( bSizer15 )
		self.m_panel7.Layout()
		bSizer15.Fit( self.m_panel7 )
		self.m_notebook4.AddPage( self.m_panel7, u"Create ENR File", False )
		self.m_panel91 = wx.Panel( self.m_notebook4, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		bSizer17 = wx.BoxSizer( wx.VERTICAL )

		gSizer15 = wx.GridSizer( 0, 2, 0, 0 )

		self.m_button14 = wx.Button( self.m_panel91, wx.ID_ANY, u"Room Temp", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer15.Add( self.m_button14, 0, wx.ALL, 5 )

		self.m_staticText42 = wx.StaticText( self.m_panel91, wx.ID_ANY, u"[measured power]", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText42.Wrap( -1 )

		gSizer15.Add( self.m_staticText42, 0, wx.ALL, 5 )

		self.m_button15 = wx.Button( self.m_panel91, wx.ID_ANY, u"Cold", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer15.Add( self.m_button15, 0, wx.ALL, 5 )

		self.m_staticText43 = wx.StaticText( self.m_panel91, wx.ID_ANY, u"[measured power]", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText43.Wrap( -1 )

		gSizer15.Add( self.m_staticText43, 0, wx.ALL, 5 )

		self.m_staticText44 = wx.StaticText( self.m_panel91, wx.ID_ANY, u"Cable Loss (dB)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText44.Wrap( -1 )

		gSizer15.Add( self.m_staticText44, 0, wx.ALL, 5 )

		self.m_textCtrl291 = wx.TextCtrl( self.m_panel91, wx.ID_ANY, u"0.07", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer15.Add( self.m_textCtrl291, 0, wx.ALL, 5 )

		self.m_button16 = wx.Button( self.m_panel91, wx.ID_ANY, u"Calc Tif", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer15.Add( self.m_button16, 0, wx.ALL, 5 )

		self.m_staticText45 = wx.StaticText( self.m_panel91, wx.ID_ANY, u"[ tif ]", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText45.Wrap( -1 )

		gSizer15.Add( self.m_staticText45, 0, wx.ALL, 5 )


		bSizer17.Add( gSizer15, 0, wx.EXPAND, 5 )


		self.m_panel91.SetSizer( bSizer17 )
		self.m_panel91.Layout()
		bSizer17.Fit( self.m_panel91 )
		self.m_notebook4.AddPage( self.m_panel91, u"Meas Tif", True )

		bSizer7.Add( self.m_notebook4, 1, wx.EXPAND |wx.ALL, 5 )


		bSizer5.Add( bSizer7, 1, wx.EXPAND, 5 )


		self.SetSizer( bSizer5 )
		self.Layout()

		# Connect Events
		self.m_checkBox4.Bind( wx.EVT_CHECKBOX, self.psg_power_toggled )
		self.m_checkBox10.Bind( wx.EVT_CHECKBOX, self.hp_power_toggled )
		self.m_checkBox12.Bind( wx.EVT_CHECKBOX, self.smu_power_toggled )
		self.m_checkBox1.Bind( wx.EVT_CHECKBOX, self.voltage_bias_checked )
		self.m_checkBox2.Bind( wx.EVT_CHECKBOX, self.current_bias_checked )
		self.m_button91.Bind( wx.EVT_BUTTON, self.MotorCW )
		self.m_button101.Bind( wx.EVT_BUTTON, self.MotorCCW )
		self.m_button11.Bind( wx.EVT_BUTTON, self.reconnect_instruments_pressed )
		self.m_button5.Bind( wx.EVT_BUTTON, self.VerifySetup )
		self.m_button8.Bind( wx.EVT_BUTTON, self.ns_chopped_pressed )
		self.m_button6.Bind( wx.EVT_BUTTON, self.hotcold_chopped_pressed )
		self.m_button12.Bind( wx.EVT_BUTTON, self.create_ns_calfile )
		self.m_button14.Bind( wx.EVT_BUTTON, self.measure_tif_roomtemp )
		self.m_button15.Bind( wx.EVT_BUTTON, self.measure_tif_cold )

	def __del__( self ):
		pass


	# Virtual event handlers, override them in your derived class
	def psg_power_toggled( self, event ):
		event.Skip()

	def hp_power_toggled( self, event ):
		event.Skip()

	def smu_power_toggled( self, event ):
		event.Skip()

	def voltage_bias_checked( self, event ):
		event.Skip()

	def current_bias_checked( self, event ):
		event.Skip()

	def MotorCW( self, event ):
		event.Skip()

	def MotorCCW( self, event ):
		event.Skip()

	def reconnect_instruments_pressed( self, event ):
		event.Skip()

	def VerifySetup( self, event ):
		event.Skip()

	def ns_chopped_pressed( self, event ):
		event.Skip()

	def hotcold_chopped_pressed( self, event ):
		event.Skip()

	def create_ns_calfile( self, event ):
		event.Skip()

	def measure_tif_roomtemp( self, event ):
		event.Skip()

	def measure_tif_cold( self, event ):
		event.Skip()


