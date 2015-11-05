@echo off
call tools\buildui.bat
c:\Python27\Scripts\pyinstaller.exe --onefile VbcAnalyzer.spec

echo Build done
set /P Q=Copy executable to desktop (y/n)

echo %Q%

if "%Q%" == "y" (
	echo Copying...
	copy dist/VbcAnalyzer.exe %HOMEPATH%\Desktop
)