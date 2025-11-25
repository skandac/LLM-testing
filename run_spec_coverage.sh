#!/bin/bash

# 1. Install dependencies (optional, un-comment if needed)
# pip install pytest pytest-cov

echo "============================================"
echo "Running Specification-Guided Tests"
echo "============================================"

# Run pytest on the new test file and generate an HTML coverage report
pytest tests/test_spec_guided.py --cov=src.solutions --cov-report=html --cov-report=term-missing

echo "============================================"
echo "Coverage Report Generated."
echo "Open 'htmlcov/index.html' in your browser to view details."
echo "============================================"