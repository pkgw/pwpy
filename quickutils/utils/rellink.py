def rellink (source, dest):
    """Create a symbolic link to path *source* from path *dest*. If
    either *source* or *dest* is an absolute path, the link from
    *dest* will point to the absolute path of *source*. Otherwise, the
    link to *source* from *dest* will be a relative link."""

    from os import symlink
    from os.path import isabs, dirname, relpath, abspath

    if isabs (source):
        symlink (source, dest)
    elif isabs (dest):
        symlink (abspath (source), dest)
    else:
        symlink (relpath (source, dirname (dest)), dest)
