def words (linegen):
    for line in linegen:
        a = line.split ('#', 1)[0].strip ().split ()
        if not len (a):
            continue
        yield a


def pathwords (path, noexistok=False, **kwargs):
    try:
        with open (path, **kwargs) as f:
            for line in f:
                a = line.split ('#', 1)[0].strip ().split ()
                if not len (a):
                    continue
                yield a
    except IOError as e:
        if e.errno != 2 or not noexistok:
            raise


def pathtext (path, noexistok=False, **kwargs):
    try:
        with open (path, **kwargs) as f:
            return f
    except IOError as e:
        if e.errno == 2 and noexistok:
            return ()
        raise
