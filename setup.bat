RMDIR /Q /S build
RMDIR /Q /S dist
RMDIR /Q /S rsscrawler.egg-info
python setup.py sdist bdist_wheel
python -m twine upload dist/* -u __token__ -p %PYPI_TOKEN%
python rsscrawler/version.py > version.txt
SET /p version= < version.txt
setup_create_release.sh github_api_token=%GH_TOKEN% owner=rix1337 repo=rsscrawler version=v.%version%
pyinstaller --onefile -y -i "rsscrawler/web/img/favicon.ico" --version-file "file_version_info.txt" --add-data "rsscrawler/web;web" "RSScrawler.py" -n "rsscrawler-%version%-standalone-win32"
setup_upload_asset.sh github_api_token=%GH_TOKEN% owner=rix1337 repo=rsscrawler version=v.%version% filename=./dist/rsscrawler-%version%-standalone-win32.exe
setup_upload_asset.sh github_api_token=%GH_TOKEN% owner=rix1337 repo=rsscrawler version=v.%version% filename=./dist/rsscrawler-%version%-py3-none-any.whl
DEL /Q file_version_info.txt
DEL /Q version.txt
curl -X POST "https://hub.docker.com/api/build/v1/source/%DH_TRIGGER%/call/"
start "" https://github.com/rix1337/RSScrawler/releases
