from threading import Thread

from inspect import getsource
from utils.download import download
from utils import get_logger
import scraper
import time


class Worker(Thread):
    def __init__(self, worker_id, config, frontier):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")

        self.totalWordsLogger = get_logger("TotalWord") # Create a log file for the info you are tracking
        self.uniqueWebPagesLogger = get_logger("uniqueWebPages") # Create a log file for the unique web page by ignoring the fragments
        self.top50WordsLogger = get_logger("top50Words") # Create a log file for the top 50 frequency of words
        self.subDomainLogger = get_logger("subDomain") # Create a log file for the subdomain in ics.uci.edu

        self.config = config
        self.frontier = frontier
        # basic check for requests in scraper
        assert {getsource(scraper).find(req) for req in {"from requests import", "import requests"}} == {-1}, "Do not use requests in scraper.py"
        assert {getsource(scraper).find(req) for req in {"from urllib.request import", "import urllib.request"}} == {-1}, "Do not use urllib.request in scraper.py"
        super().__init__(daemon=True)
        
    def run(self):
        uniqueSets = set()
        uniqueSetsForICS = set()
        top50WordsDict = dict()
        subdomains = dict()
        while True:
            tbd_url = self.frontier.get_tbd_url()
            if not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")
                break
            resp = download(tbd_url, self.config, self.logger)
            self.logger.info(
                f"Downloaded {tbd_url}, status <{resp.status}>, "
                f"using cache {self.config.cache_server}.")
            scraped_urls = scraper.scraper(tbd_url, resp)

            temp_unique = scraper.getUnique(tbd_url)
            uniqueSets.add(temp_unique)
            self.uniqueWebPagesLogger.info(f"Unique Page Count: {len(uniqueSets)}")
            

            indi_ics_domain, temp_domain = scraper.getSubdomain(tbd_url)
            if indi_ics_domain:
                if temp_domain in subdomains:
                    subdomains[temp_domain].add(temp_unique)
                else:
                    subdomains[temp_domain] = set()
                    subdomains[temp_domain].add(temp_unique)
                self.subDomainLogger.info(f"{temp_domain}, {len(subdomains.keys())}, {len(subdomains[temp_domain])}, {tbd_url}")


            temp_dict = scraper.getWordsDict(tbd_url, resp)
            for k,v in temp_dict.items():
                if k in top50WordsDict.keys():
                    top50WordsDict[k] += v
                else:
                    top50WordsDict[k] = v
            top50_dict = dict(sorted(top50WordsDict.items(), key=lambda item: item[1], reverse=True))
            self.top50WordsLogger.info(f"top50Words: {list(top50_dict.keys())[:50]}")
            self.top50WordsLogger.info(f"top50Words: {list(top50_dict.values())[:50]}")

            # Get informatio about total words in a page
            totalWords = scraper.amountWords(tbd_url, resp)
            self.totalWordsLogger.info(f"Total Word: {totalWords} in {tbd_url}")


            for scraped_url in scraped_urls:
                self.frontier.add_url(scraped_url)
            self.frontier.mark_url_complete(tbd_url)
            time.sleep(self.config.time_delay)
