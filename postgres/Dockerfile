FROM postgres:15-alpine

# Copy the initialization script
# This script will run automatically when the container starts for the first time
COPY scripts/db.sql /docker-entrypoint-initdb.d/