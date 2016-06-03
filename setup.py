from distutils.core import setup
import py2exe, sys

sys.argv.append('py2exe')

setup(
    name = "RSScrawler",
    version = '1.5.7.0',
    description = "RSScrawler durchsucht MB/SJ nach in .txt Listen hinterlegten Titeln und reicht diese im .crawljob Format an JDownloader weiter",
    author = "RiX",
    windows = [{'script': 'RSScrawler.py', 
                'icon_resources': [(1, 'setup.ico')]
                }],
    options = {'py2exe': {'bundle_files': 1, 'compressed': True, 'packages': ['docopt', 'feedparser', 'BeautifulSoup', 'pycurl', 'lxml', 'requests'], 'dll_excludes': ['MSVFW32.dll', 'AVIFIL32.dll', 'AVICAP32.dll', 'ADVAPI32.dll', 'CRYPT32.dll', 'WLDAP32.dll', 'w9xpopen.exe']}},
	console=['RSScrawler.py'],
    zipfile = None,
)