

python_dir := if os_family() == "windows" { "./.venv/Scripts" } else { "./.venv/bin" }
python := python_dir + if os_family() == "windows" { "/python.exe" } else { "/python" }
system_python := if os_family() == "windows" { "python" } else { "python" }
python_as := if os_family() == "windows" { python_dir + "/activate.bat" } else { "source "+ python_dir + "/activate" }

# Set up development environment
bootstrap:
    if test ! -e build/flake; then mkdir -p build/flake; fi
    if test ! -e build/docs; then mkdir -p build/docs; fi
    if test ! -e .venv; then {{ system_python }} -m venv .venv; fi
    {{ python }} -m pip install --upgrade pip wheel pip-tools
    {{ python }} -m pip install -r requirements.txt

venv_activate:
    {{ python_as }}


run:
    {{ python }} -m tanglenomicon_data_api -c ./misc/crypt/config.yaml

flake: venv_activate
    if test ! -e build/flake; then mkdir -p build/flake; fi
    {{ python }} -m flake8 --docstring-convention numpy --format=html --htmldir=build/flake/results

sphinx: venv_activate
    if test ! -e build/docs; then mkdir -p build/docs; fi
    sphinx-build -M html docs build/docs

cloc: venv_activate
    mkdir -p docs/summary
    pygount --format=summary  --suffix=md,py,yaml

test: sphinx flake
    echo "a"s