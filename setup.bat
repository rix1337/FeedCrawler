RMDIR /Q/S build
RMDIR /Q/S dist
RMDIR /Q/S rsscrawler.egg-info
python setup.py sdist bdist_wheel
ubuntu run python setup.py sdist bdist_wheel
python -m twine upload dist/* -u __token__ -p %PYPI_TOKEN%
