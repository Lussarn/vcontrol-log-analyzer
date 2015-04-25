#!/usr/bin/python

import wx
import wx.grid
import os
import VBarLogAnalyzer
import datetime

class MainWindow(wx.Frame):
	def __init__(self):
		self.analyzer = VBarLogAnalyzer.Analyzer()
		self.batteries = []
		self.models = []
		self.batterySelected = None
		self.modelSelected = None

		interval = self.analyzer.get_date_interval()

		wx.Frame.__init__(self, None, title='VBar Control flight analyzer 2.0.3', size=(1024,600))
		self.CreateStatusBar()

		# Toolbar
#	toolbar = self.CreateToolBar(wx.TB_TEXT)
#	toolbar.AddLabelTool(1, 'Import', wx.Bitmap('assets/img/import.png'))
#		toolbar.AddLabelTool(1, 'Publish', wx.Bitmap('assets/img/publish.png'))
#		toolbar.AddLabelTool(1, 'Settings', wx.Bitmap('assets/img/settings.png'))
#	toolbar.Realize()


		# Creating the menubar.
		menuBar = wx.MenuBar()

		# Filemenu
		filemenu = wx.Menu()
		# wx.ID_ABOUT and wx.ID_EXIT are standard ids provided by wxWidgets.
		menuImport = filemenu.Append(wx.NewId(),"&Import from VBar Control"," Import data from VControl")
		menuAbout = filemenu.Append(wx.ID_ABOUT, "&About"," Information about this program")
		menuExit = filemenu.Append(wx.ID_EXIT,"E&xit"," Terminate the program")
 		menuBar.Append(filemenu, "&File") # Adding the "filemenu" to the MenuBar

		self.SetMenuBar(menuBar)  # Adding the MenuBar to the Frame content.

		# Events.
		self.Bind(wx.EVT_MENU, self.OnExit, menuExit)
		self.Bind(wx.EVT_MENU, self.OnAbout, menuAbout)
		self.Bind(wx.EVT_MENU, self.OnImport, menuImport)

		sizerMainVert = wx.BoxSizer(wx.VERTICAL)

		panelTop = wx.Panel(self)
		sizerTopHoriz = wx.BoxSizer(wx.HORIZONTAL)
		panelTop.SetSizer(sizerTopHoriz)

		# Date panel
		panelDate = wx.Panel(panelTop, -1)
		sizerTopHoriz.Add(panelDate, 0, wx.ALL, 5)
		sizerDate = wx.BoxSizer(wx.VERTICAL)
		panelDate.SetSizer(sizerDate)

		# Start date
		sizerDate.Add(wx.StaticText(panelDate, label='Start date'), 0, wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT | wx.TOP, 5)
		self.datePickerStart = wx.DatePickerCtrl(panelDate, dt=self._pydate2wxdate(interval['first']))
		sizerDate.Add(self.datePickerStart, 0, wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
		self.datePickerStart.Bind(wx.EVT_DATE_CHANGED, self.OnDateChanged)

		# End date
		sizerDate.Add(wx.StaticText(panelDate, label='End date'), 0, wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT | wx.TOP, 5)
		self.datePickerEnd = wx.DatePickerCtrl(panelDate, dt=self._pydate2wxdate(interval['last']))
		sizerDate.Add(self.datePickerEnd, 0, wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
		self.datePickerEnd.Bind(wx.EVT_DATE_CHANGED, self.OnDateChanged)

		# Battery
		panelBattery = wx.Panel(panelTop, -1, style=wx.BORDER_RAISED)
		sizerBattery = wx.BoxSizer(wx.VERTICAL)
		sizerBattery.Add(wx.StaticText(panelBattery, label='Battery'), 0, wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT | wx.TOP, 5)
		self.listBoxBattery = wx.ListBox(panelBattery, size=(200,100))
		sizerBattery.Add(self.listBoxBattery, 0, wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
		panelBattery.SetSizer(sizerBattery)
		sizerTopHoriz.Add(panelBattery, 0, wx.ALIGN_LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM, 5)
		self.listBoxBattery.Bind(wx.EVT_LISTBOX, self.OnSelectBattery)

		# Model
		panelModel = wx.Panel(panelTop, -1, style=wx.BORDER_RAISED)
		sizerModel = wx.BoxSizer(wx.VERTICAL)
		sizerModel.Add(wx.StaticText(panelModel, label='Model'), 0, wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT | wx.TOP, 5)
		self.listBoxModel = wx.ListBox(panelModel, size=(200,100))
		sizerModel.Add(self.listBoxModel, 0, wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
		panelModel.SetSizer(sizerModel)
		sizerTopHoriz.Add(panelModel, 0, wx.ALIGN_LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM, 5)
		self.listBoxModel.Bind(wx.EVT_LISTBOX, self.OnSelectModel)


		# Connection status
		panelStretch = wx.Panel(panelTop, -1) 
		sizerStretch = wx.BoxSizer(wx.VERTICAL)
		panelStretch.SetSizer(sizerStretch)
		sizerTopHoriz.Add(panelStretch, 1, wx.EXPAND)
		panelStatus = wx.Panel(panelStretch, -1)
		sizerStatus = wx.BoxSizer(wx.VERTICAL)
		panelStatus.SetSizer(sizerStatus)
		sizerStretch.Add(panelStatus, 1, wx.ALIGN_RIGHT | wx.LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM, 5)
		sizerStatus.Add(wx.StaticText(panelStatus, label='Connection status'), 0, wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM, 5)
		bitmap = wx.Bitmap(self.resource_path('assets/img/ball-red.png'), wx.BITMAP_TYPE_ANY)
		self.connection_img = wx.StaticBitmap(panelStatus, bitmap=bitmap)
		sizerStatus.Add(self.connection_img, 0, wx.CENTER)

		# Grid
		self.grid = wx.grid.Grid(self)
		self.grid.CreateGrid(10, 10)

		self.grid.ClipHorzGridLines(False)
		self.grid.ClipVertGridLines(False)
		self.grid.HideRowLabels()
		self.grid.EnableEditing(False)
		self.grid.SetDefaultCellOverflow(False)
		self.grid.SetUseNativeColLabels(True)
		self.grid.EnableGridLines(False)
		self.grid.SetSelectionMode(wx.grid.Grid.wxGridSelectRows)

		self.grid.SetColLabelAlignment(wx.ALIGN_LEFT, wx.ALIGN_CENTRE)
		self.grid.SetColLabelValue(0, 'Id')
		self.grid.SetColLabelValue(1, 'Date')
		self.grid.SetColLabelValue(2, 'Battery')
		self.grid.SetColLabelValue(3, 'Model')
		self.grid.SetColLabelValue(4, 'Duration')
		self.grid.SetColLabelValue(5, 'Capacity')
		self.grid.SetColLabelValue(6, 'Used')
		self.grid.SetColLabelValue(7, 'MinV')
		self.grid.SetColLabelValue(8, 'MaxA')
		self.grid.SetColLabelValue(9, 'IdleV')

		self.populate_gear()
		self.populate_grid()

		sizerMainVert.Add(panelTop, 0, wx.EXPAND)
		sizerMainVert.Add(self.grid, 1, wx.EXPAND)

		self.SetSizer(sizerMainVert)
		sizerMainVert.Fit(self)
		self.SetSize(wx.Size(-1, 600))

		TIMER_ID = 100  # pick a number
		self.timer = wx.Timer(self, TIMER_ID)  # message will be sent to the panel
		self.timer.Start(1000)  # x100 milliseconds
		wx.EVT_TIMER(self, TIMER_ID, self.on_timer)  # call the on_timer function

		self._vcontrol_connected = False
		self.Show()

	def OnDateChanged(self, event):
		self.populate_grid()		

	def OnSelectBattery(self, event):
		self.batterySelected = self.batteries[event.GetSelection()]
		self.populate_grid()

	def OnSelectModel(self, event):
		self.modelSelected = self.models[event.GetSelection()]
		self.populate_grid()

	def OnAbout(self,e):
		dlg = wx.MessageDialog(self, "By Linus Larsson (linus.larsson@gmail.com)",  "       VBar control log analyzer", wx.OK)
		dlg.ShowModal()
		dlg.Destroy()

	def OnExit(self,e):
		self.Close(True)  # Close the frame.

	def OnImport(self, e):
		if self.analyzer.vcontrol_is_connected() == False:
			dlg = wx.MessageDialog(self, "Unable to find VBar Control", "VBar Control message", wx.OK)
			dlg.ShowModal()
			dlg.Destroy()
			return
		self.SetStatusText('Importing from VBar Control, please wait...')
		self.analyzer.import_data()
		self.populate_gear()
		self.populate_grid()

	def populate_gear(self):
		self.batterySelected = None
		self.modelSelected = None
		self.listBoxBattery.Clear()
		gear = self.analyzer.list_gear()

		self.listBoxBattery.Clear()
		self.batteries = []
		self.listBoxBattery.Append('All batteries')
		self.batteries.append(None)
		for idbattery in gear['batteries']:
			self.listBoxBattery.Append(gear['batteries'][idbattery])
			self.batteries.append(idbattery)
		self.listBoxBattery.Select(0)
		self.listBoxBattery.EnsureVisible(0)

		self.models = []
		self.listBoxModel.Clear()
		self.listBoxModel.Append('All models')
		self.models.append(None)
		for idmodel in gear['models']:
			self.listBoxModel.Append(gear['models'][idmodel])
			self.models.append(idmodel)
		self.listBoxModel.Select(0)
		self.listBoxModel.EnsureVisible(0)



	def populate_grid(self):
		if self.grid.GetNumberRows() > 0:
			self.grid.DeleteRows(0, self.grid.GetNumberRows())

		start = self._wxdate2pydate(self.datePickerStart.GetValue())
		end = self._wxdate2pydate(self.datePickerEnd.GetValue())

		data = self.analyzer.extract(batteryid=self.batterySelected, modelid=self.modelSelected, start=start, end=end)

		i = 0
		start = None
		end = None
		session = 0
		for d in data['data']:
			self.grid.InsertRows(i, 1)
			self.grid.SetCellValue(i,0, str(d['id']))
			self.grid.SetCellValue(i,1, d['date'])
			self.grid.SetCellValue(i,2, d['battery'])
			self.grid.SetCellValue(i,3, d['model'])
			self.grid.SetCellValue(i,4, d['duration'])
			self.grid.SetCellValue(i,5, str(d['capacity']))
			self.grid.SetCellValue(i,6, d['used'])
			self.grid.SetCellValue(i,7, str(d['minv']))
			self.grid.SetCellValue(i,8, str(d['maxa']))
			self.grid.SetCellValue(i,9, str(d['idlev']))

			attr = wx.grid.GridCellAttr();
			if d['session'] % 2 == 1:
				if i % 2 == 1:
					attr.SetBackgroundColour(wx.Colour(200,255,200))
				else:
					attr.SetBackgroundColour(wx.Colour(140,200,140))
			else:
				if i % 2 == 1:
					attr.SetBackgroundColour(wx.Colour(200,200,255))
				else:
					attr.SetBackgroundColour(wx.Colour(140,140,200))

			self.grid.SetRowAttr(i, attr)
			i += 1

			if start == None:
				start = d['date']

		self.grid.AutoSizeColumns(100)
		for i in range(0, 10):
			w = self.grid.GetColSize(i)
			self.grid.SetColSize(i, w + 20)

		self.SetStatusText('Cycles: ' + str(data['totals']['cycles']) + '   Used capacity: ' + str(data['totals']['used']) + "Ah   Duration: " +str(data['totals']['duration']) + "   Sessions: " + str(data['totals']['sessions']))

	def on_timer(self, event):
		if self.analyzer.vcontrol_is_connected():
			if self._vcontrol_connected == True:
				return
			self._vcontrol_connected = True
			bitmap = wx.Bitmap(self.resource_path('assets/img/ball-green.png'), wx.BITMAP_TYPE_ANY)
			self.connection_img.SetBitmap(bitmap)
		else:
			if self._vcontrol_connected == False:
				return
			self._vcontrol_connected = False
			bitmap = wx.Bitmap(self.resource_path('assets/img/ball-red.png'), wx.BITMAP_TYPE_ANY)
			self.connection_img.SetBitmap(bitmap)

	def _pydate2wxdate(self, date):
		tt = date.timetuple()
		dmy = (tt[2], tt[1]-1, tt[0])
		return wx.DateTimeFromDMY(*dmy)
 
	def _wxdate2pydate(self, date):
		if date.IsValid():
			ymd = map(int, date.FormatISODate().split('-'))
			return datetime.date(*ymd)
		else:
			return None

	def resource_path(self, relative_path):
		try:
			# PyInstaller creates a temp folder and stores path in _MEIPASS
			base_path = sys._MEIPASS
		except Exception:
			base_path = os.path.abspath(".")

		return os.path.join(base_path, relative_path)

app = wx.App(False)
app.SetAppName("VBar control log analyzer")
app.SetMacHelpMenuTitleName("VControl")



frame = MainWindow()
frame.Show(True)
app.MainLoop()