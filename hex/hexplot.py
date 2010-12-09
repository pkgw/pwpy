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


def hexplot(xdata, ydata, groupby=None, colorby=None, pyfilter=None,
            sqlfilter=None, wherecmd='', saveas='squintplots.pdf',
            lines=False, errorbars=True):
    """
    hexplot
    =======
    
    PURPOSE:
        Plots data from squint.db, grouped and colored as requested
    
    CALLING SEQUENCE:
        hexplot(xdata, ydata, groupby=None, colorby=None, pyfilter=None,
            sqlfilter=None, wherecmd='', saveas='squintplots.pdf',
            lines=False)
    
    INPUTS:
        xdata       :=  tag for x-data in plots
        ydata       :=  tag for y-data in plots
        groupby     :=  group into separate plots by this tag
        <NOT IMPLEMENTED>colorby     :=  color by this tag
        <NOT IMPLEMENTED>pyfilter    :=
        <NOT IMPLEMENTED>sqlfilter   :=
        wherecmd    :=  'WHERE ...' command for specifying data in sql query
        saveas      :=  savename for pdf of plots
        lines       :=  whether to connect the plotted points with lines
                        (add ' ORDER BY ' to wherecmd to control line order)
        errorbars   :=  add errorbars when available
    

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
            'squintmag'
            'squintmag_uc'
            'squintangle'
            'squintangle_uc' (NOT IMPLEMENTED)
            
            
    TODO LIST:
        -fix some axis limits
        -custom axis limits
        -look into interactive plotting
        -outlier identification & option to suppress (in database buildup)
        -plot uncertainties when available (and compute them for
         derived quantities such as squintmag and squintangle)
        -compute squintangle uncertainty & catch for x/yuc assignment in plotting
         
    """
    
    # Setup pdf output
    pp = PdfPages(saveas)
    
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
            else: inputs.append(i)
            
    if 'squintaz' in inputs: inputs.append('squintaz_uc')
    if 'squintel' in inputs: inputs.append('squintel_uc')
                
    # Get rid of duplicates
    inputs = list(set(inputs))
            
    sql_cmd = 'SELECT ' + ','.join(inputs) + ' FROM runs NATURAL JOIN obs ' + wherecmd
    cursor.execute(sql_cmd)
    
    # Turn into ndarray
    sqldata = hextoolkit.sqlitecursor_to_ndarray(cursor)
    connection.close()
    
    # Create new array with derived tags, if needed
    if 'squintmag' in called_tags or 'squintmag_uc' in called_tags: getmag = True
    else: getmag = False
    
    if 'squintangle' in called_tags or 'squintangle_uc' in called_tags: getangle = True
    else: getangle = False
    
    if getmag or getangle:
        
        # Pull datatypes of queried tags
        plot_dtypes = eval(str(sqldata.dtype))
        
        # Add derived datatypes
        if getmag: 
            plot_dtypes.append(('squintmag', '<f8'))
            plot_dtypes.append(('squintmag_uc', '<f8'))
        if getangle: 
            plot_dtypes.append(('squintangle', '<f8'))
            plot_dtypes.append(('squintangle_uc', '<f8'))
            
        # Create empty array, fill in all old data...
        data = np.zeros(np.size(sqldata), dtype=plot_dtypes)
        for i in sqldata.dtype.names:
            data[i] = sqldata[i]
        
        # ... and calculate derived tags
        if getmag:
            data['squintmag'] = np.sqrt(data['squintaz'] ** 2 + data['squintel'] ** 2)
            data['squintmag_uc'] = np.sqrt((data['squintaz_uc'] * data['squintaz']) ** 2 + 
                                           (data['squintel_uc'] * data['squintel']) ** 2) / data['squintmag']
        if getangle:
            data['squintangle'] = np.arctan2(data['squintel'], data['squintaz'])
            ### Calculate squintangle uncertainty:
            #data['squintangle_uc'] = 
            
    else: data = sqldata
    
    
    ##############
    ## Plotting ##
    ##############
    
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
                
    # Plot a separate figure for each group
    for i in xrange(groupnum):
        plt.figure(i+1, figsize = (9, 9))
        plt.clf()
        
        # Pull out individual group, take everything if no grouping is specified
        if groupby != None: 
            igroup = np.where(data[groupby] == grouplist[i])
        else:
            igroup = np.where(data[xdata] == data[xdata])
            
        ixdata = data[xdata][igroup]
        iydata = data[ydata][igroup]

        # Determine errorbars as requested       
        if errorbars:
            if xdata in ['squintel', 'squintaz', 'squintmag']:
                xuc = data[xdata + '_uc'][igroup]
            else: xuc = None
            
            if ydata in ['squintel', 'squintaz', 'squintmag']:
                yuc = data[ydata + '_uc'][igroup]
            else: yuc = None
        else:
            xuc = None
            yuc = None
        
        # Plot the group, label
        if lines: plotformat = 'bo-'
        else: plotformat = 'bo'

        plt.errorbar(ixdata, iydata, xerr=xuc, yerr=yuc, fmt=plotformat)
        
        if groupby != None: 
            plt.title(groupby + ' = ' + str(grouplist[i]))
        plt.xlabel(xdata)
        plt.ylabel(ydata)
        plt.axhline(0, linestyle=':')
        plt.axvline(0, linestyle=':')
        
        # Good 5% limits
        padlimits = [np.min(ixdata), np.max(ixdata), np.min(iydata),np.max(iydata)]
        pad = 0.05
        padlimits[0] -= pad * (padlimits[1] - padlimits[0])
        padlimits[1] += pad * (padlimits[1] - padlimits[0])
        padlimits[2] -= pad * (padlimits[3] - padlimits[2])
        padlimits[3] += pad * (padlimits[3] - padlimits[2])
        
        plt.axis(padlimits)
        plt.draw()
        pp.savefig()
        
    pp.close()



