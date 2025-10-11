CREATE TABLE IF NOT EXISTS data_quality_issues (
    id SERIAL PRIMARY KEY,
    filename TEXT,
    nb_rows INT,
    nb_valid_rows INT,
    nb_invalid_rows INT,
    issue_summary TEXT,
    criticality TEXT,
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    model_name TEXT,
    input_features JSONB,
    prediction_result JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
