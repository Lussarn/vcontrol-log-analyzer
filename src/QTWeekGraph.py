"""
Weekly graph window
"""
__author__ = "linus.larsson@gmail.com"

from numpy import arange, sin, pi, arange
import matplotlib
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg  as Canvas
import matplotlib.pyplot as plt

from numpy import arange
from matplotlib.figure import Figure
from sets import Set
from matplotlib.ticker import FixedLocator
from PySide import QtGui, QtCore




class WeekGraph(Canvas):
    def __init__(self, parent, analyzer, factor, font_factor):
        self.factor = factor
        self.font_factor = font_factor
        self._analyzer = analyzer
        Canvas.__init__(self, Figure())

        self.figure = Figure()
        self.canvas = Canvas(self.figure)        
        self.figure._axes = None

    def update_graph(self, start_date, end_date, model_id, battery_id, stack_as):
        if (self.figure._axes != None):
            self.figure._axes.clear()

        self.figure.set_facecolor("white")
        self.figure._axes = self.figure.add_subplot(111)

        self.figure._axes.text(
            .5,
            1.05,
            "Cycles / week",
            horizontalalignment="center",
            transform=self.figure._axes.transAxes,
            fontsize=16*self.font_factor)

        self.figure.subplots_adjust(
            left= 0.05, 
            right= 0.95 , 
            top=0.9, bottom=0.15)
        self.figure._axes.xaxis.set_tick_params(width=0)
        self.figure._axes.yaxis.grid(True)
        self.figure._axes.yaxis.set_label_text("Cycles", fontsize=12*self.font_factor)

        self.figure._axes.text(
            .5,
            -0.15,
            "Week",
            horizontalalignment="center",
            transform=self.figure._axes.transAxes,
            fontsize=12*self.font_factor)

        data = self._analyzer.extract_to_weeks(
            battery_id=battery_id, 
            model_id=model_id, 
            start_date=start_date, 
            end_date=end_date, 
            group=stack_as
        )

        if len(data["data"]) == 0:
            data["data"].append({"week": "00     ", "group": {}})
        bar_index = 0
        ticks = []

        # Setup colors, massage the data to percent
        colors_all = list(reversed([
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
        for color_index in range(len(colors_all)):
            r, g, b = colors_all[color_index]
            colors_all[color_index] = (r / 255., g / 255., b / 255.)

        colors = colors_all
        name_colors = {}
        # Loop all bars
        for week in data["data"]:
            # Draw one bar
            bottom = 0
            # Name is model OR battery name depending on grouping
            for name in week["group"]:
                cycles = week["group"][name]

                # Assign a color to a name
                if name in name_colors:
                    color = name_colors[name]
                    # No legend (box with name if already present)
                    legend = None
                else:
                    # Wrap around if we are out of colors
                    if len(colors) == 0:
                        colors = colors_all
                    color = colors.pop()
                    name_colors[name] = color
                    legend = name

                self.figure._axes.bar(
                    left=bar_index, 
                    height=cycles, 
                    width=0.8, 
                    bottom=bottom, 
                    color=color,
                    orientation="vertical",
                    label=legend
                )
                bottom += cycles

            ticks.append(week["week"][2:])
            bar_index += 1

        # Legends
        handles, labels = self.figure._axes.get_legend_handles_labels()
        if len(data["data"]) > 1:
            self.figure._axes.legend(prop={"size": 11*self.font_factor}, frameon=False)

        keep = []
        for k in arange(0, len(ticks), float(len(ticks)) / 53):
            keep.append(int(round(k)))

        keep = Set(keep)

        for i in xrange(len(ticks)):
            if not i in keep:
                ticks[i] = ""

        self.figure._axes.xaxis.set_major_locator(FixedLocator(arange(0.4,len(ticks), 1)))
        self.figure._axes.set_xticklabels(ticks, rotation=90, fontsize=8*self.font_factor)
        self.figure._axes.set_xlim(-0.5, len(ticks) + 0.5)

        self.draw()
