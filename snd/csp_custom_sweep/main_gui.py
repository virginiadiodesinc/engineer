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
## Class MyPanel2
###########################################################################

class MyPanel2 ( wx.Panel ):

    def __init__( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( 500,300 ), style = wx.TAB_TRAVERSAL, name = wx.EmptyString ):
        wx.Panel.__init__ ( self, parent, id = id, pos = pos, size = size, style = style, name = name )

        bSizer4 = wx.BoxSizer( wx.VERTICAL )

        self.m_button6 = wx.Button( self, wx.ID_ANY, _(u"select"), wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer4.Add( self.m_button6, 0, wx.ALL, 5 )

        self.m_button2 = wx.Button( self, wx.ID_ANY, _(u"connect"), wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer4.Add( self.m_button2, 0, wx.ALL, 5 )

        self.m_button3 = wx.Button( self, wx.ID_ANY, _(u"disconnect"), wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer4.Add( self.m_button3, 0, wx.ALL, 5 )


        self.SetSizer( bSizer4 )
        self.Layout()

        # Connect Events
        self.m_button6.Bind( wx.EVT_BUTTON, self.idk )
        self.m_button2.Bind( wx.EVT_BUTTON, self.idk2 )
        self.m_button3.Bind( wx.EVT_BUTTON, self.idk3 )

    def __del__( self ):
        pass


    # Virtual event handlers, override them in your derived class
    def idk( self, event ):
        event.Skip()

    def idk2( self, event ):
        event.Skip()

    def idk3( self, event ):
        event.Skip()