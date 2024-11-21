import requests
from bs4 import BeautifulSoup
import string
import logging
import json
import time
from pathlib import Path
import os
import random

class PharmEasyScraper:
    def __init__(self):
        self.base_url = "https://pharmeasy.in/online-medicine-order/browse"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.setup_logging()
        self.setup_files()
        self.state = self.load_state()

    def setup_logging(self):
        logging.basicConfig(
            filename='scraper.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def setup_files(self):
        # Create links file 
        if not Path('links.txt').exists():
            Path('links.txt').touch()
        
        # Log file
        if not Path('scraper_state.json').exists():
            self.save_state({'current_letter': 'a', 'current_page': 0})

    def load_state(self):
        try:
            with open('scraper_state.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading state: {str(e)}")
            return {'current_letter': 'a', 'current_page': 0}

    def save_state(self, state):
        try:
            with open('scraper_state.json', 'w') as f:
                json.dump(state, f)
        except Exception as e:
            logging.error(f"Error saving state: {str(e)}")

    def save_link(self, link):
        try:
            with open('links.txt', 'a', encoding='utf-8') as f:
                f.write(link + '\n')
        except Exception as e:
            logging.error(f"Error saving link: {str(e)}")

    def get_page(self, letter, page):
        url = f"{self.base_url}?alphabet={letter}&page={page}"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logging.error(f"Error fetching page {url}: {str(e)}")
            return None

    def has_next_page(self, soup):
        # Check for the next page SVG button
        next_page = soup.find('a', href=lambda x: x and 'page=' in x)
        return bool(next_page)

    def extract_links(self, soup):
        links = []
        try:
            medicine_containers = soup.find_all('div', class_='BrowseList_medicineContainer__Fi9u7')
            for container in medicine_containers:
                link = container.find('a', class_='BrowseList_medicine__cQZkc')
                if link:
                    full_link = f"https://pharmeasy.in{link['href']}"
                    links.append(full_link)
        except Exception as e:
            logging.error(f"Error extracting links: {str(e)}")
        return links

    def scrape(self):
        current_letter = self.state['current_letter']
        current_page = self.state['current_page']
        
        logging.info(f"Starting scrape from letter {current_letter} page {current_page}")

        try:
            for letter in string.ascii_lowercase[string.ascii_lowercase.index(current_letter):]:
                page = current_page if letter == current_letter else 0
                
                while True:
                    logging.info(f"Processing letter {letter} page {page}")
                    
                    html = self.get_page(letter, page)
                    if not html:
                        break

                    soup = BeautifulSoup(html, 'html.parser')
                    links = self.extract_links(soup)

                    if not links:
                        logging.info(f"No links found for letter {letter} page {page}")
                        break

                    for link in links:
                        self.save_link(link)

                    if not self.has_next_page(soup):
                        logging.info(f"No more pages for letter {letter}")
                        break

                    page += 1
                    self.save_state({'current_letter': letter, 'current_page': page})
                    time.sleep(random.uniform(2,5))

                current_page = 0 #Starts as next alphabet starts
                
            logging.info("Scraping completed successfully")
            
        except Exception as e:
            logging.error(f"Unexpected error during scraping: {str(e)}")
            self.save_state({'current_letter': current_letter, 'current_page': current_page})
            raise

if __name__ == "__main__":
    scraper = PharmEasyScraper()
    scraper.scrape()