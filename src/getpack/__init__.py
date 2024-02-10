"""
Declarative external resources with implicit deployment.

This file is suitable to bundle with projects so they would bootstrap *getpack*
and install it from pypi, then use full set of functions.


Copyright (c) 2022 Konstantin Maslyuk. All rights reserved.

This work is licensed under the terms of the MIT license.
For a copy, see <https://opensource.org/licenses/MIT>.
"""

__version__ = '0.4.0'

from .executable import Executable, LocalExecutable  # noqa: F401
from .resource import (  # noqa: F401
    LocalResource,
    PyPiPackage,
    PythonPackage,
    Resource,
    WebPythonPackage,
    WebResource,
)
