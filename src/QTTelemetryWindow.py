"""
UI Log window
"""
__author__ = "linus.larsson@gmail.com"
import PySide
from PySide import QtCore, QtGui

from numpy import arange, sin, pi, arange
import matplotlib
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg  as FigureCanvas
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.ticker import MultipleLocator, AutoMinorLocator
from matplotlib.patches import Rectangle

import vc.globals
import vc.variable
import vc.util
import vc.screenshot
from qtui.QTDTelemetryWindow import Ui_QTDTelemetryWindow

class QTTelemetryWindow(QtGui.QMainWindow):
    def __init__(self, log_id, analyzer):
        QtGui.QMainWindow.__init__(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.ui = Ui_QTDTelemetryWindow()
        self.ui.setupUi(self)

        self.factor, self.font_factor = vc.util.rescale(self)
        self.pixmap_screenshot = vc.util.load_pixmap("screenshot.png", self.factor)

        self._background = None
        self._select_start = None

        labels = [
            "Voltage", 
            "Current", 
            "Power",
            "Headspeed", 
            "PWM", 
            "Capacity"
            "Height"
            "Speed"
        ]

        self._colors = ["#1F77B4", "#2CA02C", "#8C564B", "#FF7F0E", "#D62728", "#9467BD", "#e377c2", "#bcbd22"]
# ["#e377c2","#7f7f7f","#bcbd22","#17becf"]

        self.setStyleSheet("QCheckBox { background-color: white }")

        self.setWindowTitle(vc.globals.PROGRAM_NAME + " " + vc.globals.VERSION + " - Log Id " + str(log_id))

        ui_info = analyzer.extract_info_by_log_id(log_id)

        # Title
        info = ui_info["model"] + " - " + ui_info["battery"] + " (" + ui_info["date"] + ")"
        self.ui.label_title.setText(info)

        # data
        self._data = {} 
        for i in xrange(-1, 8):
            self._data[i] = []  # sec
        self.duration = 0
        uilog = analyzer.extract_ui_by_log_id(log_id)
        gpslog = analyzer.extract_gps_by_log_id(log_id)
        ui_data = self.merge_ui_gps_log(uilog, gpslog)
        for row in ui_data:
            self.duration = row["sec"]
            self._data[-1].append(row["sec"])
            self._data[0].append(row["voltage"])
            self._data[1].append(row["current"])
            self._data[2].append(row["voltage"] * row["current"])
            self._data[3].append(row["headspeed"])
            self._data[4].append(row["pwm"])
            self._data[5].append(row["usedcapacity"])
            self._data[6].append(row["height"])
            self._data[7].append(row["speed"])

        # Screenshot
        pixmap = QtGui.QPixmap(self.pixmap_screenshot)
        self.ui.push_buttton_screenshot.setIcon(pixmap)
        self.ui.push_buttton_screenshot.setIconSize(pixmap.rect().size())
        self.ui.push_buttton_screenshot.clicked.connect(self._on_screenshot)

        # Value labels
        self._value_on_checkboxes = {}
        self._mouse_texts = {}
        self._min_texts = {}
        self._max_texts = {}
        self._avarage_texts = {}

        for i in xrange(0, 8):
            self._value_on_checkboxes[i] = self.ui.widget_grid.findChild(QtGui.QCheckBox, "grid_check_box_" + str(i))
            if vc.variable.get("ui-show-value-" + str(i), "1") == "1":
                self._value_on_checkboxes[i].setCheckState(QtCore.Qt.Checked)
            self._value_on_checkboxes[i].stateChanged.connect(self._on_label_checkbox)
            self._mouse_texts[i] = self.ui.widget_grid.findChild(QtGui.QLabel, "grid_label_0_" + str(i))
            self._min_texts[i] = self.ui.widget_grid.findChild(QtGui.QLabel, "grid_label_1_" + str(i))
            self._max_texts[i] = self.ui.widget_grid.findChild(QtGui.QLabel, "grid_label_2_" + str(i))
            self._avarage_texts[i] = self.ui.widget_grid.findChild(QtGui.QLabel, "grid_label_3_" + str(i))

        self.show()

        # Ugly Linux fix, spines go black if connecting notify too soon
        QtCore.QTimer.singleShot(0, self.connectMatplotEvents)

    def connectMatplotEvents(self):
        # Graph
        self._figure = Figure()
        self._canvas = FigureCanvas(self._figure)
        self.ui.vertical_layout_graph.addWidget(self._canvas)
        self._figure.set_facecolor("white")
        axes = self._figure.add_subplot(111)

        # Grid lines
        axes.xaxis.grid(True)
        axes.xaxis.grid(b=True, which="major", color="0.65",linestyle="-")

        self._graphs = {}
        # Subgraphs
        self._graphs[-1] = axes
        for i in xrange(0,8):
            self._graphs[i] = self._graphs[-1].twinx()

        # plots
        self._plots = {}
        for i in xrange(0, 8):
            self._plots[i], = self._graphs[i].plot(self._data[-1], self._data[i], self._colors[i], linewidth=0.5 * self.factor)

        # scale graphs
        self._graphs[0].set_ylim(0, max(self._data[0]) * 1.7)
        self._graphs[1].set_ylim(0, max(self._data[1]) * 2)
        self._graphs[2].set_ylim(0, max(self._data[2]) * 1.5)
        self._graphs[3].set_ylim(0, max( { max(self._data[3]), 100 } ) * 1.5)
        self._graphs[5].set_ylim(0)
        self._graphs[6].set_ylim(min(self._data[6]), max(self._data[6]) + 1)
        self._graphs[7].set_ylim(0, max(self._data[7]) + 1)

        # colors and locators
        fs = 8*self.font_factor
        self._graphs[-1].xaxis.set_minor_locator(AutoMinorLocator())
        self._graphs[-1].xaxis.label.set_color("#555555")
        self._graphs[-1].tick_params(axis="x", colors="#555555", which="major", direction="in", labelsize=fs, size=4*self.factor, width=1*self.factor)
        self._graphs[-1].tick_params(axis="x", colors="#555555", which="minor", direction="in", labelsize=fs, size=2*self.factor, width=1*self.factor)

        for i in xrange(0, 8):
            self._graphs[i].yaxis.label.set_color(self._plots[i].get_color())
            self._graphs[i].yaxis.set_minor_locator(AutoMinorLocator())

        # ticks
        for i in xrange(0, 8):
            self._graphs[i].tick_params(axis="y", colors=self._plots[i].get_color(), which="major", direction="out", labelsize=fs, size=4*self.factor, width=1*self.factor)
            self._graphs[i].tick_params(axis="y", colors=self._plots[i].get_color(), which="minor", direction="out", labelsize=fs, size=2*self.factor, width=1*self.factor)

        self._update_spines()

        self._update_min_max(0, self.duration)
        self._graphs[0].set_xlim(0, self.duration)

        for i in xrange(0, 8):
            self._graphs[i].set_visible(self._value_on_checkboxes[i].isChecked());

        # Matplot events
        self._canvas.mpl_connect("button_press_event", self._on_figure_press)
        self._canvas.mpl_connect("button_release_event", self._on_figure_release)
        self._motion_wait = 4
        self._canvas.mpl_connect("motion_notify_event", self._on_figure_motion)
 
    def _update_spines(self):
        spines_data = {
            0: { "pos": "left" },  # Voltage
            1: { "pos": "left" },  # Current
            2: { "pos": "left" },  # Power
            3: { "pos": "right" }, # Headspeed
            4: { "pos": "right" }, # PWM
            5: { "pos": "right" }, # Capacity
            6: { "pos": "left" }, # Height
            7: { "pos": "right" }, # Speed
        }

        # spines
        self._graphs[-1].spines["right"].set_color("#777777")
        self._graphs[-1].spines["left"].set_color("#777777")
        self._graphs[-1].spines["top"].set_color("#777777")
        self._graphs[-1].spines["bottom"].set_color("#777777")
        self._graphs[-1].get_yaxis().set_ticks([])
        self._graphs[-1].spines["top"].set_linewidth(self.factor)
        self._graphs[-1].spines["bottom"].set_linewidth(self.factor)

        space = 0.08
        left  = space
        right = 1.0 - space

        for i in xrange(0,8):
            if self._value_on_checkboxes[i].isChecked():
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
                self._graphs[i].spines[pos].set_linewidth(self.factor)
                self._graphs[i].spines[pos].set_color(self._colors[i])
                self._graphs[i].yaxis.set_label_position(pos);
                self._graphs[i].spines[pos].set_visible(True)


        self._figure.subplots_adjust(
            left= -left / 1.7 + space, 
            right= 1 - (right - 1) / 1.7 - space, 
            top=0.97, bottom=0.09)

        # labels
        fs = 8*self.font_factor
        self._graphs[-1].set_xlabel("Flight Time (sec)", fontsize=fs)
        self._graphs[0].set_ylabel("Voltage (U)", fontsize=fs)
        self._graphs[1].set_ylabel("Current (I)", fontsize=fs)
        self._graphs[2].set_ylabel("Power (W)", fontsize=fs)
        self._graphs[3].set_ylabel("Headspeed (RPM)", fontsize=fs)
        self._graphs[4].set_ylabel("PWM (%)", fontsize=fs)
        self._graphs[5].set_ylabel("Used capacity (mAh)", fontsize=fs)
        self._graphs[6].set_ylabel("Height (M)", fontsize=fs)
        self._graphs[7].set_ylabel("Speed (Kmh)", fontsize=fs)


    def _make_patch_spines_invisible(self, ax):
        ax.set_frame_on(True)
        ax.patch.set_visible(False)
        ax.spines["left"].set_visible(False)
        for sp in ax.spines.itervalues():
            sp.set_visible(False)

    def _on_label_checkbox(self, event):
        for i in xrange(0,8):
            self._graphs[i].set_visible(self._value_on_checkboxes[i].isChecked());
            if self._value_on_checkboxes[i].isChecked():
                vc.variable.set("ui-show-value-" + str(i), "1");
            else:
                vc.variable.set("ui-show-value-" + str(i), "0");
        self._update_spines()

        self._canvas.draw()
        self._background = None

    def _on_figure_motion(self, event):
        print event
        if event.inaxes == None:
            return

        self._motion_wait -= 1
        if self._motion_wait > 0:
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
            lineh = self._graphs[7].axhline(y=event.ydata, linewidth=1, color="#000000", alpha=0.5)
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
            polygon = Rectangle((start, 0), width, y1 + 10000, facecolor=col, alpha=0.5)
            self._graphs[0].add_patch(polygon)
            self._graphs[0].draw_artist(polygon)

        self._figure.canvas.blit(self._graphs[0].bbox)
        if self._select_start == None:
            linev.remove()
            lineh.remove()
        if polygon != None:
            polygon.remove()

        for i in xrange(0, 8):
            if (i < 2):
                val = str(self._data[i][index])
            else:
                val = str(int(self._data[i][index]))                    
            self._mouse_texts[i].setText(val)

    def _on_figure_press(self, event):
        if event.button == 3:
            self._update_min_max(0, self.duration)
            self._background =  None
            self._graphs[0].set_xlim(0, self.duration)
            self._canvas.draw()

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
        self._select_start = None
        self._background = None

    def resizeEvent(self, event):
        self._background = None

    # Param start, end are seconds
    def _update_min_max(self, start, end):
        number_of_points = len(self._plots[0].get_ydata());
        index1 = int(number_of_points * start / self.duration);
        index2 = int(number_of_points * end / self.duration);

        if index2 >= len(self._data[0]):
            index2 = len(self._data[0]) - 1

        for i in xrange(0, 8):
            m = max(self._data[i][index1:index2])
            if (i < 2):
                m =  "{0:.1f}".format(round(m,1))
            else:
                m = int(m)
            self._max_texts[i].setText(str(m))

            m = min(self._data[i][index1:index2])
            if (i < 2):
                m =  "{0:.1f}".format(round(m,1))
            else:
                m = int(m)
            self._min_texts[i].setText(str(m))

        for i in xrange(0, 8):
            if i == 5:
                continue
            m = reduce(lambda x, y: x + y, self._data[i][index1:index2]) / len(self._data[i][index1:index2])
            if (i < 2):
                m =  "{0:.1f}".format(round(m,1))
            else:
                m = int(m)
            self._avarage_texts[i].setText(str(m))

        m = int((max(self._data[5][index1:index2]) - min(self._data[5][index1:index2])) / (self._data[-1][index2] - self._data[-1][index1]) * 60)
        self._avarage_texts[5].setText(str(m) + "/min")

    def _on_screenshot(self):
        if (self._background):  
            self._figure.canvas.restore_region(self._background)

        self.ui.push_buttton_screenshot.hide()
        vc.screenshot.grab(self)
        self.ui.push_buttton_screenshot.show()

    def merge_ui_gps_log(self, uilog, gpslog):
        data = uilog["data"]
        for j in xrange(len(uilog["data"])):
            row = uilog["data"][j]

            if gpslog is not None:
                timestamp_ui_row = row["sec"] + uilog["start"]
                nearest_timestamp = None
                nearest_index = -1
                for i in xrange(len(gpslog["data"])):
                    row_gps = gpslog["data"][i]
                    timestamp_gps_row = row_gps["sec"] + gpslog["start"]
                    if nearest_index == -1 or abs(timestamp_ui_row - timestamp_gps_row) < nearest_timestamp:
                        nearest_timestamp = abs(timestamp_ui_row - timestamp_gps_row)
                        nearest_index = i
                data[j]["height"] = gpslog["data"][nearest_index]["height"]
                data[j]["speed"] = gpslog["data"][nearest_index]["speed"]
            else:
                data[j]["height"] = 0
                data[j]["speed"] = 0
        return data




