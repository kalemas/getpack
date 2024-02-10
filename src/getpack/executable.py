import subprocess
import sys

from .resource import Base, Resource


class LocalExecutable(Base):
    """
    Wrapper for locally available executable.

    So it is easier to add convenience methods and accomplish nitty-gritty
    tasks.
    """
    executable = None
    popen_class = subprocess.Popen

    def __init__(self, executable=None, *args, **kwargs):
        if executable:
            self.executable = executable
        super(LocalExecutable, self).__init__(*args, **kwargs)

    def get_popen_params(self, args, kwargs):
        assert self.executable, 'Property `executable` should be provided'
        args = (self.executable, ) + args
        args = tuple(str(i) for i in args)  # conform to string (pathlib.Path)
        kwargs = dict((k, v) for k, v in kwargs.items() if k not in {
            'check',
        })
        if kwargs.get('input') is None:
            kwargs['stdin'] = subprocess.PIPE
        kwargs.setdefault('stdout', subprocess.PIPE)
        kwargs.setdefault('stderr', subprocess.PIPE)
        if not kwargs.pop('show', None):
            if sys.platform == 'win32':
                # hide console window
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                kwargs['startupinfo'] = startupinfo
        kwargs['args'] = args
        return kwargs

    def __call__(self, *args, **kwargs):
        """
        Execute process provided by this resource.

        Parameters
        -----
        input - `str`, `bytes` or Stream, process input data passed to
            `Popen.communicate()`.
        check - `bool`, whether exception should be raised if process returned
                non zero exit code. Default is `True`.
        """
        input = kwargs.pop('input', None)
        detach = kwargs.pop('detach', False)
        proc = self.make_popen(*args, **kwargs)
        if detach:
            return
        out, err = proc.communicate(input=input)
        if kwargs.get('check', True) and proc.returncode:
            raise Exception(
                'Command {!r} returned non-zero exit status: {}, output:'
                '\n{}'.format(args, proc.returncode,
                              err.decode(errors='replace')))
        return out

    def make_popen(self, *args, **kwargs):
        resolved_kwargs = self.get_popen_params(args, kwargs)
        return self.popen_class(**resolved_kwargs)


class Executable(LocalExecutable, Resource):
    """Intended for executables provided by WebResource."""

    executable_ext = ''
    if sys.platform == 'win32':
        executable_ext = '.exe'

    @property
    def executable(self):
        return self.path / (self.executable_name + self.executable_ext)

    @property
    def executable_name(self):
        try:
            return self._executable_name
        except AttributeError:
            pass
        return self.name

    @executable_name.setter
    def executable_name(self, value):
        self._executable_name = value

    def __call__(self, *args, **kwargs):
        self.provide()
        return super(Executable, self).__call__(*args, **kwargs)
