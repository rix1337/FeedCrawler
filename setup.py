# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

import glob
import io

import setuptools

web = ["web/index.html"]
web_css = []
for i in glob.glob("web/css/*"):
    web_css.append(i.replace("\\", "/"))
web_img = []
for h in glob.glob("web/img/*"):
    web_img.append(h.replace("\\", "/"))
web_js = []
for j in glob.glob("web/js/*"):
    web_js.append(j.replace("\\", "/"))


from version import getVersion

with io.open('README.md', encoding='utf-8') as f:
    long_description = '\n' + f.read()

with open('requirements.txt') as f:
    required = f.read().splitlines()

setuptools.setup(
    name="rsscrawler",
    version=getVersion().replace("v.",""),
    author="rix1337",
    author_email="",
    description="Automating JDownloader Downloads (German!)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/rix1337/RSScrawler",
    packages=setuptools.find_packages(),
    data_files=[('web', web),
                ('web/css', web_css),
                ('web/img', web_img),
                ('web/js', web_js)],
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
