import subprocess
import sys

from . import Resource


class Executable(Resource):
    executable_ext = ''
    if sys.platform == 'win32':
        executable_ext = '.exe'

    def get_popen_params(self, args, kwargs):
        args = (str(self.path /
                    (self.executable + self.executable_ext)), ) + args
        if kwargs.get('input') is None:
            kwargs['stdin'] = subprocess.PIPE
        kwargs.setdefault('stdout', subprocess.PIPE)
        kwargs.setdefault('stderr', subprocess.PIPE)
        return args, kwargs

    def __call__(self, *args, **kwargs):
        self = super(Executable, self).__call__()
        args, kwargs = self.get_popen_params(args, kwargs)
        input = kwargs.pop('input', None)
        proc = subprocess.Popen(args, **kwargs)
        out, err = proc.communicate(input=input)
        if proc.returncode:
            raise Exception(
                'Command {!r} returned non-zero exit status: {}, output:'
                '\n{}'.format(args, proc.returncode,
                              err.decode(errors='replace')))
        return out
