# -*- mode: python -*-
import sys

##### include mydir in distribution #######
def extra_datas(mydir):
    def rec_glob(p, files):
        import os
        import glob
        for d in glob.glob(p):
            if os.path.isfile(d):
                files.append(d)
            rec_glob("%s/*" % d, files)
    files = []
    rec_glob("%s/*" % mydir, files)
    extra_datas = []
    print files
    for f in files:
        extra_datas.append((f, f, 'DATA'))

    return extra_datas
###########################################

a = Analysis(['src/VbcAnalyzer.py'],
             pathex=['./src'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)

a.datas += extra_datas('assets')
a.datas += extra_datas('locale')


if "linux" in sys.platform:
    name = "VbcAnalyzer.linux"
elif "darwin" in sys.platform:
    name = "VbcAnalyzer.osx"
else:
    name = "VbcAnalyzer.exe"

for d in a.datas:
    if 'pyconfig' in d[0]: 
        a.datas.remove(d)
        break
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name=name,
          debug=False,
          strip=None,
          upx=True,
          windowed=True,
          onefile=True,
          icon='assets/logo/logo.ico',
          console=False )


if "darwin" in sys.platform:
   app = BUNDLE(exe,
                name='VbcAnalyzer.app',
                icon="assets/logo/logo.icns")
