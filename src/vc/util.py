"""
Various Util functions
"""

import os
import sys

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
