# Search Server

A secure, configurable, and high-performance string search server with SSL/TLS and mutual authentication support.

## Features

- Multiple search algorithms (Linear Search, Binary Search, Boyer-Moore, and KMP)
- SSL/TLS encryption for secure communications
- Mutual TLS (mTLS) authentication for production environments
- Configuration via INI files
- Rate limiting to prevent abuse
- Comprehensive logging and debugging
- Extensive test suite with performance benchmarks

## Local Development Setup

### 1. Prerequisites

- Python 3.8 or higher
- OpenSSL for certificate generation
- Virtual environment (recommended)

### 2. Installation

1. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Linux/Mac
   # or
   .\venv\Scripts\activate  # On Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### 3. SSL Certificate Setup

1. Generate SSL certificates for local development:
   ```bash
   ./setup_ssl.sh
   ```
   This creates the necessary certificates in the `certs/` directory.

2. Verify the certificates:
   ```bash
   ls -l certs/
   # Should show:
   # - ca.crt
   # - ca.key
   # - server.crt
   # - server.key
   # - client.crt
   # - client.key
   ```

### 4. Configuration

1. Server configuration (`config.ini`):
   ```ini
   [server]
   port = 44445
   ssl_enabled = true
   reread_on_query = false

   [file]
   linuxpath = 200k.txt

   [rate_limit]
   max_requests_per_minute = 100
   window_seconds = 60
   ```

2. Client configuration (`client_config.ini`):
   ```ini
   [server]
   port = 44445
   ssl_enabled = true

   [rate_limit]
   max_requests_per_minute = 100
   window_seconds = 60
   ```

### 5. Running Locally

1. Start the server:
   ```bash
   python3 src/server.py
   ```

2. Run the client with different search algorithms:
   ```bash
   # Linear Search (default) - Best for small files
   python3 src/client.py "search string" --algorithm linear

   # Binary Search - Best for large files
   python3 src/client.py "search string" --algorithm binary

   # Boyer-Moore Search - Best for long patterns
   python3 src/client.py "search string" --algorithm boyer_moore

   # Knuth-Morris-Pratt (KMP) Search - Best for short patterns
   python3 src/client.py "search string" --algorithm kmp
   ```

   Additional options:
   ```bash
   # Enable benchmarking to measure execution time
   python3 src/client.py "search string" --algorithm linear --benchmark

   # Use legacy protocol
   python3 src/client.py "search string" --legacy

   # Specify port (default is 44445)
   python3 src/client.py "search string" --algorithm linear --port 44445

   # Use custom config file
   python3 src/client.py "search string" --algorithm linear --config custom_config.ini

   # Set connection timeout
   python3 src/client.py "search string" --algorithm linear --timeout 5.0
   ```

3. Run tests:
   ```bash
   pytest tests/
   ```

## Production Deployment

### 1. SSL/TLS Configuration

1. Use certificates from a trusted Certificate Authority (CA)
2. Enable mutual TLS (mTLS) authentication
3. Set appropriate file permissions:
   ```bash
   chmod 600 /etc/search_server/certs/*.key
   chmod 644 /etc/search_server/certs/*.crt
   ```

### 2. System Service Setup

1. Install the service:
   ```bash
   sudo ./install.sh
   ```

2. Start the service:
   ```bash
   sudo systemctl start search-server
   ```

3. Enable auto-start:
   ```bash
   sudo systemctl enable search-server
   ```

### 3. Production Configuration

1. Set environment to production:
   ```bash
   export ENVIRONMENT=production
   ```

2. Update configuration files with production settings
3. Configure logging and monitoring
4. Set appropriate rate limits

### 4. Security Best Practices

1. Regular certificate rotation
2. Monitor SSL handshake failures
3. Review SSL-related logs
4. Secure private keys
5. Use strong cipher suites

## Performance

See the [Performance Analysis](#performance-analysis) section for detailed metrics and recommendations.

## Troubleshooting

### Common Issues

1. SSL Certificate Issues:
   - Verify certificate paths
   - Check certificate permissions
   - Ensure certificates are valid

2. Connection Issues:
   - Check port availability
   - Verify SSL configuration
   - Check firewall settings

3. Performance Issues:
   - Adjust `reread_on_query` setting
   - Monitor rate limits

## SSL/TLS and Mutual Authentication

The server and client support secure communication through SSL/TLS with optional mutual authentication.

### Certificate Setup

1. Generate SSL certificates using the provided script:
   ```bash
   mkdir -p certs
   cd certs
   openssl req -x509 -newkey rsa:4096 -keyout server.key -out server.crt -days 365 -nodes -subj "/CN=localhost"
   ```
   This will create:
   - `certs/ca.crt`: Certificate Authority certificate.
   - `certs/server.crt`: Server certificate.
   - `certs/server.key`: Server private key.
   - `certs/client.crt`: Client certificate.
   - `certs/client.key`: Client private key.

2. Certificate locations:
   - Development: `certs/` directory in project root.
   - Production: `/etc/search_server/certs/` (when installed as a service).

### SSL Configuration

1. Enable or disable SSL in `config.ini`:
   ```ini
   [server]
   ssl_enabled = true  # or false
   ```

2. Environment-specific behavior:
   - **Development** (`ENVIRONMENT` not set):
     - Self-signed certificates are accepted.
     - Client certificate verification is optional.
   - **Production** (`ENVIRONMENT=production`):
     - Requires valid certificates signed by a trusted CA.
     - Enforces mutual TLS (mTLS) authentication.
     - Client must present a valid certificate.

   **Note:** In production, the server can be configured to require client certificate verification for mutual TLS (mTLS). This is recommended for secure deployments.

3. Running with SSL:
   ```bash
   # Server
   export ENVIRONMENT=production  # For production mode.
   python3 src/server.py

   # Client
   export ENVIRONMENT=production  # For production mode.
   python3 src/client.py "search string"
   ```

### Security Best Practices

1. In production:
   - Use certificates signed by a trusted CA.
   - Keep private keys secure (600 permissions).
   - Regularly rotate certificates.
   - Enable mutual authentication.

2. Certificate permissions:
   ```bash
   chmod 600 certs/*.key
   chmod 644 certs/*.crt
   ```

3. Monitoring:
   - Check certificate expiration dates.
   - Monitor SSL handshake failures.
   - Review SSL-related logs.

## Running the Server

```bash
export ENVIRONMENT=production  # Or leave unset for development.
python3 src/server.py
```

## Running the Client

```bash
export ENVIRONMENT=production  # Or leave unset for development.
python3 src/client.py "search string"
```

## Configuration

Edit `config.ini` or provide a custom config file. Example:

```ini
[server]
port = 44445
ssl_enabled = true
reread_on_query = false

[file]
linuxpath = 200k.txt

[rate_limit]
max_requests_per_minute = 100
window_seconds = 60
```

## Running Tests

Run all tests:
```bash
pytest tests/
```

Run performance tests:
```bash
./run_tests.sh
```
Or

```bash
pytest tests/test_performance.py -v
```

## Performance

See `tests/data/performance_report.md` for detailed performance metrics of different search algorithms.

## Performance Analysis

### Search Algorithm Performance

The server implements multiple search algorithms, each optimized for different use cases:

1. **Linear Search**
   - O(n) complexity
   - Best for small files
   - Simple sequential search

2. **Binary Search**
   - O(log n) complexity
   - Best for large files
   - Requires sorted data

3. **Boyer-Moore Search**
   - O(n/m) complexity
   - Best for long patterns
   - Efficient for text search

4. **Knuth-Morris-Pratt (KMP) Search**
   - O(n) complexity
   - Best for short patterns
   - Good for pattern matching

### Performance Metrics

#### Search Algorithm Performance at 250,000 Lines

| Algorithm    | Execution Time | Best For                |
|--------------|----------------|-------------------------|
| Binary       | ~0.76ms        | Large files             |
| Linear       | ~4.66ms        | Small files             |
| Boyer-Moore  | ~251.04ms      | Long patterns           |
| KMP          | ~1037.00ms     | Short patterns          |

<!-- ![Search Algorithm Performance](tests/data/performance_report.md) -->

# Search Server Performance Report

## Test Results

```
+-------------+----------+----------+---------------+----------+
|   File Size | linear   | binary   | boyer_moore   | kmp      |
+=============+==========+==========+===============+==========+
|        1000 | 0.10 ms  | 0.01 ms  | 0.06 ms       | 0.12 ms  |
+-------------+----------+----------+---------------+----------+
|       10000 | 0.64 ms  | 0.04 ms  | 0.60 ms       | 0.54 ms  |
+-------------+----------+----------+---------------+----------+
|       50000 | 3.02 ms  | 0.24 ms  | 2.95 ms       | 3.37 ms  |
+-------------+----------+----------+---------------+----------+
|      100000 | 5.95 ms  | 0.55 ms  | 6.20 ms       | 20.47 ms |
+-------------+----------+----------+---------------+----------+
|      250000 | 15.06 ms | 1.53 ms  | 14.36 ms      | 14.02 ms |
+-------------+----------+----------+---------------+----------+
```

## Performance Charts

![Performance Comparison](tests/data/performance_chart.png)

![Performance 250k lines](tests/data/performance_bar_chart.png)

## Analysis

1. Binary search have performance for large files
2. Linear search performance - linearly with file size
3. Boyer-Moore and KMP algorithms show consistency
4. All meets the 0.5ms requirement for cached files


#### REREAD_ON_QUERY Impact

The `REREAD_ON_QUERY` configuration significantly impacts performance:

| File Size | REREAD=True | REREAD=False | Performance Impact |
|-----------|-------------|--------------|-------------------|
| 1,000     | 0.24 ms     | 0.01 ms      | 24x faster        |
| 10,000    | 2.23 ms     | 0.04 ms      | 56x faster        |
| 50,000    | 5.33 ms     | 0.11 ms      | 48x faster        |
| 100,000   | 14.95 ms    | 0.38 ms      | 39x faster        |
| 250,000   | 39.95 ms    | 0.96 ms      | 42x faster        |
--------------------------------------------------------------


![REREAD_ON_QUERY Performance Impact](tests/data/reread_performance_plot.png)



### Performance Recommendations

1. **File Size Considerations**
   - For files < 10,000 lines: Use Linear Search
   - For files > 10,000 lines: Use Binary Search
   - For pattern matching: Use Boyer-Moore for long patterns, KMP for short patterns

2. **REREAD_ON_QUERY Settings**
   - Set to `False` for better performance (caches file in memory)
   - Set to `True` only if real-time file updates are required
   - Performance impact increases with file size

3. **Memory Usage**
   - With REREAD_ON_QUERY=False: ~50MB for 250k line file
   - With REREAD_ON_QUERY=True: Minimal memory usage

4. **CPU Usage**
   - <5% under normal load
   - Peaks during file reads when REREAD_ON_QUERY=True

For more detailed performance metrics and charts, see `tests/data/performance_report.md`.

## Development Notes
- Logging is enabled and can be configured in `utils.py`.
- All code has been reviewed for PEP8 and PEP20 compliance using flake8 and manual inspection.
- For mTLS, make sure your certificates are valid and in the correct location.

---

**For more details, see the code and comments in the `src/` and `tests/` directories.**

## Requirements

- Python 3.8 or higher.
- Linux environment.
- OpenSSL for SSL certificate generation.

## Local Development Setup

1. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Generate SSL certificates (if SSL is enabled):
   ```bash
   mkdir -p certs
   cd certs
   openssl req -x509 -newkey rsa:4096 -keyout server.key -out server.crt -days 365 -nodes -subj "/CN=localhost"
   ```

## Local Usage

### Starting the Server

1. Start the server:
   ```bash
   python3 src/server.py
   ```

2. The server will start on port 44445 (configurable in `config.ini`).

### Using Different Search Algorithms

The server supports four search algorithms, each optimized for different use cases:

1. **Linear Search** (Default).
   ```bash
   # Using client.py
   python3 src/client.py "your search string" --algorithm linear
   
   # Using Python API
   from src.client import SearchClient
   client = SearchClient(port=44445)
   result = client.search_json("your search string", algorithm="linear")
   ```
   Best for small files and unsorted data.

2. **Binary Search**.
   ```bash
   # Using client.py
   python3 src/client.py "your search string" --algorithm binary
   
   # Using Python API
   from src.client import SearchClient
   client = SearchClient(port=44445)
   result = client.search_json("your search string", algorithm="binary")
   ```
   Best for large files and sorted data.

3. **Boyer-Moore Search**.
   ```bash
   # Using client.py
   python3 src/client.py "your search string" --algorithm boyer_moore
   
   # Using Python API
   from src.client import SearchClient
   client = SearchClient(port=44445)
   result = client.search_json("your search string", algorithm="boyer_moore")
   ```
   Best for long patterns and text search.

4. **Knuth-Morris-Pratt (KMP) Search**.
   ```bash
   # Using client.py
   python3 src/client.py "your search string" --algorithm  kmp
   
   # Using Python API
   from src.client import SearchClient
   client = SearchClient(port=44445)
   result = client.search_json("your search string", algorithm="kmp")
   ```
   Best for short patterns and pattern matching.

### Legacy Protocol

For backward compatibility, the server also supports a legacy protocol:
```bash
# Using client.py
python3 src/client.py "your search string"

# Using Python API
from src.client import SearchClient
client = SearchClient(port=44445)
result = client.search("your search string")
```

### Benchmarking

To enable benchmarking and see execution times:
```bash
# Using client.py
python3 src/client.py "your search string" linear --benchmark

# Using Python API
from src.client import SearchClient
client = SearchClient(port=44445)
result = client.search_json("your search string", algorithm="linear", benchmark=True)
```

### SSL Configuration

1. Enable or disable SSL in `config.ini`:
   ```