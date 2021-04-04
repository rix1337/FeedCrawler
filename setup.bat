RMDIR /Q /S build
RMDIR /Q /S dist
RMDIR /Q /S rsscrawler.egg-info
python setup.py sdist bdist_wheel
python -m twine upload dist/* -u __token__ -p %PYPI_TOKEN%
python rsscrawler/version.py > version.txt
SET /p version= < version.txt
setup_create_release.sh github_api_token=%GH_TOKEN% owner=rix1337 repo=rsscrawler version=v.%version%
REN *.spec rsscrawler-%version%-standalone-win64.spec
pyinstaller --onefile -y -i "rsscrawler/web/img/favicon.ico" --version-file "file_version_info.txt" --hidden-import "_rapidfuzz_cpp" --add-data "%localappdata%\Programs\Python\Python39\Lib\site-packages\cloudscraper\;cloudscraper" --add-data "rsscrawler/web;web" "FeedCrawler.py" -n "rsscrawler-%version%-standalone-win64"
setup_upload_asset.sh github_api_token=%GH_TOKEN% owner=rix1337 repo=rsscrawler version=v.%version% filename=./dist/rsscrawler-%version%-standalone-win64.exe
setup_upload_asset.sh github_api_token=%GH_TOKEN% owner=rix1337 repo=rsscrawler version=v.%version% filename=./dist/rsscrawler-%version%-py3-none-any.whl
DEL /Q file_version_info.txt
DEL /Q version.txt
curl -X POST "https://hub.docker.com/api/build/v1/source/%DH_TRIGGER%/call/"
start "" https://github.com/rix1337/FeedCrawler/releases
