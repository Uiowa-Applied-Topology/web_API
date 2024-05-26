
set export

PYTHONPATH := "."
system_python := if os_family() == "windows" { "python" } else { "python" }
python_dir := if os_family() == "windows" { "./.venv/Scripts" } else { "./.venv/bin" }
python_exe := python_dir + if os_family() == "windows" { "/python.exe" } else { "/python" }

# Set up development environment
bootstrap:
    if test ! -e build/flake; then mkdir -p build/flake; fi
    if test ! -e build/docs; then mkdir -p build/docs; fi
    if test ! -e .venv; then {{ system_python }} -m venv .venv; fi
    {{ python_exe }} -m pip install --upgrade pip wheel pip-tools
    {{ python_exe }} -m pip install -r requirements.txt


run:
    {{ python_exe }} -m tanglenomicon_data_api -c ./misc/crypt/config.yaml

dev:
    {{ python_exe }} -m tanglenomicon_data_api -c ./misc/crypt/dev_config_server.yaml

flake:
    if test ! -e build/flake; then mkdir -p build/flake; fi
    {{ python_exe }} -m flake8 --docstring-convention numpy --format=html --htmldir=build/flake/results

sphinx:
    if test ! -e build/docs; then mkdir -p build/docs; fi
    {{ python_dir }}/sphinx-build -M html docs build/docs

cloc:
    mkdir -p docs/summary
    {{ python_dir}}/pygount --format=summary  --suffix=md,py,yaml

pytest:
    {{ python_exe }} -m pytest

test: flake sphinx pytest cloc
    echo "Done"