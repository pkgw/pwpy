# hexplot.py
# Keaton Burns, University of California Berkeley, 09/28/2010
"""Tools for visualizing data from hex SQLite database"""


import numpy as np
import sqlite3
import matplotlib
matplotlib.use('pdf')
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
import hextoolkit


def hexplot(xdata, ydata, groupby=None, colorby=None, wherecmd='',
            saveas='squintplots.pdf', title=None, lines=False, errorbars=True, 
            xlim=None, ylim=None):
    """
    hexplot
    =======
    
    PURPOSE:
        Plots data from squint.db, grouped and colored as requested
    
    CALLING SEQUENCE:
        hexplot(xdata, ydata, groupby=None, colorby=None, wherecmd='',
                saveas='squintplots.pdf', title=None, lines=False, errorbars=True, 
                exclude_flagged=True, xlim=None, ylim=None)
    
    INPUTS:
        xdata       :=  tag for x-data in plots
        ydata       :=  tag for y-data in plots
        groupby     :=  group into separate plots by this tag
        <NOT IMPLEMENTED>colorby     :=  color by this tag
        wherecmd    :=  'WHERE ...' command for specifying data in sql query
        saveas      :=  savename for pdf of plots
        title       :=  title to add to all plots
        lines       :=  whether to connect the plotted points with lines
                        (add ' ORDER BY ' to wherecmd to control line order)
        errorbars   :=  add errorbars when available
        exclude_flagged :=  remove datapoints which have been flagged
        xlim        :=  user-specified x-axis limits (xmin, xmax)
        ylim        :=  user-specified y-axis limits (ymin, ymax)
    

    TAG LIST:
        In SQL database:
            'date'
            'source'
            'freq'
            'flux'
            'archsummpath'      (not physical)
            'rid'               (not physical)
            'antnum'
            'antname'
            'feed'
            'squintaz'
            'squintaz_uc'
            'squintel'
            'squintel_uc'
            'sefd'
            'sumchisq'
        Derived from SQL database:
            'antfeed'
            'squintmag'
            'squintmag_uc'
            'squintangle'
            'squintangle_uc'
            
            
    TODO LIST:
        -look into interactive plotting
        -outlier identification & option to suppress (in database buildup)
        -color
        -filtering by uc
        -mag vs feed by ant
         
    """
    
    ###########
    ## Query ##
    ###########
    
    # Connect to sqlite database
    connection = sqlite3.connect(hextoolkit.getdbpath ())
    cursor = connection.cursor()
    
    # Query for necessary information
    inputs = []
    called_tags = [xdata, ydata, groupby, colorby]
    for i in called_tags:
        if i != None: 
            if i in ('squintmag', 'squintmag_uc', 'squintangle', 'squintangle_uc'):
                inputs.append('squintaz')
                inputs.append('squintel')
            elif i in ('antfeed'):
                inputs.append('antnum')
                inputs.append('round(feed,1) as feed')
            elif i in ('feed'):
                inputs.append('round(feed,1) as feed')
            else:
                inputs.append(i)
            
    if 'squintaz' in inputs: inputs.append('squintaz_uc')
    if 'squintel' in inputs: inputs.append('squintel_uc')
                
    # Get rid of duplicates
    inputs = list(set(inputs))
    
    # Take out flaggeg data
    if exclude_flagged:
        if wherecmd == '':
            wherecmd = 'WHERE flag=0'
        else:
            wherecmd = 'WHERE flag=0 AND ' + wherecmd[6:]
            
    sql_cmd = 'SELECT ' + ','.join(inputs) + ' FROM runs NATURAL JOIN obs ' + wherecmd
    cursor.execute(sql_cmd)
    
    # Turn into ndarray
    sqldata = hextoolkit.sqlitecursor_to_ndarray(cursor)
    connection.close()
    
    # Create new array with derived tags, if needed
    getmag = 'squintmag' in called_tags or 'squintmag_uc' in called_tags
    getangle = 'squintangle' in called_tags or 'squintangle_uc' in called_tags
    getantfeed = 'antfeed' in called_tags

    extra_dtypes = []

    if getmag:
        extra_dtypes.append(('squintmag', '<f8'))
        extra_dtypes.append(('squintmag_uc', '<f8'))
    if getangle:
        extra_dtypes.append(('squintangle', '<f8'))
        extra_dtypes.append(('squintangle_uc', '<f8'))
    if getantfeed:
        extra_dtypes.append(('antfeed', '<f8'))

    if len (extra_dtypes) == 0:
        data = sqldata
    else:
        dtypes = eval(str(sqldata.dtype)) + extra_dtypes
        data = np.zeros(np.size(sqldata), dtype=dtypes)
        for i in sqldata.dtype.names:
            data[i] = sqldata[i]
        
    if getmag:
        data['squintmag'] = np.sqrt(data['squintaz'] ** 2 + data['squintel'] ** 2)
        data['squintmag_uc'] = np.sqrt((data['squintaz_uc'] * data['squintaz']) ** 2 + 
                                       (data['squintel_uc'] * data['squintel']) ** 2) / data['squintmag']

    if getangle:
        data['squintangle'] = np.arctan2(data['squintel'], data['squintaz'])
        el_over_az_uc = (np.sqrt((data['squintel_uc'] / data['squintel']) ** 2 +
                                 (data['squintaz_uc'] / data['squintaz']) ** 2)
                         * data['squintel'] / data['squintaz'])
        data['squintangle_uc'] = (el_over_az_uc /
                                  (1 + (data['squintel'] / data['squintaz']) ** 2))

    if getantfeed:
        data['antfeed'] = data['antnum'] * 1000 + data['feed']


    ##############
    ## Plotting ##
    ##############
     
    # Setup pdf output
    pp = PdfPages(saveas)
    
    # Get number of and list of groups
    groupnum = 1
    if groupby != None:
        grouplist = np.unique(data[groupby])
        groupnum = np.size(grouplist)
        if groupnum > 100:
            print 'HEXPLOT: Requested grouping would yield over 100 plots'
            print 'HEXPLOT: Quitting...'
            pp.close()
            return
            
    # Get number of and list of coloring groups
    palette = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
    colornum = 1
    if colorby != None:
        colorlist = np.unique(data[colorby])
        colornum = np.size(colorlist)
        if colornum > len(palette):
            print 'HEXPLOT: Requested coloring would yield over', len(palette), 'colors'
            print 'HEXPLOT: Quitting...'
            pp.close()
            return
                
    # Plot a separate figure for each group
    for i in xrange(groupnum):
        plt.figure(i+1, figsize=(9, 9))
        plt.clf()
        plt.subplots_adjust(left=0.125, right=0.9, bottom=0.125, top=0.9)
        
        # Pull out individual group, take everything if no grouping is specified
        if groupby != None: 
            igroup = np.where(data[groupby] == grouplist[i])
        else:
            igroup = np.where(data[xdata] == data[xdata])
            
        ixdata = data[xdata][igroup]
        iydata = data[ydata][igroup]

        # Determine errorbars as requested
        [xuc, yuc] = [None, None]
        
        if errorbars:
            if xdata in ['squintel', 'squintaz', 'squintmag', 'squintangle']:
                xuc = data[xdata + '_uc'][igroup]

            if ydata in ['squintel', 'squintaz', 'squintmag', 'squintangle']:
                yuc = data[ydata + '_uc'][igroup]

        # Plot the group
        if lines: linestyle = 'o-'
        else: linestyle = 'o'

        for j in xrange(colornum):
            if colorby != None:
                cgroup = np.where(data[colorby][igroup] == colorlist[j])
            else:
                cgroup = np.where(data[xdata][igroup] == data[xdata][igroup])
                
            if np.size(cgroup) == 0: continue
            
            plotformat = palette[j] + linestyle
            
            [cxuc, cyux] = [None, None]
            if xuc != None: cxuc = xuc[cgroup]
            if yuc != None: cyuc = yuc[cgroup]
            
            clabel = colorby + ' = ' + str(colorlist[j])
            
            plt.errorbar(ixdata[cgroup], iydata[cgroup], xerr=cxuc, yerr=cyuc, 
                         fmt=plotformat, label=clabel)
        
        # Add labels and lines at axes
        title_list = []
        if title != None: title_list.append(title)
        if groupby != None: title_list.append(groupby + ' = ' + str(grouplist[i]))
        plt.title(', '.join(title_list))
        plt.xlabel(xdata)
        plt.ylabel(ydata)
        plt.axhline(0, linestyle=':', color='k')
        plt.axvline(0, linestyle=':', color='k')
        plt.legend()
        
        # Data limits
        plotlimits = [np.min(ixdata), np.max(ixdata), np.min(iydata),np.max(iydata)]
        
        # Modify for particular tags:
        # Lower limit zero
        if ydata in ['squintaz_uc', 'squintel_uc', 'squintmag', 'squintmag_uc', 
                     'squintangle_uc', 'sefd', 'sumchisq']:
            plotlimits[2] = 0.0
        
        # Symmetric about zero
        if ydata in ['squintaz', 'squintel']:
            plotlimits[2] = -np.max(np.abs(plotlimits[2:4]))
            plotlimits[3] = np.max(np.abs(plotlimits[2:4]))
        if xdata in ['squintaz', 'squintel']:
            plotlimits[0] = -np.max(np.abs(plotlimits[0:2]))
            plotlimits[1] = np.max(np.abs(plotlimits[0:2]))
        
        # Specific values
        if ydata in ['squintangle']:
            plotlimits[2] = -np.pi
            plotlimits[3] = np.pi
        if xdata in ['squintangle']:
            plotlimits[0] = -np.pi
            plotlimits[1] = np.pi

        # Square up if comparing like quantities
        arcmin = ['squintaz', 'squintel', 'squintmag']
        arcmin_uc = ['squintaz_uc', 'squintel_uc', 'squintmag_uc']
        if xdata in arcmin and ydata in arcmin:
            plotlimits = [-np.max(plotlimits), np.max(plotlimits), 
                          -np.max(plotlimits), np.max(plotlimits)]
        elif xdata in arcmin_uc and ydata in arcmin_uc:
            plotlimits = [np.min(plotlimits), np.max(plotlimits), 
                          np.min(plotlimits), np.max(plotlimits)]
 
        # Allow user determination
        if xlim != None:
            plotlimits[0:2] = list(xlim)
        if ylim != None:
            plotlimits[2:] = list(ylim)
        
        # Pad plot limits on all sides
        pad = 0.05
        plotlimits[0] -= pad * (plotlimits[1] - plotlimits[0])
        plotlimits[1] += pad * (plotlimits[1] - plotlimits[0])
        plotlimits[2] -= pad * (plotlimits[3] - plotlimits[2])
        plotlimits[3] += pad * (plotlimits[3] - plotlimits[2])
        
        plt.axis(plotlimits)
            
        plt.draw()
        pp.savefig()
        
    pp.close()



