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
## Class SmarterSynthGUI
###########################################################################

class SmarterSynthGUI ( wx.Frame ):

    def __init__( self, parent ):
        wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = wx.EmptyString, pos = wx.DefaultPosition, size = wx.Size( 500,300 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )

        self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )

        bSizer15 = wx.BoxSizer( wx.HORIZONTAL )

        m_listBox1Choices = []
        self.m_listBox1 = wx.ListBox( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, m_listBox1Choices, 0 )
        bSizer15.Add( self.m_listBox1, 1, wx.ALL|wx.EXPAND, 5 )

        bSizer3 = wx.BoxSizer( wx.VERTICAL )


        bSizer3.Add( ( 0, 0), 1, wx.EXPAND, 5 )

        self.m_button3 = wx.Button( self, wx.ID_ANY, _(u"---->"), wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer3.Add( self.m_button3, 0, wx.ALL, 5 )


        bSizer3.Add( ( 0, 0), 1, wx.EXPAND, 5 )

        self.m_button4 = wx.Button( self, wx.ID_ANY, _(u"---->"), wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer3.Add( self.m_button4, 0, wx.ALL, 5 )


        bSizer3.Add( ( 0, 0), 1, wx.EXPAND, 5 )

        self.m_button5 = wx.Button( self, wx.ID_ANY, _(u"---->"), wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer3.Add( self.m_button5, 0, wx.ALL, 5 )


        bSizer3.Add( ( 0, 0), 1, wx.EXPAND, 5 )


        bSizer3.Add( ( 0, 0), 1, wx.EXPAND, 5 )


        bSizer3.Add( ( 0, 0), 1, wx.EXPAND, 5 )


        bSizer3.Add( ( 0, 0), 1, wx.EXPAND, 5 )


        bSizer15.Add( bSizer3, 0, wx.EXPAND, 5 )

        self.m_panel10 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer16 = wx.BoxSizer( wx.VERTICAL )

        self.m_staticText47 = wx.StaticText( self.m_panel10, wx.ID_ANY, _(u"Synth"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText47.Wrap( -1 )

        bSizer16.Add( self.m_staticText47, 0, wx.ALL, 5 )

        self.m_textCtrl31 = wx.TextCtrl( self.m_panel10, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer16.Add( self.m_textCtrl31, 0, wx.ALL, 5 )

        self.m_staticline1 = wx.StaticLine( self.m_panel10, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
        bSizer16.Add( self.m_staticline1, 0, wx.EXPAND |wx.ALL, 5 )

        self.m_staticText48 = wx.StaticText( self.m_panel10, wx.ID_ANY, _(u"Frequency Counter"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText48.Wrap( -1 )

        bSizer16.Add( self.m_staticText48, 0, wx.ALL, 5 )

        self.m_textCtrl32 = wx.TextCtrl( self.m_panel10, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer16.Add( self.m_textCtrl32, 0, wx.ALL, 5 )

        self.m_staticline2 = wx.StaticLine( self.m_panel10, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
        bSizer16.Add( self.m_staticline2, 0, wx.EXPAND |wx.ALL, 5 )

        self.m_staticText49 = wx.StaticText( self.m_panel10, wx.ID_ANY, _(u"VDAQ SN"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText49.Wrap( -1 )

        bSizer16.Add( self.m_staticText49, 0, wx.ALL, 5 )

        self.m_textCtrl33 = wx.TextCtrl( self.m_panel10, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer16.Add( self.m_textCtrl33, 0, wx.ALL, 5 )

        m_radioBox1Choices = [ _(u"0"), _(u"1") ]
        self.m_radioBox1 = wx.RadioBox( self.m_panel10, wx.ID_ANY, _(u"VDAQ Channel"), wx.DefaultPosition, wx.DefaultSize, m_radioBox1Choices, 2, wx.RA_SPECIFY_COLS )
        self.m_radioBox1.SetSelection( 0 )
        bSizer16.Add( self.m_radioBox1, 0, wx.ALL, 5 )

        self.m_staticline3 = wx.StaticLine( self.m_panel10, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
        bSizer16.Add( self.m_staticline3, 0, wx.EXPAND |wx.ALL, 5 )

        self.m_button11 = wx.Button( self.m_panel10, wx.ID_ANY, _(u"OK"), wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer16.Add( self.m_button11, 0, wx.ALL, 5 )

        self.m_button12 = wx.Button( self.m_panel10, wx.ID_ANY, _(u"Cancel"), wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer16.Add( self.m_button12, 0, wx.ALL, 5 )


        self.m_panel10.SetSizer( bSizer16 )
        self.m_panel10.Layout()
        bSizer16.Fit( self.m_panel10 )
        bSizer15.Add( self.m_panel10, 1, wx.EXPAND |wx.ALL, 5 )


        self.SetSizer( bSizer15 )
        self.Layout()

        self.Centre( wx.BOTH )

        # Connect Events
        self.m_button3.Bind( wx.EVT_BUTTON, self.synth_selected )
        self.m_button4.Bind( wx.EVT_BUTTON, self.fc_selected )
        self.m_button5.Bind( wx.EVT_BUTTON, self.vdaq_selected )
        self.m_button11.Bind( wx.EVT_BUTTON, self.ok_pressed )
        self.m_button12.Bind( wx.EVT_BUTTON, self.cancel_pressed )

    def __del__( self ):
        pass


    # Virtual event handlers, override them in your derived class
    def synth_selected( self, event ):
        event.Skip()

    def fc_selected( self, event ):
        event.Skip()

    def vdaq_selected( self, event ):
        event.Skip()

    def ok_pressed( self, event ):
        event.Skip()

    def cancel_pressed( self, event ):
        event.Skip()


