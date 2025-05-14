# Search Server

A high-performance TCP server for string search operations in large text files.

## Features

- TCP server with SSL support
- Concurrent connection handling
- Configurable file search
- Performance optimized
- Comprehensive logging
- Unit tested

## Installation

1. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

Create a `config.ini` file in the project root with the following structure:
```ini
[server]
port = 44445
ssl_enabled = true
reread_on_query = false

[file]
linuxpath = /path/to/your/file.txt
```

## Running the Server

```bash
python src/server.py
```

## Running Tests

```bash
pytest tests/
```

## Project Structure

```
search_server/
├── src/
│   ├── __init__.py
│   ├── server.py
│   ├── config.py
│   ├── search.py
│   └── utils.py
├── tests/
│   ├── __init__.py
│   ├── test_server.py
│   ├── test_search.py
│   └── test_config.py
├── docs/
│   └── performance_report.md
├── requirements.txt
├── README.md
└── config.ini
```

## License

Proprietary and Confidential 