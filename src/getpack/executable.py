import subprocess
import sys

from .resource import Base, Resource


class LocalExecutable(Base):
    """
    Wrapper for locally available executable.

    So it is easier to add convenience methods and accomplish nitty-gritty
    tasks.
    """
    executable = None  # type: str
    popen_class = subprocess.Popen

    __default_params__ = ('detach', 'show')

    def __init__(self, executable=None, *args, **kwargs):
        if executable:
            self.executable = executable
        super(LocalExecutable, self).__init__(*args, **kwargs)

    def get_popen_params(self, args, kwargs):
        assert self.executable, 'Property `executable` should be provided'
        args = (self.executable, ) + args
        args = tuple(str(i) for i in args)  # conform to string (pathlib.Path)
        kwargs = dict(kwargs)
        if kwargs.pop('input', None) is None:
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
        return self._filter_non_popen_params(kwargs)

    def __call__(self, *args, **kwargs):
        """
        Execute process provided by this resource.

        Parameters
        -----
        input - `str`, `bytes` or Stream, process input data passed to
            `Popen.communicate()`.
        check - `bool`, whether exception should be raised if process returned
            non zero exit code. Default is `True`.
        show - `bool`, whether to show console or gui window for started
            process. `False` by default.
        detach - `bool`, do not wait for process termination, process instance
            will be returned instead of output. `False` by default.
        """
        for k in self.__default_params__:
            v = getattr(self, k, None)
            if v is not None:
                kwargs.setdefault(k, v)
        popen_kwargs = self.get_popen_params(args, kwargs)
        proc = self.popen_class(**popen_kwargs)
        if kwargs.get('detach'):
            return proc
        out, err = proc.communicate(input=kwargs.get('input'))
        if kwargs.get('check', True) and proc.returncode:
            raise Exception(
                'Command {!r} returned non-zero exit status: {}, output:'
                '\n{}'.format(args, proc.returncode,
                              err.decode(errors='replace')))
        return self._format_output(out, err, proc)

    def _filter_non_popen_params(self, kwargs):
        return dict((k, v) for k, v in kwargs.items() if k not in {
            'check', 'detach',
        })

    def _format_output(self, out, err, proc):
        return out


class Executable(LocalExecutable, Resource):
    """Intended for executables provided by WebResource."""

    executable_ext = ''
    if sys.platform == 'win32':
        executable_ext = '.exe'

    def __init__(self, *args, **kwargs):
        super(Executable, self).__init__(*args, **kwargs)
        if self.executable is None:
            name = getattr(self, 'executable_name', self.name)
            self.executable = str(self.path / (name + self.executable_ext))

    def __call__(self, *args, **kwargs):
        self.provide()
        return super(Executable, self).__call__(*args, **kwargs)
