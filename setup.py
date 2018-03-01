'''
    QBI Auto Analysis APP: setup.py (Windows 64bit MSI)
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
'''
#
# Step 1. Build first
#   python setup.py build
# View build dir contents
# Step 2. Create MSI distribution (Windows)
#   python setup.py bdist_msi
# View dist dir contents
####
# Issues with scipy and cx-freeze -> https://stackoverflow.com/questions/32432887/cx-freeze-importerror-no-module-named-scipy
# 1. changed cx_Freeze/hooks.py scipy.lib to scipy._lib (line 560)
#then run setup.py build
# 2. changed scipy/spatial cKDTree.cp35-win_amd64.pyd to ckdtree.cp35-win_amd64.pyd
# 3. change Plot.pyc to plot.pyc in multiprocessing
# test with exe
# then run bdist_msi

import os
import sys
import shutil
from os.path import join
from cx_Freeze import setup, Executable
from autoanalysis.App import __version__

application_title = 'QBI Auto Analysis - Synaptic Vesicles'
main_python_file = join('autoanalysis','App.py')
venvpython = join(sys.prefix,'Lib','site-packages')
mainpython = "D:\\Programs\\Python36"

os.environ['TCL_LIBRARY'] = join(mainpython, 'tcl', 'tcl8.6')
os.environ['TK_LIBRARY'] = join(mainpython, 'tcl', 'tk8.6')
base = None
if sys.platform == 'win32':
    base = 'Win32GUI'

build_exe_options = {
    'includes': ['idna.idnadata', "numpy", "plotly", "packaging.version","packaging.specifiers", "packaging.requirements","appdirs",'scipy.spatial.cKDTree'],
    'excludes': ['PyQt4', 'PyQt5'],
    'packages': ['scipy','seaborn', 'numpy.core._methods', 'numpy.lib.format', 'plotly'],
    'include_files': ['autoanalysis/',
                      #join(venvpython, 'seaborn', 'external'),
                      #join(mainpython, 'DLLs', 'tcl86t.dll'),
                      #join(mainpython, 'DLLs', 'tk86t.dll'),
                      (join(venvpython, 'scipy', 'special', '_ufuncs.cp36-win32.pyd'), '_ufuncs.pyd')],
    'include_msvcr': 1
}
# [Bad fix but only thing that works] NB To add Shortcut working dir - change cx_freeze/windist.py Line 61 : last None - > 'TARGETDIR'
setup(
    name=application_title,
    version=__version__,
    description='Auto analysis of synaptic vesicle particle tracking data (Anggono)',
    long_description=open('README.md').read(),
    author='Liz Cooper-Williams, QBI',
    author_email='e.cooperwilliams@uq.edu.au',
    maintainer='QBI Custom Software, UQ',
    maintainer_email='qbi-dev-admin@uq.edu.au',
    url='http://github.com/QBI-Software/AutoAnalysis_SynapticVesicles',
    license='GNU General Public License (GPL)',
    options={'build_exe': build_exe_options, },
    executables=[Executable(main_python_file, base=base, targetName='aasv_analysis.exe', icon='autoanalysis/resources/measure.ico',shortcutName=application_title, shortcutDir='DesktopFolder')]
)

#Rename ckdtree
os_version='exe.win32-3.6' #'exe.win-amd64-3.5'
ckd_version= 'cKDTree.cp36-win32.pyd'#'cKDTree.cp35-win_amd64.pyd'
shutil.move(join('build',os_version,'lib','scipy','spatial',ckd_version), join('build',os_version,'lib','scipy','spatial','ckdtree.pyd'))
shutil.copyfile(join('build',os_version,'lib','scipy','spatial','ckdtree.pyd'), join('build',os_version,'lib','scipy','spatial',ckd_version))
