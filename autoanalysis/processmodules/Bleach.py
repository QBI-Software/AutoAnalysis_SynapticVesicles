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
from os import access,R_OK
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
    def __init__(self, datafile,outputdir, sheet=0, skiprows=0, headers=None, showplots=False):
        # Load data
        try:
            super().__init__(datafile, sheet, skiprows, headers)
            #remove any extra lines
            self.data = self.data.dropna()
            msg = "BLEACH: Data loaded from %s" % self.datafile
            self.logandprint(msg)
            # Output
            self.outputdir = outputdir
            self.showplots = showplots
            # Set config defaults
            self.cfg = self.getConfigurables()
        except IOError as e:
            self.logandprint(e.args[0])
            raise e
        except Exception as e:
            self.logandprint(e.args[0])
            raise e

    def getConfigurables(self):
        '''
        List of configurable parameters in order with defaults
        :return:
        '''
        cfg = OrderedDict()
        cfg['EXPT_EXCEL']='_Processed.xlsx'
        cfg['ROI_FILE'] = '_ROIlist.csv'
        cfg['BLEACH_FILENAME'] = 'Bleach Time Trace(s).csv'
        return cfg

    def setConfigurables(self,cfg):
        '''
        Merge any variables set externally
        :param cfg:
        :return:
        '''
        if self.cfg is None:
            self.cfg = self.getConfigurables()
        for cf in cfg.keys():
            self.cfg[cf]= cfg[cf]
        self.logandprint("Config loaded")

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
        roifile = self.getFilename('ROI_FILE')
        with open(roifile, 'w') as myfile:
            for v in roilist:
                if v.startswith('ROI'):
                    myfile.write(v)
                    myfile.write('\n')
        msg = "ROI list saved: %s" % roifile
        self.logandprint(msg)

    def getFilename(self, cfgparam, input=False):
        '''
        Compile filename from config
        - if starts with underscore then append to basename otherwise use this name
        :param cfgparam: config param var eg ROI_FILE as found in cfg and db
        :param input: if this file is in the inputdir then true otherwise use outputdir
        :return: full path filename
        '''
        filename = self.cfg[cfgparam]
        if filename.startswith('_'):
            filename = self.bname + filename
        if input:
            outputfile = join(self.inputdir,filename)
        else:
            outputfile = join(self.outputdir,filename)
        return outputfile

    def run(self):
        """
        Insert and subtract bleachdata from data
        :return:
        """
        # Load bleach data
        bleachdatafile = self.getFilename('BLEACH_FILENAME', input=True)
        if access(bleachdatafile,R_OK):
            self.bleachdata = pd.read_csv(bleachdatafile, skip_blank_lines=True)
            msg = "BLEACH: Data loaded  from %s" % bleachdatafile
            self.logandprint(msg)
        else:
            raise IOError('Bleach data not accessible:', bleachdatafile)
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
                outputfile = self.getFilename('EXPT_EXCEL')
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
    parser.add_argument('--datafile', action='store', help='Data file', default="EXP44 Time Trace(s).csv")
    parser.add_argument('--bleachfile', action='store', help='Data file', default="Bleach Time Trace(s).csv")
    parser.add_argument('--outputdir', action='store', help='Output directory', default="D:\\Dropbox\\worktransfer\\Anggono\\hilary\\batchoutput")
    parser.add_argument('--inputdir', action='store', help='Input directory',
                        default="D:\\Dropbox\\worktransfer\\Anggono\\hilary\\input")
    parser.add_argument('--suffix', action='store', help='Output filename suffix', default="_Processed.xlsx")
    parser.add_argument('--roilist', action='store', help='Selected ROI list', default="_ROIlist.csv")

    return parser

####################################################################################################################
if __name__ == "__main__":

    parser = create_parser()
    args = parser.parse_args()
    inputdir = args.inputdir
    datafile = join(inputdir, args.datafile)

    print("Input:", datafile)
    print("Output:", args.outputdir)

    try:
        mod = Bleach(datafile, args.outputdir,showplots=True)
        cfg = mod.getConfigurables()
        for c in cfg.keys():
            print("config set: ",c,"=", cfg[c])
        #set values - this will be done from configdb
        cfg['EXPT_EXCEL']=args.suffix
        cfg['ROI_FILE'] = args.roilist
        cfg['BLEACH_FILENAME'] = args.bleachfile
        mod.setConfigurables(cfg)
        if mod.data is not None:
            mod.run()

    except Exception as e:
        print(e)

