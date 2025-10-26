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
from datetime import datetime, timedelta

class PakWheelsScraper:
    def __init__(self):
        self.base_url = "https://www.pakwheels.com/used-cars/karachi/24857"
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
    
    def parse_listing_date(self, date_text):
        """Parse listing date from PakWheels format"""
        if not date_text:
            return None
        
        date_text = date_text.lower().strip()
        
        try:
            # Handle "just now", "today"
            if 'just now' in date_text or 'today' in date_text:
                return datetime.now().strftime('%Y-%m-%d')
            
            # Handle "yesterday"
            if 'yesterday' in date_text:
                yesterday = datetime.now() - timedelta(days=1)
                return yesterday.strftime('%Y-%m-%d')
            
            # Handle "X hours ago"
            hours_match = re.search(r'(\d+)\s*hour', date_text)
            if hours_match:
                return datetime.now().strftime('%Y-%m-%d')
            
            # Handle "X days ago"
            days_match = re.search(r'(\d+)\s*day', date_text)
            if days_match:
                days_ago = int(days_match.group(1))
                date = datetime.now() - timedelta(days=days_ago)
                return date.strftime('%Y-%m-%d')
            
            # Handle "X weeks ago"
            weeks_match = re.search(r'(\d+)\s*week', date_text)
            if weeks_match:
                weeks_ago = int(weeks_match.group(1))
                date = datetime.now() - timedelta(weeks=weeks_ago)
                return date.strftime('%Y-%m-%d')
            
            # Handle "X months ago"
            months_match = re.search(r'(\d+)\s*month', date_text)
            if months_match:
                months_ago = int(months_match.group(1))
                date = datetime.now() - timedelta(days=months_ago*30)
                return date.strftime('%Y-%m-%d')
            
            return date_text
            
        except Exception as e:
            return date_text
    
    def is_complete_listing(self, car_data):
        """Check if listing has all required fields"""
        required_fields = ['make', 'model', 'year', 'price', 'mileage']
        return all(car_data.get(field) for field in required_fields)
    
    def check_if_sold(self, listing_element):
        """Check if listing is marked as sold"""
        try:
            # Look for "SOLD" badge or similar indicators
            sold_indicators = listing_element.find_elements(By.XPATH, ".//*[contains(text(), 'SOLD') or contains(text(), 'Sold')]")
            if sold_indicators:
                return 'Sold'
            
            # Check for strikethrough or opacity changes
            style = listing_element.get_attribute('style')
            if style and ('opacity: 0.5' in style or 'text-decoration: line-through' in style):
                return 'Sold'
            
            return 'Active'
        except:
            return 'Active'
    
    def scrape_listing(self, listing_element):
        """Extract data from a single listing card"""
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
                'registered_city': None,
                'description': None,
                'seller_type': None,
                'listing_date': None,
                'status': 'Active',
                'url': None,
                'images': [],
                'scraped_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Check if sold
            car_data['status'] = self.check_if_sold(listing_element)
            
            # Extract URL
            try:
                if listing_element.tag_name == 'a':
                    car_data['url'] = listing_element.get_attribute('href')
                else:
                    link = listing_element.find_element(By.CSS_SELECTOR, 'a[href*="/used-cars/"]')
                    car_data['url'] = link.get_attribute('href')
            except:
                pass
            
            # Extract title (usually contains Make Model Year)
            try:
                title_elem = listing_element.find_element(By.CSS_SELECTOR, '.car-name')
                car_data['title'] = title_elem.text.strip()
                
                # Parse make, model, year from title
                title_parts = car_data['title'].split()
                if len(title_parts) >= 3:
                    # Usually format: "Make Model Year" or "Year Make Model"
                    if title_parts[0].isdigit():
                        car_data['year'] = int(title_parts[0])
                        car_data['make'] = title_parts[1]
                        car_data['model'] = ' '.join(title_parts[2:])
                    elif title_parts[-1].isdigit():
                        car_data['year'] = int(title_parts[-1])
                        car_data['make'] = title_parts[0]
                        car_data['model'] = ' '.join(title_parts[1:-1])
            except:
                pass
            
            # Extract price
            try:
                price_elem = listing_element.find_element(By.CSS_SELECTOR, '.price-details')
                price_text = price_elem.text.strip()
                
                # Handle "PKR", "Lacs", "Crore"
                if 'crore' in price_text.lower():
                    num = self.extract_number(price_text)
                    car_data['price'] = num * 10000000 if num else None
                elif 'lac' in price_text.lower() or 'lakh' in price_text.lower():
                    num = self.extract_number(price_text)
                    # Handle decimal lacs (e.g., "45.5 lacs")
                    numbers = re.findall(r'[\d.]+', price_text.replace(',', ''))
                    if numbers:
                        car_data['price'] = int(float(numbers[0]) * 100000)
                else:
                    car_data['price'] = self.extract_number(price_text)
            except:
                pass
            
            # Extract location
            try:
                location_elem = listing_element.find_element(By.CSS_SELECTOR, '.location')
                car_data['location'] = location_elem.text.strip()
            except:
                pass
            
            # Extract mileage
            try:
                mileage_elem = listing_element.find_element(By.XPATH, ".//*[contains(text(), 'km') or contains(text(), 'KM')]")
                car_data['mileage'] = self.extract_number(mileage_elem.text)
            except:
                pass
            
            # Extract listing date
            try:
                date_elem = listing_element.find_element(By.CSS_SELECTOR, '.date, .time-ago')
                car_data['listing_date'] = self.parse_listing_date(date_elem.text)
            except:
                pass
            
            # Extract other specs
            try:
                specs = listing_element.find_elements(By.CSS_SELECTOR, '.specs li, .car-details li')
                for spec in specs:
                    spec_text = spec.text.strip().lower()
                    
                    if 'cc' in spec_text or 'engine' in spec_text:
                        car_data['engine_capacity'] = self.extract_number(spec_text)
                    elif 'manual' in spec_text or 'automatic' in spec_text:
                        car_data['transmission'] = spec.text.strip()
                    elif 'petrol' in spec_text or 'diesel' in spec_text or 'hybrid' in spec_text or 'cng' in spec_text:
                        car_data['fuel_type'] = spec.text.strip()
                    elif 'local' in spec_text or 'imported' in spec_text:
                        car_data['assembly'] = spec.text.strip()
            except:
                pass
            
            # Extract image
            try:
                img = listing_element.find_element(By.CSS_SELECTOR, 'img')
                img_src = img.get_attribute('src')
                if img_src:
                    car_data['images'].append(img_src)
            except:
                pass
            
            # Determine seller type (PakWheels often has dealer badges)
            try:
                dealer_badge = listing_element.find_elements(By.XPATH, ".//*[contains(text(), 'Dealer') or contains(text(), 'dealer')]")
                car_data['seller_type'] = 'Dealer' if dealer_badge else 'Individual'
            except:
                pass
            
            return car_data if self.is_complete_listing(car_data) else None
            
        except Exception as e:
            print(f"    Error parsing listing: {str(e)}")
            return None
    
    def scrape(self, max_pages=5, delay=3):
        """Main scraping function"""
        print("Starting PakWheels Karachi Cars Scraper...")
        print("Setting up Chrome driver...")
        
        self.setup_driver()
        
        try:
            for page in range(1, max_pages + 1):
                url = f"{self.base_url}?page={page}"
                print(f"\nScraping page {page}: {url}")
                
                self.driver.get(url)
                time.sleep(delay)
                
                # Wait for listings to appear
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href*="/used-cars/"]'))
                    )
                except:
                    print(f"  No listings found on page {page}")
                    continue
                
                # Scroll to load all listings (PakWheels may have lazy loading)
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                # Find all car listing links
                car_links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/used-cars/"]')
                
                # Filter to get actual car listings (not category/filter links)
                listings = []
                for link in car_links:
                    href = link.get_attribute('href')
                    if href and '/used-cars/' in href and any(x in href for x in ['/car/', '-', 'karachi']):
                        # Find the parent container that has the car info
                        try:
                            parent = link.find_element(By.XPATH, './ancestor::div[contains(@class, "well") or contains(@class, "card") or contains(@class, "listing")]')
                            if parent not in listings:
                                listings.append(parent)
                        except:
                            # If no specific parent, use the link itself
                            listings.append(link)
                print(f"  Found {len(listings)} listings")
                
                # Scrape each listing
                for idx, listing in enumerate(listings, 1):
                    print(f"  Processing listing {idx}/{len(listings)}...", end=' ')
                    car_data = self.scrape_listing(listing)
                    
                    if car_data:
                        self.cars.append(car_data)
                        print(f"✓ {car_data['year']} {car_data['make']} {car_data['model']} [{car_data['status']}]")
                    else:
                        print("✗ Skipped")
                
                print(f"Page {page} complete. Total cars: {len(self.cars)}")
                time.sleep(delay)
        
        finally:
            self.driver.quit()
            print("\nBrowser closed.")
        
        return self.cars
    
    def save_to_excel(self, filename='pakwheels_karachi_cars.xlsx'):
        """Save scraped data to Excel file"""
        if not self.cars:
            print("No cars to save!")
            return
        
        df = pd.DataFrame(self.cars)
        
        # Convert image lists to strings
        df['images'] = df['images'].apply(lambda x: ', '.join(x) if isinstance(x, list) else '')
        
        # Reorder columns
        columns_order = [
            'make', 'model', 'year', 'price', 'mileage', 'condition',
            'transmission', 'fuel_type', 'engine_capacity', 'color',
            'assembly', 'registered_city', 'location', 'city', 
            'seller_type', 'listing_date', 'status', 'title',
            'description', 'images', 'url', 'scraped_date'
        ]
        df = df[[col for col in columns_order if col in df.columns]]
        
        df.to_excel(filename, index=False, engine='openpyxl')
        print(f"\n✓ Data saved to {filename}")
        print(f"Total cars: {len(self.cars)}")
        
        # Summary statistics
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
    scraper = PakWheelsScraper()
    
    # Scrape 3 pages
    scraper.scrape(max_pages=3, delay=3)
    
    # Save to Excel
    scraper.save_to_excel('pakwheels_karachi_cars.xlsx')