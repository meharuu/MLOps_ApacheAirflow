import os, random, pandas as pd
from sqlalchemy import create_engine
from great_expectations.dataset import PandasDataset

engine = create_engine("postgresql://postgres:yourpassword@localhost/data_monitoring")

def validate_data(df):
    data = PandasDataset(df)
    issues = []
    if not data.expect_column_values_to_not_be_null("Age")["success"]:
        issues.append("Missing Age values")
    if not data.expect_column_values_to_be_between("Age", 0, 120)["success"]:
        issues.append("Invalid Age values")
    if not data.expect_column_values_to_be_in_set("Country", ["China","India","Lebanon"])["success"]:
        issues.append("Unexpected Country values")
    return issues

def process_file(file_path):
    df = pd.read_csv(file_path)
    issues = validate_data(df)

    nb_rows = len(df)
    nb_invalid = len(issues)
    nb_valid = nb_rows - nb_invalid
    criticality = "high" if nb_invalid > 5 else "medium" if nb_invalid > 0 else "none"

    engine.execute("""
        INSERT INTO data_quality_issues(filename, nb_rows, nb_valid_rows, nb_invalid_rows, issue_summary, criticality)
        VALUES (%s,%s,%s,%s,%s,%s)
    """, (file_path, nb_rows, nb_valid, nb_invalid, str(issues), criticality))

    if nb_invalid == 0:
        os.rename(file_path, file_path.replace("raw_data", "good_data"))
    else:
        os.rename(file_path, file_path.replace("raw_data", "bad_data"))

def run_ingestion():
    os.makedirs("good_data", exist_ok=True)
    os.makedirs("bad_data", exist_ok=True)
    files = [f for f in os.listdir("raw_data") if f.endswith(".csv")]
    if not files:
        print("No files left in raw_data folder.")
        return
    file = random.choice(files)
    process_file(f"raw_data/{file}")
    print(f"✅ Processed: {file}")

if __name__ == "__main__":
    run_ingestion()
