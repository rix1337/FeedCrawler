#  RSScrawler
Main code by https://github.com/dmitryint commissioned by https://github.com/rix1337

## Version 1.0.4

Code used:

https://github.com/zapp-brannigan/own-pyload-plugins/blob/master/hooks/MovieblogFeed.py

https://github.com/Gutz-Pilz/pyLoad-stuff/blob/master/SJ.py

https://github.com/bharnett/Infringer/blob/master/LinkRetrieve.py

## Description:

This script scrapes MB/SJ for titles stored in .txt files and passes them on to JDownloader via the .crawljob format

## TLDR:

0. Enable folderwatch in JDownloader 2, then Download this script and install its prerequisites
1. Set up the ```Settings.ini``` and your Lists completely, found in the ```Settings``` subdir.
2. Run the script!

## Launching the Script

Run RSScrawler.py

## Options

  ```--ontime```                  Run once and exit
  
  ```--log-level=<LOGLEVEL>```    Level which program should log messages (eg. CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET )

## Settings:
*Your Settings.ini is located in the ```Settings``` subdir and will be recreated when removed*

Descriptions of the settings are found inside the file.

Feel free to adjust the defaults to your liking, but ensure the paths inside the file are valid.

Namely: ```patternfile```,  ```seasonslist```, ```file```, ```db_file```, and ```crawljob_directory``` must **ALL** be valid.


**Set up both the paths to and the content of ```Movies.txt``` and ```Shows.txt``` Lists, before you let the script run. Else your ```db_file``` and JDownloader will be flooded by links!** 


### patternfile/seasonslist/file:

A .txt list the script will use to crawl rss feeds.

If your Lists are blank, all links from MB/SJ will be added! For this reason 2 placeholder files are added in your Settings subfolder. If you fail to point your Settings.ini towards those lists, then the same rule as with blank lists applies.

**Set the lists up before starting this script for the first time with a valid Settings.ini!***

Each line in Movies.txt should contain the title of a movie.
Each line in Shows.txt should contain the title of a show.


### db_file:

The database file prevents duplicate crawljobs


### crawljob_directoy:

Enable the Watch-Folder feature (experimental) in JDownloader first!

JDownloader crawljobs need to be placed in the ```folderwatch``` subdir of JDownloader, so adjust the Settings.ini accordingly.

### crawl3d:

Enable this option if (regardless of quality settings) you also want 3D versions of your Movies.txt to be added (in 1080p). 
By default HOU 3D-versions are blocked through the ignore option.

### crawlseasons

Enable this option if you want to crawl MB for complete seasons.

```seasonslist``` should thus be pointed to your list of Shows and ```seasonsquality``` should be your desired quality for seasons. ```seasonssource``` can also be defined (default: bluray).

### Docker Setup:
https://github.com/rix1337/docker-rsscrawler
