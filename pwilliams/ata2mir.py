ata2mir0 = {
    '1a':  0, '1b':  1, '1c':  2, '1d':  3, '1e':  4,
    '1f':  5, '1g':  6, '1h':  7, '1j':  8, '1k':  9,
    
    '2a': 10, '2b': 11, '2c': 12, '2d': 13, '2e': 14, '2f': 15,
    '2g': 16, '2h': 17, '2j': 18, '2k': 19, '2l': 20, '2m': 21,

    '3c': 22, '3d': 23, '3e': 24, '3f': 25,
    '3g': 26, '3h': 27, '3j': 28, '3l': 29,

    '4e': 30, '4f': 31, '4g': 32, '4h': 33,
    '4j': 34, '4k': 35, '4l': 36,

    '5b': 37, '5c': 38, '5e': 39,
    '5g': 40, '5h': 41
}

ata2mir = {}
mir2ata = {}
mir02ata = {}

def _map ():
    global ata2mir, mir2ata, mir02ata

    for name, num in ata2mir0.iteritems ():
        ata2mir[name] = num + 1
        mir2ata[num + 1] = name
        mir02ata[num] = name

_map ()
