# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul baut die aktuelle Version des FeedCrawlers.

import setuptools

from feedcrawler.providers.version import get_version

try:
    with open('README.md', encoding='utf-8') as f:
        long_description = f.read()
except:
    import io

    long_description = io.open('README.md', encoding='utf-8').read()

with open('requirements.txt') as f:
    required = f.read().splitlines()

setuptools.setup(
    name="feedcrawler",
    version=get_version(),
    author="rix1337",
    author_email="",
    description="Automate downloads using predefined sites and the My JDownloader API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/rix1337/FeedCrawler",
    packages=setuptools.find_packages(),
    include_package_data=True,
    install_requires=required,
    zip_safe=False,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        'console_scripts': [
            'feedcrawler = feedcrawler.crawler:start_feedcrawler',
        ],
    },
)
