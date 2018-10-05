# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

import glob

import pypandoc
import setuptools

py = []
for h in glob.glob("*.py"):
    py.append(h.replace("\\", "/"))
web = ["web/index.html"]
web_css = []
for i in glob.glob("web/css/*"):
    web_css.append(i.replace("\\", "/"))
web_img = []
for j in glob.glob("web/img/*"):
    web_img.append(j.replace("\\", "/"))
web_js = []
for k in glob.glob("web/js/*"):
    web_js.append(k.replace("\\", "/"))


from version import getVersion

try:
    long_description = pypandoc.convert('README.md', 'rst')
    long_description = long_description.replace("\r", "")  # Do not forget this line
except OSError:
    print("Pandoc not found. Long_description conversion failure.")
    import io

    # pandoc is not installed, fallback to using raw contents
    with io.open('README.md', encoding="utf-8") as f:
        long_description = f.read()

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
    data_files=[('', py),
                ('web', web),
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
