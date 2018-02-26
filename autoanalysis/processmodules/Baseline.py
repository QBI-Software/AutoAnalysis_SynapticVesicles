# -*- coding: utf-8 -*-
"""
Normalized Baseline class
    1. Reads Traces_Processed.xlsx (created by Bleach module) and list of selected ROIs (from csv generated by Bleach and edited for selection)
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
import numpy as np
import xlsxwriter
from autoanalysis.db.dbquery import DBI
from autoanalysis.processmodules.DataParser import AutoData
import plotly.graph_objs as go
from plotly import tools
from plotly import offline
from scipy.optimize import curve_fit
# MatPlotlib
import matplotlib.pyplot as plt
from matplotlib import pylab



class Normalized(AutoData):
    """
    Filter class for filtering a dataset based on a single column of data between min and max limits
    """
    def __init__(self, datafile,outputdir, sheet=0, skiprows=0, headers=None, showplots=False):
        # Load data
        try:
            sheet = 'bleach subtracted'
            super().__init__(datafile, sheet, skiprows, headers)
            msg = "BASELINE: Subtracted Data loaded from %s" % self.datafile
            self.logandprint(msg)
            self.sheet='raw'
            self.rawdata = self.load_data()
            msg = "BASELINE: Raw Data loaded  from %s" % self.datafile
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
        cfg['EXPT_EXCEL'] = '_Processed.xlsx'
        cfg['EXPT_NORM'] = '_Normalized.xlsx'
        #cfg['ROI_FILE'] = "_ROIlist.csv"
        cfg['SELECTED_ROIS'] = "_ROIlist_selected.csv"
        cfg['STIM_BELOW'] = 10
        cfg['STIM_ABOVE'] = 0
        cfg['MAX_BELOW'] = 5
        cfg['MAX_ABOVE'] = 6
        cfg['FIT_DECAY_PERIOD']=0.75 # Use 75% of trace for fitting decay

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
            self.cfg[cf] = cfg[cf]
        self.logandprint("Config loaded")

    def getRootBasename(self):
        rootbname = self.bname
        if self.cfg is not None and 'EXPT_EXCEL' in self.cfg.keys():
            suffix = self.cfg['EXPT_EXCEL'].split(".")
            if suffix[0] in rootbname:
                rootbname=rootbname.replace(suffix[0],'')
        return rootbname

    def getFilename(self, cfgparam):
        '''
        Compile filename from config
        - if starts with underscore then append to basename otherwise use this name
        :param cfgparam: config param var eg ROI_FILE as found in cfg and db
        :return: full path filename
        '''
        filename = self.cfg[cfgparam]
        if filename.startswith('_'):
            filename = self.getRootBasename() + filename
        outputfile = join(self.outputdir,filename)
        return outputfile

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
        #fig['layout']['yaxis2']['title'] = 'ROI value'
        offline.plot(fig, filename=outputfile)
        return fig

    def generateOverlay(self, xt, df, title, outputfile, df_fit=None):
        # Scatter plots
        data = []

        for col in df.columns:
            if col.startswith('ROI'):
                data.append(
                    go.Scatter(
                        x=xt,
                        y=df[col].values,
                        name=col,
                        mode='markers'
                    ))
            elif col=='Average':
                # Add Average with SD TODO
                data.append(
                    go.Scatter(
                        x=xt,
                        y=df[col].values,
                        error_y=dict(
                            type='data',
                            array=df['SD'],
                            visible=True),
                        name=col,
                        mode='lines+markers'
                    ))
        if df_fit is not None:
            data.append(go.Scatter(
                x=df_fit['x'].values,
                y=df_fit['y_fit'].values,
                name='Fit decay',
                line=dict(
                    color=('rgb(229, 61, 89)'),
                    width=3)
            ))
        layout = dict(title=title,
                      xaxis=dict(title='Time(s)'),
                      yaxis=dict(title='Signal'),
                      )

        fig = dict(data=data, layout=layout)
        offline.plot(fig, filename=outputfile)
        return data

    def loadROIlist(self,roifile):
        try:
            access(roifile,R_OK)
            df_rois = pd.read_csv(roifile, header=None)
            if len(df_rois.columns)== 2:
                df_rois.columns = ['ROI', 'SELECTED']
                df_rois_selected = df_rois[df_rois['SELECTED'] == 'y']
                roilist = df_rois_selected['ROI'].tolist()
            else:
                df_rois.columns = ['ROI']
                roilist = df_rois['ROI'].tolist()

            msg = "ROI list loaded: %s" % roifile
            self.logandprint(msg)

        except Exception as e:
            raise e

        return roilist

    def getStimulusIndex(self):
        """
        Finds row with STIM marked - stimulus timepoint
        :return:
        """
        idx = 0
        if self.rawdata is not None:
            stims = [str(x) for x in self.rawdata['Frame'] if str(x).startswith('STIM')]
            if len(stims) <=0:
                raise ValueError("STIM not found - not indicated in file")
            idx = self.rawdata[self.rawdata['Frame'].isin(stims)].index.values[0]
        else:
            raise ValueError("STIM not found - no Raw data loaded")
        return idx

    def getMaxIndex(self, df_norm):
        idx = 0

        return idx

    def subtractAvg(self,col,idx, below=0, above=0):
        """
        Subtracts Avg above/below idx. If idx is none - looks for max index in this column
        :param col:
        :param idx:
        :param below:
        :param above:
        :return:
        """
        avg = np.mean(col.iloc[idx-below:idx+above])
        col = col-avg
        return col

    def divideMaxAvg(self,col,below=0, above=0):
        """
        Finds Depleted Max (> half-way in trace)
        Calculates Max Avg above/below idx.
        Divides values by max avg
        :param col:
        :param idx:
        :param below: from this
        :param above: upto but not including this
        :return:
        """
        #Calculate average max
        n = len(col)
        lasthalf = int(n/2)
        idx = col[col==max(col[lasthalf:])].index.values[0]
        # If upper limit is more than rows > shift idx by difference (TODO check)
        if (idx+above) > n:
            shift = (idx + above) - n
            idx = idx -shift
            msg = 'Warning: Max index for %s shifted by %d' % (col.name,shift)
            self.logandprint(msg)
        avg = np.mean(col.iloc[idx-below:idx+above])
        col = col/avg
        return col

    def exp_func(self,x, a, b, c):
        return a * np.exp(-b * x) + c

    def fitDecay(self,xdata,ydata, period=0.75):
        """
        Estimate expt period as first 75% of trace then fit decay to zero
        :param xdata:
        :param ydata:
        :return: decay rate (tau)
        """
        expt_period = int(round(len(ydata) * period, 0))
        peak = np.max(ydata[0:expt_period])
        peak_idx = ydata[ydata==peak].index.values[0]
        x = xdata[peak_idx:expt_period]
        y = ydata[peak_idx:expt_period]
        popt, pcov = curve_fit(self.exp_func, x, y, p0=(peak, 1e-6, 0))
        plt.plot(x, y, 'o', x, self.exp_func(x, *popt))
        tau = 1/popt[1]
        print("Estimated amplitude: ", peak, " tau: ", tau)
        df = pd.DataFrame.from_dict({'x': x, 'y': y, 'y_fit': self.exp_func(x, *popt)})
        return (peak,tau,df )

    def fitPolynomial(self, xdata, ydata,deg=3):
        """
        Estimate polynomial fits of data - ?useful
        #matplotlib
        #plt.plot(xdata, ydata, '.', xdata, p(xdata), 'c-')
        :param xdata: time
        :param ydata: ydata
        :param deg: degrees of fit - higher is more curves but closer fits
        :return:
        """
        p = np.poly1d(np.polyfit(xdata, ydata, deg))
        return p(xdata)


    def run(self):
        """
        Insert and subtract bleachdata from data
        :return:
        """
        if not self.data.empty:
            #Get selected ROIs from list
            roilist = self.loadROIlist(self.getFilename('SELECTED_ROIS'))
            df_selected = self.data[roilist]
            # Normalize to baseline
            #Get stimulus index
            stimidx = self.getStimulusIndex()
            #Average 10 frames before stim for each ROI and subtract
            df_norm = df_selected.apply(lambda col: self.subtractAvg(col,stimidx,
                                        int(self.cfg['STIM_BELOW']),int(self.cfg['STIM_ABOVE'])))
            print("Normalized data: \n", df_norm)
            # Find max in normalized data
            df_max = df_norm.apply(lambda col: self.divideMaxAvg(col,int(self.cfg['MAX_BELOW']),int(self.cfg['MAX_ABOVE'])))
            # Add Average data
            df_max['Average'] = df_max.mean(axis=1)
            df_max['SD'] = df_max.std(axis=1)
            # Fit decay to average
            xdata = self.rawdata['Time']
            ydata = df_max['Average']
            sd = df_max['SD']
            period = float(self.cfg['FIT_DECAY_PERIOD'])
            (amplitude,tau, df_fit) = self.fitDecay(xdata,ydata,period)

            # Save data
            all={'raw': self.rawdata, 'bleach subtracted': self.data, 'normalized': df_norm, 'max_depleted':df_max, 'fit_decay': df_fit}
            outputfile = self.getFilename('EXPT_NORM')
            self.outputExcelData(outputfile, all)
            print('Normalized data saved to: ', outputfile)
            #Plot overlay
            if self.showplots:
                title = self.bname + ': ROIs normalized baseline and max depleted'
                if tau is not None:
                    title += ' [Fit amplitude=%0.2f tau=%0.4f]' % (amplitude,tau)
                plotfilename = outputfile.replace('.xlsx', '.html')
                if 'Time' in self.data.columns:
                    xt = self.data['Time']
                    self.generateOverlay(xt,df_max, title, plotfilename, df_fit)
        else:
            print("No data found: ", self.datafile)


def create_parser():
    """
    Create commandline parser
    :return:
    """

    parser = argparse.ArgumentParser(prog=sys.argv[0],
                                     description='''\
                Reads bleach data and subtracts from data with output to Excel

                 ''')
    parser.add_argument('--datafile', action='store', help='Data file', default="EXP44 Time Trace(s)_Processed.xlsx")
    parser.add_argument('--suffix', action='store', help='Output filename suffix', default="_Normalized.xlsx")
    parser.add_argument('--roifile', action='store', help='ROI list', default="_ROIlist_selected.csv")
    parser.add_argument('--outputdir', action='store', help='Output directory', default="D:\\Dropbox\\worktransfer\\Anggono\\hilary\\batchoutput")
    parser.add_argument('--stimbelow', action='store',default=10)
    parser.add_argument('--stimabove', action='store', default=0)
    parser.add_argument('--maxbelow', action='store', default=5)
    parser.add_argument('--maxabove', action='store', default=6)
    parser.add_argument('--period', action='store', default=0.75)

    return parser

####################################################################################################################
if __name__ == "__main__":

    parser = create_parser()
    args = parser.parse_args()
    inputdir = args.outputdir


    print("Input:", args.datafile)
    print("Output:", args.outputdir)

    try:
        mod = Normalized(join(inputdir, args.datafile), args.outputdir,showplots=True)
        cfg = mod.getConfigurables()
        for c in cfg.keys():
            print("config set: ",c,"=", cfg[c])
        #set values - this will be done from configdb
        cfg['EXPT_EXCEL'] = "_" + args.datafile.split("_")[-1] #_Processed.xlsx
        cfg['EXPT_NORM'] = args.suffix
        cfg['SELECTED_ROIS'] = args.roifile
        cfg['STIM_BELOW'] = args.stimbelow
        cfg['STIM_ABOVE'] = args.stimabove
        cfg['MAX_BELOW'] = args.maxbelow
        cfg['MAX_ABOVE'] = args.maxabove
        cfg['FIT_DECAY_PERIOD'] = args.period
        mod.setConfigurables(cfg)
        if mod.data is not None:
            mod.run()

    except Exception as e:
        print("Error: ", e)

