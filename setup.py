# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

import setuptools
import glob
from version import getVersion

with open("README.md", "r", encoding='utf-8') as fh:
    long_description = fh.read()

with open('requirements.txt') as f:
    required = f.read().splitlines()

py_files = glob.glob("*.py")
modules = []
for f in py_files:
    if not "setup.py" in f:
        modules.append(f.replace(".py",""))

setuptools.setup(
    name="rsscrawler",
    version=getVersion().replace("v.",""),
    author="rix1337",
    author_email="",
    description="Automating JDownloader Downloads (German!)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/rix1337/RSScrawler",
    packages=[""],
    package_data={
        "": ["web/*", "web/css/*", "web/img/*", "web/js/*"],
    },
    install_requires=required,
    classifiers=[
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        'console_scripts': [
            'RSScrawler = RSScrawler:main',
            'rsscrawler = RSScrawler:main',
        ],
},
)
