# -*- mode: python -*-

# Attempts to configure PyInstaller for roguelike
# libtcodpy *conditionally* imports numpy, but PyInstaller
# can't seem to deal with that conditionality and makes it a
# hard requirement.

block_cipher = None

fonts = [('arial12x12.png', '.')]

tcod_dlls = [('libtcod-VS.dll', '.'),
			 ('SDL.dll', '.'),
			 ('zlib1.dll', '.')]

options = [('v', None, 'OPTION'), ('u', None, 'OPTION')]

a = Analysis(['roguelike.py'],
             pathex=['C:\\Projects\\libtcodpy-tutorial'],
             binaries=tcod_dlls,
             datas=fonts,
             hiddenimports=['encodings.codecs', 'encodings.encodings', 'encodings.__builtin__',
							'ctypes.os', 'ctypes.sys', 'ctypes._ctypes', 'ctypes.struct'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
		  options,
          exclude_binaries=True,
          name='roguelike',
          debug=False,
          strip=False,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='roguelike')
