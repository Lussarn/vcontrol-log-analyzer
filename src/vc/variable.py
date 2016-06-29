"""
Module for persistent variables, config settings etc
"""
import sqlite3
import os

import vc.util

def get(name, default = ''):
    """
    Fetch a string variable, if not exists return default
    """
    if vc.globals.OS == "windows" :
        from win32com.shell import shell,shellcon
        home = shell.SHGetFolderPath(0, shellcon.CSIDL_PROFILE, None, 0)
    else:
        home = os.path.expanduser("~")

    conn = sqlite3.connect(os.path.join(home, '.vcontrol.db'))
    conn.row_factory = vc.util.sqlite_dict_factory

    try:
        cur = conn.cursor()
        cur.execute("SELECT value FROM variable WHERE name=?",[name])
        rs = cur.fetchone()
        if rs == None:
            conn.close()
            return default;
        ret = rs["value"]
    except:
        ret = default
    conn.close()
    return ret

def set(name, value):
    """
    Set a string variable
    """
    if vc.globals.OS == "windows" :
        from win32com.shell import shell,shellcon
        home = shell.SHGetFolderPath(0, shellcon.CSIDL_PROFILE, None, 0)
    else:
        home = os.path.expanduser("~")

    conn = sqlite3.connect(os.path.join(home, '.vcontrol.db'))

    cur = conn.cursor()
    cur.execute('INSERT OR REPLACE INTO variable (name, value) VALUES (?,?)',[name, value])
    conn.commit()

    conn.close()
