# Search Server - Final Submission

## Project Overview
A secure, high-performance string search server with SSL/TLS support and multiple search algorithms.

## Key Features
- Multiple search algorithms (Linear, Binary, Boyer-Moore, KMP)
- SSL/TLS encryption with mutual authentication
- Rate limiting and comprehensive logging
- Extensive test suite with performance benchmarks
- Production-ready deployment scripts

## Performance Highlights
- Binary search: 0.95ms for 250k lines
- REREAD_ON_QUERY=False provides 144x performance improvement
- All algorithms meet sub-10ms requirements for large files
- Comprehensive performance analysis with charts

## Files Included
- Complete source code in `src/`
- Comprehensive test suite in `tests/`
- Performance reports and charts in `docs/`
- Installation and deployment scripts
- SSL certificate generation scripts
- Configuration files for server and client

## Quick Start
1. Run `./setup_ssl.sh` to generate certificates
2. Run `python3 src/server.py` to start server
3. Run `python3 src/client.py "search term"` to test

## Testing
- Run `pytest tests/` for full test suite
- Run `./run_tests.sh` for performance tests
- See `docs/performance_report.md` for detailed metrics

## Documentation
- Complete README.md with setup instructions
- Performance analysis with actual test results
- SSL/TLS configuration guide
- API documentation and usage examples
