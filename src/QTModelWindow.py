"""
Model information
"""
__author__ = "linus.larsson@gmail.com"
import PySide
from PySide import QtCore, QtGui
import sys

from PIL import Image
import time
import datetime
import re
import StringIO

import vc.globals
import vc.util
import vc.screenshot
from qtui.QTDModelWindow import Ui_QTDModelWindow

class QTModelWindow(QtGui.QMainWindow):
    """
    Model info Window
    """
    def __init__(self, model_id, analyzer, main_window):
        QtGui.QMainWindow.__init__(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.ui = Ui_QTDModelWindow()
        self.ui.setupUi(self)

        self.factor, self.font_factor = vc.util.rescale(self)
        self.pixmap_screenshot = vc.util.load_pixmap("screenshot-small.png", self.factor)
        self.pixmap_clear = vc.util.load_pixmap("clear.png", self.factor)

        self._analyzer = analyzer
        self._model_id = model_id
        self._main_window = main_window

        self._data = analyzer.extract_model_info(model_id)

        self.setWindowTitle(vc.globals.PROGRAM_NAME + " " + vc.globals.VERSION + " - Model info ")

        # Model name
        self.ui.label_statistics_0.setText(self._data["name"])

        model_type = "Helicopter"
        if self._data["type"] == "MULTIROTOR":
            model_type = "Multirotor"
        elif self._data["type"] == "AIRPLANE":
            model_type = "Airplane"
        self.ui.label_statistics_1.setText(model_type)
        
        self.ui.label_statistics_2.setText(self._data["first"])
        self.ui.label_statistics_3.setText(self._data["last"])
        self.ui.label_statistics_4.setText(str(self._data["cycles"]))
        self.ui.label_statistics_5.setText(self._data["duration"])

        self.ui.push_button_screenshot.setIcon(self.pixmap_screenshot)
        self.ui.push_button_screenshot.setIconSize(self.pixmap_screenshot.rect().size())
        self.ui.push_button_screenshot.clicked.connect(self._on_screenshot)

        self.ui.push_button_clear.setIcon(self.pixmap_clear)
        self.ui.push_button_clear.setIconSize(self.pixmap_clear.rect().size())
        self.ui.push_button_clear.clicked.connect(self._on_clear)

        self.ui.text_edit_info.setPlainText(self._data["info"])
        self.highlighter = Highlighter(self.ui.text_edit_info.document())

        self.show()

        QtCore.QTimer.singleShot(0, self._load_image)

    def _load_image(self):
        photo_bitmap = self._data["image"]
        if photo_bitmap is not None:
            # Create a PIL image from the photo to be able to create the thumbnail
            photo_image_qt = photo_bitmap.toImage()
            photo_image_pil = vc.util.qt_image_to_pil_image(photo_image_qt)
            photo_image_pil.thumbnail((348 * self.factor, 196 * self.factor))
            photo_data = vc.util.pil_tobytes(photo_image_pil.convert("RGBA"),'raw','BGRA')
            qt_image = QtGui.QImage(photo_data, photo_image_pil.size[0], photo_image_pil.size[1], QtGui.QImage.Format_ARGB32)
            photo_bitmap = QtGui.QPixmap.fromImage(qt_image)
            self.ui.label_photo.setPixmap(photo_bitmap)
            self.ui.push_button_clear.setVisible(True)
        else:
            self.ui.push_button_clear.setVisible(False)
        self.ui.label_photo.installEventFilter(QDropHandler(self))


    def insert_date(self, date):
        [text, insert_pos] = self._insert_date(self.ui.text_edit_info.toPlainText(), date)
        self.ui.text_edit_info.setPlainText(text)
        self.ui.text_edit_info.setFocus() 
        row = text[0:insert_pos].count("\n")
        cursor = QtGui.QTextCursor(self.ui.text_edit_info.document().findBlockByLineNumber(row))
        self.ui.text_edit_info.setTextCursor(cursor)


    def _insert_date(self, text, date):
        """
        Insert a date at the correct place in the info
        """
        date_timestamp = self._date_to_timestamp(date)
        regexp_date = "## \\d\\d\\d\\d-\\d\\d-\\d\\d ##"
        insert_pos = len(text) -1
        for m in re.finditer(regexp_date, text):
            date_match = m.group(0)
            date_match_timestamp = self._date_to_timestamp(date_match[3:13])
            if date_match_timestamp is None:
                continue
            start = m.start()

            if date_match_timestamp > date_timestamp:
                text = text[0:start] + "## " + date + " ##\n\n" + text[start:]
                insert_pos = start + 17
                return [text, insert_pos]

            if date_match_timestamp == date_timestamp:
                insert_pos = start + 17
                return [text, insert_pos]

        text = (text.rstrip() + "\n\n## " + date + " ##").lstrip() + "\n\n"
        return [text, len(text) -1]

    def _date_to_timestamp(self, date):
        try:
            t = time.mktime(datetime.datetime.strptime(date, "%Y-%m-%d").timetuple())
        except:
            t = None
        return t

    def _set_photo_bitmap(self, photo_bitmap):
        self.ui.label_photo.setPixmap(photo_bitmap)

    def _on_screenshot(self):
        self.ui.label_information.hide()
        self.ui.push_button_screenshot.hide()
        self.ui.push_button_clear.hide()
        self.ui.text_edit_info.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff);
        self.ui.text_edit_info.setFrameStyle(QtGui.QFrame.NoFrame);
        vc.screenshot.grab(self, False)
        self.ui.text_edit_info.setFrameStyle(QtGui.QFrame.Panel);
        self.ui.text_edit_info.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded);
        self.ui.push_button_screenshot.show()
        self.ui.push_button_clear.show()
        self.ui.label_information.show()

    def _on_clear(self):
        msg_box = QtGui.QMessageBox()
        msg_box.setIcon(QtGui.QMessageBox.Question)
        msg_box.setWindowTitle(vc.globals.PROGRAM_NAME)
        msg_box.setText("Delete photo?")
        msg_box.setStandardButtons(QtGui.QMessageBox.Yes);
        msg_box.addButton(QtGui.QMessageBox.No);
        if msg_box.exec_() == QtGui.QMessageBox.No:
            return

        self.ui.label_photo.setText("Drop photo here")
        self.ui.push_button_clear.setVisible(False)
        # Clear images to model in DB
        self._analyzer.clear_model_image(self._model_id)
        self._main_window.populate_gear()
        self._main_window.populate_grid()



    def closeEvent(self, event):
        self._save()
        self._main_window.populate_grid(reload=False)
        del self._main_window.model_windows[self._model_id]
        event.accept()

    def _save(self):
        self._analyzer.set_model_info(self._model_id, self.ui.text_edit_info.toPlainText())
        self._main_window.update_gear(
            type="model",
            id=self._model_id,
            data={"info": self.ui.text_edit_info.toPlainText()}
        )            
 
class QDropHandler(QtCore.QObject):

    def __init__(self, parent=None):
        QtCore.QObject.__init__(self, parent)
        self._model_window = parent

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.DragEnter:
            # we need to accept this event explicitly to be able to receive QDropEvents!
            event.accept()
        if event.type() == QtCore.QEvent.Drop:
            try:
                filename = None
                md = event.mimeData()
                if md.hasUrls():
                    for url in md.urls():
                        # OSX Workaround
                        if vc.globals.OS == "osx":
                            from Foundation import NSURL
                            filename = str(NSURL.URLWithString_(str(url.toString())).filePathURL().path())
                        else:
                            filename = url.toLocalFile()
                        break
                event.accept()
                if filename is None:
                    return

                photo_original_image_pil = Image.open(filename)
                # Copy the image since we need 3 of them (Original, thumb and info size)
                # The info thumb is never saved, but updated in the info window
                photo_thumb_image_pil = photo_original_image_pil.copy()
                photo_info_image_pil = photo_original_image_pil.copy()

                # Create thumbnail
                photo_thumb_image_pil.thumbnail((280, 158))
                photo_thumb_string_io = StringIO.StringIO()
                photo_thumb_image_pil.save(photo_thumb_string_io, "PNG")
                photo_thumb_image_pil = photo_thumb_string_io.getvalue()

                # Create original
                photo_original_image_pil.thumbnail((1152, 648))
                result = StringIO.StringIO()
                photo_original_image_pil.save(result, "PNG")
                photo_original_image_pil = result.getvalue()

                # Save images to model in DB
                self._model_window._analyzer.set_model_image(self._model_window._model_id, photo_thumb_image_pil, photo_original_image_pil)

                # Update model info window with new image
                photo_info_image_pil.thumbnail((348, 196))

                photo_data = vc.util.pil_tobytes(photo_info_image_pil.convert("RGBA"), 'raw', 'BGRA')
                qt_image = QtGui.QImage(photo_data, photo_info_image_pil.size[0], photo_info_image_pil.size[1], QtGui.QImage.Format_ARGB32)
                photo_bitmap = QtGui.QPixmap.fromImage(qt_image)
                self._model_window.ui.label_photo.setPixmap(photo_bitmap)
                self._model_window.ui.push_button_clear.setVisible(True)

                self._model_window._main_window.populate_gear()
                self._model_window._main_window.populate_grid()

            except Exception as e:
                print e
                pass

        return QtCore.QObject.eventFilter(self, obj, event)


class Highlighter(QtGui.QSyntaxHighlighter):
    def __init__(self, parent=None):
        super(Highlighter, self).__init__(parent)

        self.hl_rules = []

        date_format = QtGui.QTextCharFormat()
        date_format.setFontWeight(QtGui.QFont.Bold)
        date_format.setForeground(QtCore.Qt.darkBlue)
        self.hl_rules.append((QtCore.QRegExp("## \\d\\d\\d\\d-\\d\\d-\\d\\d ##"), date_format))

        self.info_format = QtGui.QTextCharFormat()
        self.info_format.setFontFamily("Courier New")
        self.info_format.setFontWeight(QtGui.QFont.Normal)
        self.info_format.setForeground(QtCore.Qt.black)

        self.log_format = QtGui.QTextCharFormat()
        self.log_format.setFontWeight(QtGui.QFont.Normal)
        self.log_format.setForeground(QtCore.Qt.black)

    def highlightBlock(self, text):
        if self.currentBlockState() == 1 and self.previousBlockState() == -1:
            self.setCurrentBlockState(-1)

        if self.currentBlockState() == 2 and self.previousBlockState() == -1:
            self.setCurrentBlockState(-1)

        if self.previousBlockState() == 1:
            self.setCurrentBlockState(2)

        if self.previousBlockState() == 2:
            self.setCurrentBlockState(2)


        for pattern, format in self.hl_rules:
            expression = QtCore.QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)
                self.setCurrentBlockState(1)

        if self.currentBlockState() == -1:
            self.setFormat(0,len(text), self.info_format)

        if self.currentBlockState() ==  2:
            self.setFormat(0, len(text), self.log_format)


