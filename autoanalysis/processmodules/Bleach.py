# -*- coding: utf-8 -*-
"""
Bleach class
    1. Read INPUTFILES as CSV (Traces data, Bleach data)
    - expects Time,Frame colums in Traces data and Average in Bleach data
    2. Subtracts bleach data from traces
    3. Outputs data to excel (with raw, processed tabs) - including Time
    4. Generates list of ROIs for selection
    5. Generates plots of each ROI as interactive html plots - multiple pages of 9 plots per page


Created on 23 Feb 2018

@author: Liz Cooper-Williams, QBI, e.cooperwilliams@uq.edu.au
"""

import argparse
import logging
import sys
from os.path import join, basename, splitext
from collections import OrderedDict
import pandas as pd
import xlsxwriter
from autoanalysis.db.dbquery import DBI
from autoanalysis.processmodules.DataParser import AutoData
import plotly.graph_objs as go
from plotly import tools
from plotly import offline


class Bleach(AutoData):
    """
    Filter class for filtering a dataset based on a single column of data between min and max limits
    """
    def __init__(self, datafiles,outputdir, sheet=0, skiprows=0, headers=None, showplots=False):
        #Two input data files 1. Datafile 2. Bleachdata
        if isinstance(datafiles, list) and len(datafiles)==2:
            datafile = datafiles[0]
            bleachfile = datafiles[1]
        else:
            raise IOError("Two input files required: datafile and bleachdata")
        # Load data

        super().__init__(datafile, sheet, skiprows, headers)
        msg = "BLEACH: Data loaded from %s" % self.datafile
        self.logandprint(msg)
        self.datafile = bleachfile
        self.bleachdata = self.load_data()
        msg = "BLEACH: Data loaded  from %s" % self.datafile
        self.logandprint(msg)
        # Output
        self.suffix = 'Empty.xlsx' #maybe overwritten by configurables
        self.outputdir = outputdir
        self.showplots = showplots

    def getConfigurables(self):
        '''
        List of configurable parameters in order with defaults
        :return:
        '''
        cfg = OrderedDict()
        cfg['EXPT_EXCEL']='*Empty.xlsx'
        return cfg

    def setConfigurables(self,cfg):
        if 'EXPT_EXCEL' in cfg.keys() and cfg['EXPT_EXCEL'] is not None:
            self.suffix = cfg['EXPT_EXCEL']
            if self.suffix.startswith('*'):
                self.suffix = self.suffix[1:]

    def outputExcelData(self, outputfile,all):
        writer = pd.ExcelWriter(outputfile, engine='xlsxwriter')
        for field in all.keys():
            df_all = all[field]
            df_all.to_excel(writer, index=False, sheet_name=field)
        else:
            return outputfile

    def generatePlots(self,xt, df, title,outputfile):
        # Scatter plots
        fig = tools.make_subplots(rows=3, cols=3, shared_xaxes=True, subplot_titles=df.columns)
        pnum =0
        for row in range(1,4):
            for col in range(1,4):
                if pnum < len(df.columns):
                    fig.append_trace(
                        go.Scatter(
                            x=xt,
                            y=df[df.columns[pnum]].values,
                            name=df[df.columns[pnum]].name,
                            mode='markers'
                        ), row=row, col=col)
                    pnum += 1
        fig['layout']['title'] = title
        fig['layout']['xaxis2']['title'] = 'Time (s)'
        #fig['layout']['yaxis2']['title'] = 'Signal'
        offline.plot(fig, filename=outputfile)
        return fig

    def saveROIlist(self,roilist):

        outputfile = join(self.outputdir, self.bname + self.roilist)
        with open(outputfile, 'w') as myfile:
            for v in roilist:
                if v.startswith('ROI'):
                    myfile.write(v)
                    myfile.write('\n')
        msg = "ROI list saved: %s" % outputfile
        self.logandprint(msg)

    def run(self):
        """
        Insert and subtract bleachdata from data
        :return:
        """
        if not self.data.empty:
            #subtract per row
            hdrs = [h for h in self.data.columns if h.startswith('ROI')]
            df_subtracted = self.data[hdrs].subtract(self.bleachdata['Average'], axis=0)
            #insert bleach avg column
            self.data['Bleach Average']=self.bleachdata['Average']
            if 'Time' in self.data.columns:
                df_subtracted['Time'] = self.data['Time']
            traces = {'raw': self.data, 'bleach subtracted': df_subtracted}
            try:
                outputfile = join(self.outputdir, self.bname + "_" + self.suffix)
                self.outputExcelData(outputfile,traces)
                msg = "Subtracted Data saved: %s" % outputfile
                self.logandprint(msg)
                # Save ROI list to csv
                self.saveROIlist(df_subtracted.columns.tolist())

                if self.showplots:
                    title = self.bname +': ROIs with Bleach Subtracted'
                    if 'Time' in df_subtracted.columns:
                        xt = df_subtracted['Time']
                    else:
                        raise ValueError('Time column is missing - no plots generated')
                    pagenum =1
                    start=0
                    endplot = 0
                    n = len(df_subtracted.columns)
                    for endplot in range(start,n,9):
                        if endplot ==0:
                            continue
                        plotfilename = outputfile.replace('.xlsx',"_"+ str(pagenum) + '.html')
                        self.generatePlots(xt,df_subtracted[df_subtracted.columns[start:endplot]], title, plotfilename)
                        msg = "Subtracted Data plots: %s" % plotfilename
                        self.logandprint(msg)
                        pagenum += 1
                        start += 9
                    #remaining plots
                    if endplot < n-1:
                        plotfilename = outputfile.replace('.xlsx', "_" + str(pagenum) + '.html')
                        self.generatePlots(xt, df_subtracted[df_subtracted.columns[endplot:n-1]], title, plotfilename)
                        msg = "Subtracted Data plots: %s" % plotfilename
                        self.logandprint(msg)
            except IOError as e:
                raise e

def create_parser():
    """
    Create commandline parser
    :return:
    """

    parser = argparse.ArgumentParser(prog=sys.argv[0],
                                     description='''\
                Reads bleach data and subtracts from data with output to Excel

                 ''')
    parser.add_argument('--datafile', action='store', help='Data file', default="EXP44_Empty_Time Trace(s).csv")
    parser.add_argument('--bleachfile', action='store', help='Data file', default="Bleach Time Trace(s).csv")
    parser.add_argument('--outputdir', action='store', help='Output directory', default="D:\\Projects\\Anggono\\data")
    parser.add_argument('--suffix', action='store', help='Output filename suffix', default="Processed.xlsx")
    parser.add_argument('--roilist', action='store', help='Selected ROI list', default="_ROIlist.csv")

    return parser

####################################################################################################################
if __name__ == "__main__":

    parser = create_parser()
    args = parser.parse_args()
    inputdir = args.outputdir
    datafiles = [join(inputdir, args.datafile),join(inputdir, args.bleachfile)]

    print("Input:", datafiles)
    print("Output:", args.outputdir)

    try:
        mod = Bleach(datafiles, args.outputdir,showplots=False)
        cfg = mod.getConfigurables()
        for c in cfg.keys():
            print("config set: ",c,"=", cfg[c])
        #set values - this will be done from configdb
        cfg['EXPT_EXCEL']=args.suffix
        cfg['ROI_LIST'] = args.roilist
        mod.setConfigurables(cfg)
        if mod.data is not None:
            mod.run()

    except Exception as e:
        print("Error: ", e)

