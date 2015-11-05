"""
About dialog
"""
__author__ = "linus.larsson@gmail.com"

from PySide import QtCore, QtGui

import vc.globals
import vc.util
from  qtui.QTDAboutDialog import Ui_AboutDialog

class QTAboutDialog(QtGui.QDialog):
    """
    Opens a dialog for the scale of the image (image size)
    """
    def __init__(self, parent):
        QtGui.QDialog.__init__(self, parent)
        self.ui = Ui_AboutDialog()
        self.ui.setupUi(self)
        self.factor, self.font_factor = vc.util.rescale(self)

        self.setWindowTitle(vc.globals.PROGRAM_NAME + " " + vc.globals.VERSION)

        font = self.ui.label_title.font();
        font.setPixelSize(27 * self.font_factor);
        font.setBold(True);
        self.ui.label_title.setFont(font)
        self.ui.label_title.setText(vc.globals.PROGRAM_NAME)

        font = self.ui.label_version.font();
        font.setPixelSize(14 * self.font_factor);
        font.setBold(True);
        self.ui.label_version.setFont(font)
        self.ui.label_version.setText(vc.globals.VERSION)

        logo_pixmap = QtGui.QPixmap(vc.util.resource_path("assets/logo/logo512.png"))
        logo_pixmap = logo_pixmap.scaledToHeight(int(logo_pixmap.height() * self.factor / 2.0), QtCore.Qt.SmoothTransformation)

        self.ui.label_logo.setPixmap(logo_pixmap)
        self.ui.label_logo.setText("")

        font = self.ui.text_browser_info.font();
        font.setPixelSize(10 * self.font_factor);
        self.ui.text_browser_info.setFont(font)


        text = '' \
                + vc.globals.PROGRAM_NAME + ' is distributed under Apache Licence, v2.0<br /><br />' \
               '&copy; 2015 - Linus Larsson (linus.larsson@gmail.com)<br /><br />' \
               '<a href="http://www.linlar.org/vbc">http://www.linlar.org/vbc</a>' \
               ''

        self.ui.text_browser_info.setHtml(text);

        self.ui.push_button_close.clicked.connect(self._on_close)
        self.show()

    def _on_close(self):
        self.close()

