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
## Class MyDialog1
###########################################################################

class MyDialog1 ( wx.Dialog ):

    def __init__( self, parent ):
        wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = wx.EmptyString, pos = wx.DefaultPosition, size = wx.DefaultSize, style = wx.DEFAULT_DIALOG_STYLE )

        self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )

        bSizer4 = wx.BoxSizer( wx.VERTICAL )

        self.m_textCtrl4 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer4.Add( self.m_textCtrl4, 0, wx.ALL, 5 )

        self.m_button7 = wx.Button( self, wx.ID_ANY, _(u"ok"), wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer4.Add( self.m_button7, 0, wx.ALL, 5 )

        self.m_button8 = wx.Button( self, wx.ID_ANY, _(u"cancel"), wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer4.Add( self.m_button8, 0, wx.ALL, 5 )


        self.SetSizer( bSizer4 )
        self.Layout()
        bSizer4.Fit( self )

        self.Centre( wx.BOTH )

        # Connect Events
        self.m_button7.Bind( wx.EVT_BUTTON, self.ok_pressed )
        self.m_button8.Bind( wx.EVT_BUTTON, self.cancel_pressed )

    def __del__( self ):
        pass


    # Virtual event handlers, override them in your derived class
    def ok_pressed( self, event ):
        event.Skip()

    def cancel_pressed( self, event ):
        event.Skip()


