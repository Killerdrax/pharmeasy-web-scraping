import requests
from bs4 import BeautifulSoup
import json
import logging
import time
import random
from pathlib import Path
from typing import Dict, Any, List
import os

class MedicineDetailsScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # Define the structure of data to scrape - easy to modify
        self.data_structure = {
            'uses': {'id': 'uses', 'type': 'text_with_hidden'},
            'side_effects': {'id': 'sideEffects', 'type': 'list'},
            'how_it_works': {'id': 'modeOfAction', 'type': 'text'},
            'consumption': {'id': 'directionsForUse', 'type': 'list'}
            # New fields, following the same pattern
        }
        self.setup_logging()
        self.setup_files()
        self.state = self.load_state()

    def setup_logging(self):
        logging.basicConfig(
            filename='medicine_scraper.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def setup_files(self):
        # Create necessary files if they don't exist
        if not Path('medicine_data.json').exists():
            self.save_json({})
        if not Path('scraper_progress.json').exists():
            self.save_state({'last_processed_link': None})

    def load_state(self) -> Dict:
        try:
            with open('scraper_progress.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading state: {str(e)}")
            return {'last_processed_link': None}

    def save_state(self, state: Dict):
        try:
            with open('scraper_progress.json', 'w') as f:
                json.dump(state, f)
        except Exception as e:
            logging.error(f"Error saving state: {str(e)}")

    def load_json(self) -> Dict:
        try:
            with open('medicine_data.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading JSON: {str(e)}")
            return {}

    def save_json(self, data: Dict):
        try:
            with open('medicine_data.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Error saving JSON: {str(e)}")

    def get_page(self, url: str) -> str:
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logging.error(f"Error fetching page {url}: {str(e)}")
            return None

    def extract_medicine_name(self, soup: BeautifulSoup) -> str:
        try:
            name_div = soup.find('h1', class_='MedicineOverviewSection_medicineName__dHDQi')
            return name_div.text.strip() if name_div else None
        except Exception as e:
            logging.error(f"Error extracting medicine name: {str(e)}")
            return None

    def extract_text_with_hidden(self, section) -> str:
        try:
            text_div = section.find('div', class_='Text_text__i_fng')
            if text_div:
                visible_text = text_div.get_text(strip=True)
                hidden_span = text_div.find('span', hidden=True)
                hidden_text = hidden_span.get_text(strip=True) if hidden_span else ''
                return f"{visible_text}{hidden_text}"
            return ""
        except Exception as e:
            logging.error(f"Error extracting text with hidden: {str(e)}")
            return ""

    def extract_list_items(self, section) -> List[str]:
        try:
            items = section.find_all('div', class_='Text_text__i_fng List_text__7rJzx')
            return [item.get_text(strip=True) for item in items] if items else []
        except Exception as e:
            logging.error(f"Error extracting list items: {str(e)}")
            return []

    def extract_text(self, section) -> str:
        try:
            text_div = section.find('div', class_='Text_text__i_fng')
            return text_div.get_text(strip=True) if text_div else ""
        except Exception as e:
            logging.error(f"Error extracting text: {str(e)}")
            return ""

    def extract_section_data(self, soup: BeautifulSoup, section_id: str, section_type: str) -> Any:
        section = soup.find('div', {'id': section_id})
        if not section:
            return "" if section_type == 'text' else []
        
        if section_type == 'text_with_hidden':
            return self.extract_text_with_hidden(section)
        elif section_type == 'list':
            return self.extract_list_items(section)
        elif section_type == 'text':
            return self.extract_text(section)
        return None

    def process_medicine_page(self, url: str) -> Dict:
        html = self.get_page(url)
        if not html:
            return None

        soup = BeautifulSoup(html, 'html.parser')
        medicine_name = self.extract_medicine_name(soup)
        
        if not medicine_name:
            logging.error(f"Could not find medicine name for URL: {url}")
            return None

        # Check if the main container exists
        details_container = soup.find('div', class_='DescriptionTabs_root__YOrb_')
        
        medicine_data = {
            'url': url,
        }

        # If details container exists, extract all defined fields
        if details_container:
            for field, config in self.data_structure.items():
                medicine_data[field] = self.extract_section_data(
                    details_container, 
                    config['id'], 
                    config['type']
                )
        else:
            # If details container doesn't exist, set all fields to empty values
            for field, config in self.data_structure.items():
                medicine_data[field] = "" if config['type'] == 'text' else []

        return {medicine_name: medicine_data}

    def scrape_all_medicines(self):
        try:
            with open('links.txt', 'r') as f:
                links = f.readlines()

            # Remove whitespace and empty lines
            links = [link.strip() for link in links if link.strip()]

            # Find start point if resuming
            start_index = 0
            if self.state['last_processed_link']:
                try:
                    start_index = links.index(self.state['last_processed_link']) + 1
                except ValueError:
                    start_index = 0

            medicine_data = self.load_json()

            for link in links[start_index:]:
                logging.info(f"Processing: {link}")
                
                # Random delay
                time.sleep(random.uniform(2, 4))

                medicine_info = self.process_medicine_page(link)
                if medicine_info:
                    medicine_data.update(medicine_info)
                    # Save progress periodically
                    self.save_json(medicine_data)
                    self.save_state({'last_processed_link': link})

            logging.info("Scraping completed successfully")

        except Exception as e:
            logging.error(f"Unexpected error during scraping: {str(e)}")
            raise

if __name__ == "__main__":
    scraper = MedicineDetailsScraper()
    scraper.scrape_all_medicines()