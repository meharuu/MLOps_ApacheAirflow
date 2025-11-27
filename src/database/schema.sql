-- Predictions table (for storing model predictions)
CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    prediction_id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    features JSONB NOT NULL,                 -- Store input features as JSON
    prediction FLOAT NOT NULL,                -- Model prediction
    prediction_class VARCHAR(50),             -- For classification tasks
    probability_0 FLOAT,                      -- Probability for class 0
    probability_1 FLOAT,                      -- Probability for class 1
    confidence_score FLOAT,                   -- Confidence of prediction
    source VARCHAR(50) NOT NULL,              -- 'webapp' or 'scheduled_job'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    batch_id VARCHAR(100),                    -- For grouping batch predictions
    api_version VARCHAR(20),                  -- Model API version used
    model_version VARCHAR(50)                 -- Model version that made prediction
);

-- Data quality issues table (for storing ingestion errors)
CREATE TABLE IF NOT EXISTS data_quality_issues (
    id SERIAL PRIMARY KEY,
    issue_id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL,
    error_type VARCHAR(100) NOT NULL,         -- e.g., 'Missing Values', 'Unknown Category'
    column_name VARCHAR(100),                 -- Column where error occurred
    affected_rows INTEGER,                    -- Number of rows with this error
    error_count INTEGER DEFAULT 1,
    error_details JSONB,                      -- Detailed error info
    severity VARCHAR(20),                     -- 'HIGH', 'MEDIUM', 'LOW'
    is_resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

-- Ingestion statistics table (for monitoring)
CREATE TABLE IF NOT EXISTS ingestion_statistics (
    id SERIAL PRIMARY KEY,
    batch_id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL,
    total_rows INTEGER NOT NULL,
    valid_rows INTEGER NOT NULL,
    invalid_rows INTEGER NOT NULL,
    quality_score FLOAT,                      -- 0-1, valid_rows / total_rows
    processing_time_ms FLOAT,                 -- How long validation took
    validation_status VARCHAR(50),            -- 'PASSED', 'FAILED', 'PARTIAL'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Data drift table (for tracking feature distribution changes)
CREATE TABLE IF NOT EXISTS data_drift (
    id SERIAL PRIMARY KEY,
    drift_id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    feature_name VARCHAR(100) NOT NULL,
    train_mean FLOAT,                         -- Mean from training data
    train_std FLOAT,                          -- Std dev from training data
    serving_mean FLOAT,                       -- Mean from serving data
    serving_std FLOAT,
    drift_score FLOAT,                        -- Statistical drift measure
    drift_detected BOOLEAN,
    threshold FLOAT DEFAULT 0.15,             -- Alert threshold
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Model performance table (for tracking predictions over time)
CREATE TABLE IF NOT EXISTS model_performance (
    id SERIAL PRIMARY KEY,
    performance_id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    batch_id VARCHAR(100),
    prediction_count INTEGER DEFAULT 0,       -- How many predictions in this batch
    avg_prediction FLOAT,                     -- Average prediction value
    min_prediction FLOAT,
    max_prediction FLOAT,
    most_common_class VARCHAR(50),            -- Most predicted class
    zero_predictions INTEGER DEFAULT 0,       -- Count of predictions = 0
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_predictions_source_created ON predictions(source, created_at);
CREATE INDEX idx_predictions_batch_id ON predictions(batch_id);
CREATE INDEX idx_quality_issues_filename ON data_quality_issues(filename);
CREATE INDEX idx_quality_issues_error_type ON data_quality_issues(error_type);
CREATE INDEX idx_quality_issues_severity ON data_quality_issues(severity);
CREATE INDEX idx_ingestion_stats_created ON ingestion_statistics(created_at);
CREATE INDEX idx_data_drift_feature ON data_drift(feature_name);