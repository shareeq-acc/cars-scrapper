"""
Master script to run all car scrapers and combine data
"""
import pandas as pd
from datetime import datetime
import os

class MasterCarsScraper:
    def __init__(self):
        self.all_cars = []
        self.output_dir = 'scraped_cars_data'
        
        # Create output directory if it doesn't exist
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def run_olx_scraper(self, max_pages=5):
        """Run OLX cars scraper"""
        print("\n" + "="*60)
        print("STARTING OLX CARS SCRAPER")
        print("="*60)
        
        try:
            from olx_cars_scraper import OLXCarsScraper
            scraper = OLXCarsScraper()
            cars = scraper.scrape(max_pages=max_pages, delay=2)
            
            # Add source column
            for car in cars:
                car['source'] = 'OLX'
            
            self.all_cars.extend(cars)
            
            # Save individual file
            scraper.save_to_excel(f'{self.output_dir}/olx_karachi_cars.xlsx')
            print(f"✓ OLX scraper completed: {len(cars)} cars")
            
        except Exception as e:
            print(f"✗ Error running OLX scraper: {str(e)}")
    
    def run_pakwheels_scraper(self, max_pages=3):
        """Run PakWheels scraper"""
        print("\n" + "="*60)
        print("STARTING PAKWHEELS SCRAPER")
        print("="*60)
        
        try:
            from pakwheels_scraper import PakWheelsScraper
            scraper = PakWheelsScraper()
            cars = scraper.scrape(max_pages=max_pages, delay=3)
            
            # Add source column
            for car in cars:
                car['source'] = 'PakWheels'
            
            self.all_cars.extend(cars)
            
            # Save individual file
            scraper.save_to_excel(f'{self.output_dir}/pakwheels_karachi_cars.xlsx')
            print(f"✓ PakWheels scraper completed: {len(cars)} cars")
            
        except Exception as e:
            print(f"✗ Error running PakWheels scraper: {str(e)}")
    
    def clean_data(self, df):
        """Basic data cleaning"""
        print("\nCleaning data...")
        
        # Remove duplicates based on title, make, model, year, and price
        initial_count = len(df)
        df = df.drop_duplicates(subset=['make', 'model', 'year', 'price'], keep='first')
        removed = initial_count - len(df)
        print(f"  Removed {removed} duplicate listings")
        
        # Remove rows with missing critical data
        df = df.dropna(subset=['price', 'make', 'model', 'year'])
        print(f"  Removed listings with missing critical data")
        
        # Remove outliers
        # Remove cars with price = 0 or unreasonably high/low
        df = df[(df['price'] > 100000) & (df['price'] < 100000000)]
        
        # Remove cars with unrealistic years
        current_year = datetime.now().year
        df = df[(df['year'] >= 1980) & (df['year'] <= current_year + 1)]
        
        # Remove cars with unrealistic mileage
        if 'mileage' in df.columns:
            df = df[(df['mileage'].isna()) | ((df['mileage'] >= 0) & (df['mileage'] <= 1000000))]
        
        print(f"  Final count: {len(df)} cars")
        
        return df
    
    def add_derived_features(self, df):
        """Add useful derived features for ML"""
        print("\nAdding derived features...")
        
        # Car age
        current_year = datetime.now().year
        df['car_age'] = current_year - df['year']
        
        # Price category
        def price_category(price):
            if price < 1000000:
                return 'Budget'
            elif price < 3000000:
                return 'Mid-Range'
            elif price < 7000000:
                return 'Premium'
            else:
                return 'Luxury'
        
        df['price_category'] = df['price'].apply(price_category)
        
        # Mileage category
        if 'mileage' in df.columns:
            def mileage_category(km):
                if pd.isna(km):
                    return 'Unknown'
                elif km < 50000:
                    return 'Low'
                elif km < 100000:
                    return 'Medium'
                elif km < 200000:
                    return 'High'
                else:
                    return 'Very High'
            
            df['mileage_category'] = df['mileage'].apply(mileage_category)
        
        # Days since listing (if listing_date available)
        if 'listing_date' in df.columns:
            try:
                df['listing_date'] = pd.to_datetime(df['listing_date'], errors='coerce')
                df['days_since_listing'] = (datetime.now() - df['listing_date']).dt.days
            except:
                pass
        
        print("  Added: car_age, price_category, mileage_category, days_since_listing")
        
        return df
    
    def combine_and_save(self):
        """Combine all data and save to master Excel file"""
        if not self.all_cars:
            print("\n✗ No data to combine!")
            return
        
        print("\n" + "="*60)
        print("COMBINING DATA FROM ALL SOURCES")
        print("="*60)
        
        # Convert to DataFrame
        df = pd.DataFrame(self.all_cars)
        
        # Clean data
        df = self.clean_data(df)
        
        # Add derived features
        df = self.add_derived_features(df)
        
        # Standardize columns across sources
        standard_columns = [
            'source', 'make', 'model', 'year', 'price', 'mileage', 
            'car_age', 'price_category', 'mileage_category',
            'condition', 'transmission', 'fuel_type', 'engine_capacity',
            'color', 'assembly', 'registered_city', 'location', 'city',
            'seller_type', 'listing_date', 'days_since_listing', 'status',
            'title', 'description', 'images', 'url', 'scraped_date'
        ]
        
        # Add missing columns with None
        for col in standard_columns:
            if col not in df.columns:
                df[col] = None
        
        # Reorder columns
        df = df[[col for col in standard_columns if col in df.columns]]
        
        # Sort by price
        df = df.sort_values('price', ascending=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'{self.output_dir}/karachi_cars_master_{timestamp}.xlsx'
        
        # Save to Excel with multiple sheets
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Main data
            df.to_excel(writer, sheet_name='All Cars', index=False)
            
            # Summary by make
            if 'make' in df.columns:
                make_summary = df.groupby('make').agg({
                    'price': ['mean', 'min', 'max', 'count'],
                    'year': 'mean',
                    'mileage': 'mean'
                }).round(0)
                make_summary.to_excel(writer, sheet_name='Summary by Make')
            
            # Active vs Sold
            if 'status' in df.columns:
                status_summary = df.groupby('status').agg({
                    'price': ['mean', 'count'],
                    'year': 'mean'
                }).round(0)
                status_summary.to_excel(writer, sheet_name='Status Summary')
        
        print(f"\n✓ Master file saved: {filename}")
        print(f"Total cars: {len(df)}")
        
        # Print detailed summary
        self.print_summary(df)
        
        return df
    
    def print_summary(self, df):
        """Print comprehensive summary statistics"""
        print("\n" + "="*60)
        print("SUMMARY STATISTICS")
        print("="*60)
        
        print("\n--- Data Sources ---")
        if 'source' in df.columns:
            print(df['source'].value_counts())
        
        print("\n--- Price Statistics ---")
        print(f"Average Price: PKR {df['price'].mean():,.0f}")
        print(f"Median Price: PKR {df['price'].median():,.0f}")
        print(f"Min Price: PKR {df['price'].min():,.0f}")
        print(f"Max Price: PKR {df['price'].max():,.0f}")
        
        print("\n--- Year Distribution ---")
        print(f"Oldest: {df['year'].min()}")
        print(f"Newest: {df['year'].max()}")
        print(f"Average Year: {df['year'].mean():.0f}")
        
        print("\n--- Top 10 Most Common Makes ---")
        if 'make' in df.columns:
            print(df['make'].value_counts().head(10))
        
        print("\n--- Top 10 Most Common Models ---")
        if 'model' in df.columns:
            print(df['model'].value_counts().head(10))
        
        print("\n--- Status Distribution ---")
        if 'status' in df.columns:
            print(df['status'].value_counts())
            print(f"\nSold Rate: {(df['status'] == 'Sold').sum() / len(df) * 100:.1f}%")
        
        print("\n--- Transmission Type ---")
        if 'transmission' in df.columns:
            print(df['transmission'].value_counts())
        
        print("\n--- Fuel Type ---")
        if 'fuel_type' in df.columns:
            print(df['fuel_type'].value_counts())
        
        print("\n--- Assembly ---")
        if 'assembly' in df.columns:
            print(df['assembly'].value_counts())
        
        print("\n--- Average Price by Make (Top 10) ---")
        if 'make' in df.columns:
            price_by_make = df.groupby('make')['price'].mean().sort_values(ascending=False).head(10)
            for make, price in price_by_make.items():
                print(f"{make}: PKR {price:,.0f}")
        
        print("\n--- Average Price by Year ---")
        recent_years = df[df['year'] >= 2015].groupby('year')['price'].mean().sort_index()
        for year, price in recent_years.items():
            print(f"{int(year)}: PKR {price:,.0f}")
    
    def run_all(self, olx_pages=5, pakwheels_pages=3):
        """Run all scrapers"""
        start_time = datetime.now()
        
        print("\n" + "="*60)
        print("KARACHI CARS DATA SCRAPER")
        print("="*60)
        print(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run scrapers
        self.run_olx_scraper(max_pages=olx_pages)
        self.run_pakwheels_scraper(max_pages=pakwheels_pages)
        
        # Combine and save
        df = self.combine_and_save()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds() / 60
        
        print("\n" + "="*60)
        print(f"SCRAPING COMPLETED!")
        print(f"Duration: {duration:.2f} minutes")
        print(f"End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        return df


# Main execution
if __name__ == "__main__":
    # Configuration
    OLX_PAGES = 5          # Number of pages to scrape from OLX
    PAKWHEELS_PAGES = 3    # Number of pages to scrape from PakWheels
    
    # Create and run master scraper
    master = MasterCarsScraper()
    df = master.run_all(olx_pages=OLX_PAGES, pakwheels_pages=PAKWHEELS_PAGES)
    
    print("\n✓ All done! Check the 'scraped_cars_data' folder for output files.")
    print("\nNext steps for ML:")
    print("1. Explore the data in Excel")
    print("2. Use pandas for deeper analysis")
    print("3. Build price prediction models")
    print("4. Analyze factors affecting resale value")