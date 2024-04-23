import os
import sys
from setuptools import setup, Extension, find_packages

version_dict = {}
with open("leat/version.py") as fp:
    exec(fp.read(), version_dict)
__version__ = version_dict["__version__"]

setup(
    name="leat",
    version=__version__,
    description="Light-weight ethical auditing tool for data-centric AI developers",
    url="https://github.com/markgraves/leat",
    license="LGPL-2.1",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "openpyxl",
        "pandas>0.25",
        "pdfminer.six",
        "python-pptx",
    ],
    extras_require={"dev": ["pytest", "black", "myst-parser"]},
    entry_points={
        "console_scripts": ["leat=leat.cli:mail"],
    },
)
