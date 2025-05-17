# Search Server

A high-performance TCP server for string search operations with SSL support and rate limiting.

## Features

- TCP server with unlimited concurrent connections
- Multiple search algorithms (Linear, Binary, Boyer-Moore, KMP)
- SSL authentication support
- Rate limiting
- Configurable file path and search behavior
- Performance optimized (0.5ms when REREAD_ON_QUERY is FALSE)
- Comprehensive logging
- PEP8 and PEP20 compliant
- Statically typed

## Requirements

- Python 3.8+
- Linux environment
- OpenSSL for SSL certificate generation

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd search_server
```

2. Run the setup script:
```bash
./setup_ubuntu.sh
```

3. Generate SSL certificates (if SSL is enabled):
```bash
./setup_ssl.sh
```

## Service Installation

To install and run the server as a systemd service:

1. Copy the service file:
```bash
sudo cp search_server.service /etc/systemd/system/
```

2. Create the installation directory:
```bash
sudo mkdir -p /opt/search_server
```

3. Copy the project files:
```bash
sudo cp -r * /opt/search_server/
```

4. Set up the environment:
```bash
cd /opt/search_server
sudo ./setup_ubuntu.sh
```

5. Generate SSL certificates (if SSL is enabled):
```bash
sudo ./setup_ssl.sh
```

6. Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable search_server
sudo systemctl start search_server
```

7. Check service status:
```bash
sudo systemctl status search_server
```

8. View logs:
```bash
sudo journalctl -u search_server -f
```

To stop the service:
```bash
sudo systemctl stop search_server
```

To disable the service:
```bash
sudo systemctl disable search_server
```

## Configuration

The server is configured through `config.ini`:

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

## Usage

### Starting the Server

```bash
python3 src/server.py
```

### Using the Client

```bash
python3 src/client.py "search_string" [algorithm]
```

Available algorithms:
- linear
- binary
- boyer_moore
- kmp

Example:
```bash
python3 src/client.py "test_string" binary
```

## Search Algorithms

1. **Linear Search**
   - Simple sequential search
   - O(n) time complexity
   - Best for small files

2. **Binary Search**
   - Requires sorted data
   - O(log n) time complexity
   - Best for large files

3. **Boyer-Moore Search**
   - Efficient for long patterns
   - O(n/m) time complexity
   - Good for text search

4. **Knuth-Morris-Pratt (KMP) Search**
   - Efficient for short patterns
   - O(n) time complexity
   - Good for pattern matching

## Performance

The server is optimized for performance:
- 0.5ms execution time when REREAD_ON_QUERY is FALSE
- 40ms execution time when REREAD_ON_QUERY is TRUE
- Handles files up to 250,000 rows efficiently

## SSL Configuration

SSL is configured through certificates in the `certs` directory:
- `server.crt`: Server certificate
- `server.key`: Server private key

To generate new certificates:
```bash
./setup_ssl.sh
```

## Rate Limiting

The server implements rate limiting to prevent abuse:
- Configurable requests per minute
- Per-client tracking
- Configurable time window

## Logging

The server provides comprehensive logging:
- Debug information for each request
- Error logging
- Performance metrics

## Testing

Run the performance tests:
```bash
./run_tests.sh
```

## Project Structure

```
search_server/
├── src/
│   ├── server.py      # Main server implementation
│   ├── client.py      # Client implementation
│   ├── search.py      # Search algorithms
│   ├── config.py      # Configuration handling
│   ├── rate_limiter.py # Rate limiting
│   └── utils.py       # Utility functions
├── tests/
│   ├── test_performance.py
│   └── data/
├── certs/             # SSL certificates
├── config.ini         # Configuration file
├── setup_ubuntu.sh    # Setup script
├── setup_ssl.sh       # SSL setup script
└── run_tests.sh       # Test runner
```

## Performance Analysis

### Search Algorithm Performance

The server implements multiple search algorithms, each optimized for different use cases. Here's a detailed performance analysis:

![Search Algorithm Performance](tests/data/performance_chart.png)

Performance comparison across different file sizes:
- Linear Search: O(n) complexity, best for small files
- Binary Search: O(log n) complexity, best for large files
- Boyer-Moore: O(n/m) complexity, efficient for long patterns
- KMP: O(n) complexity, efficient for short patterns

### Performance at 250,000 Lines

![Performance at 250k Lines](tests/data/performance_bar_chart.png)

At maximum file size (250,000 lines):
- Binary Search: ~0.76ms
- Linear Search: ~4.66ms
- Boyer-Moore: ~251.04ms
- KMP: ~1037.00ms

### REREAD_ON_QUERY Performance

![REREAD_ON_QUERY Performance](tests/data/reread_performance_plot.png)

Performance comparison with REREAD_ON_QUERY enabled vs disabled:
- With REREAD_ON_QUERY=False: ~0.5ms (cached)
- With REREAD_ON_QUERY=True: ~40ms (file read)

### Performance Results Table

```
+-------------+----------+----------+---------------+------------+
|   File Size | linear   | binary   | boyer_moore   | kmp        |
+=============+==========+==========+===============+============+
|        1000 | 0.02 ms  | 0.00 ms  | 0.84 ms       | 3.54 ms    |
+-------------+----------+----------+---------------+------------+
|       10000 | 0.16 ms  | 0.02 ms  | 9.90 ms       | 47.25 ms   |
+-------------+----------+----------+---------------+------------+
|       50000 | 1.04 ms  | 0.10 ms  | 50.53 ms      | 189.62 ms  |
+-------------+----------+----------+---------------+------------+
|      100000 | 1.88 ms  | 0.21 ms  | 110.38 ms     | 381.67 ms  |
+-------------+----------+----------+---------------+------------+
|      250000 | 4.66 ms  | 0.76 ms  | 251.04 ms     | 1037.00 ms |
+-------------+----------+----------+---------------+------------+
```

### Performance Recommendations

1. **Small Files (< 10,000 lines)**:
   - Use Linear Search for simplicity
   - Binary Search for slightly better performance

2. **Medium Files (10,000 - 50,000 lines)**:
   - Binary Search is recommended
   - Linear Search is acceptable

3. **Large Files (> 50,000 lines)**:
   - Binary Search is strongly recommended
   - Avoid Boyer-Moore and KMP for large files

4. **REREAD_ON_QUERY Settings**:
   - Set to FALSE for maximum performance
   - Set to TRUE only when file changes frequently

## Author

[Samuel Godad] 

