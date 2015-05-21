import sqlite3
import os

def get(name, default = ''):
	conn = sqlite3.connect(os.path.join(os.path.expanduser("~"), '.vcontrol.db'))

	cur = conn.cursor()
	cur.execute("SELECT value FROM variable WHERE name=?",[name])
	rs = cur.fetchone()
	if rs == None:
		conn.close()
		return default;

	ret = rs[0]
	conn.close()
	return ret

def set(name, value):
	conn = sqlite3.connect(os.path.join(os.path.expanduser("~"), '.vcontrol.db'))

	cur = conn.cursor()
	cur.execute('INSERT OR REPLACE INTO variable (name, value) VALUES (?,?)',
	 	[name, value])
	conn.commit()

	conn.close()