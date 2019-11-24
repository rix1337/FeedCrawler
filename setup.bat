RMDIR /Q /S build
RMDIR /Q /S dist
RMDIR /Q /S rsscrawler.egg-info
python setup.py sdist bdist_wheel
python -m twine upload dist/* -u __token__ -p %PYPI_TOKEN%
python rsscrawler/version.py > version.txt
SET /p version= < version.txt
pyinstaller --onefile -y -i "rsscrawler/web/img/favicon.ico" --version-file "file_version_info.txt" --add-data "rsscrawler/web;web" "RSScrawler.py" -n "rsscrawler-%version%-standalone-win32"
DEL /Q file_version_info.txt
DEL /Q version.txt
