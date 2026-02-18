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
## Class OrmViewerFrame
###########################################################################

class OrmViewerFrame ( wx.Frame ):

    def __init__( self, parent ):
        wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = wx.EmptyString, pos = wx.DefaultPosition, size = wx.Size( 500,521 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )

        self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )

        bSizer1 = wx.BoxSizer( wx.VERTICAL )

        m_listBox1Choices = []
        self.m_listBox1 = wx.ListBox( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, m_listBox1Choices, 0 )
        bSizer1.Add( self.m_listBox1, 1, wx.ALL|wx.EXPAND, 5 )

        m_listBox2Choices = []
        self.m_listBox2 = wx.ListBox( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, m_listBox2Choices, 0 )
        bSizer1.Add( self.m_listBox2, 1, wx.ALL|wx.EXPAND, 5 )

        self.m_textCtrl1 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer1.Add( self.m_textCtrl1, 0, wx.ALL, 5 )

        self.m_button1 = wx.Button( self, wx.ID_ANY, _(u"MyButton"), wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer1.Add( self.m_button1, 0, wx.ALL, 5 )

        m_listBox4Choices = []
        self.m_listBox4 = wx.ListBox( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, m_listBox4Choices, 0 )
        bSizer1.Add( self.m_listBox4, 1, wx.ALL|wx.EXPAND, 5 )


        self.SetSizer( bSizer1 )
        self.Layout()

        self.Centre( wx.BOTH )

        # Connect Events
        self.m_listBox1.Bind( wx.EVT_LISTBOX, self.table_selected )
        self.m_listBox2.Bind( wx.EVT_LISTBOX, self.column_selected )
        self.m_button1.Bind( wx.EVT_BUTTON, self.run_query )

    def __del__( self ):
        pass


    # Virtual event handlers, override them in your derived class
    def table_selected( self, event ):
        event.Skip()

    def column_selected( self, event ):
        event.Skip()

    def run_query( self, event ):
        event.Skip()