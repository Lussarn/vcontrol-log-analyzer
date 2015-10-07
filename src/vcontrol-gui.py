#!/usr/bin/python

import locale
import gettext

import wx
import datetime
import sys
import os

from MainWindow import MainWindow
import vc.globals
import vc.util

reqLang = None

# parse args (Only --lang at the moment)
sys.argv.pop(0)
if len(sys.argv) > 0:
	command = sys.argv.pop(0)
	if command == '--lang':
		if len(sys.argv) > 0:
			reqLang = sys.argv.pop(0)

# Setup gettext language
try: 
	if reqLang == None:
		systemLocale = locale.getdefaultlocale();
		reqLang = systemLocale[0].split('_')[0]
except:
	pass

lang = 'en'
if (reqLang in vc.globals.TRANSLATIONS):
	lang = reqLang
loc = gettext.translation('vbcfa', localedir=vc.util.resource_path('locale'), languages=[lang])
loc.install()

#locale.setlocale(locale.LC_ALL, "sve")
#print datetime.datetime.now().strftime('%x %X')

app = wx.App(False)
app.SetAppName("VBar control log analyzer")
app.SetMacHelpMenuTitleName("VControl")

frame = MainWindow()
app.MainLoop()
