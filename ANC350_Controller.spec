# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

_project_root = Path(SPECPATH)

a = Analysis(
    [str(_project_root / 'app' / 'main.py')],
    pathex=[str(_project_root)],
    binaries=[],
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
    optimize=0,
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
    strip=False,
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
)
