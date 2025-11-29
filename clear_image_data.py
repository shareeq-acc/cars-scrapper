import pandas as pd
import os

def load_dataset(filename='pakwheels_main_dataset.xlsx'):
    """Load the main dataset"""
    if not os.path.exists(filename):
        print(f"❌ Error: {filename} not found!")
        return None
    
    try:
        df = pd.read_excel(filename, engine='openpyxl')
        print(f"✓ Loaded dataset: {len(df)} records")
        return df
    except Exception as e:
        print(f"❌ Error loading dataset: {e}")
        return None

def save_dataset(df, filename='pakwheels_main_dataset.xlsx'):
    """Save updated dataset"""
    try:
        df.to_excel(filename, index=False, engine='openpyxl')
        print(f"\n✓ Dataset saved to {filename}")
    except Exception as e:
        print(f"\n❌ Error saving dataset: {e}")

def find_records_with_data(df):
    """Find records that have all_images or exterior_color set"""
    records_with_data = []
    
    # Check if columns exist
    has_images_col = 'all_images' in df.columns
    has_color_col = 'exterior_color' in df.columns
    
    if not has_images_col and not has_color_col:
        print("⚠️  Neither 'all_images' nor 'exterior_color' columns exist in dataset")
        return []
    
    for i in range(len(df)):
        has_data = False
        
        if has_images_col:
            val = df.at[i, 'all_images']
            if pd.notna(val) and val != '':
                has_data = True
        
        if has_color_col:
            val = df.at[i, 'exterior_color']
            if pd.notna(val) and val != '':
                has_data = True
        
        if has_data:
            records_with_data.append(i)
    
    return records_with_data

def clear_data_in_range(df, start_idx, end_idx):
    """Clear all_images and exterior_color data in specified range"""
    columns_to_clear = []
    
    if 'all_images' in df.columns:
        columns_to_clear.append('all_images')
    if 'exterior_color' in df.columns:
        columns_to_clear.append('exterior_color')
    if 'body_condition' in df.columns:
        columns_to_clear.append('body_condition')
    if 'mechanical_condition' in df.columns:
        columns_to_clear.append('mechanical_condition')
    if 'registered_in' in df.columns:
        columns_to_clear.append('registered_in')
    
    cleared_count = 0
    
    for i in range(start_idx, end_idx + 1):
        if i >= len(df):
            break
        
        for col in columns_to_clear:
            if pd.notna(df.at[i, col]) and df.at[i, col] != '':
                df.at[i, col] = ''
                cleared_count += 1
    
    return df, cleared_count, columns_to_clear


if __name__ == "__main__":
    print("=" * 50)
    print("Clear Image Data Tool")
    print("=" * 50)
    
    # Load dataset
    print("\nLoading dataset...")
    df = load_dataset()
    
    if df is None:
        exit(1)
    
    # Find records with data
    print("\nScanning for records with image/color data...")
    records_with_data = find_records_with_data(df)
    
    if not records_with_data:
        print("\n✓ No records found with image or color data!")
        exit(0)
    
    # Display ranges
    print(f"\n📊 Found {len(records_with_data)} record(s) with data")
    print(f"\n📍 Records with data:")
    
    # Group consecutive records into ranges
    ranges = []
    if records_with_data:
        start = records_with_data[0]
        end = records_with_data[0]
        
        for i in range(1, len(records_with_data)):
            if records_with_data[i] == end + 1:
                end = records_with_data[i]
            else:
                ranges.append((start, end))
                start = records_with_data[i]
                end = records_with_data[i]
        
        ranges.append((start, end))
    
    # Display ranges
    for start, end in ranges:
        if start == end:
            print(f"  - Record #{start + 1}")
        else:
            print(f"  - Records #{start + 1} to #{end + 1}")
    
    print(f"\n  First record with data: #{records_with_data[0] + 1}")
    print(f"  Last record with data: #{records_with_data[-1] + 1}")
    
    # Ask user for range to clear
    print("\n" + "=" * 50)
    print("Enter the range of records to clear:")
    print("(Record numbers are 1-based, e.g., 1 for first record)")
    
    while True:
        try:
            start_num = int(input(f"\nStarting record number (1-{len(df)}): "))
            if start_num < 1 or start_num > len(df):
                print(f"Please enter a number between 1 and {len(df)}")
                continue
            break
        except ValueError:
            print("Invalid input. Please enter a valid number.")
    
    while True:
        try:
            end_num = int(input(f"Ending record number ({start_num}-{len(df)}): "))
            if end_num < start_num or end_num > len(df):
                print(f"Please enter a number between {start_num} and {len(df)}")
                continue
            break
        except ValueError:
            print("Invalid input. Please enter a valid number.")
    
    # Convert to 0-based index
    start_idx = start_num - 1
    end_idx = end_num - 1
    
    # Confirm
    print(f"\n⚠️  WARNING: This will clear image and color data for records #{start_num} to #{end_num}")
    print(f"   Total records to clear: {end_idx - start_idx + 1}")
    
    confirm = input("\nAre you sure? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("\n❌ Operation cancelled.")
        exit(0)
    
    # Clear data
    print("\nClearing data...")
    df, cleared_count, columns_cleared = clear_data_in_range(df, start_idx, end_idx)
    
    print(f"\n✓ Cleared data from columns: {', '.join(columns_cleared)}")
    print(f"✓ Total fields cleared: {cleared_count}")
    
    # Save dataset
    print("\nSaving dataset...")
    save_dataset(df)
    
    print("\n" + "=" * 50)
    print("✓ Complete!")
    print("=" * 50)
