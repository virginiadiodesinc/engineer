# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version 4.2.1-0-g80c4cb6)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc

import gettext
_ = gettext.gettext

###########################################################################
## Class MyFrame1
###########################################################################

class MyFrame1 ( wx.Frame ):

    def __init__( self, parent ):
        wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = wx.EmptyString, pos = wx.DefaultPosition, size = wx.Size( 498,586 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )

        self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )

        bSizer1 = wx.BoxSizer( wx.VERTICAL )

        self.m_panel1 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer2 = wx.BoxSizer( wx.VERTICAL )

        self.m_staticText1 = wx.StaticText( self.m_panel1, wx.ID_ANY, _(u"address"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText1.Wrap( -1 )

        bSizer2.Add( self.m_staticText1, 0, wx.ALL, 5 )

        self.m_textCtrl1 = wx.TextCtrl( self.m_panel1, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer2.Add( self.m_textCtrl1, 0, wx.ALL, 5 )

        self.m_button1 = wx.Button( self.m_panel1, wx.ID_ANY, _(u"connect"), wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer2.Add( self.m_button1, 0, wx.ALL, 5 )

        self.m_button3 = wx.Button( self.m_panel1, wx.ID_ANY, _(u"PSG_connect"), wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer2.Add( self.m_button3, 0, wx.ALL, 5 )

        self.m_button2 = wx.Button( self.m_panel1, wx.ID_ANY, _(u"*idn"), wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer2.Add( self.m_button2, 0, wx.ALL, 5 )

        self.m_textCtrl2 = wx.TextCtrl( self.m_panel1, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.TE_MULTILINE )
        bSizer2.Add( self.m_textCtrl2, 1, wx.ALL, 5 )

        self.m_button4 = wx.Button( self.m_panel1, wx.ID_ANY, _(u"power_on"), wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer2.Add( self.m_button4, 0, wx.ALL, 5 )

        self.m_button5 = wx.Button( self.m_panel1, wx.ID_ANY, _(u"power_off"), wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer2.Add( self.m_button5, 0, wx.ALL, 5 )

        self.m_textCtrl3 = wx.TextCtrl( self.m_panel1, wx.ID_ANY, _(u"10"), wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer2.Add( self.m_textCtrl3, 0, wx.ALL, 5 )

        self.m_button6 = wx.Button( self.m_panel1, wx.ID_ANY, _(u"set freq"), wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer2.Add( self.m_button6, 0, wx.ALL, 5 )

        self.m_button7 = wx.Button( self.m_panel1, wx.ID_ANY, _(u"get_freq"), wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer2.Add( self.m_button7, 0, wx.ALL, 5 )

        self.m_textCtrl4 = wx.TextCtrl( self.m_panel1, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer2.Add( self.m_textCtrl4, 0, wx.ALL, 5 )


        self.m_panel1.SetSizer( bSizer2 )
        self.m_panel1.Layout()
        bSizer2.Fit( self.m_panel1 )
        bSizer1.Add( self.m_panel1, 1, wx.EXPAND |wx.ALL, 5 )


        self.SetSizer( bSizer1 )
        self.Layout()

        self.Centre( wx.BOTH )

        # Connect Events
        self.m_button1.Bind( wx.EVT_BUTTON, self.connect_pressed )
        self.m_button3.Bind( wx.EVT_BUTTON, self.psg_connect_pressed )
        self.m_button2.Bind( wx.EVT_BUTTON, self.idn_pressed )
        self.m_button4.Bind( wx.EVT_BUTTON, self.power_on_pressed )
        self.m_button5.Bind( wx.EVT_BUTTON, self.power_off_pressed )
        self.m_button6.Bind( wx.EVT_BUTTON, self.set_freq_pressed )
        self.m_button7.Bind( wx.EVT_BUTTON, self.get_freq_pressed )

    def __del__( self ):
        pass


    # Virtual event handlers, override them in your derived class
    def connect_pressed( self, event ):
        event.Skip()

    def psg_connect_pressed( self, event ):
        event.Skip()

    def idn_pressed( self, event ):
        event.Skip()

    def power_on_pressed( self, event ):
        event.Skip()

    def power_off_pressed( self, event ):
        event.Skip()

    def set_freq_pressed( self, event ):
        event.Skip()

    def get_freq_pressed( self, event ):
        event.Skip()


