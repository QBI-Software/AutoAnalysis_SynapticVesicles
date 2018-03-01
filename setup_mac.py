"""
Usage:
    python3 setup.py py2app

    [ref: http://doc.qt.io/qt-4.8/deployment-mac.html]
"""
from setuptools import setup
from plistlib import Plist
from os.path import join
import sys
from autoanalysis.App import __version__
application_title = 'QBI AutoAnalysis SynapticVesicles'
main_python_file = join('autoanalysis','App.py')
venvpython = join(sys.prefix,'Lib','site-packages')
mainpython = "D:\\Programs\\Python36"

# Add info to MacOSX plist
# plist = Plist.fromFile('Info.plist')
plist = dict(CFBundleDisplayName=application_title,
             NSHumanReadableCopyright='Copyright (c) 2018 Queensland Brain Institute',
             CFBundleTypeIconFile='autoanalysis/resources/measure.ico',
             CFBundleVersion=__version__)

APP = ['appgui.py']
DATA_FILES = ['autoanalysis/resources/']
OPTIONS = {'argv_emulation': True,
           'plist': plist,
           'iconfile': 'autoanalysis/resources/measure.ico',
           'includes': ['idna.idnadata', "numpy", "plotly", "packaging.version","packaging.specifiers", "packaging.requirements","appdirs",'scipy.spatial.cKDTree'],
    'excludes': ['PyQt4', 'PyQt5'],
    'packages': ['scipy','seaborn', 'numpy.core._methods', 'numpy.lib.format', 'plotly'],
    'include_files': ['autoanalysis/', (join(venvpython, 'scipy', 'special', '_ufuncs.cp36-win32.pyd'), '_ufuncs.pyd')],
           }

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
