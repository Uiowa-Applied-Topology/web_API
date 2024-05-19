

python_dir := if os_family() == "windows" { "./.venv/Scripts" } else { "./.venv/bin" }
python := python_dir + if os_family() == "windows" { "/python.exe" } else { "/python" }
system_python := if os_family() == "windows" { "python" } else { "python" }


# Set up development environment
bootstrap:
    if test ! -e build/flake; then mkdir -p build/flake; fi
    if test ! -e build/docs; then mkdir -p build/docs; fi
    if test ! -e .venv; then {{ system_python }} -m venv .venv; fi
    {{ python }} -m pip install --upgrade pip wheel pip-tools
    {{ python }} -m pip install -r requirements.txt

run:
    {{ python }} -m tanglenomicon_data_api -c ./misc/crypt/config.yaml

flake:
    if test ! -e build/flake; then mkdir -p build/flake; fi
    {{ python }} -m flake8 --docstring-convention numpy --format=html --htmldir=build/flake/results

sphinx:
    if test ! -e build/docs; then mkdir -p build/docs; fi
    sphinx-build -M html docs build/docs

autodoc:
    sphinx-apidoc -o docs/_autosummary tanglenomicon_data_api

test: sphinx flake
    echo "a"s