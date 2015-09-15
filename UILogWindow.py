import wx
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.ticker import MultipleLocator, AutoMinorLocator
from matplotlib.patches import Rectangle

import Variable

class UILogWindow(wx.Frame):
	def __init__(self, logId, analyzer):
		self.background = None
		self.selectStart = None
		data = analyzer.extract_ui(logId)

		labels = ['Voltage', 'Current', 'Power', 'Headspeed', 'PWM', 'Capacity']
		self.colors = ["#1F77B4", "#2CA02C", "#8C564B", "#FF7F0E", "#D62728", "#9467BD"]

		wx.Frame.__init__(self, None, title='VBar Control flight analyzer v2.7.1 - Log Id ' + logId, size=(1200, 700))
		self.figure = Figure()
		self.axes = self.figure.add_subplot(111)
		self.canvas = FigureCanvas(self, -1, self.figure)

		sizerMainVert = wx.BoxSizer(wx.VERTICAL)
		self.figure.set_facecolor('white')

		uiInfo = analyzer.extract_info_by_logid(logId)

		info = uiInfo['model'] + " - " + uiInfo['battery'] + " (" + uiInfo['date'] + ")"
		infoText = wx.StaticText(self, label=info, style=wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE)
		infoText.SetFont(wx.Font(18, wx.DECORATIVE, wx.NORMAL, wx.NORMAL))
		sizerMainVert.AddSpacer(10) 
		sizerMainVert.Add(infoText, 0, wx.EXPAND)

		sizerMainVert.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.GROW)
		self.SetSizer(sizerMainVert)

		# Grid lines
		self.axes.xaxis.grid(True)
		self.axes.xaxis.grid(b=True, which='major', color='0.65',linestyle='-')

		self.graphs = {}
		# Subgraphs
		self.graphs[-1] = self.axes
		for i in xrange(0,6):
			self.graphs[i] = self.graphs[-1].twinx()


		# data
		self.data = {} 
		for i in xrange(-1, 6):
			self.data[i] = []  # sec
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
			self.plots[i], = self.graphs[i].plot(self.data[-1], self.data[i], self.colors[i], linewidth=0.5)

		# scale graphs
		self.graphs[0].set_ylim(0, max(self.data[0]) * 1.7)
		self.graphs[1].set_ylim(0, max(self.data[1]) * 2)
		self.graphs[2].set_ylim(0, max(self.data[2]) * 1.5)
		self.graphs[3].set_ylim(0, max( { max(self.data[3]), 100 } ) * 1.5)
		self.graphs[5].set_ylim(0)

		# labels
		self.graphs[-1].set_xlabel("Duration (sec)", fontsize='x-small')
		self.graphs[0].set_ylabel("Voltage(U)", fontsize='x-small')
		self.graphs[1].set_ylabel("Current(I)", fontsize='x-small')
		self.graphs[2].set_ylabel("Power (W)", fontsize='x-small')
		self.graphs[3].set_ylabel("Headspeed (RPM)", fontsize='x-small')
		self.graphs[4].set_ylabel("PWM (%)", fontsize='x-small')
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
			t1.SetForegroundColour(self.colors[i])
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
		self.spines()

		# matplot events
		self.figure.canvas.mpl_connect('motion_notify_event', self.OnMotion)
		self.figure.canvas.mpl_connect('button_press_event', self.OnPress)
		self.figure.canvas.mpl_connect('button_release_event', self.OnRelease)
		self.figure.canvas.mpl_connect('resize_event', self.OnResize)

		self.Show()
		for i in xrange(0,6):
			self.graphs[i].set_visible(self.valueOnCheck[i].IsChecked());
		self.canvas.draw()
		self.canvas.Refresh()

	def spines(self):
		spinesData = {
			0: { 'pos': 'left' }, # Voltage
			1: { 'pos': 'left' }, # Current
			2: { 'pos': 'left' }, # Power
			3: { 'pos': 'right' }, # Headspeed
			4: { 'pos': 'right' }, # PWM
			5: { 'pos': 'right' }, # Capacity
		}

		# spines
		self.graphs[-1].spines['right'].set_color("#777777")
		self.graphs[-1].spines['left'].set_color("#777777")
		self.graphs[-1].spines['top'].set_color("#777777")
		self.graphs[-1].spines['bottom'].set_color("#777777")
		self.graphs[-1].get_yaxis().set_ticks([])

		space = 0.08
		left  = space
		right = 1.0 - space

		for i in xrange(0,6):
			if self.valueOnCheck[i].IsChecked():
				pos = spinesData[i]['pos']
				if pos == 'left':
					left -= space
					self.graphs[i].spines["left"].set_position(("axes", left))
					self.graphs[i].yaxis.tick_left()
				else:
					right += space
					self.graphs[i].spines["right"].set_position(("axes", right))
					self.graphs[i].yaxis.tick_right()

				self.make_patch_spines_invisible(self.graphs[i])
				self.graphs[i].spines[pos].set_visible(True)
				self.graphs[i].spines[pos].set_color(self.colors[i])
				self.graphs[i].yaxis.set_label_position(pos);

		self.figure.subplots_adjust(
			left= -left / 1.7 + space, 
			right= 1 - (right - 1) / 1.7 - space, 
			top=0.97, bottom=0.09)

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

		self.spines()

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
		self.canvas.draw()
		self.canvas.Refresh()

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
