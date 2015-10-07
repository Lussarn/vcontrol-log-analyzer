"""
Weekly graph window
"""
__author__ = "linus.larsson@gmail.com"

from numpy import arange
from matplotlib.figure import Figure
from sets import Set
from matplotlib.ticker import FixedLocator

class WeekGraph(Figure):
    def __init__(self, main_window, analyzer):
        self._main_window = main_window
        self._analyzer = analyzer
        Figure.__init__(self)
        self._axes = None

    def update(self, start_date, end_date, model_id, battery_id, stack_as):
        if (self._axes != None):
            self._axes.clear()

        self.set_facecolor("white")
        self._axes = self.add_subplot(111)

        self._axes.text(
            .5,
            1.05,
            _("Cycles / week").decode("utf8"),
            horizontalalignment="center",
            transform=self._axes.transAxes,
            fontsize=16)

        self.subplots_adjust(
            left= 0.05, 
            right= 0.95 , 
            top=0.9, bottom=0.15)
        self._axes.xaxis.set_tick_params(width=0)
        self._axes.yaxis.grid(True)
        self._axes.yaxis.set_label_text(_("Cycles").decode("utf8"), fontsize=12)

        self._axes.text(
            .5,
            -0.15,
            _("Week").decode("utf8"),
            horizontalalignment="center",
            transform=self._axes.transAxes)

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

                self._axes.bar(
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
        handles, labels = self._axes.get_legend_handles_labels()
        if len(data["data"]) > 1:
            self._axes.legend(prop={"size": 11}, frameon=False)

        keep = []
        for k in arange(0, len(ticks), float(len(ticks)) / 53):
            keep.append(int(round(k)))

        keep = Set(keep)

        for i in xrange(len(ticks)):
            if not i in keep:
                ticks[i] = ""

        self._axes.xaxis.set_major_locator(FixedLocator(arange(0.4,len(ticks), 1)))
        self._axes.set_xticklabels(ticks, rotation=90, fontsize=8)
        self._axes.set_xlim(-0.5, len(ticks) + 0.5)
        
        self.canvas.draw()
