import matplotlib
matplotlib.use("Qt4Agg")
matplotlib.rcParams['backend.qt4'] = 'PySide'

import PySide
from PySide import QtCore, QtGui
import math
import os
import datetime

import vc.util
import vc.variable
import vc.globals
import vc.backend

from QTWeekGraph import WeekGraph
from QTTelemetryWindow import QTTelemetryWindow
from QTModelWindow import QTModelWindow
from QTLogWindow import QTLogWindow
from QTAboutDialog import QTAboutDialog
from KMLExport import KMLExport

from ImportThread import ImportThread

from qtui.QTDMainWindow import Ui_QTDMainWindow

class NoteWidget(QtGui.QWidget):
  
    def __init__(self, draw_icon, have_log, factor):
        self.factor = factor
        self._note_bitmap = vc.util.load_pixmap("note.png", factor)
        self._bullet_bitmap = vc.util.load_pixmap("bullet.png", factor)
        self._draw_icon = draw_icon
        self._have_log = have_log

        super(NoteWidget, self).__init__()
        self.initUI()
        
    def initUI(self):        
        pass

    def paintEvent(self, paintEvent):
        qp = QtGui.QPainter()
        qp.begin(self)
        self.drawWidget(qp)
        qp.end()

    def drawWidget(self, qp):    
        qp.fillRect(self.rect(), QtGui.QColor("#1F77B4")); 
        if self._draw_icon:
            qp.drawPixmap(2 * self.factor, 2 * self.factor, self._note_bitmap)
        if self._have_log:
            qp.drawPixmap(20 * self.factor, 2 * self.factor, self._bullet_bitmap)



class WindowMain(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.ui = Ui_QTDMainWindow()
        self.ui.setupUi(self)

        self.factor, self.font_factor = vc.util.rescale(self)

        self._analyzer = vc.backend.Analyzer()
        self.resize(
            int(float(vc.variable.get("gui-window-width", 1100))) * self.factor,
            int(float(vc.variable.get("gui-window-height", 700))) * self.factor
        )
        self.ui.push_button_import.setVisible(False)

        self.pixmap_connection_off = vc.util.load_pixmap("connection-off.png", self.factor)
        self.pixmap_connection_on = vc.util.load_pixmap("connection-on.png", self.factor)

        self.setWindowTitle(vc.globals.PROGRAM_NAME + " " + vc.globals.VERSION)

        # battery id
        self._battery_selected = None

        # Model id
        self._model_selected = None

        self._show_all_flights = False

        self._stack_weekly_graph_as = "model"

        self._model_thumb_id = None

        self._vcontrol_connected = False

        self._import_thread = None

        # Open sub windows
        self.model_windows = {}
        self.telemetry_windows = {}
        self.log_windows = {}

        self.kml_export = KMLExport(self._analyzer)

        # Seasons
        seasons = self._analyzer.get_seasons()
        self.ui.combo_box_season.addItem("All seasons", 0)
        for idx, value in enumerate(seasons):
            self.ui.combo_box_season.addItem(value, idx + 1)
        self.ui.combo_box_season.setCurrentIndex(self.ui.combo_box_season.count()-1)

        # Table headers
        table_headers = ["Id", "Date", "Battery Name", "Model Name", "Flight Time", "Capacity", "Used Capacity", "MinV", "MaxA", "IdleV", "VBLog", "UILog", "KML"]
        self.ui.table_widget_data.setHorizontalHeaderLabels(table_headers)

        for index, width in enumerate([50 * self.factor, 120 * self.factor, 120 * self.factor, 120 * self.factor, 65 * self.factor, 65 * self.factor, 80 * self.factor, 50 * self.factor, 50 * self.factor, 50 * self.factor, 50 * self.factor, 50 * self.factor]):
            self.ui.table_widget_data.setColumnWidth(index, width)

        self.ui.table_widget_data.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignLeft)
        self.ui.table_widget_data.horizontalHeader().setStretchLastSection(True)
        self.ui.table_widget_data.verticalHeader().setDefaultSectionSize(20 * self.factor)

        # Connection
        self.ui.label_image_connection.setPixmap(self.pixmap_connection_off)

        # Signals
        self.ui.list_widget_model.clicked.connect(self._on_select_model)
        self.ui.list_widget_battery.clicked.connect(self._on_select_battery)
        self.ui.combo_box_season.currentIndexChanged.connect(self._on_season_changed)
        self.ui.radio_button_all_flights.toggled.connect(self._on_select_all_flights)
        self.ui.radio_button_stack_as_model.toggled.connect(self._on_select_stack_as_model)
        self.ui.tab_widget.currentChanged.connect(self._on_tab_changed)
        self.ui.table_widget_data.cellClicked.connect(self._on_table_cell_click)
        self.ui.action_menu_import.triggered.connect(self._on_import)
        self.ui.action_menu_about.triggered.connect(self._on_about)
        self.ui.action_menu_exit.triggered.connect(self._on_exit)
        self.ui.push_button_model.clicked.connect(self._on_model_clicked)
        self.ui.push_button_import.clicked.connect(self._on_import)

        # Init weekly graph
        self._week_graph = WeekGraph( self.ui.tab_2, self._analyzer, self.factor, self.font_factor)
        self.ui.horizontal_layout_weekly.addWidget(self._week_graph)

        # Init scan timer
        timer = QtCore.QTimer(self)
        timer.timeout.connect(self._on_connection_timer)

        self.populate_gear()
        self.populate_grid()
        self.show()
        self.raise_()
        timer.start(1000)


    def closeEvent(self, event):
        if self._import_thread is not None:
            event.ignore()
            return
        for key, window in self.telemetry_windows.iteritems():
            try:
                window.hide()
            except:
                pass
        for key, window in self.log_windows.iteritems():
            try:
                window.hide()
            except:
                pass
        for key, window in self.model_windows.iteritems():
            try:
                window.hide()
            except:
                pass
        event.accept()

    def populate_gear(self):
        self._battery_selected = None
        self._model_selected = None

        season = self.ui.combo_box_season.currentText()
        if season == "All seasons":
            start_date = datetime.datetime.strptime("1900", "%Y")
            end_date = datetime.datetime.strptime("3000", "%Y")
        else:
            start_date = datetime.datetime.strptime(season, "%Y")
            end_date = datetime.datetime.strptime(str(int(season) + 1), "%Y")

        self._gear = self._analyzer.get_gear(start_date, end_date, self.factor)

        self.ui.list_widget_battery.clear()
        self.ui.list_widget_battery.addItem("All batteries")
        for battery in self._gear["batteries"]:
            self.ui.list_widget_battery.addItem(battery["name"])

        self.ui.list_widget_model.clear()
        self.ui.list_widget_model.addItem("All models")
        for model in self._gear["models"]:
            self.ui.list_widget_model.addItem(model["name"])
 
        self.ui.list_widget_model.item(0).setSelected(True)
        self.ui.list_widget_battery.item(0).setSelected(True)


        self._model_thumb_id = None
        self.ui.push_button_model.hide()

    def populate_grid(self, reload=True):
        if reload:
            while self.ui.table_widget_data.rowCount() > 0:
                self.ui.table_widget_data.removeRow(0)

        season = self.ui.combo_box_season.currentText()
        if season == "All seasons":
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
                    self.ui.table_widget_data.insertRow(row_index)

                item = NoteWidget(
                    draw_icon=self._model_selected is not None, 
                    have_log=session_have_flight_log,
                    factor=self.factor
                )
                self.ui.table_widget_data.setCellWidget(row_index, 0, item)

                item = QtGui.QTableWidgetItem(flight_date)
                item.setFlags(QtCore.Qt.NoItemFlags)
                item.setTextAlignment(QtCore.Qt.AlignCenter)
                item.setBackground(QtGui.QBrush(QtGui.QColor("#1F77B4")))
                item.setForeground(QtGui.QBrush(QtGui.QColor("#FFFFFF")))
                self.ui.table_widget_data.setItem(row_index, 1, item)
                self.ui.table_widget_data.setSpan(row_index, 1, 1, 12)

                row_color_index = 0
                row_index += 1

            if reload:
                self.ui.table_widget_data.insertRow(row_index)

            cols = [
                str(d["id"]),
                d["date"],
                d["battery"],
                d["model"],
                d["duration"],
                str(d["capacity"]),
                d["used"],
                str(d["minv"]),
                str(d["maxa"]),
                str(d["idlev"]),
                ("Show" if str(d["havevbarlog"]) == "1" else ""),
                ("Show" if str(d["haveuilog"]) == "1" else ""),
                ("Save" if str(d["havegpslog"]) == "1" else ""),
            ]

            if row_color_index % 2 == 0:
                item_color = QtGui.QBrush(QtGui.QColor("#FFFFFF"))
            else:
                item_color = QtGui.QBrush(QtGui.QColor("#C8C8C8"))
            
            for index, value in enumerate(cols):
                item = QtGui.QTableWidgetItem(value)
                item.setBackground(item_color)
                if  d["havevbarlogproblem"] == 1 and index == 10:
                    if row_color_index % 2 == 0:
                        item.setBackground(QtGui.QBrush(QtGui.QColor("#FFAAAA")))
                    else:
                        item.setBackground(QtGui.QBrush(QtGui.QColor("#C86666")))
                if index == 10 or index == 11 or index == 12:
                    item.setForeground(QtGui.QBrush(QtGui.QColor("#0000FF")))
               
                self.ui.table_widget_data.setItem(row_index, index, item)
 
            row_color_index += 1
            row_index += 1
            
            start_date = d["date"]
            old_session = d["session"]


        # Resize columns to content        
        self.ui.table_widget_data.horizontalHeader().setStretchLastSection(False)
        widths = {}
        for index in xrange(0, 13):
            widths[index] = self.ui.table_widget_data.columnWidth(index)
            if index == 11:
                widths[index] = 50 * self.factor

        self.ui.table_widget_data.setVisible(False);
        self.ui.table_widget_data.resizeColumnsToContents();
        for index in xrange(0, 13):
            new_width = self.ui.table_widget_data.columnWidth(index) + (20 * self.factor)
            if new_width < widths[index]:
                new_width = widths[index]
            self.ui.table_widget_data.setColumnWidth(index, new_width)

        self.ui.table_widget_data.setVisible(True);
        self.ui.table_widget_data.horizontalHeader().setStretchLastSection(True)


        self.ui.statusbar.showMessage(
            "Cycles" + ": " + str(self._grid_data["totals"]["cycles"]) + "   " + 
            "Used capacity" + ": " + str(self._grid_data["totals"]["used"]) + "Ah   " + 
            "Flight time" + ": " +str(self._grid_data["totals"]["duration"]) + "   " + 
            "Sessions" + ": " + str(self._grid_data["totals"]["sessions"]))

        self._week_graph.update_graph(
            start_date=start_date, 
            end_date=end_date, 
            model_id=self._model_selected,
            battery_id=self._battery_selected, 
            stack_as=self._stack_weekly_graph_as
        )

    def resizeEvent(self, event):
        vc.variable.set("gui-window-width", str(self.frameGeometry().width() / self.factor))
        vc.variable.set("gui-window-height", str(self.frameGeometry().height() / self.factor))

    def _on_season_changed(self, event):
        self._battery_selected = None
        self._model_selected = None
        self.populate_gear()
        self.populate_grid()

    def _on_select_model(self, event):
        if (event.row() == 0):
            self._model_selected = None
        else:
            self._model_selected = self._gear["models"][event.row() - 1]["id"]
        self.populate_grid()

        if self._model_selected is None:
            self._model_thumb_id = None
            self.ui.push_button_model.hide()
        else:
            for index, model in enumerate(self._gear["models"]):
                if (model["id"] == self._model_selected):
                    self.ui.push_button_model.setIcon(self._gear["models"][index]["thumb"]);
                    self.ui.push_button_model.setIconSize(self._gear["models"][index]["thumb"].rect().size());
            self.ui.push_button_model.show()
            self._model_thumb_id = self._model_selected

    def _on_select_battery(self, event):
        if (event.row() == 0):
            self._battery_selected = None
        else:
            self._battery_selected = self._gear["batteries"][event.row() - 1]["id"]
        self.populate_grid()
        self._model_thumb_id = None
        self.ui.push_button_model.hide()

    def _on_select_all_flights(self, event):
        self._show_all_flights = event
        self.populate_grid()

    def _on_select_stack_as_model(self, event):
        if event:
            self._stack_weekly_graph_as = "model"
        else:
            self._stack_weekly_graph_as = "battery"
        self.populate_grid()        

    def _on_table_cell_click(self, row, column):
        isTitle = column < 2 and self.ui.table_widget_data.columnSpan(row, column + 1) == 11

        if isTitle:
            if self._model_selected is None:
                self._model_thumb_id = None
                self.ui.push_button_model.hide()
            self.ui.table_widget_data.clearSelection()

            if column == 0 and self._model_selected is not None:
                try:
                    self.model_windows[self._model_selected].raise_()
                    self.model_windows[self._model_selected].activateWindow()
                except:
                    self.model_windows[self._model_selected] = QTModelWindow(self._model_selected, self._analyzer, self)
                self.model_windows[self._model_selected].insert_date(self.ui.table_widget_data.item(row, 1).text())
            return

        if (self._gear != None):
            for model in self._gear["models"]:
                if model["name"] == self.ui.table_widget_data.item(row, 3).text():
                    self.ui.push_button_model.setIcon(model["thumb"]);
                    self.ui.push_button_model.setIconSize(model["thumb"].rect().size());
                    self.ui.push_button_model.show()
                    self._model_thumb_id = model["id"]
                    break

        if column < 10:
            return

        log_id = int(self.ui.table_widget_data.item(row, 0).text())
        if (column == 11):
            if self.ui.table_widget_data.item(row, column).text() != "Show":
                return
            try:
                self.telemetry_windows[log_id].raise_()
                self.telemetry_windows[log_id].activateWindow()
            except:
                self.telemetry_windows[log_id] = QTTelemetryWindow(log_id, self._analyzer)

        if (column == 10):
            if self.ui.table_widget_data.item(row, column).text() != "Show":
                return
            try:
                self.log_windows[log_id].raise_()
                self.log_windows[log_id].activateWindow()
            except:
                self.log_windows[log_id] = QTLogWindow(log_id, self._analyzer)

        if (column == 12):
            if self.ui.table_widget_data.item(row, column).text() != "Save":
                return
            self.kml_export.save(log_id)

        return

    def _on_tab_changed(self, index):
        self.ui.stacked_widget_main.setCurrentIndex(index)

    def _on_model_clicked(self):
        if self._model_thumb_id is None:
            return

        try:
            self.model_windows[self._model_thumb_id].raise_()
            self.model_windows[self._model_thumb_id].activateWindow()
        except:
            self.model_windows[self._model_thumb_id] = QTModelWindow(self._model_thumb_id, self._analyzer, self)

    def _on_connection_timer(self):
        if self._analyzer.vcontrol_is_connected():
            if self._vcontrol_connected == True:
                return
            self._vcontrol_connected = True
            self.ui.label_image_connection.setPixmap(self.pixmap_connection_on)
            self.ui.push_button_import.setVisible(True)
        else:
            if self._vcontrol_connected == False:
                return
            self._vcontrol_connected = False
            self.ui.label_image_connection.setPixmap(self.pixmap_connection_off)
            self.ui.push_button_import.setVisible(False)

    def _on_import(self):
        if self._import_thread is not None:
            return
        if self._analyzer.vcontrol_is_connected() == False:
            msg_box = QtGui.QMessageBox()
            msg_box.setIcon(QtGui.QMessageBox.Critical)
            msg_box.setWindowTitle("VBar Control message")
            msg_box.setText("Error: Unable to find VBar Control!\n\nMake sure VBar Control is connected\nand set to USB disk mode")
            msg_box.exec_()
            return
        self.setEnabled(False)
        self.ui.statusbar.showMessage("Importing from VBar Control, please wait...")
        self._import_thread = ImportThread()
        self._import_thread.import_update_signal.sig.connect(self._import_update_callback)
        self._import_thread.import_done_signal.sig.connect(self._import_done)
        self._import_thread.start()

    def _import_update_callback(self, str):
        self.ui.statusbar.showMessage(str)

    def _import_done(self):
        self._import_thread = None
        self.setEnabled(True)

        seasons = self._analyzer.get_seasons()
        self.ui.combo_box_season.blockSignals(True)
        while self.ui.combo_box_season.count() > 0:
            self.ui.combo_box_season.removeItem(0)
        self.ui.combo_box_season.addItem("All seasons", 0)
        for idx, value in enumerate(seasons):
            self.ui.combo_box_season.addItem(value, idx + 1)
        self.ui.combo_box_season.setCurrentIndex(self.ui.combo_box_season.count() - 1)
        self.ui.combo_box_season.blockSignals(False)

        self.populate_gear()
        self.populate_grid()


    def _on_about(self):
        dialog = QTAboutDialog(self)
        dialog.exec_()

    def _on_exit(self):
        if self._import_thread is not None:
            return
        self.close()

    def update_gear(self, type, id, data):
        if type == "model":
            type = "models"
        if type == "battery":
            type = "batteries"

        for index, gear in enumerate(self._gear[type]):
            if gear["id"] == id:
                for key, value in data.iteritems():
                    self._gear[type][index][key] = value


if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    try:
        WINDOW_ICON = QtGui.QPixmap(vc.util.resource_path("assets/logo/logo256.png"))
        app.setWindowIcon(WINDOW_ICON)
        window = WindowMain()
        sys.exit(app.exec_())
    except Exception:
        import traceback
        var = traceback.format_exc()
        msg_box = QtGui.QMessageBox()
        msg_box.setIcon(QtGui.QMessageBox.Critical)
        msg_box.setWindowTitle("VBar Control message")
        msg_box.setText("UNRECOVERABLE ERROR!\n\n" + var)
        msg_box.exec_()


