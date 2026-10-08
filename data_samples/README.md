cat > data_samples/README.md <<'EOF'
# Data Samples

This folder contains small sample files for demonstration purposes only.

The full pipeline generates much larger datasets which are intentionally excluded from the GitHub repository.

Excluded folders:
- raw_data/
- silver/
- gold/
- analytics/
- logs/

To generate full datasets, run the pipeline locally.

Example:

python -m pipelines.job_market_pipeline
EOF