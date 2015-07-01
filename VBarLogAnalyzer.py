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

		cur = self._conn.cursor()
		cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='vbarlog'")
		rs = cur.fetchone()
		if rs == None:
			print "Creating database table vbarlog";
			cur = self._conn.cursor()
			cur.execute("CREATE TABLE vbarlog (id INTEGER PRIMARY KEY autoincrement, logid INTEGER, original_filename VARCHAR(255), model VARCHAR(255), date DATETIME, severity INTEGER, message VARCHAR(255))");
			self._conn.commit();
			cur = self._conn.cursor()
			cur.execute("CREATE INDEX idx_vbar_logid ON vbarlog (logid)");
			self._conn.commit();


		cur = self._conn.cursor()
		cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='uilog'")
		rs = cur.fetchone()
		if rs == None:
			print "Creating database table uilog";
			cur = self._conn.cursor()
			cur.execute("CREATE TABLE uilog (id INTEGER PRIMARY KEY autoincrement, logid INTEGER, original_filename VARCHAR(255), model VARCHAR(255), date DATETIME, ampere NUMERIC(3,1), voltage NUMERIC(3,1), usedcapacity NUMERIC(3,1), headspeed INTEGER, pwm INTEGER)");
			self._conn.commit();
			cur = self._conn.cursor()
			cur.execute("CREATE INDEX idx_ui_logid ON uilog (logid)");
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

		self._import_model_logs();

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
					logid = cur.lastrowid
					self._db().commit()

					# Lets see if we got a vbar log for this flight

					cur = self._db().cursor()
					cur.execute("SELECT original_filename FROM vbarlog vbl WHERE model=? AND logid IS NULL AND (date = ? AND message = 'VBar Logfile End') OR (date <= ? AND (SELECT original_filename FROM vbarlog WHERE id=vbl.id + 1 AND date > ?) = vbl.original_filename) ORDER BY date DESC LIMIT 1",
						[model, date, date, date])
					rs = cur.fetchone()
					if rs != None:
						vbarFile = rs[0]
						cur = self._db().cursor()
						cur.execute('UPDATE vbarlog SET logid = ? WHERE original_filename = ?',
						 	[logid, vbarFile])
						self._db().commit()
						
						uiFile = vbarFile.replace('_vbar.log', '_ui.csv')
						cur = self._db().cursor()
						cur.execute('UPDATE uilog SET logid = ? WHERE original_filename = ?',
						 	[logid, uiFile])
						self._db().commit()

		return imported

	def _import_model_logs(self):
		base = self._find_vcontrol_path()
		logPath = os.path.join(base, 'log')
		modelDirs = [ os.path.join(logPath,f) for f in os.listdir(logPath) if os.path.isdir(os.path.join(logPath,f)) ]
		for modelPath in modelDirs:
			# Open all vbar files and check if they need importing
			vbarFiles = [ f for f in os.listdir(modelPath) if os.path.isfile(os.path.join(modelPath, f))  and '_vbar.log' in f ]
			for vbarFile in vbarFiles:
				# import the vbar file
				with open(os.path.join(modelPath, vbarFile)) as f:
					lines = f.readlines()
				lines = [x.strip() for x in lines]

				error = False
				firstLine = False
				lastHour = ''
				cur = self._db().cursor()
				for line in lines:
					if firstLine == False:
						firstLine = True
						cols = line.split(' -- ')
						if len(cols) != 4 and cols[0] != 'VBar Start':
							error = True
							break
						modelName = unicode(cols[1], errors='ignore')
						startdate = date = datetime.datetime.strptime(cols[2],'%d.%m.%Y')
						continue

					if ('VBar Logfile End' in line):
						cols = line.split(' -- ')
						sqlDate = datetime.datetime.strptime(cols[1] + ' ' + cols[2],'%d.%m.%Y %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
						cur.execute('INSERT INTO vbarlog (original_filename, model, date, severity, message) VALUES (?,?,?,?,?)',
						 	[vbarFile, modelName, sqlDate, 1, 'VBar Logfile End'])
						self._db().commit()
						break

					cols = line.split(';')
					hour = cols[0][:2]
					# Rollover on date
					if (lastHour == '23' and hour == '00'):
						date = date + datetime.timedelta(days = 1)
					sqlDate = date.strftime('%Y-%m-%d') + ' ' + cols[0]

					if (lastHour == ''):
						cur.execute('SELECT count(*) from vbarlog where model=? and date=?', [modelName, sqlDate])
						rs = cur.fetchone()
						if rs[0] != 0:
							error = True
							break

					lastHour = hour
					cur.execute('INSERT INTO vbarlog (original_filename, model, date, severity, message) VALUES (?,?,?,?,?)',
					 	[vbarFile, modelName, sqlDate, int(cols[1]), cols[2]])
				self._db().commit()

				if error == True:
					continue

				# See if we have an ui file for this flight
				uiFile = vbarFile.replace('_vbar.log', '_ui.csv')
				if not os.path.isfile(os.path.join(modelPath, uiFile)):
					continue

				with open(os.path.join(modelPath, uiFile)) as f:
					lines = f.readlines()
				lines = [x.strip() for x in lines]
	
				# remove first line
				lines.pop(0)

				date = startdate

				for line in lines:
					cols = line.split(';')
					if len(cols) != 6:
						continue
		
					hour = cols[0][:2]
					# Rollover on date
					if (lastHour == '23' and hour == '00'):
						date = date + datetime.timedelta(days = 1)
					sqlDate = date.strftime('%Y-%m-%d') + ' ' + cols[0]

					cur.execute('INSERT INTO uilog (original_filename, model, date, ampere, voltage, usedcapacity, headspeed, pwm) VALUES (?,?,?,?,?,?,?,?)',
					 	[uiFile, modelName, sqlDate, float(cols[1]), float(cols[2]), float(cols[3]), int(cols[4]), int(cols[5])])
				self._db().commit()
		return

	def _import_ui(self, logid, date, modelPath):
		# First we need to find the file containing UI data for this flight
		# It is not guaranteed to be there. 
		# We do this by comparing the date with the dates in the _ui files
		uiFilenames = [ os.path.join(modelPath,f) for f in os.listdir(modelPath) if os.path.isfile(os.path.join(batteryPath,f)) and "_ui" in f ]
		for filename in uiFilenames:
			# read lines
			with open(filename) as f:
				lines = f.readlines()
			lines = [x.strip() for x in lines] 
			for line in lines:
				cols = line.split(';')
				if len(cols) < 6:
					continue
				if cols[0] == 'Date':
					continue

	def _find_vcontrol_path(self):
#		return '/Users/linus/vcontrol'
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
			SELECT l.id, b.name as batteryname, m.name as modelname, l.date, l.duration, l.capacity, l.used, l.minvoltage, l.maxampere, l.uid, \
			(select count(*) > 1 from vbarlog vbl WHERE l.id=vbl.logid) as havevbarlog, \
			(select count(*) > 1 from uilog ul WHERE l.id=ul.logid) as haveuilog \
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
			data.append({'id': row[0], 'date': row[3], 'battery': row[1], 'model': row[2], 'duration': duration, 'capacity': row[5], 'used': used, 'minv': row[7], 'maxa': row[8], 'idlev': row[9], 'session': session, 'havevbarlog': row[10], 'haveuilog': row[11] })
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

	def extract_ui(self, logId):
		sql = "\
			SELECT  model, date, ampere, voltage, usedcapacity, headspeed, pwm FROM uilog where logid=" + str(logId)

		cur = self._db().cursor()
		out = []
		clipStart = False
		clipEnd = False
		i = 0
		lastNotZero = 0
		for row in cur.execute(sql):
			if clipStart == False and int(row[5]) == 0:
				continue
			if clipStart == False:
				clipStart = row[1]

			out.append({
				'model': row[0],
				'current': float(row[2]),
				'voltage': float(row[3]),
				'usedcapacity': float(row[4]),
				'headspeed': int(row[5]),
				'pwm': int(row[6])
			})
			if int(row[5]) != 0:
				lastNotZero = i
				clipEnd = row[1]
			i+=1

		out = out[0:lastNotZero]

		# Now we shuold evenly distribute end over the
		# seconds in clipStart and clipEnd
		# We need to know the number of seconds beetween clipStart and clipEnd
		start =time.mktime(time.strptime(clipStart, '%Y-%m-%d %H:%M:%S'))
		end =time.mktime(time.strptime(clipEnd, '%Y-%m-%d %H:%M:%S'))
		dur = end - start

		for i,row in enumerate(out):
			out[i]['sec'] = (float(i) / len(out)) * dur

		return out

	def extract_log(self, logId):
		sql = "\
			SELECT  model, date, severity, message FROM vbarlog where logid=" + str(logId)
		cur = self._db().cursor()
		out = []
		for row in cur.execute(sql):
			out.append({
				'model': row[0],
				'date': row[1],
				'severity': int(row[2]),
				'message': row[3]
			})
		return out
