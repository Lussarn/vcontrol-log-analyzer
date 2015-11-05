"""
VBar Log
"""
__author__ = "linus.larsson@gmail.com"
from PySide import QtCore, QtGui

import re

import vc.globals
import vc.util
import vc.screenshot
from qtui.QTDLogWindow import Ui_QTDLogWindow

class QTLogWindow(QtGui.QMainWindow):
    """
    VBar log Window
    """
    def __init__(self, log_id, analyzer):
        QtGui.QMainWindow.__init__(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.ui = Ui_QTDLogWindow()
        self.ui.setupUi(self)

        self.factor, self.font_factor = vc.util.rescale(self)

        self.setWindowTitle(vc.globals.PROGRAM_NAME + " " + vc.globals.VERSION + " - Log Id " + str(log_id))

        data = analyzer.extract_vbar_log(log_id)
        text = ""
        for row in data:
            line = row["date"] + " (" + str(row["severity"]) + ") " + row["message"] + "\n"
            text += line

        self.ui.text_edit_log.setPlainText(text)
        self.highlighter = Highlighter(self.ui.text_edit_log.document())

        self.show()

class Highlighter(QtGui.QSyntaxHighlighter):
    def __init__(self, parent=None):
        super(Highlighter, self).__init__(parent)

        self.hl_rules = []

        severe_format = QtGui.QTextCharFormat()
        severe_format.setFontWeight(QtGui.QFont.Bold)
        severe_format.setFontFamily("Courier New")
        severe_format.setForeground(QtCore.Qt.red)
        self.hl_rules.append((QtCore.QRegExp("^.*\\(4\\).*$"), severe_format))

        ok_format = QtGui.QTextCharFormat()
        ok_format.setFontWeight(QtGui.QFont.Bold)
        ok_format.setForeground(QtCore.Qt.black)
        ok_format.setFontFamily("Courier New")
        self.hl_rules.append((QtCore.QRegExp("^.*\\([123]\\).*$"), ok_format))

    def highlightBlock(self, text):
        for pattern, format in self.hl_rules:
            expression = QtCore.QRegExp(pattern)
            index = expression.indexIn(text)
            if index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, format)
                break
