import sqlite3
import os
import datetime
import time
import sys
import subprocess
import re

class Analyzer:

	def __init__(self):
		self._conn = None

	def _db(self):
		if self._conn == None:
			self._conn = sqlite3.connect(os.path.join(os.path.expanduser("~"), '.vcontrol.db'))

		# Create tables if necesarry
		cur = self._conn.cursor()
		cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='battery'")
		rs = cur.fetchone()
		if rs == None:
			print "Creating database table battery";
			cur = self._conn.cursor()
			cur.execute("CREATE TABLE battery (id INTEGER PRIMARY KEY autoincrement NOT NULL, name TEXT)")
			self._conn.commit();

		cur = self._conn.cursor()
		cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='model'")
		rs = cur.fetchone()
		if rs == None:
			print "Creating database table model";
			cur = self._conn.cursor()
			cur.execute("CREATE TABLE model (id INTEGER PRIMARY KEY autoincrement NOT NULL, name TEXT)")
			self._conn.commit();

		cur = self._conn.cursor()
		cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='batterylog'")
		rs = cur.fetchone()
		if rs == None:
			print "Creating database table batterylog";
			cur = self._conn.cursor()
			cur.execute("CREATE TABLE batterylog (id INTEGER PRIMARY KEY autoincrement, date datetime, batteryid INTEGER, modelid INTEGER, duration INTEGER, capacity INTEGER, used INTEGER, minvoltage NUMERIC(3,1), maxampere NUMERIC(3,1), uid NUMERIC(3,1))");
			self._conn.commit();

		cur = self._conn.cursor()
		cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='variable'")
		rs = cur.fetchone()
		if rs == None:
			print "Creating database table variable";
			cur = self._conn.cursor()
			cur.execute("CREATE TABLE variable (name VARCHAR(255) PRIMARY KEY, value TEXT)");
			self._conn.commit();

		return self._conn

	def get_battery_id(self, name):
		cur = self._db().cursor()
		cur.execute('SELECT id FROM battery WHERE name=?', [name])
		rs = cur.fetchone()
		if rs != None:
			id = rs[0]
		else:
			cur = self._db().cursor()
			cur.execute('INSERT INTO battery (name) VALUES (?)', [name])
			id = cur.lastrowid;
			self._db().commit()
		return id;

	def get_model_id(self, name):
		cur = self._db().cursor()
		cur.execute('SELECT id FROM model WHERE name=?', [name])
		rs = cur.fetchone()
		if rs != None:
			id = rs[0]
		else:
			cur = self._db().cursor()
			cur.execute('INSERT INTO model (name) VALUES (?)', [name])
			id = cur.lastrowid;
			self._db().commit()
		return id;

	def list_gear(self):
		cur = self._db().cursor()
		gear = {'batteries': {}, 'models': {}} 
		for row in cur.execute('SELECT * FROM battery'):
			gear['batteries'][row[0]] = row[1]
		for row in cur.execute('SELECT * FROM model'):
			gear['models'][row[0]] = row[1]
		return gear

	def import_data(self):
		base = self._find_vcontrol_path()

		batteryPath = os.path.join(base, 'battery')
		if not os.path.isdir(batteryPath):
			self.error = "VControl path not found, mounted?"
			return False

		batteryDirs = [ os.path.join(batteryPath,f) for f in os.listdir(batteryPath) if os.path.isdir(os.path.join(batteryPath,f)) and os.path.exists(os.path.join(batteryPath, f, 'name')) ]
		imported = []
		for d in batteryDirs:
			name = open(os.path.join(d, 'name')).read(255).strip().strip("\x00")
			batteryid = self.get_battery_id(name)
			with open(os.path.join(d, 'log.csv')) as f:
				lines = f.readlines()
			lines = [x.strip() for x in lines] 	

			for line in lines:
				cols = line.split(';')
				if len(cols) < 8:
					continue

				date = cols.pop(0)
				date = time.strftime('%Y-%m-%d %H:%M:%S', time.strptime(date,'%d.%m.%Y %H:%M:%S'))
				capacity = cols.pop(0)
				used = cols.pop(0)
				duration = cols.pop(0)
				minvoltage = cols.pop(0)
				maxampere = cols.pop(0)
				uid = cols.pop(0)
				if len(cols) == 0:
					model = "Unknown model"
				else:
					model = cols.pop(0)
				modelid = self.get_model_id(model)

				cur = self._db().cursor()
				cur.execute('SELECT id FROM batterylog WHERE batteryid=? and date=?', [batteryid, date])
				rs = cur.fetchone()
				if rs == None:
					imported.append([name, model]) 
					cur = self._db().cursor()
					cur.execute('INSERT INTO batterylog (date, batteryid, modelid, duration, capacity, used, minvoltage, maxampere, uid) VALUES (?,?,?,?,?,?,?,?,?)',
					 	[date, batteryid, modelid, duration, capacity, used, minvoltage, maxampere, uid])
					self._db().commit()
		return imported

	def _find_vcontrol_path(self):
		if 'linux' in sys.platform:
#			return "/tmp";
			drives=subprocess.Popen('mount', shell=True, stdout=subprocess.PIPE)
			lines, err=drives.communicate()
			words = lines.split()
			path = None
			for word in words:
				if word.find('/VControl') >= 0:
					path = word
					break
		elif 'darwin' in sys.platform:
			listdrives=subprocess.Popen('mount', shell=True, stdout=subprocess.PIPE)
			lines, err=listdrives.communicate()
			path = None
			if lines.find(' /Volumes/VControl ') >= 0:
				path = '/Volumes/VControl'
		elif 'win' in sys.platform:
			cmd = 'wmic'
			if os.path.isfile('c:\\windows\\system32\\wbem\\wmic.exe'):
				cmd = 'c:\\windows\\system32\\wbem\\wmic.exe'

			drivelist = subprocess.Popen(cmd + ' volume get driveletter,label', shell=False, stdout=subprocess.PIPE)
			lines, err = drivelist.communicate()
			lines = lines.split('\r\n')
			path = None
			for line in lines:
				words = line.split()
				if len(words) < 2:
					continue
				if words[1] == "VControl":
					path = words[0] + '\\'
					break

		return path

	def vcontrol_is_connected(self):
		if self._find_vcontrol_path() == None:
			return False
		return True

	def extract(self, batteryid=None, modelid=None, start=None, end=None):
		sql = "\
			SELECT l.id, b.name as batteryname, m.name as modelname, l.date, l.duration, l.capacity, l.used, l.minvoltage, l.maxampere, l.uid \
			FROM batterylog l \
			LEFT JOIN battery b on b.id=l.batteryid \
			LEFT JOIN model m on m.id=l.modelid \
			WHERE l.used * 4 > l.capacity"
		if batteryid != None:
			sql += " AND l.batteryid=" + str(batteryid)
		if modelid != None:
			sql += " AND l.modelid=" + str(modelid)
		if start != None:
			sql += " AND l.date >= '" + str(start) + "'"
		if end != None:
			sql += " AND l.date < '" + str(end) + "'"
		
		sql += " ORDER BY date"

		cur = self._db().cursor()
		cycles = 0
		capacityused = 0;
		flighttime = 0
		data = []
		session = 0
		olddate = datetime.datetime(1970,1,1)
		for row in cur.execute(sql):
			# Calculate the session based on date
			date = datetime.datetime.strptime(row[3], '%Y-%m-%d %H:%M:%S')
			datediff = date - olddate
			delta_seconds = datediff.total_seconds()
			if delta_seconds > (60 * 60 * 3):
				session += 1

			capacityused += row[6];
			cycles += 1
			duration = "{0:02d}:{1:02d}".format(int(row[4] / 60), int(row[4] % 60))
			flighttime += row[4]
			used = str(row[6]) + ' (' + str(int(float(row[6]) / row[5] * 100)) + '%)'
			data.append({'id': row[0], 'date': row[3], 'battery': row[1], 'model': row[2], 'duration': duration, 'capacity': row[5], 'used': used, 'minv': row[7], 'maxa': row[8], 'idlev': row[9], 'session': session})
			olddate = date

		capacityused = round(float(capacityused) / 1000, 2)
		t = "{0:02d}:{1:02d}:{2:02d}".format(int(flighttime / 3600), int((flighttime % 3600) / 60), int(flighttime % 60))
		totals = {'cycles': cycles, 'used': capacityused, 'duration': t, 'sessions':session}; 
		return {'data' : data, 'totals': totals }

	def get_date_interval(self):
		cur = self._db().cursor()
		cur.execute("SELECT MIN(date) AS mindate, MAX(date(date, '+1 day')) AS maxdate FROM batterylog WHERE used * 4 > capacity")
		rs = cur.fetchone()
		if rs == (None, None):
			return { 'first': datetime.datetime(2000,1,1), 'last': datetime.datetime(2030,1,1) }

		return {
			'first': datetime.datetime.strptime(rs[0][0:10],'%Y-%m-%d'),
			'last': datetime.datetime.strptime(rs[1][0:10],'%Y-%m-%d')
		}

	def extract_byweek(self, batteryid=None, modelid=None, start=None, end=None, group='model'):
		sql = "\
			SELECT (STRFTIME('%Y', date) || '-' || STRFTIME('%W', date)),count(*) AS week FROM batterylog WHERE used * 4 > capacity GROUP BY (STRFTIME('%Y', date) || '-' || STRFTIME('%W', date))"

		data = self.extract(batteryid,modelid,start,end)
		out = []

		if len(data['data']) > 0:
			current = datetime.datetime.strptime(data['data'][0]['date'], '%Y-%m-%d %H:%M:%S');
			currentYear = current.isocalendar()[0];
			currentWeek = current.isocalendar()[1];
			current = datetime.datetime.strptime(str(currentYear) + "-" + str(currentWeek - 1) + "-1", '%Y-%W-%w');
			currentWeekStr = str(current.isocalendar()[0]) + "-" + str(current.isocalendar()[1])
			out.append({'week': currentWeekStr, 'group': {}})

			data['data'] = list(reversed(data['data']))

			while True:
				row = data['data'][-1]
				rowDate = datetime.datetime.strptime(row['date'], '%Y-%m-%d %H:%M:%S').isocalendar();
				year = rowDate[0];
				week = rowDate[1];
				weekStr = str(year) + "-" + str(week)
				if out[-1]['week'] == weekStr:
					if row[group] not in out[-1]['group']:
						out[-1]['group'][row[group]] = 0
					out[-1]['group'][row[group]] += 1
					data['data'].pop()
					if len(data['data']) == 0:
						break
				else:
					current = current + datetime.timedelta(days=7)
					currentWeekStr = str(current.isocalendar()[0]) + "-" + str(current.isocalendar()[1])
					out.append({'week': currentWeekStr, 'group': {}})


		data['data'] = out
		return data
