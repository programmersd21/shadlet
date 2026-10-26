# installation

## install from pypi

Install the core package:

```bash
pip install shadlet
```

For desktop packaging support (PyInstaller):

```bash
pip install "shadlet[desktop]"
```

For development (testing, linting, building):

```bash
pip install "shadlet[dev]"
```

## install from source

Requirements:
- Python 3.11 or newer
- Node.js 20 or newer
- npm

```bash
git clone https://github.com/programmersd21/shadlet.git
cd shadlet
uv venv --python 3.11
uv pip install -e '.[dev]'
```

## verify environment

Run the built-in diagnostic tool:

```bash
shadlet doctor
shadlet info
```
