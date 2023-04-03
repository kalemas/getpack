import subprocess
import sys

from .resource import Resource


class Executable(Resource):
    executable_ext = ''
    if sys.platform == 'win32':
        executable_ext = '.exe'

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
        self.provide()
        resolved_kwargs = self.get_popen_params(args, kwargs)
        input = kwargs.pop('input', None)
        proc = subprocess.Popen(**resolved_kwargs)
        out, err = proc.communicate(input=input)
        if proc.returncode:
            raise Exception(
                'Command {!r} returned non-zero exit status: {}, output:'
                '\n{}'.format(args, proc.returncode,
                              err.decode(errors='replace')))
        return out
