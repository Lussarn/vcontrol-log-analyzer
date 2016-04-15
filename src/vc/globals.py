"""
Global Config variables 
"""
import sys

# Program name
PROGRAM_NAME = "VBar Control flight analyzer"

# Program version
VERSION = "v4.1.0"

# Implemented translations
TRANSLATIONS = ['en']


if sys.platform.startswith("linux"):
    OS = "linux"
elif sys.platform.startswith("darwin"):
    OS = "osx"
elif sys.platform.startswith("win32"):
    OS = "windows"
else:
    print "Unknown OS"
    exit
