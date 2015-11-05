"""
Various Util functions
"""

import PySide
from PySide import QtCore, QtGui
import math

import os
import sys

from PIL import Image
from cStringIO import StringIO

import vc.globals

def resource_path(relative_path):
    """
    Return base path to analyzer

    PyInstaller creates a temp folder and stores path in _MEIPASS

    use resource path when loading an asset such as an image
    to get the correct path
    """

    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
        
    return os.path.join(base_path, relative_path)


def sqlite_dict_factory(cursor, row):
    """
    Dictionary factory for sqlite

    usuage:
    conn.row_factory = sqllite_dict_factory
    """
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def rescale(widget, factor=None):
    font_factor = 1
    if factor is None:
        if vc.globals.OS == "windows":
            font = QtGui.QFont("Courier New", 12)
            font = QtGui.QFont(font, widget)
            fm = QtGui.QFontMetrics(font)
            factor = fm.height() / 18.0
            font_factor = factor
        else:
            factor = 1
            font_factor = 1
        if vc.globals.OS == "osx":
            font_factor *= 1.07


    if isinstance(widget, QtGui.QMainWindow) or isinstance(widget, QtGui.QDialog):
        w, h = widget.width(), widget.height()
        widget.resize(w * factor, h * factor)

    try:
        x = widget.x()
        y = widget.y()
        if x != 0 or y != 0:
            widget.move(x * factor, y * factor)
    except:
        pass


    try:
        widget.maximumWidth()

        widget.setMinimumWidth(widget.minimumWidth() * factor)

        if widget.maximumWidth() < 100000:
            widget.setMaximumWidth(widget.maximumWidth() * factor)

        widget.setMinimumHeight(widget.minimumHeight() * factor)

        if widget.maximumHeight() < 100000:
            widget.setMaximumHeight(widget.maximumHeight() * factor)

    except:
        pass

    try:
        margins = widget.getContentsMargins()
        widget.setContentsMargins(
            math.ceil(margins[0] * factor),
            math.ceil(margins[1] * factor),
            math.ceil(margins[2] * factor),
            math.ceil(margins[3] * factor)
        )
    except:
        pass

    try:
        s = widget.spacing()
        if s > 1:
            widget.setSpacing(s * factor)
    except:
        pass


    try:
        s = widget.horizontalSpacing()
        if s > 1:
            widget.setHorizontalSpacing(s * factor)
        s = widget.verticalSpacing()
        if s > 1:
            widget.setVerticalSpacing(s * factor)
    except:
        pass

    # OSX Use Helvetica Neue on controls whoch don't allign correctly
    if vc.globals.OS == "osx":
        if isinstance(widget, QtGui.QPushButton) or isinstance(widget, QtGui.QComboBox) or isinstance(widget, QtGui.QRadioButton) or isinstance(widget, QtGui.QCheckBox):
            font = QtGui.QFont("Helvetica Neue")
            widget.setFont(font)


    for child in widget.children():
        rescale(child, factor)

    return factor, font_factor

def pil_tobytes(image, encoder_name='raw', *args):
    try:
        return image.tobytes(encoder_name, args)
    except:
        pass
    return image.tostring(encoder_name, args)

def load_pixmap(name, factor):
    if factor == 1:
        dpi = "low"
        multiplier = 1
    else:
        dpi = "hi"
        multiplier = 2
    filename = resource_path("assets/img/" + dpi + "dpi/" + name)
    pixmap = QtGui.QPixmap(filename)
    if factor > 1:
        pixmap = pixmap.scaledToHeight(int(pixmap.height() * factor / multiplier), QtCore.Qt.SmoothTransformation)
    return pixmap

def qt_image_to_pil_image(image_qt):
    buffer = QtCore.QBuffer()
    buffer.open(QtCore.QIODevice.ReadWrite)
    image_qt.save(buffer, "PNG")
    strio = StringIO()
    strio.write(buffer.data())
    buffer.close()
    strio.seek(0)
    pil_image = Image.open(strio)
    return pil_image

def pil_image_to_qt_image(image_pil):
    data = pil_tobytes(image_pil.convert("RGBA"), 'raw','BGRA')
    qt_image = QtGui.QImage(data, image_pil.size[0], image_pil.size[1], QtGui.QImage.Format_ARGB32)
    return qt_image
