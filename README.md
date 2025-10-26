# Karachi Cars Scraper

A comprehensive web scraper for collecting car listings from OLX and PakWheels in Karachi, Pakistan.

## Features

- **OLX Scraper**: Extracts car listings from OLX.com.pk Karachi cars section
- **PakWheels Scraper**: Extracts car listings from PakWheels.com Karachi section
- **Master Scraper**: Combines both scrapers and merges data
- **Data Export**: Saves results to Excel files with comprehensive car information
- **Setup Verification**: Test script to verify all dependencies and connectivity

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd cars-scrapper
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # On Windows
   # source venv/bin/activate  # On Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Google Chrome**
   - Download and install from: https://www.google.com/chrome/
   - ChromeDriver will be automatically managed by webdriver-manager

## Usage

### Test Setup
Before running the scrapers, verify your setup:
```bash
python test_setup.py
```

### Individual Scrapers

**OLX Scraper:**
```bash
python olx_cars_scraper.py
```

**PakWheels Scraper:**
```bash
python pakwheels_scraper.py
```

### Master Scraper (Recommended)
Run both scrapers and combine results:
```bash
python master_cars_scraper.py
```

## Output

The scrapers generate Excel files with the following information:
- Make, Model, Year
- Price (in PKR)
- Mileage
- Location in Karachi
- Fuel Type
- Transmission
- Seller Type
- Listing Date
- Images URLs
- Original listing URLs

## Data Fields

| Field | Description |
|-------|-------------|
| make | Car manufacturer (Toyota, Honda, etc.) |
| model | Car model (Corolla, Civic, etc.) |
| year | Manufacturing year |
| price | Price in Pakistani Rupees |
| mileage | Odometer reading in kilometers |
| location | Specific area in Karachi |
| fuel_type | Petrol, Diesel, Hybrid, CNG |
| transmission | Manual or Automatic |
| seller_type | Individual, Dealer, or Featured |
| listing_date | When the ad was posted |
| status | Active or Sold |
| url | Original listing URL |

## Configuration

### Scraping Parameters
You can modify these parameters in the scraper files:
- `max_pages`: Number of pages to scrape (default: 5 for OLX, 3 for PakWheels)
- `delay`: Delay between requests in seconds (default: 2-3 seconds)

### URLs
- **OLX**: `https://www.olx.com.pk/karachi_g4060695/cars_c84`
- **PakWheels**: `https://www.pakwheels.com/used-cars/karachi/24857`

## Expected Results

- **OLX**: ~40-50 cars per page, 5 pages = ~200-250 cars
- **PakWheels**: ~20-30 cars per page, 3 pages = ~60-90 cars
- **Total**: ~260-340 car listings
- **Runtime**: 15-25 minutes for complete scraping

## Troubleshooting

### Common Issues

1. **No cars found**: 
   - Check internet connection
   - Verify URLs are accessible
   - Run `test_setup.py` to diagnose

2. **Chrome/ChromeDriver issues**:
   - Ensure Google Chrome is installed
   - ChromeDriver is auto-managed by webdriver-manager

3. **Package installation errors**:
   ```bash
   pip install --upgrade pip
   pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt
   ```

4. **Slow performance**:
   - Increase delay between requests
   - Reduce number of pages to scrape

## Dependencies

- **selenium**: Web browser automation
- **beautifulsoup4**: HTML parsing
- **pandas**: Data manipulation and Excel export
- **requests**: HTTP requests
- **webdriver-manager**: Automatic ChromeDriver management
- **openpyxl**: Excel file handling
- **lxml**: XML/HTML parsing

## Legal Notice

This scraper is for educational and research purposes only. Please:
- Respect the websites' robots.txt and terms of service
- Use reasonable delays between requests
- Don't overload the servers
- Use the data responsibly

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is for educational purposes. Please respect the terms of service of the scraped websites.