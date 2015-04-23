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

		wx.Frame.__init__(self, None, title='VBar control log analyzer', size=(1024,600))
		self.CreateStatusBar()

		# Toolbar
		toolbar = self.CreateToolBar(wx.TB_TEXT)
		toolbar.AddLabelTool(1, 'Import', wx.Bitmap('assets/img/import.png'))
#		toolbar.AddLabelTool(1, 'Publish', wx.Bitmap('assets/img/publish.png'))
#		toolbar.AddLabelTool(1, 'Settings', wx.Bitmap('assets/img/settings.png'))
		toolbar.Realize()


		# Creating the menubar.
		menuBar = wx.MenuBar()

		# Filemenu
		filemenu = wx.Menu()
		# wx.ID_ABOUT and wx.ID_EXIT are standard ids provided by wxWidgets.
		menuAbout = filemenu.Append(wx.ID_ABOUT, "&About"," Information about this program")
		menuExit = filemenu.Append(wx.ID_EXIT,"E&xit"," Terminate the program")
		menuImport = filemenu.Append(wx.NewId(),"&Import"," Import data from VControl")
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
		panelDate = wx.Panel(panelTop, -1, style=wx.BORDER_RAISED)
		sizerTopHoriz.Add(panelDate, 0, wx.ALL | wx.EXPAND, 5)
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
		sizerStatus.Add(wx.StaticText(panelStatus, label='Connection status'), 0, wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT | wx.TOP, 5)
		self.bitmap_connection_off = wx.Bitmap('assets/img/ball-red.png', wx.BITMAP_TYPE_ANY)
		self.bitmap_connection_on = wx.Bitmap('assets/img/ball-green.png', wx.BITMAP_TYPE_ANY)
		self.connection_img = wx.StaticBitmap(panelStatus, bitmap=self.bitmap_connection_off)
		sizerStatus.Add(self.connection_img, 1,  wx.CENTER | wx.TOP)

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

		sizerMainVert.Add(panelTop, 1, wx.EXPAND)
		sizerMainVert.Add(self.grid, 1, wx.EXPAND)


		self.SetSizer(sizerMainVert)
		sizerMainVert.Fit(self)
		self.SetSize(wx.Size(-1, 600))
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
		# Create a message dialog box
		dlg = wx.MessageDialog(self, "By Linus Larsson (linus.larsson@gmail.com)",  "       VBar control log analyzer", wx.OK)
		dlg.ShowModal() # Shows it
		dlg.Destroy() # finally destroy it when finished.

	def OnExit(self,e):
		self.Close(True)  # Close the frame.

	def OnImport(self, e):
		self.Close(True)  # Close the frame.

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
			if i % 2 == 1:
				attr.SetBackgroundColour(wx.Colour(255,255,255))
			else:
				attr.SetBackgroundColour(wx.Colour(220,220,220))

			self.grid.SetRowAttr(i, attr)
			i += 1

			if start == None:
				start = d['date']

		self.grid.AutoSizeColumns(100)
		for i in range(0, 10):
			w = self.grid.GetColSize(i)
			self.grid.SetColSize(i, w + 20)

		self.SetStatusText('Cycles: ' + str(data['totals']['cycles']) + '   Used capacity: ' + str(data['totals']['used']) + "Ah   Duration: " +str(data['totals']['duration']))

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


app = wx.App(False)
app.SetAppName("VBar control log analyzer")
app.SetMacHelpMenuTitleName("VControl")

frame = MainWindow()
frame.Show(True)
app.MainLoop()