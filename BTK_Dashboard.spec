# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, copy_metadata, collect_submodules

# Collect streamlit's static files and metadata so the UI renders
datas = []
datas += collect_data_files('streamlit')
datas += copy_metadata('streamlit')
datas += copy_metadata('plotly')

# Ensure our local application files are bundled into the executable
datas += [
    ('app.py', '.'),
    ('data_processor.py', '.'),
    ('components', 'components'),
    ('.streamlit', '.streamlit')
]

# Streamlit uses many dynamic imports internally (like magic_funcs). 
# We explicitly force PyInstaller to bundle all streamlit submodules.
hidden_imports = collect_submodules('streamlit')

a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='BTK_Admin_Dashboard',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
