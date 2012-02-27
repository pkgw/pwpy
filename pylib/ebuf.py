"""Create a file-like object that, when written to, will
dump its contents into a temporary buffer in an Emacs server."""

import os, subprocess

_template = '''
(with-current-buffer
  (get-buffer-create "*PyPipe*")
  (delete-region (point-min) (point-max))
  (insert-file "/proc/%d/fd/%d")
  (set-window-buffer nil "*PyPipe*"))
'''

class ebuf (object):
    file = None
    proc = None

    def __init__ (self):
        readfd, writefd = os.pipe ()

        self.file = os.fdopen (writefd, 'w', 0)

        # Important to note that the emacsclient process doesn't do
        # any piping itself -- it just tells the emacs server how to
        # access the readable end of our pipe. close_fds is important
        # to not deadlock since otherwise the pipe into emacs would be
        # considered not "closed" while emacsclient was alive.

        self.proc = subprocess.Popen (['emacsclient', '-e',
                                       _template % (os.getpid (), readfd)],
                                      close_fds=True, shell=False)

    def close (self):
        if self.file is not None:
            self.file.close ()
            self.file = None

        if self.proc is not None:
            exitcode = self.proc.wait ()
            if exitcode:
                raise OSError ('emacsclient returned exit code %d' % exitcode)
            self.proc = None

    def __del__ (self):
        self.close ()

    def __enter__ (self):
        return self

    def __exit__ (self, exctype, excvalue, traceback):
        self.close ()

    def _check (self):
        if self.file is None:
            raise ValueError ('operating on closed ebuf')

    def flush (self):
        self._check ()
        self.file.flush ()

    def fileno (self):
        self._check ()
        return self.file.fileno ()

    def isatty (self):
        self._check ()
        return False

    def write (self, text):
        self._check ()
        self.file.write (text)

    def writelines (self, seq):
        self._check ()
        self.file.writelines (seq)

    def _illegal (self, *args, **kwargs):
        import errno
        raise IOError ((errno.EBADF, 'Bad file descriptor'))

    next = _illegal
    read = _illegal
    readline = _illegal
    readlines = _illegal
    xreadlines=  _illegal
    seek = _illegal
    tell = _illegal
    truncate = _illegal

    # ignore all the boring properties, blah
