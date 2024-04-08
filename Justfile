

python_dir := if os_family() == "windows" { "./.venv/Scripts" } else { "./.venv/bin" }
python := python_dir + if os_family() == "windows" { "/python.exe" } else { "/python" }
system_python := if os_family() == "windows" { "python" } else { "python" }


# Set up development environment
bootstrap:
    if test ! -e .venv; then {{ system_python }} -m venv .venv; fi
    {{ python }} -m pip install --upgrade pip wheel pip-tools
    {{ python_dir }}/pip-sync

run:
    {{ python }} -m tanglenomicon_data_api -f ./misc/crypt/config.yaml

test:
    pytest