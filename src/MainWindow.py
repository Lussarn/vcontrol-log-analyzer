"""
Main window
"""
__author__ = "linus.larsson@gmail.com"

from numpy import arange, sin, pi, arange
import matplotlib
matplotlib.use("WXAgg")
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas

import math
import wx
import wx.grid
import os
import datetime
from wx.lib.wordwrap import wordwrap

import vc.util
import vc.variable
import vc.globals
import vc.backend
from UILogWindow import UILogWindow
from VBLogWindow import VBLogWindow
from ModelInfoWindow import ModelInfoWindow
from WeekGraph import WeekGraph

class SessionGridCellRenderer(wx.grid.PyGridCellRenderer):
    def __init__(self, draw_icon, have_log):
        self._note_bitmap = wx.Bitmap(vc.util.resource_path("assets/img/icon-note16.png"), wx.BITMAP_TYPE_ANY);
        self._bullet_bitmap = wx.Bitmap(vc.util.resource_path("assets/img/icon-bullet16.png"), wx.BITMAP_TYPE_ANY);
        self._draw_icon = draw_icon
        self._have_log = have_log
        super(SessionGridCellRenderer, self).__init__()

    def Draw(self, grid, attr, dc, rect, row, col, isSelected):
        if not isSelected:
            background_brush = wx.Brush(attr.GetBackgroundColour())
        else:
            background_brush = wx.Brush(grid.GetSelectionBackground())

        dc.SetBrush(background_brush)
        dc.DrawRectangle(rect.X, rect.Y, rect.Width, rect.Height)
        if self._draw_icon:
            dc.DrawBitmap(self._note_bitmap, rect.X + 1, rect.Y + 1)
        if self._have_log:
            dc.DrawBitmap(self._bullet_bitmap, rect.X + 20, rect.Y + 1)

    def GetBestSize(self, grid, attr, dc, row, col):
        return wx.Size(18, 18)

    def Clone(self):
        return SessionGridCellRenderer()

class MainWindow(wx.Frame):
    def __init__(self):
        self._analyzer = vc.backend.Analyzer(self.import_callback)

        # Models and batteries structure
        self._gear = None

        # battery id
        self._battery_selected = None

        # Model id
        self._model_selected = None

        # Model id
        self._model_thumb_id = None

        # Open model windows
        self.model_info_windows = {}

        self._grid_data = None

        seasons = self._analyzer.get_seasons()

        width = int(vc.variable.get("gui-window-width", "1024"))
        height = int(vc.variable.get("gui-window-height", "600"))

        wx.Frame.__init__(self, None, title=vc.globals.PROGRAM_NAME + " " + vc.globals.VERSION, size=(width, height))
        # WX Frame function
        self.CreateStatusBar()

        # Creating the menubar.
        menu_bar = wx.MenuBar()

        # File menu
        file_menu = wx.Menu()
        import_menu = file_menu.Append(wx.NewId(), _("Import from VBar Control").decode("utf-8"), _("Import from VBar Control").decode("utf-8"))
        about_menu = file_menu.Append(wx.ID_ABOUT, _("About flight analyzer").decode("utf8"), _("Information about VBar Control flight analyzer").decode("utf8"))
        exit_menu = file_menu.Append(wx.ID_EXIT, _("Exit").decode("utf8"), _("Terminate the program").decode("utf8"))
        menu_bar.Append(file_menu, _("File").decode("utf8"))
        self.SetMenuBar(menu_bar)

        # Menu Events
        self.Bind(wx.EVT_MENU, self._on_exit, exit_menu)
        self.Bind(wx.EVT_MENU, self._on_about, about_menu)
        self.Bind(wx.EVT_MENU, self._on_import, import_menu)
        main_vertical_sizer = wx.BoxSizer(wx.VERTICAL)

        top_panel = wx.Panel(self)
        self._top_horizontal_sizer = wx.BoxSizer(wx.HORIZONTAL)
        top_panel.SetSizer(self._top_horizontal_sizer)

        # Season panel
        season_panel = wx.Panel(top_panel, -1)
        self._top_horizontal_sizer.Add(season_panel, 0, wx.ALL, 5)
        season_vertical_sizer = wx.BoxSizer(wx.VERTICAL)
        season_panel.SetSizer(season_vertical_sizer)

        # Season
        season_vertical_sizer.Add(wx.StaticText(season_panel, label=_("Season").decode("utf8")), 0, wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT | wx.TOP, 5)
        self._season_combo_box = wx.ComboBox(season_panel, choices=[_("All seasons").decode("utf8")] + seasons, size=(146,20))
        self._season_combo_box.SetEditable(False)
        self._season_combo_box.SetStringSelection(seasons[-1])
        season_vertical_sizer.Add(self._season_combo_box, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        self._season_combo_box.Bind(wx.EVT_COMBOBOX, self._on_season_changed)

        # Model image, add it to season panel
        self._thumb_bitmap_button = wx.BitmapButton(
            season_panel, 
            -1, 
            wx.Bitmap(vc.util.resource_path("assets/img/icon-helicopter.png"), wx.BITMAP_TYPE_ANY), 
            pos=(0, 0)
        )
        season_vertical_sizer.Add(self._thumb_bitmap_button, 0, wx.ALIGN_CENTER | wx.ALIGN_BOTTOM)
        self.Bind(wx.EVT_BUTTON, self._on_model_info, self._thumb_bitmap_button)
        self._thumb_bitmap_button.Hide()

        # Model panel
        model_panel = wx.Panel(top_panel, -1, style=wx.BORDER_RAISED)
        model_vertical_sizer = wx.BoxSizer(wx.VERTICAL)
        model_vertical_sizer.Add(wx.StaticText(model_panel, label=_("Model").decode("utf8")), 0, wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT | wx.TOP, 5)
        self._model_list_box = wx.ListBox(model_panel, size=(200,100))
        model_vertical_sizer.Add(self._model_list_box, 0, wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        model_panel.SetSizer(model_vertical_sizer)
        self._top_horizontal_sizer.Add(model_panel, 0, wx.ALIGN_LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM, 5)
        self._model_list_box.Bind(wx.EVT_LISTBOX, self._on_select_model)

        # Battery panel
        battery_panel = wx.Panel(top_panel, -1, style=wx.BORDER_RAISED)
        battery_vertical_sizer = wx.BoxSizer(wx.VERTICAL)
        battery_vertical_sizer.Add(wx.StaticText(battery_panel, label=_("Battery").decode("utf8")), 0, wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT | wx.TOP, 5)
        self._battery_list_box = wx.ListBox(battery_panel, size=(200,100))
        battery_vertical_sizer.Add(self._battery_list_box, 0, wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        battery_panel.SetSizer(battery_vertical_sizer)
        self._top_horizontal_sizer.Add(battery_panel, 0, wx.ALIGN_LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM, 5)
        self._battery_list_box.Bind(wx.EVT_LISTBOX, self._on_select_battery)

        # Extra GUI data
        _extra_panel = wx.Panel(top_panel, -1)
        self._extra_vertical_sizer = wx.BoxSizer(wx.VERTICAL)
        _extra_panel.SetSizer(self._extra_vertical_sizer)
        self._top_horizontal_sizer.Add(_extra_panel, 0, wx.ALL, 5)

        # Stack / Used for the weekly graph
        self._stack_panel = wx.Panel(_extra_panel, -1)
        stack_vertical_sizer = wx.BoxSizer(wx.VERTICAL)
        self._stack_panel.SetSizer(stack_vertical_sizer)
        stack_vertical_sizer.Add(wx.StaticText(self._stack_panel, label=_("Stack graph as").decode("utf8")), 0, wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT | wx.TOP, 5)
        self._stack_model_radio_button = wx.RadioButton(self._stack_panel, 0, _("Model").decode("utf8"), style = wx.RB_GROUP)
        self._stack_battery_radio_button = wx.RadioButton(self._stack_panel, 0, _("Battery").decode("utf8"))
        self._stack_model_radio_button.SetValue(True)
        self._stack_weekly_graph_as = "model"
        stack_vertical_sizer.Add(self._stack_model_radio_button,  1, wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.TOP, 5)
        stack_vertical_sizer.Add(self._stack_battery_radio_button,  1, wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        self._extra_vertical_sizer.Add(self._stack_panel, 0, wx.ALL, 5)
        self._stack_model_radio_button.Bind(wx.EVT_RADIOBUTTON, self._on_select_stack_as)
        self._stack_battery_radio_button.Bind(wx.EVT_RADIOBUTTON, self._on_select_stack_as)

        # Short flights
        self._short_flights_panel = wx.Panel(_extra_panel, -1)
        short_flights_panel = wx.BoxSizer(wx.VERTICAL)
        self._short_flights_panel.SetSizer(short_flights_panel)
        short_flights_panel.Add(wx.StaticText(self._short_flights_panel, label=_("Show logs").decode("utf8")), 0, wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT | wx.TOP, 5)
        self._flights_short_radio_button = wx.RadioButton(self._short_flights_panel, 0, _("Only more than 1/4 capacity used").decode("utf8"), style = wx.RB_GROUP)
        self._flights_all_radio_button = wx.RadioButton(self._short_flights_panel, 0, _("All logs").decode("utf8"))
        self._flights_short_radio_button.SetValue(True)
        self._show_all_flights = False
        short_flights_panel.Add(self._flights_short_radio_button,  1, wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.TOP, 5)
        short_flights_panel.Add(self._flights_all_radio_button,  1, wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        self._extra_vertical_sizer.Add(self._short_flights_panel, 0, wx.ALL, 5)
        self._flights_short_radio_button.Bind(wx.EVT_RADIOBUTTON, self._on_select_short_flights)
        self._flights_all_radio_button.Bind(wx.EVT_RADIOBUTTON, self._on_select_short_flights)

        self._stack_panel.Hide()
        self._short_flights_panel.Hide()
        self._extra_vertical_sizer.Layout()

        # Connection status
        stretch_panel = wx.Panel(top_panel, -1)
        stretch_vertical_sizer = wx.BoxSizer(wx.VERTICAL)
        stretch_panel.SetSizer(stretch_vertical_sizer)
        self._top_horizontal_sizer.Add(stretch_panel, 1, wx.EXPAND)
        connection_panel = wx.Panel(stretch_panel, -1)
        connection_vertical_sizer = wx.BoxSizer(wx.VERTICAL)
        connection_panel.SetSizer(connection_vertical_sizer)
        stretch_vertical_sizer.Add(connection_panel, 1, wx.ALIGN_RIGHT | wx.LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM, 5)
        connection_vertical_sizer.Add(wx.StaticText(connection_panel, label=_("Connection status").decode("utf8")), 0, wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM, 5)
        self._connection_static_bitmap = wx.StaticBitmap(connection_panel, bitmap=wx.Bitmap(vc.util.resource_path("assets/img/ball-red.png"), wx.BITMAP_TYPE_ANY))
        connection_vertical_sizer.Add(self._connection_static_bitmap, 0, wx.CENTER)

        # Add top panel to main vertical sizer
        main_vertical_sizer.Add(top_panel, 0, wx.EXPAND)

        # Notebook
        notebook = wx.Notebook(self)

        # Grid
        grid_panel = wx.Panel(notebook)
        grid_vertical_sizer = wx.BoxSizer(wx.VERTICAL)
        grid_panel.SetSizer(grid_vertical_sizer)
        notebook.AddPage(grid_panel, _("Data").decode("utf8"))

        self._grid = wx.grid.Grid(grid_panel)
        self._grid.CreateGrid(10, 12)

        self._grid.ClipHorzGridLines(False)
        self._grid.ClipVertGridLines(False)
        self._grid.HideRowLabels()
        self._grid.EnableEditing(False)
        self._grid.SetDefaultCellOverflow(False)
        self._grid.SetUseNativeColLabels(True)
        self._grid.EnableGridLines(False)
        self._grid.SetCellHighlightPenWidth(0)
        self._grid.DisableDragRowSize()
        self._grid.SetSelectionMode(wx.grid.Grid.wxGridSelectRows)

        self._grid.SetColLabelAlignment(wx.ALIGN_LEFT, wx.ALIGN_CENTRE)
        self._grid.SetColLabelValue(0, "Id")
        self._grid.SetColLabelValue(1, _("Date").decode("utf8"))
        self._grid.SetColLabelValue(2, _("Battery").decode("utf8"))
        self._grid.SetColLabelValue(3, _("Model").decode("utf8"))
        self._grid.SetColLabelValue(4, _("Duration").decode("utf8"))
        self._grid.SetColLabelValue(5, _("Capacity").decode("utf8"))
        self._grid.SetColLabelValue(6, _("Used").decode("utf8"))
        self._grid.SetColLabelValue(7, _("MinV").decode("utf8"))
        self._grid.SetColLabelValue(8, _("MaxA").decode("utf8"))
        self._grid.SetColLabelValue(9, _("IdleV").decode("utf8"))
        self._grid.SetColLabelValue(10, _("VBLog").decode("utf8"))
        self._grid.SetColLabelValue(11, _("UILog").decode("utf8"))

        grid_vertical_sizer.Add(self._grid, 1, wx.EXPAND)

        self._grid.Bind(wx.grid.EVT_GRID_SELECT_CELL, self._on_grid_select)
        self._grid.Bind(wx.grid.EVT_GRID_RANGE_SELECT, self._on_grid_range_select)

        # Week graph
        week_graph_panel = wx.Panel(notebook)
        week_graph_vertical_sizer = wx.BoxSizer(wx.VERTICAL)
        week_graph_panel.SetSizer(week_graph_vertical_sizer)
        notebook.AddPage(week_graph_panel, _("Weekly flights").decode("utf8"))
        self._week_graph = WeekGraph(self, self._analyzer)
        week_graph_vertical_sizer.Add(
            FigureCanvas(week_graph_panel, 
            -1,
            self._week_graph),
            1,
            wx.LEFT | wx.TOP | wx.GROW
        )

        # Add notebook
        main_vertical_sizer.Add(notebook, 1, wx.EXPAND)
        notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self._on_notebook_changed)

        self.SetSizer(main_vertical_sizer)
        main_vertical_sizer.Fit(self)
        self.SetSize(wx.Size(width, height))

        TIMER_ID = 100
        self.timer = wx.Timer(self, TIMER_ID)
        self.timer.Start(1000)
        wx.EVT_TIMER(self, TIMER_ID, self._on_connection_timer)

        self._vcontrol_connected = False

        self.populate_grid()
        self.populate_gear()

        self.Show()
        self._short_flights_panel.Show()
        self._stack_panel.Hide()
        self._extra_vertical_sizer.Layout()
        self._top_horizontal_sizer.Layout()
        self.Bind(wx.EVT_SIZE, self._on_resize_window)

    def _on_resize_window(self,event):
        vc.variable.set("gui-window-width", str(event.GetSize()[0]))
        vc.variable.set("gui-window-height", str(event.GetSize()[1]))
        event.Skip()

    def _on_notebook_changed(self, event):
        if event.GetSelection() == 0:
            self._stack_panel.Hide()
            self._short_flights_panel.Show()
        elif event.GetSelection() == 1:
            self._short_flights_panel.Hide()
            self._stack_panel.Show()
        self._extra_vertical_sizer.Layout()
        event.Skip()

    def _on_select_stack_as(self, event):
        if event.GetEventObject() == self._stack_model_radio_button:
            self._stack_weekly_graph_as = "model"
        else:
            self._stack_weekly_graph_as = "battery"
        self.populate_grid()        

    def _on_select_short_flights(self, event):
        if event.GetEventObject() == self._flights_short_radio_button:
            self._show_all_flights = False
        else:
            self._show_all_flights = True
        self.populate_grid()

    def _on_season_changed(self, event):
        self._battery_selected = None
        self._model_selected = None
        self.populate_grid()        
        self.populate_gear()

    def _on_select_battery(self, event):
        if (event.GetSelection() == 0):
            self._battery_selected = None
        else:
            self._battery_selected = self._gear["batteries"][event.GetSelection() - 1]["id"]
        self.populate_grid()
        self._model_thumb_id = None
        self._thumb_bitmap_button.Hide()
        self._top_horizontal_sizer.Layout()

    def _on_select_model(self, event):
        if (event.GetSelection() == 0):
            self._model_selected = None
        else:
            self._model_selected = self._gear["models"][event.GetSelection() - 1]["id"]
        self.populate_grid()

        if self._model_selected is None:
            self._model_thumb_id = None
            self._thumb_bitmap_button.Hide()
        else:
            for index, model in enumerate(self._gear["models"]):
                if (model["id"] == self._model_selected):
                    self._thumb_bitmap_button.SetBitmapLabel(
                        self._gear["models"][index]["thumb"]
                    )
            self._thumb_bitmap_button.Show()
            self._model_thumb_id = self._model_selected
        self._top_horizontal_sizer.Layout()

    def _on_grid_select(self, event):
        row = event.GetRow()
        sx, sy = self._grid.GetCellSize(row, 1) 

        if sy != 1:
            if self._model_selected is None:
                self._model_thumb_id = None
                self._thumb_bitmap_button.Hide()
            self._top_horizontal_sizer.Layout()
            self._grid.ClearSelection()

            if (event.GetCol() == 0):
                if self._model_selected is not None:
                    if self._model_selected not in self.model_info_windows:
                        self.model_info_windows[self._model_selected] = ModelInfoWindow(self._model_selected, self._analyzer, self)
                    else:
                        self.model_info_windows[self._model_selected].Iconize(False)
                        self.model_info_windows[self._model_selected].Raise()
                    self.model_info_windows[self._model_selected].insert_date(self._grid.GetCellValue(row, 1))

            return

        if (self._gear != None):
            for model in self._gear["models"]:
                if model["name"] == self._grid.GetCellValue(row, 3):
                    self._thumb_bitmap_button.SetBitmapLabel(model["thumb"])
                    self._thumb_bitmap_button.Show()
                    self._model_thumb_id = model["id"]
                    break
        self._top_horizontal_sizer.Layout()

        col = event.GetCol()
        if col < 10:
            return
        if self._grid.GetCellValue(row, col) != _("Show").decode("utf8"):
            return
        log_id = self._grid.GetCellValue(row, 0)
        if (col == 11):
            frame = UILogWindow(log_id, self._analyzer)
        if (col == 10):
            frame = VBLogWindow(log_id, self._analyzer)

    def _on_grid_range_select(self, event):
        rows = self._grid.GetSelectedRows()
        if len(rows) > 1:
            row = rows[0]
            self._grid.SelectRow(row)
            self._thumb_bitmap_button.Hide()
            self._model_thumb_id = 0
            for model in self._gear["models"]:
                if model["name"] == self._grid.GetCellValue(row, 3):
                    self._thumb_bitmap_button.SetBitmapLabel(model["thumb"])
                    self._thumb_bitmap_button.Show()
                    self._model_thumb_id = model["id"]
                    break
            self._top_horizontal_sizer.Layout()
            return

    def _on_about(self,event):
        info = wx.AboutDialogInfo()
        info.SetIcon(wx.Icon(vc.util.resource_path("assets/img/vfc-logo-small.png"), wx.BITMAP_TYPE_PNG))
        info.Name = vc.globals.PROGRAM_NAME
        info.Version = vc.globals.VERSION
        info.Copyright = "(C) 2015 Linus Larsson"
        info.Description = wordwrap(
            "VBar Control flight analyzer is a "
            "program for tracking flights and telemetry "
            "data  recorded in Mikado VBar Control",
            250, wx.ClientDC(self))
        info.WebSite = ("http://linlar.org/vbc", "http://linlar.org/vbc")
        info.Developers = ["Linus Larsson - linus.larsson@gmail.com"]
        info.License = wordwrap("Apache Licence, v2.0", 500,
        wx.ClientDC(self))
        wx.AboutBox(info)

    def _on_exit(self,e):
        self.Close(True)  # Close the frame.

    def _on_import(self, e):
        if self._analyzer.vcontrol_is_connected() == False:
            dlg = wx.MessageDialog(self, _("Unable to find VBar Control").decode("utf8"), _("VBar Control message").decode("utf8"), wx.OK)
            dlg.ShowModal()
            dlg.Destroy()
            return
        self.SetStatusText(_("Importing from VBar Control, please wait...").decode("utf8"))
        self.Disable()
        self._analyzer.import_data()
        self.Enable()

        seasons = self._analyzer.get_seasons()
        self._season_combo_box.Clear()
        self._season_combo_box.Append(_("All seasons").decode("utf8"))
        for s in seasons:
            self._season_combo_box.Append(s)
        self._season_combo_box.SetStringSelection(seasons[-1])

        self.populate_grid()
        self.populate_gear()

    def _on_model_info(self, event):
        if self._model_thumb_id is None:
            return

        if self._model_thumb_id not in self.model_info_windows:
            self.model_info_windows[self._model_thumb_id] = ModelInfoWindow(self._model_thumb_id, self._analyzer, self)
        else:
            self.model_info_windows[self._model_thumb_id].Iconize(False)
            self.model_info_windows[self._model_thumb_id].Raise()


    def import_callback(self, str):
        self.SetStatusText(_("Importing from VBar Control").decode("utf8") + ": " + str)
        wx.Yield()


    def populate_gear(self):
        self._battery_selected = None
        self._model_selected = None
        self._battery_list_box.Clear()

        season = self._season_combo_box.GetStringSelection()
        if season == _("All seasons").decode("utf8"):
            start_date = datetime.datetime.strptime("1900", "%Y")
            end_date = datetime.datetime.strptime("3000", "%Y")
        else:
            start_date = datetime.datetime.strptime(season, "%Y")
            end_date = datetime.datetime.strptime(str(int(season) + 1), "%Y")

        self._gear = self._analyzer.get_gear(start_date, end_date)

        self._battery_list_box.Clear()
        self._battery_list_box.Append(_("All batteries").decode("utf8"))
        for index, battery in enumerate(self._gear["batteries"]):
            self._battery_list_box.Append(self._gear["batteries"][index]["name"])
        self._battery_list_box.Select(0)
        self._battery_list_box.EnsureVisible(0)

        self._model_list_box.Clear()
        self._model_list_box.Append(_("All models").decode("utf8"))
        for index, model in enumerate(self._gear["models"]):
            self._model_list_box.Append(self._gear["models"][index]["name"])
        self._model_list_box.Select(0)
        self._model_list_box.EnsureVisible(0)

        self._model_thumb_id = None
        self._thumb_bitmap_button.Hide()
        self._top_horizontal_sizer.Layout()

    def update_gear(self, type, id, data):
        if type == "model":
            type = "models"
        if type == "battery":
            type = "batteries"

        for index, gear in enumerate(self._gear[type]):
            if gear["id"] == id:
                for key, value in data.iteritems():
                    self._gear[type][index][key] = value

    def populate_grid(self, reload=True):
        # Grid
        if reload and self._grid.GetNumberRows() > 0:
            self._grid.DeleteRows(0, self._grid.GetNumberRows())

        season = self._season_combo_box.GetStringSelection()
        if season == _("All seasons").decode("utf8"):
            start_date = datetime.datetime.strptime("1900", "%Y")
            end_date = datetime.datetime.strptime("3000", "%Y")
        else:
            start_date = datetime.datetime.strptime(season, "%Y")
            end_date = datetime.datetime.strptime(str(int(season) + 1), "%Y")

        if reload:
            self._grid_data = self._analyzer.extract(
                battery_id=self._battery_selected, 
                model_id=self._model_selected, 
                start_date=start_date, 
                end_date=end_date, 
                all_flights=self._show_all_flights
            )

        row_index = 0
        start_date = None
        old_session = 0
        row_color_index = 0
        for d in list(reversed(self._grid_data["data"])):

            flight_date = str(d["date"][0:10])

            if d["session"] != old_session:

                session_have_flight_log = False
                if self._model_selected is not None:
                    # Find out if model has flight log
                    for index, model in enumerate(self._gear["models"]):
                        if model["name"] == d["model"]:
                            search_date = "## " + flight_date + " ##"
                            if model["info"].find(search_date) >= 0:
                                session_have_flight_log = True
                            break

                if reload:
                    self._grid.InsertRows(row_index, 1)

                self._grid.SetCellRenderer(
                    row_index, 
                    0, 
                    SessionGridCellRenderer(
                        draw_icon=self._model_selected is not None, 
                        have_log=session_have_flight_log
                    )
                )

                self._grid.SetCellValue(row_index, 1, flight_date);
                self._grid.SetCellSize(row_index, 1, 1, 11);
                self._grid.SetCellAlignment(row_index, 1, wx.ALIGN_CENTRE, wx.ALIGN_CENTRE);
                self._grid.SetCellTextColour(row_index, 1, "#ffffff")

                attr = wx.grid.GridCellAttr();
                attr.SetBackgroundColour("#1F77B4")
                self._grid.SetRowAttr(row_index, attr)
                row_color_index = 0
                row_index += 1

            if reload:
                self._grid.InsertRows(row_index, 1)

            self._grid.SetCellValue(row_index,0, str(d["id"]))
            self._grid.SetCellValue(row_index,1, d["date"])
            self._grid.SetCellValue(row_index,2, d["battery"])
            self._grid.SetCellValue(row_index,3, d["model"])
            self._grid.SetCellValue(row_index,4, d["duration"])
            self._grid.SetCellValue(row_index,5, str(d["capacity"]))
            self._grid.SetCellValue(row_index,6, d["used"])
            self._grid.SetCellValue(row_index,7, str(d["minv"]))
            self._grid.SetCellValue(row_index,8, str(d["maxa"]))
            self._grid.SetCellValue(row_index,9, str(d["idlev"]))
            self._grid.SetCellValue(row_index,10, _("Show").decode("utf8") if str(d["havevbarlog"]) == "1" else "")
            self._grid.SetCellValue(row_index,11, _("Show").decode("utf8") if str(d["haveuilog"]) == "1" else "")

            attr = wx.grid.GridCellAttr();
            if row_color_index % 2 == 0:
                attr.SetBackgroundColour(wx.Colour(255,255,255))
            else:
                attr.SetBackgroundColour(wx.Colour(200,200,200))
            self._grid.SetRowAttr(row_index, attr)

            if d["havevbarlogproblem"] == 1:
                if row_color_index % 2 == 0:
                    self._grid.SetCellBackgroundColour(row_index, 10, "#ffaaaa")
                else:
                    self._grid.SetCellBackgroundColour(row_index, 10, "#c86666")

            self._grid.SetCellTextColour(row_index, 10, "#0000ff") 
            self._grid.SetCellTextColour(row_index, 11, "#0000ff") 
            row_color_index += 1
            row_index += 1

            start_date = d["date"]
            old_session = d["session"]

        self._grid.AutoSizeColumns(100)
        for row_index in range(0, 12):
            self._grid.SetColSize(row_index, self._grid.GetColSize(row_index) + 20)

        self.SetStatusText(
            _("Cycles").decode("utf8") + ": " + str(self._grid_data["totals"]["cycles"]) + "   " + 
            _("Used capacity").decode("utf8") + ": " + str(self._grid_data["totals"]["used"]) + "Ah   " + 
            _("Duration").decode("utf8") + ": " +str(self._grid_data["totals"]["duration"]) + "   " + 
            _("Sessions") + ": " + str(self._grid_data["totals"]["sessions"]))

        self._week_graph.update(
            start_date=start_date, 
            end_date=end_date, 
            battery_id=self._model_selected, 
            model_id=self._battery_selected,
            stack_as=self._stack_weekly_graph_as
        )

    def _on_connection_timer(self, event):
        if self._analyzer.vcontrol_is_connected():
            if self._vcontrol_connected == True:
                return
            self._vcontrol_connected = True
            self._connection_static_bitmap.SetBitmap(wx.Bitmap(vc.util.resource_path("assets/img/ball-green.png"), wx.BITMAP_TYPE_ANY))
        else:
            if self._vcontrol_connected == False:
                return
            self._vcontrol_connected = False
            self._connection_static_bitmap.SetBitmap(wx.Bitmap(vc.util.resource_path("assets/img/ball-red.png"), wx.BITMAP_TYPE_ANY))

    def _pydate2wxdate(self, date):
        tt = date.timetuple()
        dmy = (tt[2], tt[1]-1, tt[0])
        return wx.DateTimeFromDMY(*dmy)
 
    def _wxdate2pydate(self, date):
        if date.IsValid():
            ymd = map(int, date.FormatISODate().split("-"))
            return datetime.date(*ymd)
        else:
            return None
