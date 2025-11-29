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
from dotenv import load_dotenv
import groq
import base64
import requests
from io import BytesIO
from PIL import Image
import re

class ImageScraper:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        self.driver = None
        self.dataset_file = 'pakwheels_main_dataset.xlsx'
        self.image_column = 'all_images'
        
        # Setup Groq API client
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            print("⚠️  WARNING: GROQ_API_KEY not found in environment variables!")
            print("   AI analysis will be skipped.")
            self.groq_client = None
        else:
            try:
                self.groq_client = groq.Groq(api_key=api_key)
                print("✓ Groq API client initialized")
            except Exception as e:
                print(f"⚠️  Error initializing Groq client: {e}")
                self.groq_client = None
    
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
    
    def scrape_listing_details(self, url):
        """Scrape images and additional details from a listing URL"""
        try:
            self.driver.get(url)
            time.sleep(2)
            
            # Wait for page to load
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'body'))
                )
            except:
                print("  ⚠️  Page not loaded")
                return [], {}
            
            # Scrape images
            image_urls = []
            try:
                image_elements = self.driver.find_elements(By.CSS_SELECTOR, 'ul.gallery li img')
                
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
            except:
                pass
            
            # Scrape additional details
            details = {
                'exterior_color': None,
                'body_condition': None,
                'mechanical_condition': None,
                'registered_in': None
            }
            
            try:
                # Find all list items with car details
                detail_items = self.driver.find_elements(By.CSS_SELECTOR, 'ul.car-details li, ul.list-unstyled li')
                
                for item in detail_items:
                    text = item.text.strip()
                    
                    # Extract color
                    if 'Color' in text or 'Colour' in text:
                        # Format: "Color: White" or "Exterior Color: Silver"
                        parts = text.split(':')
                        if len(parts) == 2:
                            details['exterior_color'] = parts[1].strip()
                    
                    # Extract body condition
                    elif 'Body Condition' in text or 'Exterior Condition' in text:
                        parts = text.split(':')
                        if len(parts) == 2:
                            details['body_condition'] = parts[1].strip()
                    
                    # Extract mechanical condition
                    elif 'Mechanical Condition' in text or 'Engine Condition' in text:
                        parts = text.split(':')
                        if len(parts) == 2:
                            details['mechanical_condition'] = parts[1].strip()
                    
                    # Extract registered city
                    elif 'Registered In' in text or 'Registration City' in text:
                        parts = text.split(':')
                        if len(parts) == 2:
                            details['registered_in'] = parts[1].strip()
            except:
                pass
            
            # Try alternative selectors for details
            try:
                # Look for data in structured format
                color_elem = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Color') or contains(text(), 'Colour')]/following-sibling::*[1]")
                if color_elem and not details['exterior_color']:
                    details['exterior_color'] = color_elem[0].text.strip()
                
                # Look in table format
                rows = self.driver.find_elements(By.CSS_SELECTOR, 'table tr, .generic-table tr')
                for row in rows:
                    cells = row.find_elements(By.TAG_NAME, 'td')
                    if len(cells) >= 2:
                        key = cells[0].text.strip().lower()
                        value = cells[1].text.strip()
                        
                        if 'color' in key or 'colour' in key:
                            details['exterior_color'] = value
                        elif 'body' in key and 'condition' in key:
                            details['body_condition'] = value
                        elif 'mechanical' in key or ('engine' in key and 'condition' in key):
                            details['mechanical_condition'] = value
                        elif 'registered' in key:
                            details['registered_in'] = value
            except:
                pass
            
            return image_urls, details
            
        except Exception as e:
            print(f"  ❌ Error scraping details: {str(e)}")
            return [], {}
    
    def update_images(self, df, start_idx, count):
        """Update images and details for specified number of listings"""
        updated = 0
        
        # Add new columns if they don't exist
        new_columns = [
            'exterior_color', 'body_condition', 'mechanical_condition', 'registered_in',
            'ai_exterior_color', 'ai_secondary_color', 'ai_body_condition', 
            'ai_condition_score', 'ai_has_visible_damage', 'ai_damage_details',
            'ai_interior_condition', 'ai_presentation_score', 'ai_confidence'
        ]
        for col in new_columns:
            if col not in df.columns:
                df[col] = ''
        
        for i in range(start_idx, min(start_idx + count, len(df))):
            url = df.at[i, 'url']
            
            print(f"\n[{i+1}/{len(df)}] Processing: {url}")
            
            # Scrape images and details
            images, details = self.scrape_listing_details(url)
            
            if images:
                # Join images with semicolon separator
                df.at[i, self.image_column] = '; '.join(images)
                print(f"  ✓ Found {len(images)} images")
                updated += 1
            else:
                df.at[i, self.image_column] = ''
                print(f"  ⚠️  No images found")
            
            # Update scraped details
            details_found = []
            if details['exterior_color']:
                df.at[i, 'exterior_color'] = details['exterior_color']
                details_found.append(f"Color: {details['exterior_color']}")
            
            if details['body_condition']:
                df.at[i, 'body_condition'] = details['body_condition']
                details_found.append(f"Body: {details['body_condition']}")
            
            if details['mechanical_condition']:
                df.at[i, 'mechanical_condition'] = details['mechanical_condition']
                details_found.append(f"Mechanical: {details['mechanical_condition']}")
            
            if details['registered_in']:
                df.at[i, 'registered_in'] = details['registered_in']
                details_found.append(f"Registered: {details['registered_in']}")
            
            if details_found:
                print(f"  📋 Scraped: {', '.join(details_found)}")
            
            # AI Analysis
            if images and self.groq_client:
                ai_fields = self.analyze_car_images(images)
                
                # Update AI fields
                for field, value in ai_fields.items():
                    df.at[i, field] = value
                
                # Display AI results
                if ai_fields['ai_exterior_color']:
                    print(f"  🤖 AI Analysis:")
                    print(f"     Color: {ai_fields['ai_exterior_color']}", end='')
                    if ai_fields['ai_secondary_color'] and ai_fields['ai_secondary_color'] != 'None':
                        print(f" + {ai_fields['ai_secondary_color']}")
                    else:
                        print()
                    
                    print(f"     Condition: {ai_fields['ai_body_condition']} (Score: {ai_fields['ai_condition_score']}/10)")
                    print(f"     Damage: {ai_fields['ai_has_visible_damage']} - {ai_fields['ai_damage_details']}")
                    print(f"     Interior: {ai_fields['ai_interior_condition']}")
                    print(f"     Presentation: {ai_fields['ai_presentation_score']}/10")
                    print(f"     Confidence: {ai_fields['ai_confidence']}")
                    
                    # Compare scraped vs AI color
                    if details['exterior_color'] and ai_fields['ai_exterior_color']:
                        scraped_color = details['exterior_color'].lower()
                        ai_color = ai_fields['ai_exterior_color'].lower()
                        if scraped_color not in ai_color and ai_color not in scraped_color:
                            print(f"     ⚠️  Color mismatch: Scraped='{details['exterior_color']}' vs AI='{ai_fields['ai_exterior_color']}'")
            
            time.sleep(2)  # Be polite to the server
        
        return df, updated
    
    def download_and_encode_image(self, image_url):
        """Download image and convert to base64"""
        try:
            # Add headers to avoid 403 Forbidden
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.pakwheels.com/',
                'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Sec-Fetch-Dest': 'image',
                'Sec-Fetch-Mode': 'no-cors',
                'Sec-Fetch-Site': 'same-site'
            }
            response = requests.get(image_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Open image and convert to RGB if needed
            img = Image.open(BytesIO(response.content))
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize if too large (max 1024px on longest side)
            max_size = 1024
            if max(img.size) > max_size:
                ratio = max_size / max(img.size)
                new_size = tuple(int(dim * ratio) for dim in img.size)
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # Convert to base64
            buffered = BytesIO()
            img.save(buffered, format="JPEG", quality=85)
            img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            return img_base64
        except Exception as e:
            print(f"    ⚠️  Error downloading image: {e}")
            return None
    
    def analyze_car_images(self, image_urls):
        """Analyze car images using Groq Vision API"""
        if not self.groq_client:
            return self._empty_ai_fields()
        
        if not image_urls:
            return self._empty_ai_fields()
        
        # Use up to 5 images (Llama 4 Scout limit)
        images_to_analyze = image_urls[:5]
        
        try:
            # Download and encode first image
            print(f"    🤖 Analyzing {len(images_to_analyze)} image(s) with Llama 4 Scout Vision...")
            img_base64 = self.download_and_encode_image(images_to_analyze[0])
            
            if not img_base64:
                return self._empty_ai_fields()
            
            # Create prompt for structured analysis
            prompt = """Analyze this car listing photo carefully and provide detailed assessment.

Respond in EXACTLY this format (one field per line):

PRIMARY_COLOR: [main exterior color - be specific like "Pearl White", "Metallic Silver", "Black", etc.]
SECONDARY_COLOR: [secondary/accent color if visible, otherwise "None"]
BODY_CONDITION: [Excellent/Very Good/Good/Fair/Poor]
CONDITION_SCORE: [numeric score 1-10, where 10 is perfect]
HAS_VISIBLE_DAMAGE: [Yes/No - for scratches, dents, rust, paint issues]
DAMAGE_DETAILS: [brief description of any visible damage, or "None visible"]
INTERIOR_CONDITION: [Excellent/Very Good/Good/Fair/Poor if visible, otherwise "Not visible"]
PRESENTATION_SCORE: [1-10 rating for photo quality, cleanliness, and presentation]
CONFIDENCE: [High/Medium/Low - your confidence in this analysis]

Be precise and honest. If you can't see something clearly, say so."""

            # Call Groq API with Llama 4 Scout Vision (current production model)
            response = self.groq_client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{img_base64}"
                                }
                            }
                        ]
                    }
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            # Parse response
            ai_response = response.choices[0].message.content
            return self._parse_ai_response(ai_response)
            
        except Exception as e:
            print(f"    ❌ AI analysis error: {e}")
            return self._empty_ai_fields()
    
    def _empty_ai_fields(self):
        """Return empty AI fields"""
        return {
            'ai_exterior_color': '',
            'ai_secondary_color': '',
            'ai_body_condition': '',
            'ai_condition_score': '',
            'ai_has_visible_damage': '',
            'ai_damage_details': '',
            'ai_interior_condition': '',
            'ai_presentation_score': '',
            'ai_confidence': ''
        }
    
    def _parse_ai_response(self, response_text):
        """Parse AI response into structured fields"""
        fields = self._empty_ai_fields()
        
        try:
            lines = response_text.strip().split('\n')
            
            for line in lines:
                if ':' not in line:
                    continue
                
                key, value = line.split(':', 1)
                key = key.strip().upper()
                value = value.strip()
                
                if 'PRIMARY' in key and 'COLOR' in key:
                    fields['ai_exterior_color'] = value
                elif 'SECONDARY' in key and 'COLOR' in key:
                    fields['ai_secondary_color'] = value
                elif 'BODY' in key and 'CONDITION' in key:
                    fields['ai_body_condition'] = value
                elif 'CONDITION' in key and 'SCORE' in key:
                    fields['ai_condition_score'] = value
                elif 'VISIBLE' in key and 'DAMAGE' in key:
                    fields['ai_has_visible_damage'] = value
                elif 'DAMAGE' in key and 'DETAILS' in key:
                    fields['ai_damage_details'] = value
                elif 'INTERIOR' in key and 'CONDITION' in key:
                    fields['ai_interior_condition'] = value
                elif 'PRESENTATION' in key and 'SCORE' in key:
                    fields['ai_presentation_score'] = value
                elif 'CONFIDENCE' in key:
                    fields['ai_confidence'] = value
        
        except Exception as e:
            print(f"    ⚠️  Error parsing AI response: {e}")
        
        return fields
    
    def save_dataset(self, df):
        """Save updated dataset"""
        try:
            # Show column info before saving
            ai_columns = [col for col in df.columns if col.startswith('ai_')]
            print(f"\n📋 Dataset has {len(ai_columns)} AI columns: {', '.join(ai_columns)}")
            
            # Check if any AI data exists
            ai_data_count = 0
            for col in ai_columns:
                non_empty = df[col].notna().sum() - (df[col] == '').sum()
                if non_empty > 0:
                    ai_data_count += non_empty
                    print(f"   {col}: {non_empty} records with data")
            
            if ai_data_count == 0:
                print("   ⚠️  No AI data found in any records!")
            
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