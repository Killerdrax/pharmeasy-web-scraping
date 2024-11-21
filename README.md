# pharmeasy-web-scraping

Created a scraper using beautiful Soup, It scrapes and gets all the links from all medicines page and saves it in links.txt file. From the links.txt file we go through all the links and scrape the nessacerry data and store it in json such that its easy to manage and acessess compared to CSV. Some values I scrape are not available so its left blank. Created log file to monitor any errors and start from where it left.

Getlinks.py has dynamic pagination, where it scrapes all links in letter A, once all pagination is done it moves to letter B.

I have attached the reference file as well to get the gist of extracted data.
