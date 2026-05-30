# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

_project_root = Path(SPECPATH)

# If running in a conda environment, include required DLLs from Library/bin.
# Derive conda prefix from the running Python executable (handles unactivated conda).
_conda_prefix = os.environ.get('CONDA_PREFIX', '')
if not _conda_prefix:
    # e.g. <conda_env>/python.exe → derive conda prefix
    _py_exe = Path(os.path.abspath(sys.executable))
    if (_py_exe.parent / 'Library' / 'bin').is_dir():
        _conda_prefix = str(_py_exe.parent)
    elif (_py_exe.parent.parent / 'Library' / 'bin').is_dir():
        _conda_prefix = str(_py_exe.parent.parent)

_conda_binaries = []
if _conda_prefix:
    _conda_lib_bin = Path(_conda_prefix) / 'Library' / 'bin'
    if _conda_lib_bin.is_dir():
        # libffi is required by _ctypes.pyd in conda-packaged Python
        for _dll in _conda_lib_bin.glob('ffi*.dll'):
            _conda_binaries.append((str(_dll), '.'))

a = Analysis(
    [str(_project_root / 'app' / 'main.py')],
    pathex=[str(_project_root)],
    binaries=_conda_binaries,
    datas=[
        (str(_project_root / 'anc350v4.dll'), '.'),
        (str(_project_root / 'libusb0.dll'), '.'),
        (str(_project_root / 'app' / 'icon.png'), '.'),
    ],
    hiddenimports=[
        'pyqtgraph',
        'pyqtgraph.graphicsItems',
        'anc350._dll',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'scipy', 'pandas', 'matplotlib', 'PIL', 'numba', 'llvmlite',
        'skimage', 'scikit-learn', 'sklearn', 'tables', 'h5py',
        'astropy', 'astropy_iers_data', 'imageio', 'pywt', 'tifffile',
        'bokeh', 'plotly', 'holoviews', 'datashader', 'panel',
        'altair', 'seaborn', 'statsmodels', 'patsy',
        'dask', 'distributed', 'xarray', 'pyarrow', 'fsspec',
        'sphinx', 'docutils', 'nbformat', 'nbconvert', 'notebook',
        'jupyterlab', 'ipython', 'ipykernel', 'jedi', 'parso',
        'spyder', 'spyder_kernels', 'qtconsole', 'QDarkStyle',
        'black', 'yapf', 'pylint', 'astroid', 'isort', 'rope',
        'pytest', 'flake8', 'pyflakes', 'pydocstyle', 'autopep8',
        'nltk', 'textdistance', 'scrapy', 'twisted', 'lxml',
        'sqlalchemy', 'botocore', 'aiobotocore', 's3fs',
        'bcrypt', 'paramiko', 'cryptography', 'pyOpenSSL',
        'streamlit', 'flask', 'werkzeug', 'jinja2', 'babel',
        'rich', 'markdown', 'pygments',
        'openpyxl', 'xlwings',
        'psutil',
        'PyQt5.QtWebEngineWidgets',
    ],
    noarchive=False,
    optimize=1,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ANC350_Controller',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(_project_root / 'app' / 'icon.png'),
    version=str(_project_root / 'app' / 'version_info.txt'),
)
