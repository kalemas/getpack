import subprocess
import sys

from .resource import Resource


class Executable(Resource):
    executable_ext = ''
    if sys.platform == 'win32':
        executable_ext = '.exe'
    popen_class = subprocess.Popen

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

    @property
    def executable(self):
        return self.path / (self.executable_name + self.executable_ext)

    def get_popen_params(self, args, kwargs):
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
        self.provide()
        input = kwargs.pop('input', None)
        proc = self.make_popen(*args, **kwargs)
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
