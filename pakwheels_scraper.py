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
import json
import os
from datetime import datetime, timedelta

class PakWheelsScraper:
    def __init__(self):
        self.base_url = "https://www.pakwheels.com/used-cars/search/-/"
        self.cars = []
        self.driver = None
        self.progress_file = 'scraper_progress.json'
        self.main_dataset_file = 'pakwheels_main_dataset.xlsx'
    
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
        """Extract data from a single listing card (li element)"""
        try:
            car_data = {
                'title': None,
                'price': None,
                'make': None,
                'model': None,
                'year': None,
                'mileage': None,
                'location': None,
                'city': None,
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
            
            # Check if featured
            try:
                featured = listing_element.find_elements(By.CSS_SELECTOR, '.featured-ribbon')
                car_data['seller_type'] = 'Featured' if featured else 'Individual'
            except:
                pass
            
            # Extract URL and title from h3 > a
            try:
                title_link = listing_element.find_element(By.CSS_SELECTOR, '.search-title a.car-name')
                car_data['url'] = title_link.get_attribute('href')
                car_data['title'] = title_link.text.strip()
                
                # Parse make, model, year from title
                # Format: "Honda N Wgn 2023 G for Sale" -> Make: Honda, Model: N Wgn, Year: 2023
                title_parts = car_data['title'].replace(' for Sale', '').split()
                
                # Find year (4-digit number)
                year_idx = None
                for idx, part in enumerate(title_parts):
                    if part.isdigit() and len(part) == 4:
                        car_data['year'] = int(part)
                        year_idx = idx
                        break
                
                if year_idx is not None:
                    car_data['make'] = title_parts[0] if year_idx > 0 else None
                    if year_idx > 1:
                        car_data['model'] = ' '.join(title_parts[1:year_idx])
                    elif year_idx == 1:
                        car_data['model'] = title_parts[year_idx + 1] if len(title_parts) > year_idx + 1 else None
            except Exception as e:
                pass
            
            # Extract price from .price-details
            try:
                price_elem = listing_element.find_element(By.CSS_SELECTOR, '.price-details')
                price_text = price_elem.text.strip()
                
                # Handle "PKR 35.75 lacs" format
                if 'crore' in price_text.lower():
                    numbers = re.findall(r'[\d.]+', price_text.replace(',', ''))
                    if numbers:
                        car_data['price'] = int(float(numbers[0]) * 10000000)
                elif 'lac' in price_text.lower() or 'lakh' in price_text.lower():
                    numbers = re.findall(r'[\d.]+', price_text.replace(',', ''))
                    if numbers:
                        car_data['price'] = int(float(numbers[0]) * 100000)
                else:
                    car_data['price'] = self.extract_number(price_text)
            except:
                pass
            
            # Extract location from .search-vehicle-info
            try:
                location_elem = listing_element.find_element(By.CSS_SELECTOR, '.search-vehicle-info li')
                car_data['location'] = location_elem.text.strip()
                car_data['city'] = car_data['location']
            except:
                pass
            
            # Extract specs from .search-vehicle-info-2
            try:
                specs = listing_element.find_elements(By.CSS_SELECTOR, '.search-vehicle-info-2 li')
                for spec in specs:
                    spec_text = spec.text.strip()
                    
                    # Year (if not already extracted)
                    if spec_text.isdigit() and len(spec_text) == 4 and not car_data['year']:
                        car_data['year'] = int(spec_text)
                    
                    # Mileage (e.g., "35,000 km")
                    elif 'km' in spec_text.lower():
                        car_data['mileage'] = self.extract_number(spec_text)
                    
                    # Fuel type
                    elif spec_text.lower() in ['petrol', 'diesel', 'hybrid', 'cng', 'electric']:
                        car_data['fuel_type'] = spec_text
                    
                    # Engine capacity (e.g., "660 cc")
                    elif 'cc' in spec_text.lower():
                        car_data['engine_capacity'] = self.extract_number(spec_text)
                    
                    # Transmission
                    elif spec_text.lower() in ['automatic', 'manual']:
                        car_data['transmission'] = spec_text
            except:
                pass
            
            # Extract listing date from .dated
            try:
                date_elem = listing_element.find_element(By.CSS_SELECTOR, '.dated')
                date_text = date_elem.text.strip().replace('Updated ', '')
                car_data['listing_date'] = self.parse_listing_date(date_text)
            except:
                pass
            
            # Extract image
            try:
                img = listing_element.find_element(By.CSS_SELECTOR, '.img-box img.pic')
                img_src = img.get_attribute('src')
                if img_src:
                    car_data['images'].append(img_src)
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
    
    def load_progress(self):
        """Load scraping progress from file"""
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        return {'last_page': 0, 'last_scrape_date': None}
    
    def save_progress(self, page_number):
        """Save scraping progress to file"""
        progress = {
            'last_page': page_number,
            'last_scrape_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        with open(self.progress_file, 'w') as f:
            json.dump(progress, f, indent=2)
    
    def remove_duplicates(self):
        """Remove duplicate entries based on URL"""
        if not self.cars:
            return 0
        
        initial_count = len(self.cars)
        
        # Create DataFrame and remove duplicates based on URL
        df = pd.DataFrame(self.cars)
        df_unique = df.drop_duplicates(subset=['url'], keep='first')
        
        self.cars = df_unique.to_dict('records')
        removed = initial_count - len(self.cars)
        
        if removed > 0:
            print(f"  🗑️  Removed {removed} duplicate(s)")
        
        return removed
    
    def load_main_dataset(self):
        """Load existing main dataset"""
        if os.path.exists(self.main_dataset_file):
            try:
                df = pd.read_excel(self.main_dataset_file, engine='openpyxl')
                print(f"✓ Loaded main dataset: {len(df)} existing records")
                return df
            except Exception as e:
                print(f"⚠️  Error loading main dataset: {e}")
                return None
        return None
    
    def save_to_excel(self, filename='pakwheels_karachi_cars.xlsx', append_mode=False):
        """Save scraped data to Excel file"""
        if not self.cars:
            print("No cars to save!")
            return
        
        df_new = pd.DataFrame(self.cars)
        
        # Convert image lists to strings
        df_new['images'] = df_new['images'].apply(lambda x: ', '.join(x) if isinstance(x, list) else '')
        
        # Reorder columns
        columns_order = [
            'make', 'model', 'year', 'price', 'mileage', 'condition',
            'transmission', 'fuel_type', 'engine_capacity', 'color',
            'assembly', 'registered_city', 'location', 'city', 
            'seller_type', 'listing_date', 'status', 'title',
            'description', 'images', 'url', 'scraped_date'
        ]
        df_new = df_new[[col for col in columns_order if col in df_new.columns]]
        
        if append_mode:
            # Load existing dataset
            df_existing = self.load_main_dataset()
            
            if df_existing is not None:
                # Combine datasets
                df_combined = pd.concat([df_existing, df_new], ignore_index=True)
                
                # Remove duplicates based on URL
                initial_count = len(df_combined)
                df_combined = df_combined.drop_duplicates(subset=['url'], keep='first')
                removed = initial_count - len(df_combined)
                
                print(f"\n📊 Dataset merge:")
                print(f"  - Existing records: {len(df_existing)}")
                print(f"  - New records: {len(df_new)}")
                print(f"  - Duplicates removed: {removed}")
                print(f"  - Total unique records: {len(df_combined)}")
                
                df_new = df_combined
        
        df_new.to_excel(filename, index=False, engine='openpyxl')
        print(f"\n✓ Data saved to {filename}")
        print(f"Total cars: {len(df_new)}")
        
        # Summary statistics
        print("\n--- Summary Statistics ---")
        if 'price' in df_new.columns:
            print(f"Average Price: PKR {df_new['price'].mean():,.0f}")
            print(f"Price Range: PKR {df_new['price'].min():,.0f} - PKR {df_new['price'].max():,.0f}")
        if 'year' in df_new.columns:
            print(f"Year Range: {df_new['year'].min()} - {df_new['year'].max()}")
        if 'make' in df_new.columns:
            print(f"\nTop 5 Makes:")
            print(df_new['make'].value_counts().head(5))
        if 'status' in df_new.columns:
            print(f"\nStatus Distribution:")
            print(df_new['status'].value_counts())


# Usage Example
if __name__ == "__main__":
    print("=" * 50)
    print("PakWheels Cars Scraper")
    print("=" * 50)
    
    scraper = PakWheelsScraper()
    
    # Load and show progress
    progress = scraper.load_progress()
    if progress['last_page'] > 0:
        print(f"\n📊 Last scraping session:")
        print(f"  - Last page scraped: {progress['last_page']}")
        print(f"  - Date: {progress['last_scrape_date']}")
    
    # Check if main dataset exists
    dataset_exists = os.path.exists(scraper.main_dataset_file)
    if dataset_exists:
        df_existing = scraper.load_main_dataset()
        if df_existing is not None:
            print(f"  - Main dataset has {len(df_existing)} records")
    
    # Ask user: new or append
    print("\n" + "=" * 50)
    while True:
        mode = input("\nCreate NEW dataset or APPEND to main dataset? (new/append): ").strip().lower()
        if mode in ['new', 'append']:
            break
        print("Invalid input. Please enter 'new' or 'append'.")
    
    append_mode = (mode == 'append')
    
    if append_mode and not dataset_exists:
        print("\n⚠️  Main dataset doesn't exist. Will create a new one.")
        append_mode = False
    
    # Get page range from user
    print("\n" + "=" * 50)
    while True:
        try:
            start_page = int(input("\nEnter starting page number: "))
            if start_page < 1:
                print("Page number must be at least 1. Please try again.")
                continue
            break
        except ValueError:
            print("Invalid input. Please enter a valid number.")
    
    while True:
        try:
            end_page = int(input("Enter ending page number: "))
            if end_page < start_page:
                print(f"Ending page must be >= starting page ({start_page}). Please try again.")
                continue
            break
        except ValueError:
            print("Invalid input. Please enter a valid number.")
    
    total_pages = end_page - start_page + 1
    print(f"\n{'📝 Mode: APPEND to main dataset' if append_mode else '🆕 Mode: CREATE new dataset'}")
    print(f"Will scrape {total_pages} page(s) from page {start_page} to {end_page}")
    print("Starting in 3 seconds...")
    time.sleep(3)
    
    scraper.setup_driver()
    
    # Scrape pages
    print("\nStarting scrape...")
    try:
        for page in range(start_page, end_page + 1):
            url = f"{scraper.base_url}?page={page}"
            print(f"\n{'='*50}")
            print(f"Scraping page {page}/{end_page}")
            print(f"{'='*50}")
            
            scraper.driver.get(url)
            time.sleep(3)
            
            # Wait for listings to appear
            try:
                WebDriverWait(scraper.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'li.classified-listing'))
                )
            except:
                print(f"  ⚠️  No listings found on page {page}")
                continue
            
            # Scroll to load all listings
            scraper.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Find all car listing <li> elements
            listings = scraper.driver.find_elements(By.CSS_SELECTOR, 'li.classified-listing')
            print(f"  Found {len(listings)} listings")
            
            # Scrape each listing
            for idx, listing in enumerate(listings, 1):
                print(f"  [{idx}/{len(listings)}] ", end='')
                car_data = scraper.scrape_listing(listing)
                
                if car_data:
                    scraper.cars.append(car_data)
                    print(f"✓ {car_data['year']} {car_data['make']} {car_data['model']} - PKR {car_data['price']:,}")
                else:
                    print("✗ Skipped (incomplete data)")
            
            print(f"\n✓ Page {page} complete. Total scraped: {len(scraper.cars)}")
            
            # Save progress
            scraper.save_progress(page)
            
            # Remove duplicates every 5 pages
            if page % 5 == 0:
                print(f"\n🔍 Checking for duplicates...")
                scraper.remove_duplicates()
            
            time.sleep(3)
        
        scraper.driver.quit()
        print("\n✓ Browser closed.")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Scraping interrupted by user.")
        if scraper.driver:
            scraper.driver.quit()
        # Save progress even if interrupted
        if scraper.cars:
            scraper.save_progress(page)
    except Exception as e:
        print(f"\n❌ Error during scraping: {str(e)}")
        if scraper.driver:
            scraper.driver.quit()
    
    # Final duplicate check
    if scraper.cars:
        print(f"\n🔍 Final duplicate check...")
        scraper.remove_duplicates()
    
    # Save to Excel
    if scraper.cars:
        print("\n" + "=" * 50)
        print("Saving data...")
        print("=" * 50)
        
        if append_mode:
            scraper.save_to_excel(scraper.main_dataset_file, append_mode=True)
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'pakwheels_cars_{timestamp}.xlsx'
            scraper.save_to_excel(filename, append_mode=False)
            
            # Also save as main dataset if user wants
            save_as_main = input("\nSave this as the main dataset? (yes/no): ").strip().lower()
            if save_as_main == 'yes':
                scraper.save_to_excel(scraper.main_dataset_file, append_mode=False)
                print(f"✓ Also saved as main dataset: {scraper.main_dataset_file}")
    else:
        print("\n⚠️  No cars scraped. Nothing to save.")