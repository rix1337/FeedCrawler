import multiprocessing

from feedcrawler import crawler

if __name__ == '__main__':
    multiprocessing.freeze_support()
    crawler.main()
