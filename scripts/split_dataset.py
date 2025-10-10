import pandas as pd, os, numpy as np, sys

def split_dataset(dataset_path, raw_folder, num_files):
    os.makedirs(raw_folder, exist_ok=True)
    df = pd.read_csv(dataset_path)
    splits = np.array_split(df, num_files)
    for i, split_df in enumerate(splits):
        split_df.to_csv(f"{raw_folder}/data_part_{i}.csv", index=False)
    print(f"✅ Created {num_files} CSV files in {raw_folder}")

if __name__ == "__main__":
    dataset = sys.argv[1] if len(sys.argv) > 1 else "data.csv"
    split_dataset(dataset, "raw_data", 10)
