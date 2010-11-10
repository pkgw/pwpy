# hextoolkit.py
# Keaton Burns, University of California Berkeley, 09/28/2010
"""Commonly used hex analysis code"""


import os
import os.path
from os.path import join
import numpy as np
import sqlite3


# Set location of database file
dbpath = '/ataarchive/scratch/hexproc/squint.db'


def infopath(*args):
    return join(os.path.dirname(__file__), *args)


def antnum(astr):
    """Return ATA antenna number given antenna name"""
    telnum = np.genfromtxt(infopath('telnum.txt'), dtype='|S2', comments='#')
    return telnum.tostring().index(astr)/2 + 1


def antname(anum):
    """Return ATA antenna name given antenna number"""
    telnum = np.genfromtxt(infopath('telnum.txt'), dtype='|S2', comments='#')
    return telnum[anum - 1]


def sqlitedb_to_ndarray(fname, table='data', str_length=20):
    """Load table from a table in a sqlite3 .db file to a numpy ndarray"""
    
    connection = sqlite3.connect(fname)
    cursor = connection.cursor()
    cursor.execute('select * from ' + table)
    
    # Get data types
    types = []
    data = cursor.fetchall()
    if data == []: return None
    for i in xrange(np.size(data[0])):
        if type(data[0][i]) == unicode: 
            # Take longest string over all rows
            istrlength = str_length
            for j in data:
                if len(j[i]) > istrlength: istrlength = len(j[i])
            types.append('S%s' % istrlength)
        if type(data[0][i]) == float: types.append('float')
        if type(data[0][i]) == int: types.append('int')
    
    # Get column names
    varnm = [i[0] for i in cursor.description]
    
    # Autodetected dtype
    dtype = zip(varnm, types)
    data = np.array(data, dtype = dtype)
    
    # closing the connection
    connection.close()
    
    return data
	
	
def sqlitecursor_to_ndarray(cursor, str_length = 20):
    """Load table from sqlite3 cursor selection to a numpy ndarray"""

    # Get data types
    types = []
    data = cursor.fetchall()
    if data == []: return None
    for i in xrange(np.size(data[0])):
        if type(data[0][i]) == unicode: 
            istrlength = str_length
            for j in data:
                if len(j[i]) > istrlength: istrlength = len(j[i])
            types.append('S%s' % istrlength)
        if type(data[0][i]) == float: types.append('float')
        if type(data[0][i]) == int: types.append('int')

    # Get column names
    varnm = [i[0] for i in cursor.description]

    # Autodetected dtype
    dtype = zip(varnm, types)
    data = np.array(data, dtype = dtype)

    return data
    
    
def atatojday(atadate):
    """
    atatojday
    =========
    
    PURPOSE:
        Converts data-databounds date strings into Julian days
        
    CALLING SEQUENCE:
        atatojday(datestr)
        
    """ 
    
    # Sample atadate: '10Sep08:11:25:55.0'
    
    # Split off semicolons and pull out components
    atadate = atadate.split(':')
    
    date = atadate[0]
    hour = float(atadate[1])
    min = float(atadate[2])
    sec = float(atadate[3])
    
    year = int('20' + date[0:2])
    month = date[2:-2]
    day = int(date[-2:])
    
    if month == 'Jan': month = 1
    elif month == 'Feb': month = 2
    elif month == 'Mar': month = 3
    elif month == 'Apr': month = 4
    elif month == 'May': month = 5
    elif month == 'Jun': month = 6
    elif month == 'Jul': month = 7
    elif month == 'Aug': month = 8
    elif month == 'Sep': month = 9
    elif month == 'Oct': month = 10
    elif month == 'Nov': month = 11
    elif month == 'Dec': month = 12
    
    # Construct Julian Day (by Wikipedia's algorithm)
    a = (14 - month) / 12
    y = year + 4800 - a
    m = month + 12*a - 3
    
    JDN = day + (153 * m + 2) / 5 + 365 * y + y / 4 - y / 100 + y / 400 - 32045
    JD = JDN + (hour - 12) / 24. + min / 1440. + sec / 86400.
    return JD
    

def feedID(antnum, julday):
    """Return feed number for antenna antum on day julday"""
  
    # Read in feedswapjd.txt file
    feedlog = np.genfromtxt(infopath('feedswapjd.txt'), dtype=('f' + ',i2' * 43), delimiter=',')
    
    # Find all swaps before requested julday, take ant from latest one
    afterswitch = np.where(feedlog['f0'] < julday * np.ones(np.shape(feedlog['f0'])))
    jloc = np.where(feedlog['f0'] == np.max(feedlog['f0'][afterswitch]))
     
    return feedlog[jloc][0][antnum + 1]
   

def gaussread(path):
    """
    gaussread
    =========
    
    PURPOSE:
        Reads data textfiles including:
            data-gaussfits, data-sefd, data-sinfo, data-archsummpath, data-databounds
        Reduces to numpy ndarrays
    
    CALLING SEQUENCE:
        [gread, eread, info, squint] = gaussread(path)
    
    INPUTS:
        path    :=  path to folder containing hex reduction txts
    
    """
    
    
    ##################
    ## Read in Data ##
    ##################
    
    # Read in gaussian fit file, bail if empty
    GDTYPES = 'i,S1,i,i,f,f,f,f,f,f,f,f,f,f,f'
    GNAMES = ['ANT','POL','Npts','','XiSq','AMP','AMPuc','OffRA','OffRAuc','OffDec','OffDecuc','WidthRA','WidthRAuc','WidthDec','WidthDecuc']
    try:
        gread = np.genfromtxt(join (path, 'data-gaussfits.txt'), dtype = GDTYPES, names = GNAMES, usecols = (0,1,2,3,4,5,6,7,8,9,10,11,12,13,14))#, invalid_raise = False)
    except IOError: 
        return 'GAUSSFITS_READ_FAILURE', 0, 0, 0
    
    # Read in SEFD file, intend to pass zeros if empty
    EDTYPES = 'i, S1, f, f, f, f, f'
    ENAMES = ['Ant', 'Pol', 'Avg-Amp', 'Amp-RMS', 'Avg-Pha', 'Pha-RMS', 'SEFD']
    try:
        ### NOTE:  newer versions of numpy may require skiprows --> skip_headers, also use 'invalid_raise = False'
        eread = np.genfromtxt(join (path, 'data-sefd.txt'), dtype = EDTYPES, names = ENAMES, skiprows = 2)#, invalid_raise = False)
    except IOError:
        eread = 'SEFD_READ_FAILURE'
        print 'Failed to read data-sefd.txt, inserting 0.0 for all.'
    
    # Read in run information
    sinfofile = open(join (path, 'data-sinfo.txt'), 'r')
    sinforead = sinfofile.readlines()
    sinfofile.close()
    
    for i in xrange(np.size(sinforead)): sinforead[i] = sinforead[i].strip().split()
    source = sinforead[0][1]
    freq = sinforead[1][1]
    flux = sinforead[2][1]
    
    # Read in path to archive summ path, will use as unique run identifier
    archfile = open(join (path, 'data-archsummpath.txt'), 'r')
    archread = archfile.readlines()
    archfile.close()
    archsummpath = archread[0].strip()
    
    # Read in start and end times, convert to Julian dates
    boundsfile = open(join (path, 'data-databounds.txt'), 'r')
    boundsread = boundsfile.readlines()
    boundsfile.close()
    
    for i in xrange(np.size(boundsread)): boundsread[i] = boundsread[i].strip().split()
    tstart = atatojday(boundsread[0][1])
    #tend = atatojday(boundsread[1][1])

    info = (tstart, source, freq, flux, archsummpath)
        
    
    ###########################
    ## Reduce to useful data ##
    ###########################
    
    # Find out how many x,y center pairs there are
    sqpairs = 0
    for i in xrange(1,43):
        if np.size(np.where(gread['ANT'] == i)) == 2: sqpairs += 1
    
    print 'sqpairs =', sqpairs
    
    # Define types and names for the squint ndarray
    SDTYPES = ['i', 'S2', 'i', 'f', 'f', 'f']
    SNAMES = ['antnum', 'antname', 'feed', 'squintx', 'squinty', 'sefd']
    squint = np.zeros(sqpairs, dtype = zip(SNAMES, SDTYPES))
    
    # Calculate squints
    j = 0
    for i in xrange(1,43):
        antloc = np.where(gread['ANT'] == i)
        
        # Pick antennas with x and y gaussfit data
        if np.size(antloc) == 2:
            squint[j]['antnum'] = i
            squint[j]['antname'] = antname(i)
            
            # Add feed info
            squint[j]['feed'] = feedID(i, tstart)
            
            # Squint defined from x to y, in arcminutes
            xloc = np.where(gread[antloc]['POL'] == 'x')
            yloc = np.where(gread[antloc]['POL'] == 'y')
            squint[j]['squintx'] = (gread[antloc][yloc]['OffRA'] - gread[antloc][xloc]['OffRA']) / 60.0
            squint[j]['squinty'] = (gread[antloc][yloc]['OffDec'] - gread[antloc][xloc]['OffDec']) / 60.0

            # Take SEFD as max from x and y for each antenna
            if eread == 'SEFD_READ_FAILURE':
                squint[j]['sefd'] = 0.0
            else:
                eloc = np.where(eread['Ant'] == i)
                if np.size(eloc) != 0: squint[j]['sefd'] = max(eread[eloc]['SEFD'])
            
            j += 1
            
    return gread, eread, info, squint
    

    
def gausstosql(path, RESET = 0):
    """
    gausstosql
    =========
    
    PURPOSE:
        Adds squint array data from gaussread to sqlite3 database squint.db
    
    CALLING SEQUENCE:
        gausstosql(path, RESET = 0)
    
    INPUTS:
        date        :=  path to folder containing hex reduction txts
        RESET       :=  recreates database (CAREFUL..., must be 'yesforsure')
                        backs up old database to squintOLD.db
    
    """
    
    
    # Connect to sqlite database
    connection = sqlite3.connect(dbpath)
    cursor = connection.cursor()
    
    # Run gaussread
    [gread, eread, info, squint] = gaussread(path)
    
    # Bail if fail
    if gread == 'GAUSSFITS_READ_FAILURE':
        print 'Failed to read data-gaussfits.txt, closing...'
        connection.close()
        return
    
    # Check to see if already in database
    ASPtest = info[3]
    sql_cmd = 'SELECT archsummpath,rid FROM runs;'
    cursor.execute(sql_cmd)
    ASPlist = sqlitecursor_to_ndarray(cursor)
    if ASPlist != None:
        if ASPtest in ASPlist['archsummpath']:
            rid = ASPlist['rid'][np.where(ASPlist['archsummpath'] == ASPtest)]
            print 'Run already entered into database'
            confirm = ''
            while confirm == '': confirm = raw_input('Confirm overwrite (y): ')
            if confirm[0] in ['y', 'Y', '1']:
                sql_cmd = 'DELETE FROM runs WHERE rid = ' + str(rid)
                cursor.execute(sql_cmd)
                
                sql_cmd = 'DELETE FROM obs WHERE rid = ' + str(rid)
                cursor.execute(sql_cmd)

            else:
                print 'Insertion cancelled'
                connection.close()
                return
    
    # Insert run
    # info = (tstart, source, freq, flux, archsummpath)
    run_data = str(info)
    sql_cmd = 'INSERT INTO runs (date, source, freq, flux, archsummpath) VALUES ' + str(run_data)
    cursor.execute(sql_cmd)
    runID = cursor.lastrowid
    
    # Insert observations
    for i in xrange(np.size(squint)):
        # Attach run ID
        obs_data = '(' + str(runID) + ', ' + str(squint[i])[1:]
        sql_cmd = 'INSERT INTO obs (rid, antnum, antname, feed, squintx, squinty, sefd) VALUES ' + str(obs_data)
        cursor.execute(sql_cmd)
    
    # Finish up!
    connection.commit()
    connection.close()
    
    
def resetsql():
    """Reset sql database, backup old database to squint.db.old"""
 
    # Backup database
    os.rename(dbpath, dbpath + '.old')
    print 'Moving old database to', dbpath + '.old'
    
    # Connect to sqlite database
    connection = sqlite3.connect(dbpath)
    cursor = connection.cursor()
    
    # Reset and creation routine
    # Create table to hold observations
    sql_cmd = """CREATE TABLE obs (oid INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, 
                                   rid int,
                                   antnum int,
                                   antname text,
                                   feed int,
                                   squintx float,
                                   squinty float,
                                   sefd float);"""
    cursor.execute(sql_cmd)
    
    # Create table to hold runs
    sql_cmd = """CREATE TABLE runs (rid INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, 
                                   date float,
                                   source text,
                                   freq float,
                                   flux float,
                                   archsummpath text);"""
    cursor.execute(sql_cmd) 
    
    # Close and exit
    connection.commit()
    connection.close()
    
    print 'Saving new database squint.db'
    return

    
def buildsql(rootdir):
    """
    buildsql
    ========
    
    PURPOSE:
        Rebuilds squint.db by sorting through all subdirectories of given root directory
    
    CALLING SEQUENCE:
        buildsql(rootdir)
    
    INPUTS:
        rootdir     :=  root directory to build from
    """
    
    # Reset database
    resetsql()    

    # Find all folders with data-gaussfits.txt
    gaussfitswalk = os.walk(rootdir)

    for i in gaussfitswalk:
        if 'data-gaussfits.txt' in i[2]:
            print 'Reading files from ' + i[0]
            gausstosql(i[0])



