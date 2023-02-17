### Declarative external resources any with implicit deployment

This package provide classes that allow to setup external resources (utilities,
python packages etc.) that will be deployed as they are used. In most
cases data should be on the web and it will be deployed and cached locally on
only first usage.

There are several examples in `test/` folder and `getpack.library` module
already defined and useable. But main intention is to provide framework for
declarative setup of any resource and work with it without care of deployment.
```python
from getpack.resource import WebResource
class Example(WebResource):
    version = '0.1'
    archive_url = 'https://example.com/example-0.1.zip'
```
then it would be used:
```python
import subprocess
subprocess.call(Example()().path / 'example.exe')
```
Second round braces required to actually make an effect from resource
and first round braces used to initialize resource class, that would produce
resource descriptions on the fly like follows:
```python
Example(version='0.2', archive_url='https://Example.com/example-0.2.zip')
```
You may experiment with following working snippet and try to change `PySide2`
version:
```bash
python -c "import getpack.library;getpack.library.PySide2(version='5.14.1')(); import PySide2.QtWidgets; app=PySide2.QtWidgets.QApplication(); w=PySide2.QtWidgets.QPushButton(PySide2.__version__); w.clicked.connect(w.close); w.show(); app.exec_()"
```

### TODO

- Utilize `requirements.txt` to reproduce both development and production
  environments.
