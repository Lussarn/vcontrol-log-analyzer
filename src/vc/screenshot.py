"""
Grab screenshot module
"""
__author__ = "linus.larsson@gmail.com"

from PySide import QtCore, QtGui
from PIL import Image
from cStringIO import StringIO

import vc.globals
import vc.variable
import vc.util

from qtui.QTDScreenshotDialog import Ui_QTDScreenshotDialog

class _QTScaleDialog(QtGui.QDialog):
    """
    Opens a dialog for the scale of the image (image size)
    """
    def __init__(self, parent):
        QtGui.QDialog.__init__(self, parent)
        self.ui = Ui_QTDScreenshotDialog()
        self.ui.setupUi(self)

        self.factor, self.fontfactor = vc.util.rescale(self)

        self.scale = -1
        self.setWindowTitle(vc.globals.PROGRAM_NAME + " " + vc.globals.VERSION)

        # Available resolutions
        self._scale_resolutions = [
            { "scale" : 0, "label" : "No scaling" },
            { "scale" : 600, "label" : "600px " + "width" },
            { "scale" : 700, "label" : "700px " + "width" },
            { "scale" : 800, "label" : "800px " + "width" },
            { "scale" : 900, "label" : "900px " + "width" },
            { "scale" : 1000, "label" : "1000px " + "width" },
            { "scale" : 1200, "label" : "1200px " + "width" },
            { "scale" : 1400, "label" : "1400px " + "width" },
        ]

        # Build scale radiobuttons
        checked = int(vc.variable.get("screenshot-ui-scale", "0"))
        self._scale_radio_buttons = []
        for index, resolution in enumerate(self._scale_resolutions):
            scale_button = QtGui.QRadioButton(resolution["label"], self.ui.frame_resolutions)
            scale_button.move(6 * self.factor, (index * 26 + 6) * self.factor)
            self._scale_radio_buttons.append(scale_button)
            if index == checked:
                scale_button.toggle()


        # Signals
        self.ui.button_box.accepted.connect(self._on_save)
        self.ui.button_box.rejected.connect(self._on_close)


    def _on_save(self):
        self.scale = 0
        for index, resolution in enumerate(self._scale_resolutions):
            scale_button = self._scale_radio_buttons[index] 
            if (scale_button.isChecked()):
                self.scale = resolution["scale"]
                vc.variable.set("screenshot-ui-scale", str(index))
                break

    def _on_close(self):
        self.close()

def grab(widget, scaling=True):
    """
    Grab a screenshot with optional scaling
    """
    pixmap =  QtGui.QPixmap.grabWidget(widget)
    q_image = pixmap.toImage()

    original_width = q_image.width()
    original_height = q_image.height()

    # Optional scaling
    if (scaling):
        scale_dialog = _QTScaleDialog(widget)
        scale_dialog.exec_()

        # Cancel on the scale dialog
        if (scale_dialog.scale == -1):
            return
 
        # Scale image
        if (scale_dialog.scale > 0):
            scale_width = scale_dialog.scale
            scale_ratio = float(scale_width) / original_width
            scale_height = int(original_height * scale_ratio)
            scale_size = scale_width, scale_height

            image_pil = vc.util.qt_image_to_pil_image(q_image)
            image_pil.thumbnail(scale_size, Image.ANTIALIAS)

            data = vc.util.pil_tobytes(image_pil.convert("RGBA"), 'raw', 'BGRA')
            q_image = QtGui.QImage(data, image_pil.size[0], image_pil.size[1], QtGui.QImage.Format_ARGB32)

    screenshot_filename, _ =QtGui.QFileDialog.getSaveFileName(
        parent=widget,
        caption="Save PNG file",
        filter="All files (*.*);;PNG (*.png)",
        selectedFilter="PNG (*.png)"
    )

    if screenshot_filename is None:
        return

    try: 
        q_image.save(screenshot_filename, "png")
    except:
        msg_box = QtGui.QMessageBox()
        msg_box.setWindowTitle("VBar Control message")
        msg_box.setText("Error: Unable to save screenshot")
        msg_box.exec_()
 
