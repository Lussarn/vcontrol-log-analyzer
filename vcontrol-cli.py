#!/usr/bin/python

import sys
import VBarLogAnalyzer

def usage():
	print "vcontrol-cli.py --help                            This help"
	print "vcontrol-cli.py --version                         Version information"
	print "vcontrol-cli.py --import [PATH_TO_VCONTROL]       import data from vbar control"
	print "vcontrol-cli.py --list                            List batteries and models"
	print "vcontrol-cli.py --extract [model=id]              Extract data" 
	print "                   [battery=id]" 
	print "                   [start=YYYY-MM-DD]"
	print "                   [end=YYYY-MM-DD]"

def list_gear():
	analyzer = VBarLogAnalyzer.Analyzer()
	gear = analyzer.list_gear()

	print "Batteries:"
	for idbattery in gear['batteries']:
		print '   id:',idbattery, ' name: ',gear['batteries'][idbattery]

	print "Models:"
	for idmodel in gear['models']:
		print '   id:',idmodel, ' name: ',gear['models'][idmodel]


def extract():
	batteryid = None
	modelid = None
	start = None
	end = None

	while len(sys.argv) > 0:
		ar = sys.argv.pop(0).split('=', 1)

		if ar[0] == 'battery':
			if len(ar) != 2:
				print "Unknown battery"
				exit(1);
			batteryid = int(ar[1])

		elif ar[0] == 'model':
			if len(ar) != 2:
				print "Unknown model"
				exit(1);
			modelid = int(ar[1])

		elif ar[0] == 'start':
			if len(ar) != 2:
				print "Unknown start"
				exit(1);
			start = ar[1]

		elif ar[0] == 'end':
			if len(ar) != 2:
				print "Unknown end"
				exit(1);
			end = ar[1]

		else:
			print "Unknown extract parameter:",ar[0]
			exit(1);

	analyzer = VBarLogAnalyzer.Analyzer()

	data = analyzer.extract(batteryid=batteryid, modelid=modelid, start=start, end=end)

	header  = "+-------+---------------------+---------------------+---------------------+----------+----------+-------------+-------+-------+-------+-------+-------+"
	header2 = "+-----------------------------+-------------------------------------------+-----------------------------------+---------------------------------------+"

	print header
	print "| Id    | Date                | Battery             | Model               | Duration | Capacity | Used        | MinV  | MaxA  | IdleV | VBLog | UILog |" 
#	print header

	session = 0
	for row in data['data']:
		if session != row['session']:
			session = row['session']
			print header

		havevbarlog=' '
		if row['havevbarlog'] == 1:
			havevbarlog = '  *'

		haveuilog=' '
		if row['haveuilog'] == 1:
			haveuilog = '  *'

		print "| {0:<6}| {1:<20}| {2:<20}| {3:<20}| {4:<9}| {5:<9}| {6:<12}| {7:<6}| {8:<6}| {9:<6}| {10:<6}| {11:<6}|".format(
			row['id'],
			row['date'],
			row['battery'],
			row['model'], 
			row['duration'],
			row['capacity'],
			row['used'], 
			row['minv'], 
			row['maxa'], 
			row['idlev'],
			havevbarlog,
			haveuilog
		)

	print header
	print "| Cycles: {0:<19} | Capacity used: {1:<26} | Duration: {2:<23} | Sessions: {3:<27} |".format(str(data['totals']['cycles']), str(data['totals']['used']) + "Ah", data['totals']['duration'], data['totals']['sessions'])
	print header2

def import_data():
	analyzer = VBarLogAnalyzer.Analyzer()
	if analyzer.vcontrol_is_connected() == False:
		print "Error: No VBar Control found"
		exit(1)
	print "Importing logs from VBar Control..."
	res = analyzer.import_data()
	if res == False:
		print analyzer.error
		exit(1)

	if len(res) == 0:
		print "Nothing to import!"
		exit(0)

	for row in res:
		print "Imported Model: " + row[1], "Battery: " + row[0]


# Main start
def main():
	if len(sys.argv) == 1:
		usage()
		exit(1);

	# Shift progmran name
	sys.argv.pop(0)

	command = sys.argv.pop(0)
	if command == '--import':
		import_data()
	elif command == '--list':
		list_gear()
	elif command == '--extract':
		extract()
	elif command == '--help':
		usage()
	elif command == '--version':
		print "vcontrol-cli v2.7.1"
	else:
		usage()

main()
