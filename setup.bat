RMDIR /Q/S build
RMDIR /Q/S dist
RMDIR /Q/S rsscrawler.egg-info
python setup.py sdist bdist_wheel
python -m twine upload dist/* -u __token__ -p %PYPI_TOKEN%
pyinstaller --onefile -y -i "rsscrawler/web/img/favicon.ico" --add-data "rsscrawler/web;web" "RSScrawler.py"
