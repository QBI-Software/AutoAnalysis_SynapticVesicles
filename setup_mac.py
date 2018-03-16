'''
    QBI Auto Analysis APP: setup_mac.py (Mac OSX package)
    *******************************************************************************
    Copyright (C) 2017  QBI Software, The University of Queensland

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

Usage:
    python3 setup.py py2app

    [ref: http://doc.qt.io/qt-4.8/deployment-mac.html]
'''
import sys
from os.path import join
from os import getcwd
#Self -bootstrapping https://py2app.readthedocs.io
import ez_setup
ez_setup.use_setuptools()

from setuptools import setup

from App import __version__


application_title = 'QBI AutoAnalysis SynapticVesicles'
main_python_file = join('.','App.py')
venvpython = join(sys.prefix,'Lib','site-packages')
mainpython = "/Library/Frameworks/Python.framework/Versions/3.6/bin/python3"

# Add info to MacOSX plist
# plist = Plist.fromFile('Info.plist')
plist = dict(CFBundleDisplayName=application_title,
             NSHumanReadableCopyright='Copyright (c) 2018 Queensland Brain Institute',
             CFBundleTypeIconFile='autoanalysis/resources/newplot.ico',
             CFBundleVersion=__version__
            )

APP = ['App.py']
DATA_FILES = ['autoanalysis/resources/']
PARENTDIR= getcwd()
OPTIONS = {'argv_emulation': True,
           'use_pythonpath': True,
           'plist': plist,
           'iconfile': 'autoanalysis/resources/newplot.ico',
           #'packages': ['sqlite3','scipy', 'wx'],
           'bdist_base': join(PARENTDIR, 'build'),
           'dist_dir': join(PARENTDIR, 'dist'),
           }

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
