# -*- mode: python -*-
a = Analysis(['vcontrol-gui.py'],
             pathex=['C:\\Users\\Linus\\Desktop\\python\\vcontrol-log-analyzer'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
a.datas += [('assets/img/ball-green.png', 'C:\\Users\\Linus\\Desktop\\python\\vcontrol-log-analyzer\\assets\\img\\ball-green.png','DATA'),
('assets/img/ball-red.png', 'C:\\Users\\Linus\\Desktop\\python\\vcontrol-log-analyzer\\assets\\img\\ball-red.png','DATA')] 
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
          name='vcontrol-gui.exe',
          debug=False,
          strip=None,
          upx=True,
          console=False )