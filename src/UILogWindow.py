"""
The UI graph window
"""
__author__ = "linus.larsson@gmail.com"

import wx
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.ticker import MultipleLocator, AutoMinorLocator
from matplotlib.patches import Rectangle

import vc.globals
import vc.variable
import vc.util
import vc.screenshot

class UILogWindow(wx.Frame):
	def __init__(self, log_id, analyzer):
		self._background = None
		self._select_start = None

		labels = [
			_("Voltage").decode("utf8"), 
			_("Current").decode("utf8"), 
			_("Power").decode("utf8"),
			_("Headspeed").decode("utf8"), 
			_("PWM").decode("utf8"), 
			_("Capacity").decode("utf8")
		]

		self._colors = ["#1F77B4", "#2CA02C", "#8C564B", "#FF7F0E", "#D62728", "#9467BD"]

		wx.Frame.__init__(self, None, title=vc.globals.PROGRAM_NAME + " " + vc.globals.VERSION + " - Log Id " + log_id, size=(1200, 700))
		self._figure = Figure()
		axes = self._figure.add_subplot(111)
		self._canvas = FigureCanvas(self, -1, self._figure)

		main_vertical_sizer = wx.BoxSizer(wx.VERTICAL)
		self._figure.set_facecolor("white")

		ui_info = analyzer.extract_info_by_log_id(log_id)

		# Title
		info = ui_info["model"] + " - " + ui_info["battery"] + " (" + ui_info["date"] + ")"
		info_text = wx.StaticText(self, label=info, style=wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE)
		info_text.SetFont(wx.Font(18, wx.DECORATIVE, wx.NORMAL, wx.NORMAL))
		main_vertical_sizer.AddSpacer(10) 
		main_vertical_sizer.Add(info_text, 0, wx.EXPAND)

		main_vertical_sizer.Add(self._canvas, 1, wx.LEFT | wx.TOP | wx.GROW)
		self.SetSizer(main_vertical_sizer)

		# Grid lines
		axes.xaxis.grid(True)
		axes.xaxis.grid(b=True, which="major", color="0.65",linestyle="-")

		self._graphs = {}
		# Subgraphs
		self._graphs[-1] = axes
		for i in xrange(0,6):
			self._graphs[i] = self._graphs[-1].twinx()


		# data
		self._data = {} 
		for i in xrange(-1, 6):
			self._data[i] = []  # sec
		self.duration = 0
		for row in analyzer.extract_ui_by_log_id(log_id):
			self.duration = row["sec"]
			self._data[-1].append(row["sec"])
			self._data[0].append(row["voltage"])
			self._data[1].append(row["current"])
			self._data[2].append(row["voltage"] * row["current"])
			self._data[3].append(row["headspeed"])
			self._data[4].append(row["pwm"])
			self._data[5].append(row["usedcapacity"])

		# plots
		self._plots = {}
		for i in xrange(0, 6):
			self._plots[i], = self._graphs[i].plot(self._data[-1], self._data[i], self._colors[i], linewidth=0.5)

		# scale graphs
		self._graphs[0].set_ylim(0, max(self._data[0]) * 1.7)
		self._graphs[1].set_ylim(0, max(self._data[1]) * 2)
		self._graphs[2].set_ylim(0, max(self._data[2]) * 1.5)
		self._graphs[3].set_ylim(0, max( { max(self._data[3]), 100 } ) * 1.5)
		self._graphs[5].set_ylim(0)

		# labels
		self._graphs[-1].set_xlabel(_("Duration (sec)").decode("utf8"), fontsize="x-small")
		self._graphs[0].set_ylabel(_("Voltage (U)").decode("utf8"), fontsize="x-small")
		self._graphs[1].set_ylabel(_("Current (I)").decode("utf8"), fontsize="x-small")
		self._graphs[2].set_ylabel(_("Power (W)").decode("utf8"), fontsize="x-small")
		self._graphs[3].set_ylabel(_("Headspeed (RPM)").decode("utf8"), fontsize="x-small")
		self._graphs[4].set_ylabel(_("PWM (%)").decode("utf8"), fontsize="x-small")
		self._graphs[5].set_ylabel(_("Used capacity (mAh)").decode("utf8"), fontsize="x-small")

		# colors and locators
		self._graphs[-1].xaxis.set_minor_locator(AutoMinorLocator())
		self._graphs[0].xaxis.label.set_color("#555555")
		for i in xrange(0, 6):
			self._graphs[i].yaxis.label.set_color(self._plots[i].get_color())
			self._graphs[i].yaxis.set_minor_locator(AutoMinorLocator())

		# ticks
		for i in xrange(0, 6):
			self._graphs[i].tick_params(axis="y", colors=self._plots[i].get_color(), which="major", direction="out", labelsize="x-small", size=4, width=1)
			self._graphs[i].tick_params(axis="y", colors=self._plots[i].get_color(), which="minor", direction="out", labelsize="x-small", size=2, width=1)

		# Bottom panel
		bottom_panel = wx.Panel(self)
		bottom_sizer = wx.BoxSizer(wx.HORIZONTAL)
		bottom_panel.SetSizer(bottom_sizer)
		main_vertical_sizer.Add(bottom_panel, 0,wx.ALIGN_CENTER | wx.EXPAND)

		# Screenshot
		screenshot_panel = wx.Panel(bottom_panel)
		screenshot_sizer = wx.BoxSizer(wx.VERTICAL)
		screenshot_panel.SetSizer(screenshot_sizer)

		self._screenshot_button = wx.BitmapButton(
			screenshot_panel, 
			-1, 
			 wx.Bitmap(vc.util.resource_path("assets/img/screenshot.png"), wx.BITMAP_TYPE_PNG), 
			pos=(10, 20)
		)
		screenshot_sizer.AddStretchSpacer(1)
		screenshot_sizer.Add(self._screenshot_button, 0, wx.ALIGN_BOTTOM | wx.LEFT, 12)
		bottom_sizer.Add(screenshot_panel, 0, wx.EXPAND)
		self.Bind(wx.EVT_BUTTON, self._on_screenshot, self._screenshot_button)

		# Values
		values_panel = wx.Panel(bottom_panel)
		values_grid_sizer = wx.GridSizer(5, 7, 5, 20)
		values_panel.SetSizer(values_grid_sizer)

		values_grid_sizer.Add(wx.StaticText(values_panel), wx.EXPAND)

		# Value labels
		self._value_on_checkboxes = {}
		for i in xrange(0, 6):
			value_panel = wx.Panel(values_panel, style=wx.ALIGN_CENTER);
			value_sizer = wx.BoxSizer(wx.HORIZONTAL)
			value_panel.SetSizer(value_sizer)
			self._value_on_checkboxes[i] = wx.CheckBox(value_panel)
			value_sizer.AddStretchSpacer(1)
			value_sizer.Add(self._value_on_checkboxes[i], 0)
			value_label_text = wx.StaticText(value_panel, label=labels[i])
			value_label_text.SetForegroundColour(self._colors[i])
			value_sizer.Add(value_label_text, 0)
			value_sizer.AddStretchSpacer(1)
			# Add to sizer
			values_grid_sizer.Add(value_panel, 1, wx.EXPAND)
			if vc.variable.get("ui-show-value-" + str(i), "1") == "1":
				self._value_on_checkboxes[i].SetValue(True)
			self.Bind(wx.EVT_CHECKBOX, self._on_label_checkbox, self._value_on_checkboxes[i])

		# Mouse text
		values_grid_sizer.Add(wx.StaticText(values_panel, label=_("Mouse").decode("utf8"), style=wx.ALIGN_RIGHT), 1, wx.EXPAND)
		self._mouse_texts = {}
		for i in xrange(0, 6):
			self._mouse_texts[i] = wx.StaticText(values_panel, label="0", style=wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE)
			values_grid_sizer.Add(self._mouse_texts[i], 1, wx.EXPAND)

		# Min values		
		values_grid_sizer.Add(wx.StaticText(values_panel, label=_("Min").decode("utf8"), style=wx.ALIGN_RIGHT), 1, wx.EXPAND)
		self._min_texts = {}
		for i in xrange(0, 6):
			m = min(self._data[i])
			if (i < 2):
				m =  "{0:.1f}".format(round(m,1))
			else:
				m = int(m)
			self._min_texts[i] = wx.StaticText(values_panel, label=str(m), style=wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE)	
			values_grid_sizer.Add(self._min_texts[i], 1, wx.EXPAND)

		# Max values		
		values_grid_sizer.Add(wx.StaticText(values_panel, label=_("Max").decode("utf8"), style=wx.ALIGN_RIGHT), 1, wx.EXPAND)
		self._max_texts = {}
		for i in xrange(0, 6):
			m = max(self._data[i])
			if (i < 2):
				m =  "{0:.1f}".format(round(m,1))
			else:
				m = int(m)
			self._max_texts[i] = wx.StaticText(values_panel, label=str(m), style=wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE)	
			values_grid_sizer.Add(self._max_texts[i], 1, wx.EXPAND)

		# Average values
		values_grid_sizer.Add(wx.StaticText(values_panel, label=_("Average").decode("utf8"), style=wx.ALIGN_RIGHT), 1, wx.EXPAND)
		self._avarage_texts = {}
		for i in xrange(0, 5):
			m = reduce(lambda x, y: x + y, self._data[i]) / len(self._data[i])
			if (i < 2):
				m =  "{0:.1f}".format(round(m,1))
			else:
				m = int(m)
			self._avarage_texts[i] = wx.StaticText(values_panel, label=str(m), style=wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE)	
			values_grid_sizer.Add(self._avarage_texts[i], 1, wx.EXPAND)

		# capacity / min
		m = int((max(self._data[5]) - min(self._data[5])) / max(self._data[-1]) * 60)
		self._avarage_texts[5] = wx.StaticText(values_panel, label=str(m), style=wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE)	
		values_grid_sizer.Add(self._avarage_texts[5], 1, wx.EXPAND)

		self._update_min_max(0, self.duration)
		bottom_sizer.AddStretchSpacer(1)
		bottom_sizer.Add(values_panel, 0, wx.ALIGN_CENTER | wx.GROW)
		bottom_sizer.AddStretchSpacer(1)
		bottom_sizer.AddSpacer(50)

		main_vertical_sizer.Add((0,10))
		self.SetBackgroundColour("white")

		self._graphs[0].set_xlim(0, self.duration)
		self._update_spines()

		# Matplot events
		self._figure.canvas.mpl_connect("motion_notify_event", self._on_figure_motion)
		self._figure.canvas.mpl_connect("button_press_event", self._on_figure_press)
		self._figure.canvas.mpl_connect("button_release_event", self._on_figure_release)
		self._figure.canvas.mpl_connect("resize_event", self._on_figure_resize)

		self.Show()
		for i in xrange(0, 6):
			self._graphs[i].set_visible(self._value_on_checkboxes[i].IsChecked());
		self._canvas.draw()
		self._canvas.Refresh()

	def _update_spines(self):
		spines_data = {
			0: { "pos": "left" },  # Voltage
			1: { "pos": "left" },  # Current
			2: { "pos": "left" },  # Power
			3: { "pos": "right" }, # Headspeed
			4: { "pos": "right" }, # PWM
			5: { "pos": "right" }, # Capacity
		}

		# spines
		self._graphs[-1].spines["right"].set_color("#777777")
		self._graphs[-1].spines["left"].set_color("#777777")
		self._graphs[-1].spines["top"].set_color("#777777")
		self._graphs[-1].spines["bottom"].set_color("#777777")
		self._graphs[-1].get_yaxis().set_ticks([])

		space = 0.08
		left  = space
		right = 1.0 - space

		for i in xrange(0,6):
			if self._value_on_checkboxes[i].IsChecked():
				pos = spines_data[i]["pos"]
				if pos == "left":
					left -= space
					self._graphs[i].spines["left"].set_position(("axes", left))
					self._graphs[i].yaxis.tick_left()
				else:
					right += space
					self._graphs[i].spines["right"].set_position(("axes", right))
					self._graphs[i].yaxis.tick_right()

				self._make_patch_spines_invisible(self._graphs[i])
				self._graphs[i].spines[pos].set_visible(True)
				self._graphs[i].spines[pos].set_color(self._colors[i])
				self._graphs[i].yaxis.set_label_position(pos);

		self._figure.subplots_adjust(
			left= -left / 1.7 + space, 
			right= 1 - (right - 1) / 1.7 - space, 
			top=0.97, bottom=0.09)

	def _make_patch_spines_invisible(self, ax):
		ax.set_frame_on(True)
		ax.patch.set_visible(False)
		ax.spines["left"].set_visible(False)
		for sp in ax.spines.itervalues():
			sp.set_visible(False)

	def _on_label_checkbox(self, event):
		for i in xrange(0,6):
			self._graphs[i].set_visible(self._value_on_checkboxes[i].IsChecked());
			if self._value_on_checkboxes[i].IsChecked():
				vc.variable.set("ui-show-value-" + str(i), "1");
			else:
				vc.variable.set("ui-show-value-" + str(i), "0");


		self._update_spines()

		self._canvas.draw()
		self._canvas.Refresh()
		self._background = None

	def _on_figure_motion(self, event):
		if event.inaxes == None:
			return

		x0, y0, x1, y1 = event.inaxes.dataLim.bounds

		number_of_points = len(event.inaxes.lines[0].get_ydata())
		index = int(round((number_of_points-1) * (event.xdata-x0)/x1))

		if len(self._data[0]) < index + 1:
			return

		if self._background is None:
			self._background = self._figure.canvas.copy_from_bbox(self._graphs[0].bbox)

		# restore the clean slate background
		self._figure.canvas.restore_region(self._background)

		polygon = None
		if self._select_start == None:
			linev = self._graphs[0].axvline(x=event.xdata, linewidth=1, color="#000000", alpha=0.5)
			lineh = self._graphs[5].axhline(y=event.ydata, linewidth=1, color="#000000", alpha=0.5)
			self._graphs[0].draw_artist(linev)
			self._graphs[0].draw_artist(lineh)
		else:
			width = abs(event.xdata - self._select_start)
			start = self._select_start
			if (event.xdata < start):
				start = event.xdata
			if width < 20:
				col = "#aa4444"
			else:
				col = "#888888"
			polygon = Rectangle((start, 0), width, y1, facecolor=col, alpha=0.5)
			self._graphs[0].add_patch(polygon)
			self._graphs[0].draw_artist(polygon)

		self._figure.canvas.blit(self._graphs[0].bbox)
		if self._select_start == None:
			linev.remove()
			lineh.remove()
		if polygon != None:
			polygon.remove()

		for i in xrange(0, 6):
			if (i < 2):
				val = str(self._data[i][index])
			else:
				val = str(int(self._data[i][index]))					
			self._mouse_texts[i].SetLabel(val)

	def _on_figure_press(self, event):
		if event.button == 3:
			self._update_min_max(0, self.duration)
			self._background =  None
		 	self._graphs[0].set_xlim(0, self.duration)
			self._canvas.draw()
			self._canvas.Refresh()

		else:
			self._select_start = event.xdata


	def _on_figure_release(self, event):
		if event.button != 1:
			return

		if  self._select_start == None:
			return

		start = self._select_start
		end = event.xdata

		if end == None:
			self._select_start = None
			return

		if (end < start):
			temp = start
			start = end
			end = temp

		width = abs(end - start)
		if width >= 20:
		 	self._graphs[0].set_xlim(start, end)
			self._update_min_max(start, start + width)

		self._canvas.draw()
		self._canvas.Refresh()
		self._select_start = None
		self._background = None

	def _on_figure_resize(self, event):
		self._background = None
		self._canvas.draw()
		self._canvas.Refresh()

	# Param start, end are seconds
	def _update_min_max(self, start, end):
		number_of_points = len(self._plots[0].get_ydata());
		index1 = int(number_of_points * start / self.duration);
		index2 = int(number_of_points * end / self.duration);

		if index2 >= len(self._data[0]):
			index2 = len(self._data[0]) - 1

		for i in xrange(0, 6):
			m = max(self._data[i][index1:index2])
			if (i < 2):
				m =  "{0:.1f}".format(round(m,1))
			else:
				m = int(m)
			self._max_texts[i].SetLabel(str(m))

			m = min(self._data[i][index1:index2])
			if (i < 2):
				m =  "{0:.1f}".format(round(m,1))
			else:
				m = int(m)
			self._min_texts[i].SetLabel(str(m))

		for i in xrange(0, 5):
			m = reduce(lambda x, y: x + y, self._data[i][index1:index2]) / len(self._data[i][index1:index2])
			if (i < 2):
				m =  "{0:.1f}".format(round(m,1))
			else:
				m = int(m)
			self._avarage_texts[i].SetLabel(str(m))

		m = int((max(self._data[5][index1:index2]) - min(self._data[5][index1:index2])) / (self._data[-1][index2] - self._data[-1][index1]) * 60)
		self._avarage_texts[5].SetLabel(str(m) + "/min")

	def _on_screenshot(self, event):
		if (self._background):	
			self._figure.canvas.restore_region(self._background)
		self._screenshot_button.GetParent().GetSizer().Hide(self._screenshot_button)
		self._screenshot_button.GetParent().GetSizer().Layout()
		self._canvas.draw()
		self._canvas.Refresh()

		vc.screenshot.grab(self)

		self._screenshot_button.GetParent().GetSizer().Show(self._screenshot_button)
		self._screenshot_button.GetParent().GetSizer().Layout()

