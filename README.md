# vcontrol-log-analyzer
Log analyzer for VBar control

Vcontrol is a program to analyze battery logs from Mikado VBar Control

vcontrol is a standalone program, database is created in home directory .vcontrol.db

To start mount the vbar control and do an import (the import path is remembered and you don't need to supply it later)

vcontrol --import /path/to/vcontrol/

Now you can disconnect vbar control from computer if you wish

To list gear (batteries and helis)
vcontrol --list

To extract data
vcontrol --extract [options]