from setuptools import setup

APP = ['main.py']
DATA_FILES = ['target.jpg', 'tracker.py', 'calib_module.py']
OPTIONS = {
    'argv_emulation': True,
    'packages': ['cv2', 'numpy', 'PIL', 'tkinter'],
    'resources': DATA_FILES,
}

setup(
    app=APP,
    options={'py2app': OPTIONS},
    data_files=DATA_FILES,
    setup_requires=['py2app'],
)