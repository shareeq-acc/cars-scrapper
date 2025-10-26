from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
import re
from datetime import datetime

class OLXCarsScraper:
    def __init__(self):
        self.base_url = "https://www.olx.com.pk/karachi_g4060695/cars_c84"
        self.cars = []
        self.driver = None
    
    def setup_driver(self):
        """Setup Chrome driver with options"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
    
    def extract_number(self, text):
        """Extract numeric value from text"""
        if not text:
            return None
        numbers = re.findall(r'\d+', text.replace(',', ''))
        return int(numbers[0]) if numbers else None
    
    def parse_car_title(self, title):
        """Parse make, model, year from title"""
        if not title:
            return None, None, None
        
        words = title.split()
        make, model, year = None, None, None
        
        # Look for year (4 digits)
        for word in words:
            if word.isdigit() and len(word) == 4 and 1990 <= int(word) <= 2025:
                year = int(word)
                break
        
        # Common car makes
        makes = ['toyota', 'honda', 'suzuki', 'nissan', 'hyundai', 'kia', 'mitsubishi', 
                'daihatsu', 'proton', 'chery', 'mg', 'haval', 'bmw', 'mercedes', 'audi', 'ford']
        
        for word in words:
            if word.lower() in makes:
                make = word.title()
                break
        
        # Model is usually what's left after removing make and year
        if make and year:
            title_clean = title
            for word in words:
                if word.lower() == make.lower() or word == str(year):
                    title_clean = title_clean.replace(word, '', 1)
            model = ' '.join(title_clean.split()).strip()
        elif make:
            # If no year found, just remove make
            title_clean = title
            for word in words:
                if word.lower() == make.lower():
                    title_clean = title_clean.replace(word, '', 1)
            model = ' '.join(title_clean.split()).strip()
        
        return make, model, year
    

    
    def scrape_page(self, page_num=1):
        """Scrape a single page using the actual HTML structure"""
        url = f"{self.base_url}?page={page_num}"
        print(f"Scraping page {page_num}...")
        
        try:
            self.driver.get(url)
            time.sleep(4)  # Wait for dynamic content to load
            
            # Scroll to load all content
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            
            # Find all listing containers (li elements with article inside)
            listings = self.driver.find_elements(By.CSS_SELECTOR, 'li[title] article')
            print(f"  Found {len(listings)} listings")
            
            cars_found = []
            
            for i, listing in enumerate(listings, 1):
                try:
                    car_data = {
                        'title': None,
                        'price': None,
                        'make': None,
                        'model': None,
                        'year': None,
                        'mileage': None,
                        'location': None,
                        'city': 'Karachi',
                        'condition': None,
                        'transmission': None,
                        'fuel_type': None,
                        'engine_capacity': None,
                        'color': None,
                        'assembly': None,
                        'body_type': None,
                        'description': None,
                        'seller_type': None,
                        'listing_date': None,
                        'status': 'Active',
                        'url': None,
                        'images': [],
                        'scraped_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    # Get title from parent li element
                    parent_li = listing.find_element(By.XPATH, './..')
                    car_data['title'] = parent_li.get_attribute('title')
                    
                    # Get URL from any link in the listing
                    try:
                        link = listing.find_element(By.CSS_SELECTOR, 'a[href*="/item/"]')
                        car_data['url'] = link.get_attribute('href')
                    except:
                        pass
                    
                    # Get price - look for the price span
                    try:
                        price_elem = listing.find_element(By.CSS_SELECTOR, '.ddc1b288, [aria-label="Price"] span')
                        price_text = price_elem.text.strip()
                        
                        # Parse "Rs 12.95 Lacs" format
                        price_match = re.search(r'Rs\s*([\d.]+)\s*Lacs?', price_text, re.IGNORECASE)
                        if price_match:
                            lacs = float(price_match.group(1))
                            car_data['price'] = int(lacs * 100000)
                        else:
                            # Try other formats
                            car_data['price'] = self.extract_number(price_text)
                    except:
                        pass
                    
                    # Parse make, model, year from title
                    if car_data['title']:
                        make, model, year = self.parse_car_title(car_data['title'])
                        car_data['make'] = make
                        car_data['model'] = model
                        car_data['year'] = year
                    
                    # Get additional details from subtitle area
                    try:
                        subtitle_area = listing.find_element(By.CSS_SELECTOR, '[aria-label="Subtitle"]')
                        
                        # Extract year (if not already found)
                        if not car_data['year']:
                            year_elem = subtitle_area.find_element(By.CSS_SELECTOR, '[aria-label="Year"] span:last-child')
                            year_text = year_elem.text.strip()
                            if year_text.isdigit():
                                car_data['year'] = int(year_text)
                        
                        # Extract mileage
                        try:
                            mileage_elem = subtitle_area.find_element(By.CSS_SELECTOR, '[aria-label="Mileage"] span:last-child')
                            mileage_text = mileage_elem.text.strip()
                            car_data['mileage'] = self.extract_number(mileage_text)
                        except:
                            pass
                        
                        # Extract fuel type
                        try:
                            fuel_elem = subtitle_area.find_element(By.CSS_SELECTOR, '[aria-label="FuelType"] span:last-child')
                            car_data['fuel_type'] = fuel_elem.text.strip()
                        except:
                            pass
                    except:
                        pass
                    
                    # Get location and listing date
                    try:
                        location_elem = listing.find_element(By.CSS_SELECTOR, '[aria-label="Location"]')
                        location_text = location_elem.text.strip()
                        # Remove the bullet point and date part
                        if '•' in location_text:
                            car_data['location'] = location_text.split('•')[0].strip()
                        else:
                            car_data['location'] = location_text
                    except:
                        pass
                    
                    # Get listing date
                    try:
                        date_elem = listing.find_element(By.CSS_SELECTOR, '[aria-label="Creation date"]')
                        car_data['listing_date'] = date_elem.text.strip()
                    except:
                        pass
                    
                    # Get image URL
                    try:
                        img_elem = listing.find_element(By.CSS_SELECTOR, 'img[src*="olx.com.pk"]')
                        img_src = img_elem.get_attribute('src')
                        if img_src:
                            car_data['images'].append(img_src)
                    except:
                        pass
                    
                    # Check if listing is featured
                    try:
                        featured_elem = listing.find_element(By.CSS_SELECTOR, '[aria-label="Featured"]')
                        if featured_elem:
                            car_data['seller_type'] = 'Featured'
                    except:
                        car_data['seller_type'] = 'Individual'
                    
                    # Add to results if we have minimum required data
                    if car_data['title'] and (car_data['make'] or car_data['price']):
                        cars_found.append(car_data)
                        price_str = f"PKR {car_data['price']:,}" if car_data['price'] else "No price"
                        print(f"    ✓ {i}: {car_data['title'][:40]}... - {price_str}")
                    else:
                        print(f"    ✗ {i}: {car_data['title'][:40] if car_data['title'] else 'No title'}... - Insufficient data")
                
                except Exception as e:
                    print(f"    ✗ {i}: Error - {str(e)}")
                    continue
            
            return cars_found
            
        except Exception as e:
            print(f"Error scraping page {page_num}: {str(e)}")
            return []
    
    def scrape(self, max_pages=5, delay=2):
        """Main scraping function"""
        print("Starting OLX Karachi Cars Scraper...")
        print("Setting up Chrome driver...")
        
        self.setup_driver()
        
        try:
            print(f"Will scrape up to {max_pages} pages")
            
            for page in range(1, max_pages + 1):
                page_cars = self.scrape_page(page)
                self.cars.extend(page_cars)
                print(f"  Page {page} complete: {len(page_cars)} cars found")
                time.sleep(delay)
        
        finally:
            self.driver.quit()
            print("Browser closed.")
        
        return self.cars
    
    def save_to_excel(self, filename='olx_karachi_cars.xlsx'):
        """Save scraped data to Excel file"""
        if not self.cars:
            print("No cars to save!")
            return
        
        df = pd.DataFrame(self.cars)
        
        # Convert image lists to comma-separated strings
        df['images'] = df['images'].apply(lambda x: ', '.join(x) if isinstance(x, list) else '')
        
        # Reorder columns
        columns_order = [
            'make', 'model', 'year', 'price', 'mileage', 'condition',
            'transmission', 'fuel_type', 'engine_capacity', 'color',
            'body_type', 'assembly', 'location', 'city', 'seller_type',
            'listing_date', 'status', 'title', 'description', 
            'images', 'url', 'scraped_date'
        ]
        df = df[[col for col in columns_order if col in df.columns]]
        
        df.to_excel(filename, index=False, engine='openpyxl')
        print(f"\n✓ Data saved to {filename}")
        print(f"Total cars scraped: {len(self.cars)}")
        
        # Print summary statistics
        print("\n--- Summary Statistics ---")
        if 'price' in df.columns:
            print(f"Average Price: PKR {df['price'].mean():,.0f}")
            print(f"Price Range: PKR {df['price'].min():,.0f} - PKR {df['price'].max():,.0f}")
        if 'year' in df.columns:
            print(f"Year Range: {df['year'].min()} - {df['year'].max()}")
        if 'make' in df.columns:
            print(f"\nTop 5 Makes:")
            print(df['make'].value_counts().head(5))
        if 'status' in df.columns:
            print(f"\nStatus Distribution:")
            print(df['status'].value_counts())


# Usage Example
if __name__ == "__main__":
    scraper = OLXCarsScraper()
    
    # Scrape 5 pages
    scraper.scrape(max_pages=5, delay=2)
    
    # Save to Excel
    scraper.save_to_excel('olx_karachi_cars.xlsx')