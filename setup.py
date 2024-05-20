from setuptools import setup, find_packages
import logging

logger = logging.getLogger(__name__)

version = "0.0.1"

try:
    with open("README.md", "r") as f:
        long_desc = f.read()
except:
    logger.warning("Could not open README.md.  long_description will be set to None.")
    long_desc = None

setup(
    name="tanglenomicon_data_api",
    packages=find_packages(),
    version=version,
    description="The API for the Tanglenomicon.",
    long_description=long_desc,
    long_description_content_type="text/markdown",
    author="Joe Starr",
    # author_email = '',
    url="https://github.com/Uiowa-Applied-Topology/Tanglenomicon_API_proto",
    keywords=["topology", "knots", "tangles"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: OS Independent",
        "Framework :: IPython",
    ],
    python_requires=">=3.10",
    install_requires=[
        "scipy",
        "numpy",
        "pyyaml",
        "uvicorn[standard]",
        "fastapi",
        "motor",
        "passlib[bcrypt]",
        "python-jose[cryptography]",
        "python-multipart",
        "pydantic-settings",
        "dacite",
    ],
)
