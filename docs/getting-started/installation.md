# installation

## install from pypi

Install the core package:

```bash
pip install shadlet
```

For development (testing, linting, building):

```bash
pip install "shadlet[dev]"
```

## install from source

Requirements:
- Python 3.11 or newer

Node.js 20 or newer and npm are needed only when building the renderer from source.

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
