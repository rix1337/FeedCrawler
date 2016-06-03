from distutils.core import setup
import py2exe, sys

sys.argv.append('py2exe')

setup(
    console=[
	{
		'script': 'RSScrawler.py', 
		'icon_resources': [(0,'setup.ico')],
	}
	],
	name = 'RSScrawler',
    version = '1.6.1.0',
    description = 'RSScrawler',
    author = 'RiX',
    options = {'py2exe': {'bundle_files': 1, 'compressed': True, 'packages': ['docopt', 'feedparser', 'BeautifulSoup', 'pycurl', 'lxml', 'requests'], 'dll_excludes': ['MSVFW32.dll', 'AVIFIL32.dll', 'AVICAP32.dll', 'ADVAPI32.dll', 'CRYPT32.dll', 'WLDAP32.dll', 'w9xpopen.exe']}},
	zipfile = None,
)
