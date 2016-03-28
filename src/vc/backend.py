"""
Backend for Analyzer

Includes:
importing from Vbar Control
Reading and writing to SQLite backend
"""

import sqlite3
import os
import datetime
import time
import sys
import subprocess
import re
import StringIO
from PySide import QtCore, QtGui

import vc.util

class Analyzer:

    def __init__(self, import_callback=None):
        self._conn = None
        self._import_callback = import_callback

    def _db(self):
        """
        Returns a db connection

        Creates database and table if necesarry

        Due to the program evolving there are checks for fields and alter table
        for new functionality
        """
        if self._conn == None:
            if vc.globals.OS == "windows" :
                from win32com.shell import shell,shellcon
                home = shell.SHGetFolderPath(0, shellcon.CSIDL_PROFILE, None, 0)
            else:
                home = os.path.expanduser("~")

            self._conn = sqlite3.connect(os.path.join(home, '.vcontrol.db'))
            self._conn.row_factory = vc.util.sqlite_dict_factory
        else:
            return self._conn

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
            cur.execute("CREATE TABLE model (id INTEGER PRIMARY KEY autoincrement NOT NULL, type VARCHAR(20), name TEXT, image BLOB, thumb BLOB, info TEXT)")
            self._conn.commit();

        # Checking if image field is present on model table otherwise, add type, image and info
        cur = self._conn.cursor()
        found = False
        for row in cur.execute("PRAGMA table_info(model)"):
            if row["name"] == "image":
                found = True

        if not found:
            print "Adding type, image, thumb, info fields to model table"
            cur = self._conn.cursor()
            cur.execute("ALTER TABLE model ADD type VARCHAR(20)");
            cur.execute("ALTER TABLE model ADD image BLOB");
            cur.execute("ALTER TABLE model ADD thumb BLOB");
            cur.execute("ALTER TABLE model ADD info TEXT");
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

    def get_battery_id_by_name(self, name):
        """
        Returns a battery id by name

        Create battery in db if necesarry
        """
        cur = self._db().cursor()
        cur.execute('SELECT id FROM battery WHERE name=?', [name])
        rs = cur.fetchone()
        if rs != None:
            id = rs["id"]
        else:
            cur = self._db().cursor()
            cur.execute('INSERT INTO battery (name) VALUES (?)', [name])
            id = cur.lastrowid;
            self._db().commit()
        return id;

    def get_model_id_by_name(self, name):
        """
        Returns a model id by name

        Create model in db if necesarry
        """
        cur = self._db().cursor()
        cur.execute('SELECT id FROM model WHERE name=?', [name])
        rs = cur.fetchone()
        if rs is not None:
            id = rs["id"]
        else:
            cur = self._db().cursor()
            cur.execute('INSERT INTO model (name) VALUES (?)', [name])
            id = cur.lastrowid;
            self._db().commit()
        return id;

    def get_gear(self, start_date, end_date, factor=1):
        """
        Returns gear (models and batteries ) used beetween two dates

        gear["batteries"][0/1/2/...] = [id/name]
        gear["models"][0/1/2/...] = [id/name/type/thumb/info]
        """
        cur = self._db().cursor()
        gear = {'batteries': [], 'models': []} 
        for row in cur.execute('SELECT id, name FROM battery WHERE id in (select batteryid FROM batterylog WHERE date >= ? AND date < ?)', [start_date, end_date]):
            gear['batteries'].append({
                'id' : row['id'],
                'name' : row["name"] 
            })
        for row in cur.execute('SELECT id, name, type, thumb, info FROM model  WHERE id in (select modelid FROM batterylog WHERE date >= ? AND date < ?)', [start_date, end_date]):
            info = row["info"]
            if info == None:
                info = ""
            gear['models'].append({ 
                    'id' : row["id"],
                    'name' : row["name"],
                    'type' : row["type"],
                    'thumb' : row["thumb"],
                    'info' : info
            })
            if row["thumb"] is None:
                if row["type"] == "AIRPLANE":
                    bitmap = vc.util.load_pixmap("airplane.png", factor)
                elif row["type"] == "MULTIROTOR":
                    bitmap = vc.util.load_pixmap("multirotor.png", factor)
                else:
                    bitmap = vc.util.load_pixmap("helicopter.png", factor)
            else:
                bitmap = QtGui.QPixmap.fromImage(QtGui.QImage.fromData(str(row["thumb"])))
                bitmap = bitmap.scaledToHeight(bitmap.height() * factor / 2.0, QtCore.Qt.SmoothTransformation)
            gear['models'][len(gear['models']) - 1]['thumb'] = bitmap
        return gear

    def import_data(self):
        """
        Import batteries
        """
        self._import_model_logs();

        vcontrol_path = self._find_vcontrol_path()
        battery_path = os.path.join(vcontrol_path, 'battery')
        if not os.path.isdir(battery_path):
            self.error = "VControl path not found, mounted?"
            return False

        battery_dirs = [ os.path.join(battery_path,f) for f in os.listdir(battery_path) if os.path.isdir(os.path.join(battery_path,f)) and os.path.exists(os.path.join(battery_path, f, 'name')) ]
        imported = []
        for d in battery_dirs:
            name = open(os.path.join(d, 'name')).read(255).strip().strip("\x00")
            battery_id = self.get_battery_id_by_name(name)
            lines = {}
            try:
                with open(os.path.join(d, 'log.csv')) as f:
                    lines = f.readlines()
                lines = [x.strip() for x in lines]  
            except:
                pass

            for line_count, line in enumerate(lines):
                self.status("Checking" + " " + name + " (" + str((line_count + 1) * 100 / len(lines)) + "%)")

                cols = line.split(';')
                if len(cols) < 8:
                    continue

                date = cols.pop(0)
                try:
                    date = time.strftime('%Y-%m-%d %H:%M:%S', time.strptime(date,'%d.%m.%Y %H:%M:%S'))
                except:
                    continue
                capacity = cols.pop(0)
                used = cols.pop(0)
                duration = cols.pop(0)
                min_voltage = cols.pop(0)
                max_ampere = cols.pop(0)
                uid = cols.pop(0)
                if len(cols) == 0:
                    model_name = "Unknown model"
                else:
                    model_name = cols.pop(0)
                model_id = self.get_model_id_by_name(model_name)

                cur = self._db().cursor()
                cur.execute('SELECT id FROM batterylog WHERE batteryid=? and date=?', [battery_id, date])
                rs = cur.fetchone()
                if rs == None:
                    imported.append([model_name, model_id]) 
                    cur = self._db().cursor()
                    cur.execute('INSERT INTO batterylog (date, batteryid, modelid, duration, capacity, used, minvoltage, maxampere, uid) VALUES (?,?,?,?,?,?,?,?,?)',
                        [date, battery_id, model_id, duration, capacity, used, min_voltage, max_ampere, uid])
                    log_id = cur.lastrowid
                    self._db().commit()

                    # Lets see if we got a vbar log for this flight
                    cur = self._db().cursor()
                    cur.execute("SELECT original_filename FROM vbarlog vbl WHERE model=? AND logid IS NULL AND (date = ? AND message LIKE '%Logfile End%') OR (date <= ? AND (SELECT original_filename FROM vbarlog WHERE id=vbl.id + 1 AND date > ?) = vbl.original_filename) ORDER BY date DESC LIMIT 1",
                        [model_name, date, date, date])
                    rs = cur.fetchone()
                    if rs != None:
                        vbar_log_filename = rs["original_filename"]
                        cur = self._db().cursor()
                        cur.execute('UPDATE vbarlog SET logid = ? WHERE original_filename = ?',
                            [log_id, vbar_log_filename])
                        self._db().commit()
						
                        model_type = "HELICOPTER"
                        if vbar_log_filename.find("_vcp.log") != -1:
                            model_type = "MULTIROTOR"
                        if vbar_log_filename.find("_vplane.log") != -1:
                            model_type = "AIRPLANE"

                        # UI file has same number as VBar log file,
                        ui_log_filename = vbar_log_filename.replace('_vbar.log', '_ui.csv').replace('_vcp.log', '_ui.csv').replace('_vplane.log', '_ui.csv')

                        cur = self._db().cursor()
                        cur.execute('UPDATE uilog SET logid = ? WHERE original_filename = ?',
                            [log_id, ui_log_filename])
                        cur.execute('UPDATE model SET type = ? WHERE name = ?',
                            [model_type, model_name])
                        self._db().commit()

        return imported

    def _import_model_logs(self):
        vcontrol_path = self._find_vcontrol_path()
        log_path = os.path.join(vcontrol_path, 'log')
        for model_path in [ os.path.join(log_path, f) for f in os.listdir(log_path) if os.path.isdir(os.path.join(log_path, f)) ]:
            # Open all vbar files and check if they need importing
            for vbar_filename in [ f for f in os.listdir(model_path) if os.path.isfile(os.path.join(model_path, f))  and ('_vbar.log' in f or '_vcp.log' in f or '_vplane.log' in f) ]:
                self.status("Checking" + " " + vbar_filename)
                # import the vbar file
                with open(os.path.join(model_path, vbar_filename)) as f:
                    lines = f.readlines()
                lines = [x.strip() for x in lines]

                error = False
                is_first_line = False
                last_hour = ''
                cur = self._db().cursor()
                for line in lines:
                    # first line fetches name and date
                    if is_first_line == False:
                        is_first_line = True
                        cols = line.split(' -- ')
                        if len(cols) != 4 and 'Start' not in cols[0]:
                            error = True
                            break
                        model_name = unicode(cols[1], errors='ignore')
                        start_date = date = datetime.datetime.strptime(cols[2],'%d.%m.%Y')
                        continue

                    if ('Logfile End' in line):
                        cols = line.split(' -- ')
                        sql_date = datetime.datetime.strptime(cols[1] + ' ' + cols[2],'%d.%m.%Y %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
                        cur.execute('INSERT INTO vbarlog (original_filename, model, date, severity, message) VALUES (?,?,?,?,?)',
                            [vbar_filename, model_name, sql_date, 1, line])
                        self._db().commit()
                        break

                    cols = line.split(';')
                    if len(cols) != 3:
                        continue
                    hour = cols[0][:2]
                    # Rollover on date
                    if (last_hour == '23' and hour == '00'):
                        date = date + datetime.timedelta(days = 1)
                    sql_date = date.strftime('%Y-%m-%d') + ' ' + cols[0]

                    if (last_hour == ''):
                        cur.execute('SELECT count(*) AS cnt from vbarlog where model=? and date=?', [model_name, sql_date])
                        rs = cur.fetchone()
                        if rs["cnt"] != 0:
                            error = True
                            break

                    last_hour = hour
                    cols[2] = unicode(cols[2], errors='ignore')

                    cur.execute('INSERT INTO vbarlog (original_filename, model, date, severity, message) VALUES (?,?,?,?,?)',
                        [vbar_filename, model_name, sql_date, int(cols[1]), cols[2]])

                self._db().commit()

                if error == True:
                    continue

                # See if we have an ui file for this flight
                ui_filename = vbar_filename.replace('_vbar.log', '_ui.csv').replace('_vcp.log', '_ui.csv').replace('_vplane.log', '_ui.csv')

                if not os.path.isfile(os.path.join(model_path, ui_filename)):
                    continue

                with open(os.path.join(model_path, ui_filename)) as f:
                    lines = f.readlines()
                lines = [x.strip() for x in lines]
	
                # remove first line
                lines.pop(0)

                date = start_date

                for line in lines:
                    cols = line.split(';')
                    if len(cols) != 6:
                        continue
		
                    hour = cols[0][:2]
                    # Rollover on date
                    if (last_hour == '23' and hour == '00'):
                        date = date + datetime.timedelta(days = 1)
                    sql_date = date.strftime('%Y-%m-%d') + ' ' + cols[0]

                    cur.execute('INSERT INTO uilog (original_filename, model, date, ampere, voltage, usedcapacity, headspeed, pwm) VALUES (?,?,?,?,?,?,?,?)',
                        [ui_filename, model_name, sql_date, float(cols[1]), float(cols[2]), float(cols[3]), int(cols[4]), int(cols[5])])
                self._db().commit()
        return

    """
    FIXME: USED AT ALL?!?
    """
    def _import_ui(self, log_id, date, model_path):
        # First we need to find the file containing UI data for this flight
        # It is not guaranteed to be there. 
        # We do this by comparing the date with the dates in the _ui files
        uiFilenames = [ os.path.join(model_path,f) for f in os.listdir(model_path) if os.path.isfile(os.path.join(battery_path,f)) and "_ui" in f ]
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

    """
    Find and return the vcontrol path, if connected
    """
    def _find_vcontrol_path(self):
        return "/home/linus/vc/joel"
        if vc.globals.OS == "linux":
            import pyudev, codecs
            path = None
            context = pyudev.Context()
            for device in context.list_devices(subsystem='block'):
                dev_node = device.device_node

                mountpoint = None
                for mount in codecs.open('/proc/mounts'):
                    dev, mp, fstype = mount.split()[:3]
                    if dev.decode('ascii') == dev_node:
                        mountpoint = mp.decode('unicode_escape')
                        break
                if mountpoint is None:
                    continue
                if os.path.isfile(mountpoint + "/vcontrol.id"):
                    path = mountpoint
                    break

        elif vc.globals.OS == "osx":
            volumes = os.listdir("/Volumes")
            path = None
            for volume in volumes:
                path_test = os.path.join("/Volumes", volume)
                if os.path.isfile(os.path.join(path_test, "vcontrol.id")):
                    path = path_test
                    break

        elif vc.globals.OS == "windows":
            import ctypes
            import time
            bitmask = ctypes.windll.kernel32.GetLogicalDrives()

            path = None
            for i in xrange(26):
                bit = 2 ** i
                if bit & bitmask:
                    drive_letter = '%s:' % chr(65 + i)
                    drive_type = ctypes.windll.kernel32.GetDriveTypeA('%s\\' % drive_letter)
                    if (drive_type == 2): # Removable
                        if os.path.isfile(drive_letter + '\\vcontrol.id'):
                            path = drive_letter
                            break
        return path

    """
    Returns true if VBar Control is connected, false if not
    """
    def vcontrol_is_connected(self):
        if self._find_vcontrol_path() == None:
            return False
        return True

    """
    Extract logrows

    slice by battery_id, model_id, start_date, end_date

    all will return all rows, not just > 1/4 flight rows
    """
    def extract(self, battery_id=None, model_id=None, start_date=None, end_date=None, all_flights=False):
        sql = "\
            SELECT l.id, b.name as batteryname, m.name as modelname, l.date, l.duration, l.capacity, l.used, l.minvoltage, l.maxampere, l.uid, \
            (select count(*) > 1 from vbarlog vbl WHERE l.id=vbl.logid) as havevbarlog, \
            (select count(*) > 1 from uilog ul WHERE l.id=ul.logid) as haveuilog, \
            (select count(*) > 1 from vbarlog vbl WHERE l.id=vbl.logid and (severity=4 and (message not like '%Extreme Vibration%' AND message not like '%Gefaehrliche Vibrationen%'))) as havevbarlogproblem \
            FROM batterylog l \
            LEFT JOIN battery b on b.id=l.batteryid \
            LEFT JOIN model m on m.id=l.modelid"
        if not all_flights:
            sql += " WHERE l.used * 4 > l.capacity"
        if battery_id is not None:
            sql += " AND l.batteryid=" + str(battery_id)
        if model_id is not None:
            sql += " AND l.modelid=" + str(model_id)
        if start_date is not None:
            sql += " AND l.date >= '" + str(start_date) + "'"
        if end_date is not None:
            sql += " AND l.date < '" + str(end_date) + "'"
		
        sql += " ORDER BY date"

        cur = self._db().cursor()
        cycles = 0
        capacity_used = 0;
        flight_time_total_sec = 0
        data = []

        session_count = 0

        # Used to calulate new session
        old_date = datetime.datetime(1970,1,1)
        for row in cur.execute(sql):
            if row["modelname"] == None:
                continue

            # Calculate the session based on date
            date = datetime.datetime.strptime(row["date"], '%Y-%m-%d %H:%M:%S')
            date_diff = date - old_date
            delta_seconds = date_diff.total_seconds()
            if delta_seconds > (60 * 60 * 3):
                session_count += 1

            capacity_used += row["used"];
            cycles += 1
            flight_time_str = "{0:02d}:{1:02d}".format(int(row["duration"] / 60), int(row["duration"] % 60))
            flight_time_total_sec += row["duration"]
            used = str(row["used"]) + ' (' + str(int(float(row["used"]) / row["capacity"] * 100)) + '%)'

            data.append({
                'id': row["id"], 
                'date': row["date"], 
                'battery': row["batteryname"], 
                'model': row["modelname"], 
                'duration': flight_time_str, 
                'capacity': row["capacity"], 
                'used': used, 
                'minv': row["minvoltage"], 
                'maxa': row["maxampere"], 
                'idlev': row["uid"], 
                'session': session_count, 
                'havevbarlog': row["havevbarlog"], 
                'haveuilog': row["haveuilog"], 
                'havevbarlogproblem': row["havevbarlogproblem"] 
            })
            old_date = date

        capacity_used = round(float(capacity_used) / 1000, 2)
        flight_time_total_str = "{0:02d}:{1:02d}:{2:02d}".format(
            int(flight_time_total_sec / 3600), 
            int((flight_time_total_sec % 3600) / 60), 
            int(flight_time_total_sec % 60)
        )

        totals = {
            'cycles': cycles, 
            'used': capacity_used, 
            'duration': flight_time_total_str, 
            'sessions': session_count
        }; 

        return {
            'data' : data, 
            'totals': totals 
        }

    """
    Returns all seasons as an array of years
    """
    def get_seasons(self):
        cur = self._db().cursor()
        cur.execute("SELECT MIN(date) AS mindate, MAX(date) AS maxdate FROM batterylog WHERE date IS NOT NULL")
        rs = cur.fetchone()

        if rs["mindate"] == None:
            return [str(datetime.datetime.now().year)]

        first = int(rs["mindate"][0:4])
        last = int(rs["maxdate"][0:4])

        out = []
        for y in xrange(first,last + 1):
            out.append(str(y))

        return out

    """
    Extract to weeks
    """
    def extract_to_weeks(self, battery_id=None, model_id=None, start_date=None, end_date=None, group='model'):
        data = self.extract(battery_id, model_id, start_date, end_date)
        out = []
        if len(data['data']) > 0:
            current = datetime.datetime.strptime(data['data'][0]['date'], '%Y-%m-%d %H:%M:%S');
            current_year = current.isocalendar()[0];
            current_week = current.isocalendar()[1];
            current = datetime.datetime.strptime(str(current_year) + "-" + str(current_week - 1) + "-1", '%Y-%W-%w');
            current_week_str = str(current.isocalendar()[0]) + "-" + str(current.isocalendar()[1])
            out.append({'week': current_week_str, 'group': {}})

            data['data'] = list(reversed(data['data']))

            while True:
                row = data['data'][-1]
                row_date = datetime.datetime.strptime(row['date'], '%Y-%m-%d %H:%M:%S').isocalendar();
                year = row_date[0];
                week = row_date[1];
                week_str = str(year) + "-" + str(week)
                if out[-1]['week'] == week_str:
                    if row[group] not in out[-1]['group']:
                        out[-1]['group'][row[group]] = 0
                    out[-1]['group'][row[group]] += 1
                    data['data'].pop()
                    if len(data['data']) == 0:
                        break
                else:
                    current = current + datetime.timedelta(days=7)
                    current_week_str = str(current.isocalendar()[0]) + "-" + str(current.isocalendar()[1])
                    out.append({'week': current_week_str, 'group': {}})

        data['data'] = out
        return data

    def extract_info_by_log_id(self, log_id):
        sql ="\
            SELECT b.name as batteryname, m.name as modelname, l.date \
            FROM batterylog l \
            LEFT JOIN battery b on b.id=l.batteryid \
            LEFT JOIN model m on m.id=l.modelid \
            WHERE l.id=" + str(log_id)

        cur = self._db().cursor()
        cur.execute(sql)
        row = cur.fetchone()
        info = {
            'model': row["modelname"],
            'battery': row["batteryname"],
            'date': row["date"]
        }
        return info

    def extract_ui_by_log_id(self, log_id):
        sql = "\
            SELECT  model, date, ampere, voltage, usedcapacity, headspeed, pwm FROM uilog where logid=" + str(log_id)

        cur = self._db().cursor()
        out = []
        clipStart = False
        clipEnd = False
        i = 0
        lastNotZero = 0
        firstNotZero = 0
        firstRPM = False
        lastRPM = False
        for row in cur.execute(sql):
            if firstRPM == False:
                firstRPM = row["date"]
            lastRPM = row["date"]

            if clipStart == False and int(row["headspeed"]) != 0:
                clipStart = row["date"]

            if  firstNotZero == 0 and int(row["headspeed"]) != 0:
                firstNotZero = i

            out.append({
                'model': row["model"],
                'current': float(row["ampere"]),
                'voltage': float(row["voltage"]),
                'usedcapacity': float(row["usedcapacity"]),
                'headspeed': int(row["headspeed"]),
                'pwm': int(row["pwm"])
            })
            if int(row["headspeed"]) != 0:
                lastNotZero = i
                clipEnd = row["date"]
            i+=1

        if clipStart == False:
            clipStart = firstRPM
            clipEnd = lastRPM
        else:
            out = out[firstNotZero:lastNotZero]

        # Now we shuold evenly distribute end over the
        # seconds in clipStart and clipEnd
        # We need to know the number of seconds beetween clipStart and clipEnd
        start =time.mktime(time.strptime(clipStart, '%Y-%m-%d %H:%M:%S'))
        end =time.mktime(time.strptime(clipEnd, '%Y-%m-%d %H:%M:%S'))
        dur = end - start

        for i,row in enumerate(out):
            out[i]['sec'] = (float(i) / len(out)) * dur

        return out

    def extract_vbar_log(self, log_id):
        sql = "\
            SELECT  model, date, severity, message FROM vbarlog where logid=" + str(log_id)
        cur = self._db().cursor()
        out = []
        for row in cur.execute(sql):
            out.append({
                'model': row["model"],
                'date': row["date"],
                'severity': int(row["severity"]),
                'message': row["message"]
            })
        return out

    def extract_model_info(self, model_id):
        cur = self._db().cursor()
        cur.execute("SELECT name, type, info, image FROM model WHERE id=?", [str(model_id)])
        row = cur.fetchone()
        name = row["name"]
        model_type = row["type"]
        info = row["info"]
        if (info is None):
            info = ""
        photo_bitmap = row["image"]
        if photo_bitmap is not None:
            photo_bitmap = QtGui.QPixmap.fromImage(QtGui.QImage.fromData(str(row["image"])))

        data = self.extract(battery_id=None, model_id=model_id, start_date=None, end_date=None, all_flights=False)
        cycles = data['totals']['cycles']
        duration = data['totals']['duration']
        first = data['data'][0]['date'][:10]
        last = data['data'][-1]['date'][:10]

        data = {
            'name': name,
            'type': model_type,
            'info': info,
            'image': photo_bitmap,
            'cycles' : cycles,
            'duration' : duration,
            'first' : first,
            'last' : last
        }

        return data

    def set_model_info(self, model_id, info):
        cur = self._db().cursor()
        cur.execute("UPDATE model set info = ? WHERE id=?", [info, str(model_id)])
        self._conn.commit();
        cur.close()

    def set_model_image(self, model_id, thumb_image, image):
        cur = self._db().cursor()
        cur.execute("UPDATE model set thumb = ?, image=? WHERE id=?", [sqlite3.Binary(thumb_image), sqlite3.Binary(image), str(model_id)])
        self._conn.commit();
        cur.close()

    def clear_model_image(self, model_id):
        cur = self._db().cursor()
        cur.execute("UPDATE model set thumb = NULL, image=NULL WHERE id=?", [str(model_id)])
        self._conn.commit();
        cur.close()
 
    def status(self, str):
        if self._import_callback is None:
            return
        self._import_callback(str)
