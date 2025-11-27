"""
Split dataset into multiple files with and without errors
This script prepares data for the ingestion pipeline
"""

import pandas as pd
import numpy as np
import os
import argparse
from pathlib import Path
from datetime import datetime
import json

def split_dataset(dataset_path, output_dir, num_files, error_rate=0.3):
    """
    Split dataset into multiple files with some containing errors
    
    Args:
        dataset_path: Path to original CSV file
        output_dir: Directory to save split files
        num_files: Number of files to create
        error_rate: Percentage of files that should have errors
    """
    # Load dataset
    df = pd.read_csv(dataset_path)
    print(f"Loaded dataset: {df.shape[0]} rows, {df.shape[1]} columns")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Calculate rows per file
    rows_per_file = len(df) // num_files
    print(f"Splitting into {num_files} files (~{rows_per_file} rows each)")
    
    # Generate file info
    file_info = []
    num_error_files = int(num_files * error_rate)
    error_indices = np.random.choice(num_files, num_error_files, replace=False)
    
    # Split and save files
    for i in range(num_files):
        start_idx = i * rows_per_file
        end_idx = start_idx + rows_per_file if i < num_files - 1 else len(df)
        
        file_df = df.iloc[start_idx:end_idx].copy()
        has_errors = i in error_indices
        
        # Add errors if needed
        if has_errors:
            error_type = np.random.choice(['missing_values', 'unknown_category', 'string_in_numeric'])
            
            if error_type == 'missing_values':
                # Add missing values
                col = np.random.choice(file_df.columns)
                mask = np.random.random(len(file_df)) < 0.2
                file_df.loc[mask, col] = np.nan
            
            elif error_type == 'unknown_category':
                # Add unknown categorical value
                cat_cols = file_df.select_dtypes(include=['object']).columns
                if len(cat_cols) > 0:
                    col = np.random.choice(cat_cols)
                    mask = np.random.random(len(file_df)) < 0.15
                    file_df.loc[mask, col] = "UNKNOWN_CATEGORY_ERROR"
            
            elif error_type == 'string_in_numeric':
                # Add string to numeric column
                num_cols = file_df.select_dtypes(include=[np.number]).columns
                if len(num_cols) > 0:
                    col = np.random.choice(num_cols)
                    mask = np.random.random(len(file_df)) < 0.1
                    file_df.loc[mask, col] = "INVALID_STRING"
        
        # Save file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data_batch_{i:03d}_{timestamp}.csv"
        filepath = os.path.join(output_dir, filename)
        file_df.to_csv(filepath, index=False)
        
        file_info.append({
            'filename': filename,
            'filepath': filepath,
            'rows': len(file_df),
            'columns': len(file_df.columns),
            'has_errors': has_errors,
            'created_at': timestamp
        })
        
        print(f"  ✓ {filename} ({len(file_df)} rows, errors={has_errors})")
    
    # Save file info
    info_file = os.path.join(output_dir, 'file_manifest.json')
    with open(info_file, 'w') as f:
        json.dump(file_info, f, indent=2)
    
    print(f"\n✅ Successfully split dataset into {num_files} files")
    print(f"   Output directory: {output_dir}")
    print(f"   Files with errors: {num_error_files}")
    print(f"   File manifest: {info_file}")
    
    return file_info


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Split dataset into multiple files')
    parser.add_argument('--dataset', required=True, help='Path to original dataset')
    parser.add_argument('--output', default='data/raw-data', help='Output directory')
    parser.add_argument('--files', type=int, default=20, help='Number of files to create')
    parser.add_argument('--error-rate', type=float, default=0.3, help='Percentage of files with errors')
    
    args = parser.parse_args()
    
    split_dataset(
        dataset_path=args.dataset,
        output_dir=args.output,
        num_files=args.files,
        error_rate=args.error_rate
    )