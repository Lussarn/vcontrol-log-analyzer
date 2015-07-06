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

		w = int(Variable.get('gui-window-width', '1024'))
		h = int(Variable.get('gui-window-height', '600'))

		wx.Frame.__init__(self, None, title='VBar Control flight analyzer v2.4.0', size=(w, h))
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

		# Stack
		self.panelStack = wx.Panel(panelTop, -1)
		sizerStack = wx.BoxSizer(wx.VERTICAL)
		self.panelStack.SetSizer(sizerStack)
		sizerStack.Add(wx.StaticText(self.panelStack, label='Stack graph as'), 0, wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT | wx.TOP, 5)
		self.radioModel = wx.RadioButton(self.panelStack, 0, "Model", style = wx.RB_GROUP)
		self.radioGraph = wx.RadioButton(self.panelStack, 0, "Battery")
		self.radioModel.SetValue(True)
		self.stackUse = 'model'
		sizerStack.Add(self.radioModel,  1, wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.TOP, 5)
		sizerStack.Add(self.radioGraph,  1, wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
		sizerTopHoriz.Add(self.panelStack, 0, wx.ALL, 5)
		self.radioModel.Bind(wx.EVT_RADIOBUTTON, self.OnSelectStack)
		self.radioGraph.Bind(wx.EVT_RADIOBUTTON, self.OnSelectStack)


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

		self.grid.Bind(wx.grid.EVT_GRID_CELL_LEFT_DCLICK, self.OnGridDClick)
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

		self.populate_gear()
		self.populate_grid()

		self.Show()
		self.panelStack.Hide()
		self.Bind(wx.EVT_SIZE, self.OnSize)

	def OnSize(self,event):
		Variable.set('gui-window-width', str(event.GetSize()[0]))
		Variable.set('gui-window-height', str(event.GetSize()[1]))
		event.Skip()

	def OnNotebookChanged(self, event):
		if event.GetSelection() == 0:
			self.panelStack.Hide()
		elif event.GetSelection() == 1:
			self.panelStack.Show()
		event.Skip()

	def OnSelectStack(self, event):
		if event.GetEventObject() == self.radioModel:
			self.stackUse = 'model'
		else:
			self.stackUse = 'battery'
		self.populate_grid()		

	def OnDateChanged(self, event):
		self.populate_grid()		

	def OnSelectBattery(self, event):
		self.batterySelected = self.batteries[event.GetSelection()]
		self.populate_grid()

	def OnSelectModel(self, event):
		self.modelSelected = self.models[event.GetSelection()]
		self.populate_grid()

	def OnGridDClick(self, event):
		# Col 10 is VBarLog
		col = event.GetCol()
		row = event.GetRow()
		if col < 10:
			return
		if self.grid.GetCellValue(row, col) != 'Yes':
			return
		logId = self.grid.GetCellValue(row, 0)
		if (col == 11):
			frame = UILogWindow(logId, self.analyzer)
		if (col == 10):
			frame = VBLogWindow(logId, self.analyzer)

	def OnGridSelect(self, event):

		row = event.GetRow()
		sx,sy = self.grid.GetCellSize(row, 0) 
		if sy != 1:
			self.grid.ClearSelection()
			return

	def OnGridRangeSelect(self, event):
		rows = self.grid.GetSelectedRows()
		print rows
		if len(rows) > 1:
			self.grid.SelectRow(rows[1])
			return
		print len(rows)

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

		interval = self.analyzer.get_date_interval()
		self.datePickerStart.SetValue(dt=self._pydate2wxdate(interval['first']))
		self.datePickerEnd.SetValue(dt=self._pydate2wxdate(interval['last']))

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
		# Grid
		if self.grid.GetNumberRows() > 0:
			self.grid.DeleteRows(0, self.grid.GetNumberRows())

		start = self._wxdate2pydate(self.datePickerStart.GetValue())
		end = self._wxdate2pydate(self.datePickerEnd.GetValue())

		data = self.analyzer.extract(batteryid=self.batterySelected, modelid=self.modelSelected, start=start, end=end)

		i = 0
		start = None
		end = None
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
			self.grid.SetCellValue(i,10, 'Yes' if str(d['havevbarlog']) == '1' else '')
			self.grid.SetCellValue(i,11, 'Yes' if str(d['haveuilog']) == '1' else '')

			attr = wx.grid.GridCellAttr();
			if c % 2 == 0:
				attr.SetBackgroundColour(wx.Colour(255,255,255))
			else:
					attr.SetBackgroundColour(wx.Colour(200,200,200))
			self.grid.SetRowAttr(i, attr)
			c += 1

			i += 1

#			if start == None:
			start = d['date']
			oldSession = d['session']

		self.grid.AutoSizeColumns(100)
		for i in range(0, 10):
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

class LineBuilder:
	def __init__(self, line):
		self.line = line
		self.xs = list(line.get_xdata())
		self.ys = list(line.get_ydata())
		self.cid = line.figure.canvas.mpl_connect('button_press_event', self)

	def __call__(self, event):
		print 'click', event
		if event.inaxes!=self.line.axes: return
		self.xs.append(event.xdata)
		self.ys.append(event.ydata)
		self.line.set_data(self.xs, self.ys)
		self.line.figure.canvas.draw()

class VBLogWindow(wx.Frame):
	def __init__(self, logId, analyzer):
		data = analyzer.extract_log(logId)
		wx.Frame.__init__(self, None, title='VBar Control flight analyzer v2.4.0 - Log Id ' + logId, size=(1200, 700))

		textarea = wx.TextCtrl(self, -1,
                                style=wx.TE_MULTILINE|wx.BORDER_SUNKEN|wx.TE_READONLY|
                                wx.TE_RICH2)

		for row in data:
			line = row['date'] + ' (' + str(row['severity']) + ') ' + row['message'] + "\n"
			textarea.AppendText(line)

		self.Show()


class UILogWindow(wx.Frame):
	def __init__(self, logId, analyzer):
		self.background = None
		self.selectStart = None
		data = analyzer.extract_ui(logId)

		wx.Frame.__init__(self, None, title='VBar Control flight analyzer v2.4.0 - Log Id ' + logId, size=(1200, 700))
		self.figure = Figure()
		self.axes = self.figure.add_subplot(111)
		self.canvas = FigureCanvas(self, -1, self.figure)

		sizerMainVert = wx.BoxSizer(wx.VERTICAL)

		self.figure.set_facecolor('white')

#		sizerMainVert.Add((0,10))
#		sizerMainVert.Add(wx.StaticText(self, label='Goblin 700 - 12S 5000mAh #1 - 2013-10-06 13:23', size=15, style=wx.ALIGN_CENTER), 0, wx.EXPAND)
		sizerMainVert.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.GROW)
		self.SetSizer(sizerMainVert)


		# Grid lines
		self.axes.xaxis.grid(True)
		self.axes.xaxis.grid(b=True, which='major', color='0.65',linestyle='-')

		# Graph size
		self.figure.subplots_adjust(left=0.19, right=0.81)

		# Subgraphs
		self.host = self.axes
		par1 = self.host.twinx()
		par2 = self.host.twinx()
		par3 = self.host.twinx()
		par4 = self.host.twinx()
		self.par5 = self.host.twinx()

		par2.spines["left"].set_position(("axes", -0.08))
		par2.yaxis.tick_left()
		self.make_patch_spines_invisible(par2)
		par2.yaxis.set_label_position('left');
		par2.spines["left"].set_visible(True)
		par2.spines["left"].set_color("#2CA02C")

		par3.spines["right"].set_position(("axes", 1.08))
		self.make_patch_spines_invisible(par3)
		par3.spines["right"].set_visible(True)
		par3.spines["right"].set_color("#D62728")

		par4.spines["right"].set_position(("axes", 1.16))
		self.make_patch_spines_invisible(par4)
		par4.spines["right"].set_visible(True)
		par4.spines["right"].set_color("#9467BD")

		self.par5.spines["left"].set_position(("axes", -0.16))
		self.par5.yaxis.tick_left()
		self.make_patch_spines_invisible(self.par5)
		self.par5.yaxis.set_label_position('left');
		self.par5.spines["left"].set_visible(True)
		self.par5.spines["left"].set_color("#8C564B")

		self.host.spines['right'].set_color("#555555")
		self.host.spines['left'].set_color("#555555")
		self.host.spines['top'].set_color("#555555")
		self.host.spines['bottom'].set_color("#555555")

		# data
		dataDate = []
		dataRPM = []
		dataCurrent = []
		dataVoltage = []
		dataPWM = []
		dataUC = []
		dataWatts = []
		self.myXLim = 0
		for row in data:
			self.myXLim = row['sec']
			dataDate.append(row['sec'])
			dataRPM.append(row['headspeed'])
			dataVoltage.append(row['voltage'])
			dataCurrent.append(row['current'])
			dataPWM.append(row['pwm'])
			dataUC.append(row['usedcapacity'])
			dataWatts.append(row['voltage'] * row['current'])

		self.p1, = self.host.plot(dataDate, dataVoltage, "#1F77B4", linewidth=0.5)
		self.p2, = par1.plot(dataDate, dataRPM, "#FF7F0E",  linewidth=0.5)
		self.p3, = par2.plot(dataDate, dataCurrent, "#2CA02C",  linewidth=0.5)
		self.p4, = par3.plot(dataDate, dataPWM,  color="#D62728", linewidth=0.5)
		self.p5, = par4.plot(dataDate, dataUC, color="#9467BD", linewidth=0.5)
		self.p6, = self.par5.plot(dataDate, dataWatts, color="#8C564B", linewidth=0.5)

		maxCurrent = max(dataCurrent)
		maxRPM = max(dataRPM)
		maxVoltage = max(dataVoltage)
		maxWatts = max(dataWatts)

		self.host.set_ylim(0, maxVoltage * 1.7)
		par2.set_ylim(0,maxCurrent * 2)
		par1.set_ylim(0,maxRPM * 1.5)
		self.par5.set_ylim(0,maxWatts * 1.5)
		par4.set_ylim(0)

		# labels
		self.host.set_xlabel("Duration (sec)", fontsize='x-small')
		self.host.set_ylabel("Voltage", fontsize='x-small')
		par1.set_ylabel("RPM", fontsize='x-small')
		par2.set_ylabel("Current(A)", fontsize='x-small')
		par3.set_ylabel("PWM", fontsize='x-small')
		par4.set_ylabel("Used capacity (mAh)", fontsize='x-small')
		self.par5.set_ylabel("Power (W)", fontsize='x-small')

		# colors
		self.host.xaxis.label.set_color('#555555')
		self.host.yaxis.label.set_color(self.p1.get_color())
		par1.yaxis.label.set_color(self.p2.get_color())
		par2.yaxis.label.set_color(self.p3.get_color())
		par3.yaxis.label.set_color(self.p4.get_color())
		par4.yaxis.label.set_color(self.p5.get_color())
		self.par5.yaxis.label.set_color(self.p6.get_color())

		# minor locator
		par2.yaxis.set_minor_locator(AutoMinorLocator())
		self.host.yaxis.set_minor_locator(AutoMinorLocator())
		self.host.xaxis.set_minor_locator(AutoMinorLocator())
		par1.yaxis.set_minor_locator(AutoMinorLocator())
		self.par5.yaxis.set_minor_locator(AutoMinorLocator())
		par3.yaxis.set_minor_locator(AutoMinorLocator())
		par4.yaxis.set_minor_locator(AutoMinorLocator())

		# ticks
		self.host.tick_params(axis='y', colors=self.p1.get_color(), which='major', direction='out', labelsize='x-small', size=4, width=1)
		self.host.tick_params(axis='y', colors=self.p1.get_color(), which='minor', direction='out', labelsize='x-small', size=2, width=1)

		par1.tick_params(axis='y', colors=self.p2.get_color(), which='major', direction='out', labelsize='x-small', size=4, width=1)
		par1.tick_params(axis='y', colors=self.p2.get_color(), which='minor', direction='out', labelsize='x-small', size=2, width=1)

		par2.tick_params(axis='y', colors=self.p3.get_color(), which='major', direction='out', labelsize='x-small', size=4, width=1)
		par2.tick_params(axis='y', colors=self.p3.get_color(), which='minor', direction='out', labelsize='x-small', size=2, width=1)

		par3.tick_params(axis='y', colors=self.p4.get_color(), which='major', direction='out', labelsize='x-small', size=4, width=1)
		par3.tick_params(axis='y', colors=self.p4.get_color(), which='minor', direction='out', labelsize='x-small', size=2, width=1)

		par4.tick_params(axis='y', colors=self.p5.get_color(), which='major', direction='out', labelsize='x-small', size=4, width=1)
		par4.tick_params(axis='y', colors=self.p5.get_color(), which='minor', direction='out', labelsize='x-small', size=2, width=1)

		self.par5.tick_params(axis='y', colors=self.p6.get_color(), which='major', direction='out', labelsize='x-small', size=4, width=1)
		self.par5.tick_params(axis='y', colors=self.p6.get_color(), which='minor', direction='out', labelsize='x-small', size=2, width=1)

		self.host.tick_params(axis='x', which='both', colors='#555555', top='off', size=2, width=1)
		self.host.tick_params(axis='x', which='major', colors='#555555', size=4, width=1)


		# Bottom panel
		panelBottom = wx.Panel(self)
		gs = wx.GridSizer(5, 7, 5, 5)
		panelBottom.SetSizer(gs)

		gs.Add(wx.StaticText(panelBottom), wx.EXPAND)
		t1 = wx.StaticText(panelBottom, label='Voltage', style=wx.ALIGN_CENTER)
		t1.SetForegroundColour("#1F77B4")
		gs.Add(t1, 1, wx.EXPAND)
		t2 = wx.StaticText(panelBottom, label='Current', style=wx.ALIGN_CENTER)
		t2.SetForegroundColour("#2CA02C")
		gs.Add(t2, 1, wx.EXPAND)
		t3 = wx.StaticText(panelBottom, label='Power', style=wx.ALIGN_CENTER)
		t3.SetForegroundColour("#8C564B")
		gs.Add(t3, 1, wx.EXPAND)
		t4 = wx.StaticText(panelBottom, label='RPM', style=wx.ALIGN_CENTER)
		t4.SetForegroundColour("#FF7F0E")		
		gs.Add(t4, 1, wx.EXPAND)
		t5 = wx.StaticText(panelBottom, label='PWM', style=wx.ALIGN_CENTER)
		t5.SetForegroundColour("#D62728")		
		gs.Add(t5, 1, wx.EXPAND)
		t6 = wx.StaticText(panelBottom, label='Capacity', style=wx.ALIGN_CENTER)
		t6.SetForegroundColour("#9467BD")		
		gs.Add(t6, 1, wx.EXPAND)

		gs.Add(wx.StaticText(panelBottom, label='Mouse:', style=wx.ALIGN_RIGHT), 1, wx.EXPAND)
		self.m1 = wx.StaticText(panelBottom, label="0", style=wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE)
		gs.Add(self.m1, 1, wx.EXPAND)
		self.m2 = wx.StaticText(panelBottom, label="0", style=wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE)
		gs.Add(self.m2, 1, wx.EXPAND)
		self.m3 = wx.StaticText(panelBottom, label="0", style=wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE)
		gs.Add(self.m3, 1, wx.EXPAND)
		self.m4 = wx.StaticText(panelBottom, label="0", style=wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE)
		gs.Add(self.m4, 1, wx.EXPAND)
		self.m5 = wx.StaticText(panelBottom, label="0", style=wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE)
		gs.Add(self.m5, 1, wx.EXPAND)
		self.m6 = wx.StaticText(panelBottom, label="0", style=wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE)
		gs.Add(self.m6, 1, wx.EXPAND)

		gs.Add(wx.StaticText(panelBottom, label='Min:', style=wx.ALIGN_RIGHT), 1, wx.EXPAND)
		m = min(dataVoltage)
		m =  "{0:.1f}".format(round(m,1))
		gs.Add(wx.StaticText(panelBottom, label=str(m), style=wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE), 1, wx.EXPAND)
		m = min(dataCurrent)
		m =  "{0:.1f}".format(round(m,1))
		gs.Add(wx.StaticText(panelBottom, label=str(m), style=wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE), 1, wx.EXPAND)
		m = min(dataWatts)
		m = int(m)
		gs.Add(wx.StaticText(panelBottom, label=str(m), style=wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE), 1, wx.EXPAND)
		m = min(dataRPM)
		m = int(m)
		gs.Add(wx.StaticText(panelBottom, label=str(m), style=wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE), 1, wx.EXPAND)
		m = min(dataPWM)
		m = int(m)
		gs.Add(wx.StaticText(panelBottom, label=str(m), style=wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE), 1, wx.EXPAND)
		m = min(dataUC)
		m = int(m)
		gs.Add(wx.StaticText(panelBottom, label=str(m), style=wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE), 1, wx.EXPAND)

		gs.Add(wx.StaticText(panelBottom, label='Max:', style=wx.ALIGN_RIGHT), 1, wx.EXPAND)
		m = max(dataVoltage)
		m =  "{0:.1f}".format(round(m,1))
		gs.Add(wx.StaticText(panelBottom, label=str(m), style=wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE), 1, wx.EXPAND)
		m = max(dataCurrent)
		m =  "{0:.1f}".format(round(m,1))
		gs.Add(wx.StaticText(panelBottom, label=str(m), style=wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE), 1, wx.EXPAND)
		m = max(dataWatts)
		m = int(m)
		gs.Add(wx.StaticText(panelBottom, label=str(m), style=wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE), 1, wx.EXPAND)
		m = max(dataRPM)
		m = int(m)
		gs.Add(wx.StaticText(panelBottom, label=str(m), style=wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE), 1, wx.EXPAND)
		m = max(dataPWM)
		m = int(m)
		gs.Add(wx.StaticText(panelBottom, label=str(m), style=wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE), 1, wx.EXPAND)
		m = max(dataUC)
		m = int(m)
		gs.Add(wx.StaticText(panelBottom, label=str(m), style=wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE), 1, wx.EXPAND)

		gs.Add(wx.StaticText(panelBottom, label='Average:', style=wx.ALIGN_RIGHT), 1, wx.EXPAND)
		avg = reduce(lambda x, y: x + y, dataVoltage) / len(dataVoltage)
		avg =  "{0:.1f}".format(round(avg,1))
		gs.Add(wx.StaticText(panelBottom, label=str(avg), style=wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE), 1, wx.EXPAND)
		avg = reduce(lambda x, y: x + y, dataCurrent) / len(dataCurrent)
		avg =  "{0:.1f}".format(round(avg,1))
		gs.Add(wx.StaticText(panelBottom, label=str(avg), style=wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE), 1, wx.EXPAND)
		avg = reduce(lambda x, y: x + y, dataWatts) / len(dataWatts)
		avg =  int(avg)
		gs.Add(wx.StaticText(panelBottom, label=str(avg), style=wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE), 1, wx.EXPAND)
		avg = reduce(lambda x, y: x + y, dataRPM) / len(dataRPM)
		avg = int(avg)
		gs.Add(wx.StaticText(panelBottom, label=str(avg), style=wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE), 1, wx.EXPAND)
		avg = reduce(lambda x, y: x + y, dataPWM) / len(dataPWM)
		avg = int(avg)
		gs.Add(wx.StaticText(panelBottom, label=str(avg), style=wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE), 1, wx.EXPAND)
		avg = (max(dataUC) - min(dataUC)) / max(dataDate) * 60
		avg =  int(avg)
		gs.Add(wx.StaticText(panelBottom, label=str(avg) + '/min', style=wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE), 1, wx.EXPAND)

		sizerMainVert.Add(panelBottom, 0, wx.LEFT | wx.TOP | wx.ALIGN_CENTER )
		sizerMainVert.Add((0,10))

		self.SetBackgroundColour('white')

		# matplot events
		self.figure.canvas.mpl_connect('motion_notify_event', self.OnMotion)
		self.figure.canvas.mpl_connect('button_press_event', self.OnPress)
		self.figure.canvas.mpl_connect('button_release_event', self.OnRelease)
		self.figure.canvas.mpl_connect('resize_event', self.OnResize)

		self.host.set_xlim(0, self.myXLim)

		self.Show()

	def make_patch_spines_invisible(self, ax):
		ax.set_frame_on(True)
		ax.patch.set_visible(False)
		ax.spines['left'].set_visible(False)
		for sp in ax.spines.itervalues():
			sp.set_visible(False)

	def OnMotion(self, event):
		if event.inaxes == None: 
			return

		x0, y0, x1, y1 = event.inaxes.dataLim.bounds

		npts = len(event.inaxes.lines[0].get_ydata())
		idx = int(round((npts-1) * (event.xdata-x0)/x1))

		p1Values = self.p1.get_ydata();
		p2Values = self.p2.get_ydata();
		p3Values = self.p3.get_ydata();
		p4Values = self.p4.get_ydata();
		p5Values = self.p5.get_ydata();
		p6Values = self.p6.get_ydata();
		if len(p1Values) < idx + 1:
			return

		if self.background is None:
			self.background = self.figure.canvas.copy_from_bbox(self.host.bbox)

		# restore the clean slate background
		self.figure.canvas.restore_region(self.background)

		polygon = None
		if self.selectStart == None:
			linev = self.host.axvline(x=event.xdata, linewidth=1, color='#000000', alpha=0.5)
			lineh = self.par5.axhline(y=event.ydata, linewidth=1, color='#000000', alpha=0.5)
			self.host.draw_artist(linev)
			self.host.draw_artist(lineh)
		else:
			width = abs(event.xdata - self.selectStart)
			start = self.selectStart
			if (event.xdata < start):
				start = event.xdata
			polygon = Rectangle((start, y0), width, y1, facecolor="grey", alpha=0.5)
			self.host.add_patch(polygon)
			self.host.draw_artist(polygon)

		self.figure.canvas.blit(self.host.bbox)
		if len(self.host.lines) > 1 :
			linev.remove()
			lineh.remove()
		if polygon != None:
			polygon.remove()

		self.m1.SetLabel(str(p1Values[idx]))
		self.m2.SetLabel(str(p3Values[idx]))
		self.m3.SetLabel(str(int(p6Values[idx])))
		self.m4.SetLabel(str(p2Values[idx]))
		self.m5.SetLabel(str(p4Values[idx]))
		self.m6.SetLabel(str(int(p5Values[idx])))

	def OnPress(self, event):
		if event.button == 3:
			self.background =  None
		 	self.host.set_xlim(0, self.myXLim)
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
		 	self.host.set_xlim(start, end)

		self.canvas.draw()
		self.canvas.Refresh()
		self.selectStart = None
		self.background = None

	def OnResize(self, event):
		self.background = None

app = wx.App(False)
app.SetAppName("VBar control log analyzer")
app.SetMacHelpMenuTitleName("VControl")

frame = MainWindow()
app.MainLoop()
