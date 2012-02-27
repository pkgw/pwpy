def djoin (*args):
    """'dotless' join, for nicer paths"""
    from os.path import join
    i = 0
    alen = len (args)

    while i < alen and (args[i] == '' or args[i] == '.'):
        i += 1

    if i == alen:
        return '.'

    return join (*args[i:])
