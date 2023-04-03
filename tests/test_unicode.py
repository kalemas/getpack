# -*- coding: utf-8 -*-
import sys

from getpack import  resource


def test_nonlatin_paths():
    local_prefix = u'папка'
    if sys.version_info < (3,):
        local_prefix = local_prefix.encode(sys.getfilesystemencoding())
    glue = resource.PyPiPackage('glue', '0.13', local_prefix=local_prefix)
    glue.cleanup()
    glue.provide()
    # glue-sdist is not possible to activate out of the box, just check file
    assert (glue.path / 'glue-0.13' / 'AUTHORS').is_file()
