
import pandas as pd
import numpy as np
import os
import random


def split_dataset_with_errors(dataset_path, raw_data_path, n_files):
    df = pd.read_csv(dataset_path)
    os.makedirs(raw_data_path, exist_ok=True)
    
    for i in range(n_files):
        temp_df = df.copy()
        
        # Randomly introduce errors
        temp_df.loc[random.sample(range(len(temp_df)), 5), 'Age'] = -12  # wrong value
        temp_df.loc[random.sample(range(len(temp_df)), 5), 'Country'] = 'France'  # unknown
        temp_df.loc[random.sample(range(len(temp_df)), 5), 'Salary'] = 'abc'  # string in numeric
        # You can add more error types here...
        
        temp_df.to_csv(os.path.join(raw_data_path, f"file_{i}.csv"), index=False)