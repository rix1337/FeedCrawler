from distutils.core import setup
import py2exe, sys

sys.argv.append('py2exe')

setup(
    options = {'py2exe': {'bundle_files': 1, 'packages': ['docopt', 'feedparser', 'BeautifulSoup', 'pycurl', 'lxml', 'requests'], 'dll_excludes': ['MSVFW32.dll', 'AVIFIL32.dll', 'AVICAP32.dll', 'ADVAPI32.dll', 'CRYPT32.dll', 'WLDAP32.dll']}},
	console=['RSScrawler.py'],
    zipfile = None,
)