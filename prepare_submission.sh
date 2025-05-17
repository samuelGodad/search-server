#!/bin/bash

# Exit on error
set -e

echo "Preparing final submission package..."

# Create submission directory
mkdir -p submission
cd submission

# Copy source files
echo "Copying source files..."
mkdir -p src
cp -r ../src/* src/

# Copy test files
echo "Copying test files..."
mkdir -p tests
cp -r ../tests/* tests/

# Copy configuration files
echo "Copying configuration files..."
cp ../config.ini .
cp ../requirements.txt .

# Generate performance report
echo "Generating performance report..."
mkdir -p docs
cd ..
source venv/bin/activate

# Run tests with coverage
echo "Generating test coverage report..."
pytest --cov=src tests/ --cov-report=html:tests/coverage_report
pytest --cov=src tests/ --cov-report=term-missing

# Generate performance report
echo "Generating performance report..."
python tests/test_performance.py --generate-report
mv tests/data/performance_report.pdf submission/docs/

# Copy installation scripts
echo "Copying installation scripts..."
cp install.sh submission/
cp uninstall.sh submission/
cp search-server.service submission/
cp setup_ssl.sh submission/

# Copy documentation
echo "Copying documentation..."
cp README.md submission/
cp LICENSE submission/

# Copy your manual daily reports
echo "Copying daily reports..."
mkdir -p submission/docs/daily_reports
cp -r ../daily_reports/* submission/docs/daily_reports/

# Create AI usage documentation
echo "Creating AI usage documentation..."
cat > submission/docs/ai_usage.md << EOL
# AI Usage Documentation

## Tools Used
- Cursor IDE
- GitHub Copilot
- ChatGPT

## AI-Assisted Tasks
1. Code Generation
   - Initial server implementation
   - Search algorithm implementations
   - Client implementation
   - Test cases

2. Code Review
   - Static type checking
   - PEP8 compliance
   - Performance optimization
   - Security review

3. Documentation
   - README generation
   - API documentation
   - Installation guide
   - Performance report

4. Testing
   - Test case generation
   - Performance testing
   - Edge case identification

## Human Contributions
1. Architecture Design
2. Algorithm Selection
3. Performance Analysis
4. Final Code Review
5. Manual Testing
6. Documentation Review
7. Daily Progress Reports
EOL

# Clean up unnecessary files
echo "Cleaning up unnecessary files..."
find submission -type d -name "__pycache__" -exec rm -rf {} +
find submission -type d -name ".pytest_cache" -exec rm -rf {} +
find submission -type f -name "*.pyc" -delete
find submission -type f -name "*.pyo" -delete
find submission -type f -name "*.pyd" -delete
find submission -type f -name ".coverage" -delete
find submission -type d -name "*.egg-info" -exec rm -rf {} +

# Create submission archive
echo "Creating submission archive..."
cd submission
tar -czf ../search_server_submission.tar.gz *

echo "Final submission package prepared successfully!"
echo "Files are in: submission/"
echo "Archive is: search_server_submission.tar.gz"
echo ""
echo "Please verify the following before submission:"
echo "1. All source files are included"
echo "2. All tests are included"
echo "3. Performance report is generated"
echo "4. Test coverage report is generated"
echo "5. Daily reports are included"
echo "6. Installation scripts are included"
echo "7. Documentation is complete"
echo "8. No unnecessary files are included" 