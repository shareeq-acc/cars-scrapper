import pandas as pd
import os

def remove_empty_columns(filename='pakwheels_main_dataset.xlsx'):
    """Remove columns that have no data (all empty or NaN)"""
    
    if not os.path.exists(filename):
        print(f"❌ Error: {filename} not found!")
        return
    
    try:
        # Load dataset
        print(f"Loading {filename}...")
        df = pd.read_excel(filename, engine='openpyxl')
        print(f"✓ Loaded dataset: {len(df)} records, {len(df.columns)} columns")
        
        # Get initial column count
        initial_columns = len(df.columns)
        initial_column_names = list(df.columns)
        
        # Find empty columns
        empty_columns = []
        for col in df.columns:
            # Check if column is completely empty (all NaN or all empty strings)
            if df[col].isna().all() or (df[col] == '').all():
                empty_columns.append(col)
        
        if not empty_columns:
            print("\n✓ No empty columns found! All columns have data.")
            return
        
        print(f"\n📋 Found {len(empty_columns)} empty column(s):")
        for col in empty_columns:
            print(f"  - {col}")
        
        # Ask for confirmation
        print("\n" + "=" * 50)
        confirm = input(f"\nRemove these {len(empty_columns)} empty column(s)? (yes/no): ").strip().lower()
        
        if confirm != 'yes':
            print("\n❌ Operation cancelled.")
            return
        
        # Remove empty columns
        print("\nRemoving empty columns...")
        df_cleaned = df.drop(columns=empty_columns)
        
        # Save cleaned dataset
        df_cleaned.to_excel(filename, index=False, engine='openpyxl')
        
        print(f"\n✓ Dataset cleaned and saved!")
        print(f"  - Original columns: {initial_columns}")
        print(f"  - Removed columns: {len(empty_columns)}")
        print(f"  - Remaining columns: {len(df_cleaned.columns)}")
        
        print("\n📊 Remaining columns:")
        for col in df_cleaned.columns:
            non_empty = df_cleaned[col].notna().sum() - (df_cleaned[col] == '').sum()
            print(f"  - {col}: {non_empty} records with data")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    print("=" * 50)
    print("Remove Empty Columns Tool")
    print("=" * 50)
    
    remove_empty_columns()
