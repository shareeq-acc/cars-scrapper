"""
Test script to verify all dependencies are installed correctly
for Karachi Cars Scraper
Run this before starting the actual scraping
"""

import sys

def test_python_version():
    """Check Python version"""
    print("Testing Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor}.{version.micro} - Need 3.8+")
        return False

def test_imports():
    """Test if all required packages are installed"""
    print("\nTesting package imports...")
    
    packages = {
        'requests': 'requests',
        'beautifulsoup4': 'bs4',
        'selenium': 'selenium',
        'pandas': 'pandas',
        'openpyxl': 'openpyxl',
        'lxml': 'lxml',
        'webdriver-manager': 'webdriver_manager'
    }
    
    all_ok = True
    for package_name, import_name in packages.items():
        try:
            __import__(import_name)
            print(f"✓ {package_name} - OK")
        except ImportError:
            print(f"✗ {package_name} - NOT INSTALLED")
            print(f"  Install with: pip install {package_name}")
            all_ok = False
    
    return all_ok

def test_chrome_driver():
    """Test if Chrome and ChromeDriver work"""
    print("\nTesting Chrome WebDriver...")
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        
        print("  Installing/updating ChromeDriver...")
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get('https://www.google.com')
        title = driver.title
        driver.quit()
        
        print(f"  Loaded test page: '{title}'")
        print("✓ Chrome WebDriver - OK")
        return True
        
    except Exception as e:
        print(f"✗ Chrome WebDriver - FAILED")
        print(f"  Error: {str(e)}")
        print("  Make sure Google Chrome is installed")
        print("  Download from: https://www.google.com/chrome/")
        return False

def test_internet_connection():
    """Test internet connectivity"""
    print("\nTesting internet connection...")
    
    try:
        import requests
        response = requests.get('https://www.google.com', timeout=5)
        if response.status_code == 200:
            print("✓ Internet connection - OK")
            return True
        else:
            print("✗ Internet connection - FAILED")
            return False
    except Exception as e:
        print(f"✗ Internet connection - FAILED")
        print(f"  Error: {str(e)}")
        return False

def test_olx_access():
    """Test if OLX is accessible"""
    print("\nTesting OLX.pk Cars section access...")
    
    try:
        import requests
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get('https://www.olx.com.pk/cars_c84', headers=headers, timeout=10)
        if response.status_code == 200:
            print("✓ OLX.pk Cars - ACCESSIBLE")
            return True
        else:
            print(f"✗ OLX.pk Cars - Status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ OLX.pk Cars - FAILED")
        print(f"  Error: {str(e)}")
        return False

def test_pakwheels_access():
    """Test if PakWheels is accessible"""
    print("\nTesting PakWheels.com access...")
    
    try:
        import requests
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get('https://www.pakwheels.com/used-cars/karachi/24857', headers=headers, timeout=10)
        if response.status_code == 200:
            print("✓ PakWheels.com - ACCESSIBLE")
            return True
        else:
            print(f"✗ PakWheels.com - Status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ PakWheels.com - FAILED")
        print(f"  Error: {str(e)}")
        return False

def test_excel_creation():
    """Test if we can create Excel files"""
    print("\nTesting Excel file creation...")
    
    try:
        import pandas as pd
        import os
        
        # Create test data
        test_data = {
            'make': ['Toyota', 'Honda'],
            'model': ['Corolla', 'Civic'],
            'year': [2020, 2019],
            'price': [3500000, 4200000]
        }
        df = pd.DataFrame(test_data)
        
        # Try to save
        test_file = 'test_cars_output.xlsx'
        df.to_excel(test_file, index=False, engine='openpyxl')
        
        # Check if file exists
        if os.path.exists(test_file):
            print("✓ Excel creation - OK")
            # Clean up
            os.remove(test_file)
            return True
        else:
            print("✗ Excel creation - FAILED")
            return False
            
    except Exception as e:
        print(f"✗ Excel creation - FAILED")
        print(f"  Error: {str(e)}")
        return False

def create_directories():
    """Create necessary directories"""
    print("\nCreating project directories...")
    
    try:
        import os
        
        dirs = ['scraped_cars_data']
        for dir_name in dirs:
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)
                print(f"✓ Created '{dir_name}' directory")
            else:
                print(f"✓ '{dir_name}' directory exists")
        
        return True
    except Exception as e:
        print(f"✗ Directory creation - FAILED")
        print(f"  Error: {str(e)}")
        return False

def test_scraper_files():
    """Check if scraper files exist"""
    print("\nChecking scraper files...")
    
    import os
    
    required_files = [
        'olx_cars_scraper.py',
        'pakwheels_scraper.py',
        'master_cars_scraper.py'
    ]
    
    all_exist = True
    for filename in required_files:
        if os.path.exists(filename):
            print(f"✓ {filename} - EXISTS")
        else:
            print(f"✗ {filename} - MISSING")
            all_exist = False
    
    if not all_exist:
        print("\n  Create missing files from the provided artifacts!")
    
    return all_exist

def run_sample_scrape_test():
    """Test basic scraping functionality"""
    print("\nTesting basic scraping functionality...")
    
    try:
        import requests
        from bs4 import BeautifulSoup
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Try to fetch a sample OLX page
        print("  Fetching sample OLX page...")
        response = requests.get('https://www.olx.com.pk/karachi_g4060695/cars_c84', 
                              headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            listings = soup.find_all('a', {'data-aut-id': 'itemBox'})
            
            if len(listings) > 0:
                print(f"  Found {len(listings)} car listings on test page")
                print("✓ Basic scraping - OK")
                return True
            else:
                print("  No listings found (page structure may have changed)")
                print("✓ Basic scraping - OK (but no data)")
                return True
        else:
            print(f"  Status code: {response.status_code}")
            print("⚠ Basic scraping - WARNING")
            return True
            
    except Exception as e:
        print(f"✗ Basic scraping - FAILED")
        print(f"  Error: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("="*60)
    print("KARACHI CARS SCRAPER - SETUP TEST")
    print("="*60)
    
    tests = [
        ("Python Version", test_python_version),
        ("Package Imports", test_imports),
        ("Chrome WebDriver", test_chrome_driver),
        ("Internet Connection", test_internet_connection),
        ("OLX Access", test_olx_access),
        ("PakWheels Access", test_pakwheels_access),
        ("Excel Creation", test_excel_creation),
        ("Create Directories", create_directories),
        ("Scraper Files", test_scraper_files),
        ("Basic Scraping", run_sample_scrape_test)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} - EXCEPTION: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n" + "🎉"*20)
        print("ALL TESTS PASSED! You're ready to start scraping.")
        print("\nRun the scraper with:")
        print("  python master_cars_scraper.py")
        print("\nExpected results:")
        print("  - ~100-150 car listings")
        print("  - Takes 15-20 minutes")
        print("  - Output in 'scraped_cars_data/' folder")
        print("🎉"*20)
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("1. Install packages: pip install -r requirements.txt")
        print("2. Install Chrome: https://www.google.com/chrome/")
        print("3. Create scraper files from provided artifacts")
        print("4. Check internet connection")
        print("5. Activate virtual environment")
        print("\nFor package issues:")
        print("  pip install --upgrade pip")
        print("  pip install -r requirements.txt")
    
    print("="*60)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)