#!/usr/bin/python

from numpy import arange, sin, pi, arange
import matplotlib
matplotlib.use('WXAgg')

import matplotlib.pyplot as plt

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wx import NavigationToolbar2Wx as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator
from matplotlib.ticker import FixedLocator
from matplotlib.ticker import MultipleLocator, AutoMinorLocator
from matplotlib.patches import Rectangle

import math
import wx
import wx.grid
import os
import VBarLogAnalyzer
import Variable
import datetime
from sets import Set

class MainWindow(wx.Frame):
	def __init__(self):
		self.analyzer = VBarLogAnalyzer.Analyzer()
		self.batteries = []
		self.models = []
		self.batterySelected = None
		self.modelSelected = None

		interval = self.analyzer.get_date_interval()
		seasons = self.analyzer.get_seasons()

		w = int(Variable.get('gui-window-width', '1024'))
		h = int(Variable.get('gui-window-height', '600'))

		wx.Frame.__init__(self, None, title='VBar Control flight analyzer v2.6.0', size=(w, h))
		self.CreateStatusBar()

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
		self.sizerTopHoriz = wx.BoxSizer(wx.HORIZONTAL)
		panelTop.SetSizer(self.sizerTopHoriz)

		# Date panel
		panelDate = wx.Panel(panelTop, -1)
		self.sizerTopHoriz.Add(panelDate, 0, wx.ALL, 5)
		sizerDate = wx.BoxSizer(wx.VERTICAL)
		panelDate.SetSizer(sizerDate)

		# Season
		sizerDate.Add(wx.StaticText(panelDate, label='Season'), 0, wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT | wx.TOP, 5)
		self.comboBoxSeason = wx.ComboBox(panelDate, choices=['All seasons'] + seasons)
		self.comboBoxSeason.SetEditable(False)
		self.comboBoxSeason.SetStringSelection(seasons[-1])
		sizerDate.Add(self.comboBoxSeason, 0, wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
		self.comboBoxSeason.Bind(wx.EVT_COMBOBOX, self.OnSeasonChanged)

		# Battery
		panelBattery = wx.Panel(panelTop, -1, style=wx.BORDER_RAISED)
		sizerBattery = wx.BoxSizer(wx.VERTICAL)
		sizerBattery.Add(wx.StaticText(panelBattery, label='Battery'), 0, wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT | wx.TOP, 5)
		self.listBoxBattery = wx.ListBox(panelBattery, size=(200,100))
		sizerBattery.Add(self.listBoxBattery, 0, wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
		panelBattery.SetSizer(sizerBattery)
		self.sizerTopHoriz.Add(panelBattery, 0, wx.ALIGN_LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM, 5)
		self.listBoxBattery.Bind(wx.EVT_LISTBOX, self.OnSelectBattery)

		# Model
		panelModel = wx.Panel(panelTop, -1, style=wx.BORDER_RAISED)
		sizerModel = wx.BoxSizer(wx.VERTICAL)
		sizerModel.Add(wx.StaticText(panelModel, label='Model'), 0, wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT | wx.TOP, 5)
		self.listBoxModel = wx.ListBox(panelModel, size=(200,100))
		sizerModel.Add(self.listBoxModel, 0, wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
		panelModel.SetSizer(sizerModel)
		self.sizerTopHoriz.Add(panelModel, 0, wx.ALIGN_LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM, 5)
		self.listBoxModel.Bind(wx.EVT_LISTBOX, self.OnSelectModel)

		# Extra GUI data
		self.panelExtra = wx.Panel(panelTop, -1)
		self.sizerExtra = wx.BoxSizer(wx.VERTICAL)
		self.panelExtra.SetSizer(self.sizerExtra)
		self.sizerTopHoriz.Add(self.panelExtra, 0, wx.ALL, 5)

		# Stack
		self.panelStack = wx.Panel(self.panelExtra, -1)
		sizerStack = wx.BoxSizer(wx.VERTICAL)
		self.panelStack.SetSizer(sizerStack)
		sizerStack.Add(wx.StaticText(self.panelStack, label='Stack graph as'), 0, wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT | wx.TOP, 5)
		self.radioModel = wx.RadioButton(self.panelStack, 0, "Model", style = wx.RB_GROUP)
		self.radioGraph = wx.RadioButton(self.panelStack, 0, "Battery")
		self.radioModel.SetValue(True)
		self.stackUse = 'model'
		sizerStack.Add(self.radioModel,  1, wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.TOP, 5)
		sizerStack.Add(self.radioGraph,  1, wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
		self.sizerExtra.Add(self.panelStack, 0, wx.ALL, 5)
		self.radioModel.Bind(wx.EVT_RADIOBUTTON, self.OnSelectStack)
		self.radioGraph.Bind(wx.EVT_RADIOBUTTON, self.OnSelectStack)

		# Short flights
		self.panelShort = wx.Panel(self.panelExtra, -1)
		sizerShort = wx.BoxSizer(wx.VERTICAL)
		self.panelShort.SetSizer(sizerShort)
		sizerShort.Add(wx.StaticText(self.panelShort, label='Show logs'), 0, wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT | wx.TOP, 5)
		self.radioShowFlights = wx.RadioButton(self.panelShort, 0, "Only more than 1/4 capacity used", style = wx.RB_GROUP)
		self.radioShowAll = wx.RadioButton(self.panelShort, 0, "All logs")
		self.radioShowFlights.SetValue(True)
		self.showAllFlights = 0
		sizerShort.Add(self.radioShowFlights,  1, wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.TOP, 5)
		sizerShort.Add(self.radioShowAll,  1, wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
		self.sizerExtra.Add(self.panelShort, 0, wx.ALL, 5)
		self.radioShowFlights.Bind(wx.EVT_RADIOBUTTON, self.OnSelectShort)
		self.radioShowAll.Bind(wx.EVT_RADIOBUTTON, self.OnSelectShort)

		self.panelStack.Hide()
		self.panelShort.Hide()
		self.sizerExtra.Layout()

		# Connection status
		panelStretch = wx.Panel(panelTop, -1)
		sizerStretch = wx.BoxSizer(wx.VERTICAL)
		panelStretch.SetSizer(sizerStretch)
		self.sizerTopHoriz.Add(panelStretch, 1, wx.EXPAND)
		panelStatus = wx.Panel(panelStretch, -1)
		sizerStatus = wx.BoxSizer(wx.VERTICAL)
		panelStatus.SetSizer(sizerStatus)
		sizerStretch.Add(panelStatus, 1, wx.ALIGN_RIGHT | wx.LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM, 5)
		sizerStatus.Add(wx.StaticText(panelStatus, label='Connection status'), 0, wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM, 5)
		bitmap = wx.Bitmap(self.resource_path('assets/img/ball-red.png'), wx.BITMAP_TYPE_ANY)
		self.connection_img = wx.StaticBitmap(panelStatus, bitmap=bitmap)
		sizerStatus.Add(self.connection_img, 0, wx.CENTER)

		# Add top panel to main vertical sizer
		sizerMainVert.Add(panelTop, 0, wx.EXPAND)

		# Notebook
		nb = wx.Notebook(self)

		# Grid
		pageGrid = wx.Panel(nb)
		sizerPagerGrid = wx.BoxSizer(wx.VERTICAL)
		pageGrid.SetSizer(sizerPagerGrid)
		nb.AddPage(pageGrid, "Data view")

		self.grid = wx.grid.Grid(pageGrid)
		self.grid.CreateGrid(10, 12)

		self.grid.ClipHorzGridLines(False)
		self.grid.ClipVertGridLines(False)
		self.grid.HideRowLabels()
		self.grid.EnableEditing(False)
		self.grid.SetDefaultCellOverflow(False)
		self.grid.SetUseNativeColLabels(True)
		self.grid.EnableGridLines(False)
		self.grid.SetCellHighlightPenWidth(0)
		self.grid.DisableDragRowSize()
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
		self.grid.SetColLabelValue(10, 'VBLog')
		self.grid.SetColLabelValue(11, 'UILog')

		sizerPagerGrid.Add(self.grid, 1, wx.EXPAND)

		self.grid.Bind(wx.grid.EVT_GRID_SELECT_CELL, self.OnGridSelect)
		self.grid.Bind(wx.grid.EVT_GRID_RANGE_SELECT, self.OnGridRangeSelect)

		# Graph
		pageGraph = wx.Panel(nb)
		sizerPagerGraph = wx.BoxSizer(wx.VERTICAL)
		pageGraph.SetSizer(sizerPagerGraph)
		nb.AddPage(pageGraph, "Graph view")

		self.figure = Figure()
		self.figure.suptitle('Cycles / week', fontsize=14, fontweight='bold')
		self.axes = self.figure.add_subplot(111)
		canvas = FigureCanvas(pageGraph, -1, self.figure)
		sizerPagerGraph.Add(canvas, 1, wx.EXPAND)
		self.figure.tight_layout(rect=[0,0.1,1,0.95])
		self.axes.xaxis.set_tick_params(width=0)
		self.axes.yaxis.grid(True)
		self.axes.yaxis.set_label_text('Cycles', fontsize=12, fontweight='bold')
		self.axes.xaxis.set_label_text('Week number', fontsize=12, fontweight='bold')

		self.figure.suptitle('Cycles / week', fontsize=14, fontweight='bold')
		self.figure.tight_layout(rect=[0.03,0.1,1,0.95])


		# Add notebook
		sizerMainVert.Add(nb, 1, wx.EXPAND)
		nb.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnNotebookChanged)

		self.SetSizer(sizerMainVert)
		sizerMainVert.Fit(self)
		self.SetSize(wx.Size(w, h))

		TIMER_ID = 100  # pick a number
		self.timer = wx.Timer(self, TIMER_ID)  # message will be sent to the panel
		self.timer.Start(1000)  # x100 milliseconds
		wx.EVT_TIMER(self, TIMER_ID, self.on_timer)  # call the on_timer function

		self._vcontrol_connected = False

		self.populate_grid()
		self.populate_gear()

		self.Show()
		self.panelShort.Show()
		self.panelStack.Hide()
		self.sizerExtra.Layout()
		self.sizerTopHoriz.Layout()
		self.Bind(wx.EVT_SIZE, self.OnSize)

	def OnSize(self,event):
		Variable.set('gui-window-width', str(event.GetSize()[0]))
		Variable.set('gui-window-height', str(event.GetSize()[1]))
		event.Skip()

	def OnNotebookChanged(self, event):
		if event.GetSelection() == 0:
			self.panelStack.Hide()
			self.panelShort.Show()
		elif event.GetSelection() == 1:
			self.panelShort.Hide()
			self.panelStack.Show()
		self.sizerExtra.Layout()
		event.Skip()

	def OnSelectStack(self, event):
		if event.GetEventObject() == self.radioModel:
			self.stackUse = 'model'
		else:
			self.stackUse = 'battery'
		self.populate_grid()		

	def OnSelectShort(self, event):
		if event.GetEventObject() == self.radioShowFlights:
			self.showAllFlights = 0
		else:
			self.showAllFlights = 1
		self.populate_grid()

	def OnSeasonChanged(self, event):
		self.populate_grid()		
		self.populate_gear()

	def OnSelectBattery(self, event):
		self.batterySelected = self.batteries[event.GetSelection()]
		self.populate_grid()

	def OnSelectModel(self, event):
		self.modelSelected = self.models[event.GetSelection()]
		self.populate_grid()

	def OnGridSelect(self, event):

		row = event.GetRow()
		sx,sy = self.grid.GetCellSize(row, 0) 
		if sy != 1:
			self.grid.ClearSelection()
			return

		col = event.GetCol()
		if col < 10:
			return
		if self.grid.GetCellValue(row, col) != 'Show':
			return
		logId = self.grid.GetCellValue(row, 0)
		if (col == 11):
			frame = UILogWindow(logId, self.analyzer)
		if (col == 10):
			frame = VBLogWindow(logId, self.analyzer)


	def OnGridRangeSelect(self, event):
		rows = self.grid.GetSelectedRows()
		if len(rows) > 1:
			self.grid.SelectRow(rows[1])
			return

	def OnAbout(self,e):
		dlg = wx.MessageDialog(self, "By Linus Larsson (linus.larsson@gmail.com)\n\nVBar log analyzer is in no way affiliated with Mikado\nor any of there products\n\nUse at your own risk",  "       VBar control log analyzer", wx.OK)
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

		seasons = self.analyzer.get_seasons()
		self.comboBoxSeason.Clear()
		self.comboBoxSeason.Append('All seasons')
		for s in seasons:
			self.comboBoxSeason.Append(s)
		self.comboBoxSeason.SetStringSelection(seasons[-1])

		self.populate_grid()
		self.populate_gear()

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
		# Grid
		if self.grid.GetNumberRows() > 0:
			self.grid.DeleteRows(0, self.grid.GetNumberRows())

		season = self.comboBoxSeason.GetStringSelection()
		if season == 'All seasons':
			start = datetime.datetime.strptime('1900', '%Y')
			end = datetime.datetime.strptime('3000', '%Y')
		else:
			start = datetime.datetime.strptime(season, '%Y')
			end = datetime.datetime.strptime(str(int(season) + 1), '%Y')

		data = self.analyzer.extract(batteryid=self.batterySelected, modelid=self.modelSelected, start=start, end=end, all=self.showAllFlights)

		i = 0
		start = None
		oldSession = 0
		c = 0
		for d in list(reversed(data['data'])):

			if d['session'] != oldSession:
				self.grid.InsertRows(i, 1)
				self.grid.SetCellValue(i, 0, str(d['date'][0:10]));
				self.grid.SetCellSize(i, 0, 1, 12);
				self.grid.SetCellAlignment(i, 0, wx.ALIGN_CENTRE, wx.ALIGN_CENTRE);
				self.grid.SetCellTextColour(i, 0, "#ffffff")
				attr = wx.grid.GridCellAttr();
				attr.SetBackgroundColour("#1F77B4")
				self.grid.SetRowAttr(i, attr)
				c = 0
				i += 1

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
			self.grid.SetCellValue(i,10, 'Show' if str(d['havevbarlog']) == '1' else '')
			self.grid.SetCellValue(i,11, 'Show' if str(d['haveuilog']) == '1' else '')

			attr = wx.grid.GridCellAttr();
			if c % 2 == 0:
				attr.SetBackgroundColour(wx.Colour(255,255,255))
			else:
				attr.SetBackgroundColour(wx.Colour(200,200,200))
			self.grid.SetRowAttr(i, attr)

			if d['havevbarlogproblem'] == 1:
				if c % 2 == 0:
					self.grid.SetCellBackgroundColour(i, 10, "#ffaaaa")
				else:
					self.grid.SetCellBackgroundColour(i, 10, "#c86666")

			self.grid.SetCellTextColour(i, 10, '#0000ff') 
			self.grid.SetCellTextColour(i, 11, '#0000ff') 
			c += 1
			i += 1

			start = d['date']
			oldSession = d['session']

		self.grid.AutoSizeColumns(100)
		for i in range(0, 12):
			w = self.grid.GetColSize(i)
			self.grid.SetColSize(i, w + 20)

		self.SetStatusText('Cycles: ' + str(data['totals']['cycles']) + '   Used capacity: ' + str(data['totals']['used']) + "Ah   Duration: " +str(data['totals']['duration']) + "   Sessions: " + str(data['totals']['sessions']))

		# Graph
		self.axes.clear()
		self.figure.suptitle('Cycles / week', fontsize=14, fontweight='bold')
		self.figure.set_facecolor('white')
		self.axes = self.figure.add_subplot(111)
		self.figure.tight_layout(rect=[0.03,0.1,0.85,0.95])
		self.axes.xaxis.set_tick_params(width=0)
		self.axes.yaxis.grid(True)
		self.axes.yaxis.set_label_text('Cycles', fontsize=12, fontweight='bold')
		self.axes.xaxis.set_label_text('Week number', fontsize=12, fontweight='bold')

		data = self.analyzer.extract_byweek(batteryid=self.batterySelected, modelid=self.modelSelected, start=start, end=end, group=self.stackUse)

		if len(data['data']) == 0:
			data['data'].append({'week': '00     ', 'group': {}})
		i = 0
		ticks = []

		allColors = list(reversed([
			(31, 119, 180),  (255, 127, 14), 
			(44, 160, 44), (214, 39, 40), 
			(148, 103, 189),  (140, 86, 75), 
			(227, 119, 194), (127, 127, 127), 
			(188, 189, 34), (23, 190, 207),
			(174, 199, 232),(255, 187, 120),
			(152, 223, 138), (255, 152, 150),
			(197, 176, 213), (196, 156, 148),
			(247, 182, 210), (199, 199, 199),
			(219, 219, 141),  (158, 218, 229)
			]))
		for ii in range(len(allColors)):
			rr, gg, bb = allColors[ii]
			allColors[ii] = (rr / 255., gg / 255., bb / 255.)

		colors = allColors
		modelColors = {}
		for week in data['data']:
			b = 0
			for model in week['group']:
				cycles = week['group'][model]
				if model in modelColors:
					color = modelColors[model]
					legend = None
				else:
					if len(colors) == 0:
						colors = allColors
					color = colors.pop()
					modelColors[model] = color
					legend = model	
				self.axes.bar(left=i-0.4, height=cycles, width=0.8, bottom=b, color=color, orientation="vertical",label=legend)
				b += cycles

			ticks.append(week['week'][2:])
			i += 1

		handles, labels = self.axes.get_legend_handles_labels()
		self.axes.legend(handles, labels, bbox_to_anchor=(1.2, 1.01), prop={'size': 10})

		keep = []
		for k in arange(0, len(ticks), float(len(ticks)) / 53):
			keep.append(int(round(k)))

		keep = Set(keep)

		for i in xrange(len(ticks)):
			if not i in keep:
				ticks[i] = ''

		self.axes.xaxis.set_major_locator(FixedLocator(arange(0,len(ticks))))
		self.axes.set_xticklabels(ticks, horizontalalignment='center', rotation=90, fontsize=8)
		self.figure.canvas.draw()

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

class VBLogWindow(wx.Frame):
	def __init__(self, logId, analyzer):
		data = analyzer.extract_log(logId)
		wx.Frame.__init__(self, None, title='VBar Control flight analyzer v2.6.0 - Log Id ' + logId, size=(1200, 700))

		textarea = wx.TextCtrl(self, -1,
                                style=wx.TE_MULTILINE|wx.BORDER_SUNKEN|wx.TE_READONLY|
                                wx.TE_RICH2)

		for row in data:
			line = row['date'] + ' (' + str(row['severity']) + ') ' + row['message'] + "\n"

			if row['severity'] == 4:
				textarea.SetDefaultStyle(wx.TextAttr(wx.RED))
			else:
				textarea.SetDefaultStyle(wx.TextAttr(wx.BLACK))
			textarea.WriteText(line)
		textarea.SetInsertionPoint(0)

		self.Show()


class UILogWindow(wx.Frame):
	def __init__(self, logId, analyzer):
		self.background = None
		self.selectStart = None
		data = analyzer.extract_ui(logId)

		labels = ['Voltage', 'Current', 'Power', 'Headspeed', 'PWM', 'Capacity']
		colors = ["#1F77B4", "#2CA02C", "#8C564B", "#FF7F0E", "#D62728", "#9467BD"]

		wx.Frame.__init__(self, None, title='VBar Control flight analyzer v2.6.0 - Log Id ' + logId, size=(1200, 700))
		self.figure = Figure()
		self.axes = self.figure.add_subplot(111)
		self.canvas = FigureCanvas(self, -1, self.figure)

		sizerMainVert = wx.BoxSizer(wx.VERTICAL)
		self.figure.set_facecolor('white')
		sizerMainVert.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.GROW)
		self.SetSizer(sizerMainVert)

		# Grid lines
		self.axes.xaxis.grid(True)
		self.axes.xaxis.grid(b=True, which='major', color='0.65',linestyle='-')

		# Graph size
		self.figure.subplots_adjust(left=0.19, right=0.81)

		self.graphs = {}
		# Subgraphs
		self.graphs[-1] = self.axes
		self.graphs[0] = self.graphs[-1].twinx()
		self.graphs[1] = self.graphs[-1].twinx()
		self.graphs[2] = self.graphs[-1].twinx()
		self.graphs[3] = self.graphs[-1].twinx()
		self.graphs[4] = self.graphs[-1].twinx()
		self.graphs[5] = self.graphs[-1].twinx()

		# spines
		self.graphs[0].spines["left"].set_position(("axes", -0.0))
		self.graphs[0].yaxis.tick_left()
		self.make_patch_spines_invisible(self.graphs[0])
		self.graphs[0].yaxis.set_label_position('left');
		self.graphs[0].spines["left"].set_visible(True)
		self.graphs[0].spines["left"].set_color(colors[0])

		self.graphs[1].spines["left"].set_position(("axes", -0.08))
		self.graphs[1].yaxis.tick_left()
		self.make_patch_spines_invisible(self.graphs[1])
		self.graphs[1].yaxis.set_label_position('left');
		self.graphs[1].spines["left"].set_visible(True)
		self.graphs[1].spines["left"].set_color(colors[1])

		self.graphs[2].spines["left"].set_position(("axes", -0.16))
		self.graphs[2].yaxis.tick_left()
		self.make_patch_spines_invisible(self.graphs[2])
		self.graphs[2].yaxis.set_label_position('left');
		self.graphs[2].spines["left"].set_visible(True)
		self.graphs[2].spines["left"].set_color(colors[2])

		self.make_patch_spines_invisible(self.graphs[3])
		self.graphs[3].spines["right"].set_visible(True)
		self.graphs[3].spines["right"].set_color(colors[3])

		self.graphs[4].spines["right"].set_position(("axes", 1.08))
		self.make_patch_spines_invisible(self.graphs[4])
		self.graphs[4].spines["right"].set_visible(True)
		self.graphs[4].spines["right"].set_color(colors[4])

		self.graphs[5].spines["right"].set_position(("axes", 1.16))
		self.make_patch_spines_invisible(self.graphs[5])
		self.graphs[5].spines["right"].set_visible(True)
		self.graphs[5].spines["right"].set_color(colors[5])

		self.graphs[-1].spines['right'].set_color("#777777")
		self.graphs[-1].spines['left'].set_color("#777777")
		self.graphs[-1].spines['top'].set_color("#777777")
		self.graphs[-1].spines['bottom'].set_color("#777777")
		self.graphs[-1].get_yaxis().set_ticks([])

		# data
		self.data = {} 
		self.data[-1] = []  # sec
		self.data[3] = []   # rpm
		self.data[1] = []   # current
		self.data[0] = []   # voltage
		self.data[4] = []   # PWM
		self.data[5] = []   # capacity
		self.data[2] = []   # power
		self.duration = 0
		for row in data:
			self.duration = row['sec']
			self.data[-1].append(row['sec'])
			self.data[0].append(row['voltage'])
			self.data[1].append(row['current'])
			self.data[2].append(row['voltage'] * row['current'])
			self.data[3].append(row['headspeed'])
			self.data[4].append(row['pwm'])
			self.data[5].append(row['usedcapacity'])

		# plots
		self.plots = {}
		for i in xrange(0, 6):
			self.plots[i], = self.graphs[i].plot(self.data[-1], self.data[i], colors[i], linewidth=0.5)

		# scale graphs
		self.graphs[0].set_ylim(0, max(self.data[0]) * 1.7)
		self.graphs[1].set_ylim(0, max(self.data[1]) * 2)
		self.graphs[2].set_ylim(0, max(self.data[2]) * 1.5)
		self.graphs[3].set_ylim(0, max( { max(self.data[3]), 100 } ) * 1.5)
		self.graphs[5].set_ylim(0)

		# labels
		self.graphs[-1].set_xlabel("Duration (sec)", fontsize='x-small')
		self.graphs[0].set_ylabel("Voltage(I)", fontsize='x-small')
		self.graphs[1].set_ylabel("Current(A)", fontsize='x-small')
		self.graphs[2].set_ylabel("Power (W)", fontsize='x-small')
		self.graphs[3].set_ylabel("Headspeed (RPM)", fontsize='x-small')
		self.graphs[4].set_ylabel("PWM", fontsize='x-small')
		self.graphs[5].set_ylabel("Used capacity (mAh)", fontsize='x-small')

		# colors and locators
		self.graphs[-1].xaxis.set_minor_locator(AutoMinorLocator())
		self.graphs[0].xaxis.label.set_color('#555555')
		for i in xrange(0, 6):
			self.graphs[i].yaxis.label.set_color(self.plots[i].get_color())
			self.graphs[i].yaxis.set_minor_locator(AutoMinorLocator())

		# ticks
		for i in xrange(0, 6):
			self.graphs[i].tick_params(axis='y', colors=self.plots[i].get_color(), which='major', direction='out', labelsize='x-small', size=4, width=1)
			self.graphs[i].tick_params(axis='y', colors=self.plots[i].get_color(), which='minor', direction='out', labelsize='x-small', size=2, width=1)

		# Bottom panel
		panelBottom = wx.Panel(self)
		gs = wx.GridSizer(5, 7, 5, 20)
		panelBottom.SetSizer(gs)

		gs.Add(wx.StaticText(panelBottom), wx.EXPAND)

		self.valueOnCheck = {}
		for i in xrange(0,6):
			p1 = wx.Panel(panelBottom, style=wx.ALIGN_CENTER);
			s1 = wx.BoxSizer(wx.HORIZONTAL)
			p1.SetSizer(s1)
			self.valueOnCheck[i] = wx.CheckBox(p1)
			s1.AddStretchSpacer(1)
			s1.Add(self.valueOnCheck[i], 0)
			t1 = wx.StaticText(p1, label=labels[i])
			t1.SetForegroundColour(colors[i])
			s1.Add(t1, 0)
			s1.AddStretchSpacer(1)
			gs.Add(p1, 1, wx.EXPAND)
			if Variable.get('ui-show-value-' + str(i), '1') == '1':
				self.valueOnCheck[i].SetValue(True)
			self.Bind(wx.EVT_CHECKBOX, self.onCheckbox, self.valueOnCheck[i])

		# Mouse text
		gs.Add(wx.StaticText(panelBottom, label='Mouse', style=wx.ALIGN_RIGHT), 1, wx.EXPAND)
		self.mouseText = {}
		for i in xrange(0, 6):
			self.mouseText[i] = wx.StaticText(panelBottom, label="0", style=wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE)
			gs.Add(self.mouseText[i], 1, wx.EXPAND)

		# Min values		
		gs.Add(wx.StaticText(panelBottom, label='Min', style=wx.ALIGN_RIGHT), 1, wx.EXPAND)
		self.minText = {}
		for i in xrange(0, 6):
			m = min(self.data[i])
			if (i < 2):
				m =  "{0:.1f}".format(round(m,1))
			else:
				m = int(m)
			self.minText[i] = wx.StaticText(panelBottom, label=str(m), style=wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE)	
			gs.Add(self.minText[i], 1, wx.EXPAND)

		# Max values		
		gs.Add(wx.StaticText(panelBottom, label='Max', style=wx.ALIGN_RIGHT), 1, wx.EXPAND)
		self.maxText = {}
		for i in xrange(0, 6):
			m = max(self.data[i])
			if (i < 2):
				m =  "{0:.1f}".format(round(m,1))
			else:
				m = int(m)
			self.maxText[i] = wx.StaticText(panelBottom, label=str(m), style=wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE)	
			gs.Add(self.maxText[i], 1, wx.EXPAND)

		# Average values
		gs.Add(wx.StaticText(panelBottom, label='Average', style=wx.ALIGN_RIGHT), 1, wx.EXPAND)
		self.avgText = {}
		for i in xrange(0, 5):
			m = reduce(lambda x, y: x + y, self.data[i]) / len(self.data[i])
			if (i < 2):
				m =  "{0:.1f}".format(round(m,1))
			else:
				m = int(m)
			self.avgText[i] = wx.StaticText(panelBottom, label=str(m), style=wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE)	
			gs.Add(self.avgText[i], 1, wx.EXPAND)

		# capacity / min
		m = int((max(self.data[5]) - min(self.data[5])) / max(self.data[-1]) * 60)
		self.avgText[5] = wx.StaticText(panelBottom, label=str(m), style=wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE)	
		gs.Add(self.avgText[5], 1, wx.EXPAND)

		self.updateMinMax(0, self.duration)

		sizerMainVert.Add(panelBottom, 0, wx.LEFT | wx.TOP | wx.ALIGN_CENTER )
		sizerMainVert.Add((0,10))
		self.SetBackgroundColour('white')


		self.graphs[0].set_xlim(0, self.duration)

		# matplot events
		self.figure.canvas.mpl_connect('motion_notify_event', self.OnMotion)
		self.figure.canvas.mpl_connect('button_press_event', self.OnPress)
		self.figure.canvas.mpl_connect('button_release_event', self.OnRelease)
		self.figure.canvas.mpl_connect('resize_event', self.OnResize)

		self.Show()
		self.canvas.draw()
		self.canvas.Refresh()
		for i in xrange(0,6):
			self.graphs[i].set_visible(self.valueOnCheck[i].IsChecked());
		self.canvas.draw()
		self.canvas.Refresh()


	def make_patch_spines_invisible(self, ax):
		ax.set_frame_on(True)
		ax.patch.set_visible(False)
		ax.spines['left'].set_visible(False)
		for sp in ax.spines.itervalues():
			sp.set_visible(False)

	def onCheckbox(self, event):
		for i in xrange(0,6):
			self.graphs[i].set_visible(self.valueOnCheck[i].IsChecked());
			if self.valueOnCheck[i].IsChecked():
				Variable.set('ui-show-value-' + str(i), '1');
			else:
				Variable.set('ui-show-value-' + str(i), '0');

		self.canvas.draw()
		self.canvas.Refresh()
		self.background = None

	def OnMotion(self, event):
		if event.inaxes == None:
			return

		x0, y0, x1, y1 = event.inaxes.dataLim.bounds

		npts = len(event.inaxes.lines[0].get_ydata())
		idx = int(round((npts-1) * (event.xdata-x0)/x1))

		if len(self.data[0]) < idx + 1:
			return

		if self.background is None:
			self.background = self.figure.canvas.copy_from_bbox(self.graphs[0].bbox)

		# restore the clean slate background
		self.figure.canvas.restore_region(self.background)

		polygon = None
		if self.selectStart == None:
			linev = self.graphs[0].axvline(x=event.xdata, linewidth=1, color='#000000', alpha=0.5)
			lineh = self.graphs[5].axhline(y=event.ydata, linewidth=1, color='#000000', alpha=0.5)
			self.graphs[0].draw_artist(linev)
			self.graphs[0].draw_artist(lineh)
		else:
			width = abs(event.xdata - self.selectStart)
			start = self.selectStart
			if (event.xdata < start):
				start = event.xdata
			if width < 20:
				col = '#aa4444'
			else:
				col = '#888888'
			polygon = Rectangle((start, 0), width, y1, facecolor=col, alpha=0.5)
			self.graphs[0].add_patch(polygon)
			self.graphs[0].draw_artist(polygon)

		self.figure.canvas.blit(self.graphs[0].bbox)
		if self.selectStart == None:
			linev.remove()
			lineh.remove()
		if polygon != None:
			polygon.remove()

		for i in xrange(0, 6):
			if (i < 2):
				val = str(self.data[i][idx])
			else:
				val = str(int(self.data[i][idx]))					
			self.mouseText[i].SetLabel(val)

	def OnPress(self, event):
		if event.button == 3:
			self.updateMinMax(0, self.duration)
			self.background =  None
		 	self.graphs[0].set_xlim(0, self.duration)
			self.canvas.draw()
			self.canvas.Refresh()

		else:
			self.selectStart = event.xdata


	def OnRelease(self, event):
		if event.button != 1:
			return

		if  self.selectStart == None:
			return

		start = self.selectStart
		end = event.xdata

		if end == None:
			self.selectStart = None
			return

		if (end < start):
			temp = start
			start = end
			end = temp

		width = abs(end - start)
		if width >= 20:
		 	self.graphs[0].set_xlim(start, end)
			self.updateMinMax(start, start + width)

		self.canvas.draw()
		self.canvas.Refresh()
		self.selectStart = None
		self.background = None

	def OnResize(self, event):
		self.background = None

	# Param start, end are seconds
	def updateMinMax(self, start, end):
		npts = len(self.plots[0].get_ydata());
		idx1 = int(npts * start / self.duration);
		idx2 = int(npts * end / self.duration);

		if idx2 >= len(self.data[0]):
			idx2 = len(self.data[0]) - 1

		for i in xrange(0, 6):
			m = max(self.data[i][idx1:idx2])
			if (i < 2):
				m =  "{0:.1f}".format(round(m,1))
			else:
				m = int(m)
			self.maxText[i].SetLabel(str(m))

			m = min(self.data[i][idx1:idx2])
			if (i < 2):
				m =  "{0:.1f}".format(round(m,1))
			else:
				m = int(m)
			self.minText[i].SetLabel(str(m))

		for i in xrange(0, 5):
			m = reduce(lambda x, y: x + y, self.data[i][idx1:idx2]) / len(self.data[i][idx1:idx2])
			if (i < 2):
				m =  "{0:.1f}".format(round(m,1))
			else:
				m = int(m)
			self.avgText[i].SetLabel(str(m))

		m = int((max(self.data[5][idx1:idx2]) - min(self.data[5][idx1:idx2])) / (self.data[-1][idx2] - self.data[-1][idx1]) * 60)
		self.avgText[5].SetLabel(str(m) + '/min')

app = wx.App(False)
app.SetAppName("VBar control log analyzer")
app.SetMacHelpMenuTitleName("VControl")

frame = MainWindow()
app.MainLoop()
