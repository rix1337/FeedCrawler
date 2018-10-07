# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

import setuptools

from version import getVersion

try:
    with open('README.md', encoding='utf-8') as f:
        long_description = f.read()
except:
    import io
    long_description = io.open('README.md', encoding='utf-8').read()

with open('requirements.txt') as f:
    required = f.read().splitlines()


def package_files(directory):
    import os
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join(path, filename))
    return paths


extra_files = package_files('web')


setuptools.setup(
    name="rsscrawler",
    version=getVersion().replace("v.",""),
    author="rix1337",
    author_email="",
    description="Automating JDownloader Downloads (German!)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/rix1337/RSScrawler",
    packages=['.'],
    package_data={'.': extra_files},
    install_requires=required,
    zip_safe=False,
    classifiers=[
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        'console_scripts': [
            'rsscrawler = RSScrawler:main',
        ],
},
)
