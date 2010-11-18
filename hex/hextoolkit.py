# hextoolkit.py
# Keaton Burns, University of California Berkeley, 09/28/2010
"""
Commonly used hex analysis code.
Contains functions infopath, antnum, antname, sqlitedb_to_ndarray,
    sqlitecursor_to_ndarray, atatojday, feedID, gaussread, gausstosql,
    resetsql, buildsql, hexfromtxt
"""


import os
import os.path
from os.path import join
import numpy as np
import sqlite3

# Set things up so we can dumpy numpy array values right
# into sqlite databases.
sqlite3.register_adapter (np.int32, int)
sqlite3.register_adapter (np.float32, float)
sqlite3.register_adapter (np.string_, str)

# Set location of database file
def getdbpath ():
    if 'SQUINTDBPATH' in os.environ:
        return os.environ['SQUINTDBPATH']
    return '/ataarchive/scratch/hexproc/squint.db'


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
    GNAMES = ('ANT,POL,Npts,,XiSq,AMP,AMPuc,OffAz,OffAzuc,OffEl,'
              'OffEluc,WidthRA,WidthRAuc,WidthDec,WidthDecuc')
    gread = hexfromtxt(join(path, 'data-gaussfits.txt'), dtype=GDTYPES, names=GNAMES, colnum=15)
    if gread == None: return 'GAUSSFITS_READ_FAILURE', 0, 0, 0
    
    # Read in SEFD file, intend to pass zeros if empty
    EDTYPES = 'i,S1,f,f,f,f,f'
    ENAMES = 'Ant,Pol,Avg-Amp,Amp-RMS,Avg-Pha,Pha-RMS,SEFD'
    eread = hexfromtxt(join(path, 'data-sefd.txt'), dtype=EDTYPES, names=ENAMES, skip_header=2)
    if eread == None:
        eread = 'SEFD_READ_FAILURE'
        print 'GAUSSREAD: Failed to read data-sefd.txt, inserting 0.0 for all.'
    
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
    
    print 'GAUSSREAD: sqpairs =', sqpairs
    # Uncomment following line: will not add runs to database if no corresponding obs
    #if sqpairs == 0: return 'NO_SQUINT_PAIRS', 0, 0, 0
    
    # Define types and names for the squint ndarray
    SDTYPES = 'i S2 i f f f f f f'.split ()
    SNAMES = ['antnum', 'antname', 'feed', 'squintaz', 'squintaz_uc',
              'squintel', 'squintel_uc', 'sefd', 'sumchisq']
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
            squint[j]['squintaz'] = (gread[antloc][yloc]['OffAz'] - gread[antloc][xloc]['OffAz']) / 60.0
            squint[j]['squintaz_uc'] = np.sqrt (gread[antloc][yloc]['OffAzuc']**2 +
                                                gread[antloc][xloc]['OffAzuc']**2) / 60.0
            squint[j]['squintel'] = (gread[antloc][yloc]['OffEl'] - gread[antloc][xloc]['OffEl']) / 60.0
            squint[j]['squintel_uc'] = np.sqrt (gread[antloc][yloc]['OffEluc']**2 +
                                                gread[antloc][xloc]['OffEluc']**2) / 60.0

            # Take SEFD as max from x and y for each antenna
            if eread == 'SEFD_READ_FAILURE':
                squint[j]['sefd'] = 0.0
            else:
                eloc = np.where(eread['Ant'] == i)
                if np.size(eloc) != 0: squint[j]['sefd'] = max(eread[eloc]['SEFD'])

            squint[j]['sumchisq'] = gread[antloc][xloc]['XiSq'] + gread[antloc][yloc]['XiSq']
            j += 1
            
    return gread, eread, info, squint
    
    
def gausstosql(path, replacedups=True):
    """
    gausstosql
    =========
    
    PURPOSE:
        Adds squint array data from gaussread to the squint SQL database.
    
    CALLING SEQUENCE:
        gausstosql(path)
    
    INPUTS:
        path        :=  path to folder containing hex reduction txts
        replacedups :=  whether information for hex runs that have already
                        been entered into the database should replace the
                        preexisting information. If False, the new information
                        will be ignored.
    """
    
    # Run gaussread
    [gread, eread, info, squint] = gaussread(path)
    
    # Bail if fail
    if gread == 'GAUSSFITS_READ_FAILURE':
        print 'GAUSSTOSQL: Failed to read data-gaussfits.txt, closing...'
        return
    # If 'NO_SQUINT_PAIRS' flagging is activated in gaussread, this will catch
    if gread == 'NO_SQUINT_PAIRS':
        print 'GAUSSTOSQL: No squint pairs found, closing...'
        return
    
    # Connect to sqlite database
    connection = sqlite3.connect(getdbpath ())
    cursor = connection.cursor()
    
    # Check to see if already in database
    ASPtest = info[4]
    cursor.execute('SELECT rid FROM runs WHERE archsummpath = ?', 
                   (ASPtest, ))
    matches = cursor.fetchall ()

    if len (matches) > 0:
        rid = matches[0][0]

        if not replacedups:
            print 'GAUSSTOSQL: Run', ASPtest, 'already entered into database; dropping new data'
            connection.close ()
            return

        print 'GAUSSTOSQL: Run', ASPtest, 'already entered into database; replacing old data'
        cursor.execute('DELETE FROM runs WHERE rid = ?', (rid, ))
        cursor.execute('DELETE FROM obs WHERE rid = ?', (rid, ))

    # Insert data. NULL values will be replaced with automatic object ids.
    cursor.execute('INSERT INTO runs VALUES (NULL,?,?,?,?,?)', info)
    runID = cursor.lastrowid
    cursor.executemany ('INSERT INTO obs VALUES (NULL,?,?,?,?,?,?,?,?,?,?)',
                        ((runID, ) + tuple (row) for row in squint))
    
    # Finish up!
    connection.commit()
    connection.close()
    
    
def resetsql():
    """Reset sql database, backup old database to squint.db.old"""
 
    # Backup database
    dbpath = getdbpath ()
    try:
        os.rename(dbpath, dbpath + '.old')
        print 'RESETSQL: Moved old database to', dbpath + '.old'
    except OSError, e:
        # Ignore the error if the database doesn't yet exist.
        if e.errno != 2:
            raise

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
                                   squintaz float,
                                   squintaz_uc float,
                                   squintel float,
                                   squintel_uc float,
                                   sefd float,
                                   sumchisq float);"""
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
    
    print 'RESETSQL: Saving new database squint.db'
    return

    
def buildsql(rootdir):
    """
    buildsql
    ========
    
    PURPOSE:
        Adds to squint.db by sorting through all subdirectories of given root directory
        NOTE: Does not reset database, instead adds to current database
              To reset use resetsql()

    CALLING SEQUENCE:
        buildsql(rootdir)
    
    INPUTS:
        rootdir     :=  root directory to add from
    """
   
    # Find all folders with data-gaussfits.txt

    def load (unused, dirname, filenames):
        if 'data-gaussfits.txt' in filenames:
            print dirname
            gausstosql (dirname)

    os.path.walk (rootdir, load, None)


def hexfromtxt(fname, dtype=float, names=None, skip_header=0, colnum=0):    
    """
    hexfromtxt
    ==========
    
    PURPOSE:
        Mimic numpy.genfromtxt from 1.4+ versions of numpy
        Read whitespace-separated text files into ndarray
        
    CALLING SEQUENCE:
        filearray = hexfromtxt(fname, dtype=float, names=None, skip_header=0, colnum=0)
        
    INPUTS:
        fname       :=  path to text file
        dtype       :=  list of column datatypes as strings, or string of datatypes separated by commas (no spaces)
                        (default all floats)
        names       :=  list of column names, or string of names separated by commas (no spaces)
                        (default 'f0','f1',...,'fn')
        skip_header :=  number of lines to skip at top of file
        colnum      :=  number of columns to look for
                        (if not specified, will look at dtype then names then first row after header)
    """

    # Read lines from file, skipping header
    file = open(fname, 'r')
    fileread = file.readlines()[skip_header:]
    file.close
    
    # Bail if empty
    if fileread == []: return None
    
    # Turn entries into lists of strings
    fileread = [i.strip().split() for i in fileread]
    
    # Change string dtype, names into list
    if type(dtype) == type(str()): dtype = dtype.split(',')
    if type(names) == type(str()): names = names.split(',')
    
    # If colnum not specified, take as number of dtype, then names, then first element
    if colnum == 0: 
        if type(dtype) == type(list()): colnum = len(dtype)
        elif type(names) == type(list()): colnum = len(names)
        else: colnum = len(fileread[0])
    
    # Get lists of proper-length elements
    filelist = []
    for i in fileread:
        if len(i) == colnum:
            filelist.append(i)
        else: print 'HEXFROMTXT: Rejecting row, wrong number of elements'

    # Create proper ndarray
    if names == None:
        if dtype == float: passdtype = (',f' * colnum)[1:]
        else: passdtype = ','.join(dtype)
    elif dtype == float:
        passdtype = zip(names, (',f' * colnum)[1:].strip().split())
    else: passdtype = zip(names, dtype)
    
    filearray = np.zeros(len(filelist), dtype=passdtype)
    
    # Add data to array
    for i in xrange(len(filelist)):
        for j in xrange(colnum):
            filearray[i][j] = filelist[i][j]
    
    return filearray
