# hexplot.py
# Keaton Burns, University of California Berkeley, 09/28/2010
"""Tools for visualizing data from hex SQLite database"""

import hextoolkit
import numpy as np
import sqlite3
import matplotlib
matplotlib.use('pdf')
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.pylab import plt

def hexplot(xdata, ydata, groupby = '', colorby = '', pyfilter = '',
            sqlfilter = '', wherecmd = '', saveas='squintplots.pdf',
            lines=False):
    """
    hexplot
    =======
    
    PURPOSE:
        Plots data from squint.db, grouped and colored as requested
    
    CALLING SEQUENCE:
        hexplot(xdata, ydata, groupby = '', colorby = '', pyfilter = '', 
                sqlfilter = '', wherecmd='', saveas='squintplots.pdf')
    
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
    

    TAG LIST:
        In SQL database:
            'date'
            'source'
            'freq'
            'flux'
            'archsummpath'
            'rid'
            'antnum'
            'antname'
            'feed'
            'squintx'
            'squinty'
            'sefd'
        Derived from SQL database:
            'squintmag'
            <NOT IMPLEMENTED>'squintangle'
            
            
    TODO LIST:
        -limit group numbers
        -fix some axis limits
        -custom axis limits
        -line plotting & ordering
        -look into interactive plotting
        -outlier identification & option to suppress (in database buildup)
        -suppress addition printing
            
    """
    
    # Setup pdf output
    pp = PdfPages(saveas)
    
    # Connect to sqlite database
    connection = sqlite3.connect(hextoolkit.getdbpath ())
    cursor = connection.cursor()
    
    # Query for necessary information
    inputs = []
    called_tags = [xdata, ydata, groupby, colorby]
    for i in called_tags:
        if i != '': 
            if i in ('squintmag', 'squintangle'):
                inputs.append('squintx')
                inputs.append('squinty')
            else: inputs.append(i)
    sql_cmd = 'SELECT ' + ','.join(inputs) + ' FROM runs NATURAL JOIN obs ' + wherecmd
    cursor.execute(sql_cmd)
    
    # Turn into ndarray
    sqldata = hextoolkit.sqlitecursor_to_ndarray(cursor)
    
    # Create new array with derived tags, if needed
    if 'squintmag' in called_tags or 'squintangle' in called_tags:
        plot_dtypes = eval(str(sqldata.dtype))
        
        if 'squintmag' in called_tags: plot_dtypes.append(('squintmag', '<f8'))
        if 'squintangle' in called_tags: plot_dtypes.append(('squintangle', '<f8'))
        data = np.zeros(np.size(sqldata), dtype=plot_dtypes)
        
        # Add all old data...
        for i in sqldata.dtype.names:
            data[i] = sqldata[i]
        
        # ... and calculate derived tage
        if 'squintmag' in called_tags:
            data['squintmag'] = np.sqrt(data['squintx'] ** 2 + data['squinty'] ** 2)
        if 'squintangle' in called_tags:
            data['squintangle'] = np.arctan2(data['squinty'], data['squintx'])
    else: data = sqldata
    
    # Get number of and list of groups
    groupnum = 1
    if groupby != '':
        grouplist = np.unique(data[groupby])
        groupnum = np.size(grouplist)
                
    # Plot a separate figure for each group
    for i in xrange(groupnum):
        plt.figure(i+1, figsize = (9, 9))
        plt.clf()
        
        # Pull out individual group
        if groupby != '':
            igroup = np.where(data[groupby] == grouplist[i])
            ixdata = data[xdata][igroup]
            iydata = data[ydata][igroup]
        else:
            ixdata = data[xdata]
            iydata = data[ydata]
        
        # Plot the group, label
        if lines:
            plt.plot(ixdata, iydata)
        else:
            plt.scatter(ixdata, iydata)
        
        if groupby != '': plt.title(groupby + ' = ' + str(grouplist[i]))
        plt.xlabel(xdata)
        plt.ylabel(ydata)
        plt.axhline(0, linestyle = ':')
        plt.axvline(0, linestyle = ':')
        
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
