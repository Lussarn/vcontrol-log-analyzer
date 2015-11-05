"""
Import thread
"""
#  self.longthread.signal.sig.connect(self.longoperationcomplete)

__author__ = "linus.larsson@gmail.com"

from PySide import QtCore, QtGui

import vc.backend

class ImportDoneSignal(QtCore.QObject):
    sig = QtCore.Signal()

class ImportUpdateSignal(QtCore.QObject):
    sig = QtCore.Signal(str)


class ImportThread(QtCore.QThread):
    def __init__(self, parent = None):
        super(ImportThread, self).__init__(parent)
        self._analyzer = vc.backend.Analyzer(self._import_callback)
        self.import_done_signal = ImportDoneSignal()
        self.import_update_signal = ImportUpdateSignal()

    def run(self):
        self._analyzer.import_data()
        self.import_done_signal.sig.emit()

    def _import_callback(self, str):
        self.import_update_signal.sig.emit(str)
