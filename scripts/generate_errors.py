"""
Custom Data Error Generator for Road Accident Dataset
Generates 9+ realistic error types for your specific dataset
"""

import pandas as pd
import numpy as np
import os
import argparse
from datetime import datetime
import json

class RoadAccidentErrorGenerator:
    """Generate realistic data quality issues for road accident data"""
    
    def __init__(self, df, output_dir='data/raw-data'):
        self.df = df.copy()
        self.output_dir = output_dir
        self.error_log = []
        os.makedirs(output_dir, exist_ok=True)
        
        # Define expected values for validation
        self.road_types = ['highway', 'local_road', 'motorway', 'roundabout', 'urban']
        self.road_signs = ['yes', 'no']
        self.public_road = ['yes', 'no']
        self.time_of_day = ['day', 'night', 'dawn', 'dusk']
        self.holiday = ['yes', 'no']
        self.school_season = ['yes', 'no']
        self.weather = ['clear', 'rain', 'fog', 'snow', 'storm']
        self.lighting = ['daylight', 'street_lit', 'dark']
    
    def error_1_missing_required_column(self, df, required_col):
        """Error 1: Drop a required column entirely"""
        df_error = df.drop(columns=[required_col], errors='ignore')
        self.error_log.append({
            'error_type': 'Missing Required Column',
            'column': required_col,
            'description': f'Column {required_col} is completely missing',
            'severity': 'HIGH',
            'affected_rows': len(df)
        })
        return df_error
    
    def error_2_missing_values(self, df, column, percentage=0.2):
        """Error 2: Introduce missing values (NaN) in a column"""
        df_error = df.copy()
        mask = np.random.random(len(df_error)) < percentage
        df_error.loc[mask, column] = np.nan
        affected_rows = mask.sum()
        self.error_log.append({
            'error_type': 'Missing Values',
            'column': column,
            'affected_rows': int(affected_rows),
            'percentage': percentage * 100,
            'description': f'{affected_rows} missing values in {column}',
            'severity': 'MEDIUM'
        })
        return df_error
    
    def error_3_invalid_road_type(self, df, percentage=0.15):
        """Error 3: Invalid road type values"""
        df_error = df.copy()
        mask = np.random.random(len(df_error)) < percentage
        df_error.loc[mask, 'road_type'] = 'INVALID_ROAD_TYPE'
        affected_rows = mask.sum()
        self.error_log.append({
            'error_type': 'Invalid Categorical Value',
            'column': 'road_type',
            'valid_values': self.road_types,
            'invalid_value': 'INVALID_ROAD_TYPE',
            'affected_rows': int(affected_rows),
            'description': f'{affected_rows} rows have invalid road_type value',
            'severity': 'HIGH'
        })
        return df_error
    
    def error_4_invalid_lanes(self, df, percentage=0.1):
        """Error 4: Negative or zero number of lanes (should be >= 1)"""
        df_error = df.copy()
        mask = np.random.random(len(df_error)) < percentage
        df_error.loc[mask, 'num_lanes'] = np.random.choice([-1, 0, 999], mask.sum())
        affected_rows = mask.sum()
        self.error_log.append({
            'error_type': 'Out of Range Value',
            'column': 'num_lanes',
            'valid_range': '[1, 10]',
            'invalid_values': '[-1, 0, 999]',
            'affected_rows': int(affected_rows),
            'description': f'{affected_rows} rows have invalid num_lanes (negative/zero)',
            'severity': 'MEDIUM'
        })
        return df_error
    
    def error_5_invalid_curvature(self, df, percentage=0.12):
        """Error 5: Curvature outside valid range (should be 0-180 degrees)"""
        df_error = df.copy()
        mask = np.random.random(len(df_error)) < percentage
        df_error.loc[mask, 'curvature'] = np.random.choice([-45, 200, 999], mask.sum())
        affected_rows = mask.sum()
        self.error_log.append({
            'error_type': 'Out of Range Value',
            'column': 'curvature',
            'valid_range': '[0, 180] degrees',
            'invalid_values': '[-45, 200, 999]',
            'affected_rows': int(affected_rows),
            'description': f'{affected_rows} rows have curvature outside valid range',
            'severity': 'MEDIUM'
        })
        return df_error
    
    def error_6_invalid_speed_limit(self, df, percentage=0.08):
        """Error 6: Speed limit with invalid values (negative or unrealistic)"""
        df_error = df.copy()
        mask = np.random.random(len(df_error)) < percentage
        df_error.loc[mask, 'speed_limit'] = np.random.choice([-50, 0, 500], mask.sum())
        affected_rows = mask.sum()
        self.error_log.append({
            'error_type': 'Invalid Speed Limit',
            'column': 'speed_limit',
            'valid_range': '[20, 130] km/h',
            'affected_rows': int(affected_rows),
            'description': f'{affected_rows} rows have invalid speed_limit',
            'severity': 'HIGH'
        })
        return df_error
    
    def error_7_invalid_lighting(self, df, percentage=0.1):
        """Error 7: Invalid lighting conditions"""
        df_error = df.copy()
        mask = np.random.random(len(df_error)) < percentage
        df_error.loc[mask, 'lighting'] = 'BRIGHT_NEON'
        affected_rows = mask.sum()
        self.error_log.append({
            'error_type': 'Invalid Categorical Value',
            'column': 'lighting',
            'valid_values': self.lighting,
            'invalid_value': 'BRIGHT_NEON',
            'affected_rows': int(affected_rows),
            'description': f'{affected_rows} rows have invalid lighting condition',
            'severity': 'MEDIUM'
        })
        return df_error
    
    def error_8_invalid_weather(self, df, percentage=0.09):
        """Error 8: Invalid weather values"""
        df_error = df.copy()
        mask = np.random.random(len(df_error)) < percentage
        df_error.loc[mask, 'weather'] = 'TORNADO'
        affected_rows = mask.sum()
        self.error_log.append({
            'error_type': 'Invalid Categorical Value',
            'column': 'weather',
            'valid_values': self.weather,
            'invalid_value': 'TORNADO',
            'affected_rows': int(affected_rows),
            'description': f'{affected_rows} rows have invalid weather value',
            'severity': 'MEDIUM'
        })
        return df_error
    
    def error_9_invalid_yes_no_fields(self, df, percentage=0.07):
        """Error 9: Invalid values in yes/no fields"""
        df_error = df.copy()
        yes_no_columns = ['road_signs_present', 'public_road', 'holiday', 'school_season']
        
        # Find valid columns
        valid_cols = [col for col in yes_no_columns if col in df_error.columns]
        
        for col in valid_cols:
            mask = np.random.random(len(df_error)) < percentage
            df_error.loc[mask, col] = 'MAYBE'
        
        affected_rows = mask.sum()
        self.error_log.append({
            'error_type': 'Invalid Boolean/Yes-No Value',
            'columns': valid_cols,
            'valid_values': ['yes', 'no'],
            'invalid_value': 'MAYBE',
            'affected_rows': int(affected_rows),
            'description': f'{affected_rows} rows have invalid yes/no values',
            'severity': 'HIGH'
        })
        return df_error
    
    def error_10_string_in_numeric(self, df, percentage=0.06):
        """Error 10: String values in numeric columns"""
        df_error = df.copy()
        numeric_cols = ['num_lanes', 'curvature', 'speed_limit', 'num_reported_accidents']
        
        for col in numeric_cols:
            if col in df_error.columns:
                mask = np.random.random(len(df_error)) < percentage
                df_error.loc[mask, col] = 'N/A'
        
        affected_rows = mask.sum()
        self.error_log.append({
            'error_type': 'String in Numeric Column',
            'columns': numeric_cols,
            'invalid_string': 'N/A',
            'affected_rows': int(affected_rows),
            'description': f'{affected_rows} rows have string values in numeric columns',
            'severity': 'HIGH'
        })
        return df_error
    
    def error_11_duplicate_rows(self, df, percentage=0.05):
        """Error 11: Duplicate rows (exact copies)"""
        df_error = df.copy()
        n_duplicates = int(len(df_error) * percentage)
        if n_duplicates > 0:
            random_indices = np.random.choice(len(df_error), n_duplicates, replace=True)
            df_error = pd.concat([df_error, df_error.iloc[random_indices]], ignore_index=True)
        
        self.error_log.append({
            'error_type': 'Duplicate Rows',
            'duplicate_count': n_duplicates,
            'description': f'{n_duplicates} exact duplicate rows added',
            'severity': 'LOW'
        })
        return df_error
    
    def error_12_invalid_time_of_day(self, df, percentage=0.08):
        """Error 12: Invalid time of day values"""
        df_error = df.copy()
        mask = np.random.random(len(df_error)) < percentage
        df_error.loc[mask, 'time_of_day'] = 'MIDNIGHT'
        affected_rows = mask.sum()
        self.error_log.append({
            'error_type': 'Invalid Time of Day',
            'column': 'time_of_day',
            'valid_values': self.time_of_day,
            'invalid_value': 'MIDNIGHT',
            'affected_rows': int(affected_rows),
            'description': f'{affected_rows} rows have invalid time_of_day',
            'severity': 'MEDIUM'
        })
        return df_error
    
    def error_13_negative_accidents(self, df, percentage=0.05):
        """Error 13: Negative number of reported accidents"""
        df_error = df.copy()
        mask = np.random.random(len(df_error)) < percentage
        df_error.loc[mask, 'num_reported_accidents'] = -np.random.randint(1, 10, mask.sum())
        affected_rows = mask.sum()
        self.error_log.append({
            'error_type': 'Negative Value Error',
            'column': 'num_reported_accidents',
            'valid_range': '[0, ∞)',
            'affected_rows': int(affected_rows),
            'description': f'{affected_rows} rows have negative accident counts',
            'severity': 'HIGH'
        })
        return df_error
    
    def error_14_accident_risk_out_of_range(self, df, percentage=0.07):
        """Error 14: Accident risk outside 0-1 range (should be probability)"""
        df_error = df.copy()
        mask = np.random.random(len(df_error)) < percentage
        df_error.loc[mask, 'accident_risk'] = np.random.choice([-0.5, 1.5, 2.0], mask.sum())
        affected_rows = mask.sum()
        self.error_log.append({
            'error_type': 'Out of Range Probability',
            'column': 'accident_risk',
            'valid_range': '[0, 1]',
            'affected_rows': int(affected_rows),
            'description': f'{affected_rows} rows have accident_risk outside [0,1]',
            'severity': 'HIGH'
        })
        return df_error
    
    def error_15_whitespace_padding(self, df, percentage=0.08):
        """Error 15: Inconsistent whitespace in categorical values"""
        df_error = df.copy()
        categorical_cols = ['road_type', 'lighting', 'weather', 'time_of_day']
        
        for col in categorical_cols:
            if col in df_error.columns:
                mask = np.random.random(len(df_error)) < percentage
                df_error.loc[mask, col] = '  ' + df_error.loc[mask, col].astype(str) + '  '
        
        affected_rows = mask.sum()
        self.error_log.append({
            'error_type': 'Whitespace Padding',
            'columns': categorical_cols,
            'affected_rows': int(affected_rows),
            'description': f'{affected_rows} rows have extra whitespace in categorical values',
            'severity': 'LOW'
        })
        return df_error
    
    def generate_clean_file(self):
        """Generate a file with no errors"""
        return self.df.copy()
    
    def generate_file_with_errors(self, errors_config):
        """Generate file with specified errors"""
        df = self.df.copy()
        
        for error_method, params in errors_config:
            if hasattr(self, error_method):
                df = getattr(self, error_method)(df, **params)
        
        return df
    
    def print_error_log(self):
        """Print summary of all generated errors"""
        print("\n" + "="*80)
        print("DATA ERROR SUMMARY FOR ROAD ACCIDENT DATASET")
        print("="*80)
        print(f"\nTotal error types: {len(self.error_log)}")
        
        for i, error in enumerate(self.error_log, 1):
            print(f"\n{i}. {error['error_type']} [Severity: {error['severity']}]")
            print(f"   Description: {error['description']}")
            for key, value in error.items():
                if key not in ['error_type', 'description', 'severity']:
                    print(f"   {key}: {value}")


def generate_test_dataset_with_errors():
    """Generate test dataset and create files with various error types"""
    
    # Create sample dataset
    print("Creating sample road accident dataset...")
    n_rows = 500
    
    data = {
        'id': range(1, n_rows + 1),
        'road_type': np.random.choice(['highway', 'local_road', 'motorway', 'roundabout', 'urban'], n_rows),
        'num_lanes': np.random.randint(1, 6, n_rows),
        'curvature': np.random.uniform(0, 180, n_rows),
        'speed_limit': np.random.choice([30, 50, 70, 90, 110, 130], n_rows),
        'lighting': np.random.choice(['daylight', 'street_lit', 'dark'], n_rows),
        'weather': np.random.choice(['clear', 'rain', 'fog', 'snow', 'storm'], n_rows),
        'road_signs_present': np.random.choice(['yes', 'no'], n_rows),
        'public_road': np.random.choice(['yes', 'no'], n_rows),
        'time_of_day': np.random.choice(['day', 'night', 'dawn', 'dusk'], n_rows),
        'holiday': np.random.choice(['yes', 'no'], n_rows),
        'school_season': np.random.choice(['yes', 'no'], n_rows),
        'num_reported_accidents': np.random.randint(0, 20, n_rows),
        'accident_risk': np.random.uniform(0, 1, n_rows)
    }
    
    df = pd.DataFrame(data)
    print(f"✅ Created dataset with {n_rows} rows and {len(df.columns)} columns")
    print(f"Columns: {list(df.columns)}")
    
    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Generate road accident dataset with various error types'
    )
    parser.add_argument('--dataset', help='Path to existing dataset (optional)')
    parser.add_argument('--output', default='data/raw-data', help='Output directory')
    parser.add_argument('--files', type=int, default=30, help='Number of files to create')
    parser.add_argument('--rows', type=int, default=500, help='Rows per file')
    
    args = parser.parse_args()
    
    # Load or create dataset
    if args.dataset:
        print(f"Loading dataset from {args.dataset}...")
        df = pd.read_csv(args.dataset)
    else:
        print("No dataset provided, generating sample dataset...")
        df = generate_test_dataset_with_errors()
    
    print(f"\nDataset shape: {df.shape}")
    print(f"Columns: {list(df.columns)}\n")
    
    # Initialize error generator
    generator = RoadAccidentErrorGenerator(df, args.output)
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    # Generate files with different error patterns
    print("Generating files with error patterns...")
    
    errors_to_generate = [
        ('error_3_invalid_road_type', {'percentage': 0.1}),
        ('error_4_invalid_lanes', {'percentage': 0.08}),
        ('error_5_invalid_curvature', {'percentage': 0.07}),
        ('error_6_invalid_speed_limit', {'percentage': 0.1}),
        ('error_7_invalid_lighting', {'percentage': 0.08}),
        ('error_8_invalid_weather', {'percentage': 0.09}),
        ('error_9_invalid_yes_no_fields', {'percentage': 0.1}),
        ('error_10_string_in_numeric', {'percentage': 0.06}),
        ('error_12_invalid_time_of_day', {'percentage': 0.08}),
        ('error_13_negative_accidents', {'percentage': 0.05}),
        ('error_14_accident_risk_out_of_range', {'percentage': 0.07}),
        ('error_15_whitespace_padding', {'percentage': 0.08}),
    ]
    
    # Generate files with errors
    for i in range(args.files):
        start_idx = i * args.rows
        end_idx = min(start_idx + args.rows, len(df))
        
        file_df = df.iloc[start_idx:end_idx].copy()
        
        # Randomly select 1-3 error types for this file
        selected_errors = np.random.choice(
            len(errors_to_generate),
            size=np.random.randint(1, 3),
            replace=False
        )
        
        for error_idx in selected_errors:
            error_method, params = errors_to_generate[error_idx]
            file_df = getattr(generator, error_method)(file_df, **params)
        
        # Save file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"road_accident_batch_{i:03d}_{timestamp}.csv"
        filepath = os.path.join(args.output, filename)
        file_df.to_csv(filepath, index=False)
        
        num_errors = len(selected_errors)
        print(f"  ✓ {filename} ({len(file_df)} rows, {num_errors} error types)")
    
    # Print error summary
    generator.print_error_log()
    
    # Save manifest
    manifest = {
        'dataset_name': 'Road Accident Dataset',
        'total_columns': len(df.columns),
        'columns': list(df.columns),
        'error_types_generated': len(errors_to_generate),
        'files_created': args.files,
        'rows_per_file': args.rows,
        'created_at': datetime.now().isoformat(),
        'errors': generator.error_log
    }
    
    manifest_file = os.path.join(args.output, 'manifest.json')
    with open(manifest_file, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"\n✅ Manifest saved: {manifest_file}")
    print(f"\n✅ Successfully created {args.files} files with errors in: {args.output}")