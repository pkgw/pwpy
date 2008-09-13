# Configuration settings

# The directory where the raw data live.
raw=""

# A shell glob expression (that is, with * and ?)
# that matches raw data filenames in the directory $raw.
rawglob=""

# Each raw data filename is considered a list of
# "items" separated by dashes. This is the number of the 
# item (starting at 1) that gives the frequency in a given
# raw dataset. E.g., if your file is named hello-what-1430-3c286-good,
# then freqitem is 3
freqitem=""

# As above, but for the source of a raw dataset. In the
# above example, srcitem would be 4
srcitem=""

# The source to be used as a flux and phase calibration reference
cal=""
