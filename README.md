#  RSScrawler
Main code by https://github.com/dmitryint commissioned by https://github.com/rix1337

## Version 0.9.0

Code used:

https://github.com/zapp-brannigan/own-pyload-plugins/blob/master/hooks/MovieblogFeed.py

https://github.com/Gutz-Pilz/pyLoad-stuff/blob/master/SJ.py

https://github.com/bharnett/Infringer/blob/master/LinkRetrieve.py

## Description:

This script scrapes MB/SJ for titles stored in .txt files and passes them on to JDownloader via the .crawljob format

## TLDR:

1. Run the script once. Stop it afterwards.
2. Set up ```Settings.conf``` and your Lists completely, found in the ```Settings``` subdir.
3. Run the script as you wish.

## Launching the Script

Run RSScrawler.py

## Options

  ```--ontime```                  Run once and exit
  
  ```--log-level=<LOGLEVEL>```    Level which program should log messages (eg. CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET )

## Settings:
*Your Settings.conf is placed in the ```Settings``` subdir*

On the first run Settings.conf will be created with default values set. Hints as to what Settings mean are found in ```rssconfig.py```.

Feel free to adjust those defaults to your liking, but again ensure paths inside the file are valid.

Namely: ```patternfile```, ```db_file```, and ```crawljob_directory``` must be valid.


**Again: set up both the ```Movies.txt``` and ```Shows.txt``` Lists completely before you let the script run. Else your ```db_file``` and JDownloader will be flooded by links!** 


### patternfile:

A .txt list the script will use to crawl rss feeds.

If your Lists are blank, all links from MB/SJ will be added!

Set the lists up before starting this script for the first time with a valid Settings.conf!

Each line in Movies.txt should contain the title of a movie.
Each line in Shows.txt should contain the title of a show.


### db_file:

The database file prevents duplicate crawljobs


### crawljob_directoy:

Enable the Watch-Folder feature (experimental) in JDownloader first!

JDownloader crawljobs need to be placed in the ```folderwatch``` subdir of JDownloader, so adjust the Settings.conf
