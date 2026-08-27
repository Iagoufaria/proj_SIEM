# -*- mode: python ; coding: utf-8 -*-
# Spec do PyInstaller para gerar o executavel do SIEM TCC.
# Gere o .exe rodando (no Windows, dentro do venv do projeto):
#     pyinstaller siem.spec
#
# O executavel final aparece em dist/SIEM_TCC.exe

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
    ],
    hiddenimports=[
        'webview.platforms.winforms',
        'webview.platforms.edgechromium',
        'flask_login',
        'flask_wtf',
        'argon2',
        '_cffi_backend',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='SIEM_TCC',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # troque para True temporariamente se precisar ver logs/erros
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,              # opcional: aponte para um arquivo .ico do seu projeto
)
