#  RSScrawler
Main code by https://github.com/dmitryint commissioned by https://github.com/rix1337

## Version 0.7.2

This project relies heavily on these three projects:

https://github.com/zapp-brannigan/own-pyload-plugins/blob/master/hooks/MovieblogFeed.py

https://github.com/Gutz-Pilz/pyLoad-stuff/blob/master/SJ.py

https://github.com/bharnett/Infringer/blob/master/LinkRetrieve.py

## Description:

This script scrapes MB/SJ for titles stored in .txt files and passes them on to JDownloader via the .crawljob format

## TLDR:

1. Adjust ```settings.conf``` path in ```rssconfig.py``` and run the script once. Stop it afterwards.
2. Set up ```settings.conf```completely.
3. Run the script as you wish.

## Settings:
*Your settings.conf must be placed at a location your python instance can write to.*

Thus, adjust line 7 of ```rssconfig.py``` to ensure your settings will be saved.

On the first run settings.conf will be created with default values set. Hints as to what settings mean are found in ```rssconfig.py```.

Feel free to adjust those defaults to your liking, but again ensure paths inside the file are valid.

Namely: ```patternfile```, ```db_file```, and ```crawljob_directory``` must be valid.


**Again: set up both MB/SJ completely before you let the script run. Else your ```db_file``` and JDownloader will be flooded by links!** 


### patternfile:

A .txt list the script will use to crawl rss feeds.

If your Lists are blank, all links from MB/SJ will be added!

Set the lists up before starting this script for the first time with a valid settings.conf!

MB List items are made up of lines containing: ```Title,Resolution,ReleaseGroup,```

Example: ```Funny Movie,720p,GR0UP,```

The file is invalid if one comma is missing!

Leaving Resolution or Release Group blank is also valid

The database file prevents duplicate crawljobs

SJ List items are made up of lines containing: Title

Example: ```Funny TV-Show```


### db_file:

The database file prevents duplicate crawljobs


### crawljob_directoy:

Enable the Watch-Folder feature (experimental) in JDownloader first!

JDownloader crawljobs need to be placed in the ```folderwatch``` subdir of JDownloader, so adjust the settings.conf
