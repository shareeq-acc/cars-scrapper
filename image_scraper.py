from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
import os

class ImageScraper:
    def __init__(self):
        self.driver = None
        self.dataset_file = 'pakwheels_main_dataset.xlsx'
        self.image_column = 'all_images'
    
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
    
    def load_dataset(self):
        """Load the main dataset"""
        if not os.path.exists(self.dataset_file):
            print(f"❌ Error: {self.dataset_file} not found!")
            return None
        
        try:
            df = pd.read_excel(self.dataset_file, engine='openpyxl')
            print(f"✓ Loaded dataset: {len(df)} records")
            return df
        except Exception as e:
            print(f"❌ Error loading dataset: {e}")
            return None
    
    def scrape_images_from_url(self, url):
        """Scrape all images from a listing URL"""
        try:
            self.driver.get(url)
            time.sleep(2)
            
            # Wait for gallery to load
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'ul.gallery'))
                )
            except:
                print("  ⚠️  Gallery not found")
                return []
            
            # Find all image elements in the gallery
            image_elements = self.driver.find_elements(By.CSS_SELECTOR, 'ul.gallery li img')
            
            image_urls = []
            for img in image_elements:
                # Check if it's the inspection pitch image
                title = img.get_attribute('title')
                alt = img.get_attribute('alt')
                
                if title and 'Inspection Pitching Image' in title:
                    continue
                if alt and 'Inspection Pitching Image' in alt:
                    continue
                
                # Get image URL from data-original or data-src or src
                img_url = (img.get_attribute('data-original') or 
                          img.get_attribute('data-src') or 
                          img.get_attribute('src'))
                
                if img_url and 'pakwheels.com/ad_pictures' in img_url:
                    # Remove thumbnail prefix if present
                    img_url = img_url.replace('/tn_', '/')
                    if img_url not in image_urls:
                        image_urls.append(img_url)
            
            return image_urls
            
        except Exception as e:
            print(f"  ❌ Error scraping images: {str(e)}")
            return []
    
    def update_images(self, df, start_idx, count):
        """Update images for specified number of listings"""
        updated = 0
        
        for i in range(start_idx, min(start_idx + count, len(df))):
            url = df.at[i, 'url']
            
            print(f"\n[{i+1}/{len(df)}] Processing: {url}")
            
            # Scrape images
            images = self.scrape_images_from_url(url)
            
            if images:
                # Join images with semicolon separator
                df.at[i, self.image_column] = '; '.join(images)
                print(f"  ✓ Found {len(images)} images")
                updated += 1
            else:
                df.at[i, self.image_column] = ''
                print(f"  ⚠️  No images found")
            
            time.sleep(2)  # Be polite to the server
        
        return df, updated
    
    def save_dataset(self, df):
        """Save updated dataset"""
        try:
            df.to_excel(self.dataset_file, index=False, engine='openpyxl')
            print(f"\n✓ Dataset saved to {self.dataset_file}")
        except Exception as e:
            print(f"\n❌ Error saving dataset: {e}")


if __name__ == "__main__":
    print("=" * 50)
    print("PakWheels Image Scraper")
    print("=" * 50)
    
    scraper = ImageScraper()
    
    # Load dataset
    print("\nLoading dataset...")
    df = scraper.load_dataset()
    
    if df is None:
        exit(1)
    
    # Add image column if it doesn't exist
    if scraper.image_column not in df.columns:
        df[scraper.image_column] = ''
        print(f"✓ Added new column: {scraper.image_column}")
    
    # Check how many listings already have images
    updated_count = df[scraper.image_column].notna().sum() - (df[scraper.image_column] == '').sum()
    not_updated_count = len(df) - updated_count
    
    print(f"\n📊 Dataset Status:")
    print(f"  - Total listings: {len(df)}")
    print(f"  - Already updated: {updated_count}")
    print(f"  - Not updated: {not_updated_count}")
    
    if not_updated_count == 0:
        print("\n✓ All listings already have images!")
        exit(0)
    
    # Find first listing without images
    first_not_updated = None
    for i in range(len(df)):
        if pd.isna(df.at[i, scraper.image_column]) or df.at[i, scraper.image_column] == '':
            first_not_updated = i
            break
    
    if first_not_updated is not None:
        print(f"\n📍 First listing without images: #{first_not_updated + 1}")
        print(f"   URL: {df.at[first_not_updated, 'url']}")
    
    # Ask user how many to update
    print("\n" + "=" * 50)
    while True:
        try:
            count = int(input(f"\nHow many listings do you want to update? (max {not_updated_count}): "))
            if count < 1:
                print("Please enter a number greater than 0.")
                continue
            if count > not_updated_count:
                print(f"Maximum available: {not_updated_count}")
                continue
            break
        except ValueError:
            print("Invalid input. Please enter a valid number.")
    
    print(f"\n✓ Will update {count} listing(s) starting from #{first_not_updated + 1}")
    print("Starting in 3 seconds...")
    time.sleep(3)
    
    # Setup driver
    print("\nSetting up Chrome driver...")
    scraper.setup_driver()
    
    # Update images
    print("\nStarting image scraping...")
    print("=" * 50)
    
    try:
        df, updated = scraper.update_images(df, first_not_updated, count)
        
        scraper.driver.quit()
        print("\n✓ Browser closed.")
        
        # Save dataset
        print("\n" + "=" * 50)
        print("Saving dataset...")
        scraper.save_dataset(df)
        
        print("\n" + "=" * 50)
        print("✓ Complete!")
        print(f"  - Updated: {updated} listings")
        print(f"  - Remaining: {not_updated_count - updated} listings")
        print("=" * 50)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user.")
        if scraper.driver:
            scraper.driver.quit()
        
        # Save progress
        print("\nSaving progress...")
        scraper.save_dataset(df)
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        if scraper.driver:
            scraper.driver.quit()
