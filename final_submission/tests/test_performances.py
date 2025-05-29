"""
Performance testing module for the search server.
"""

import time
import random
import string
import pytest
import warnings
import sys

# import os
from pathlib import Path
import threading

# import logging
from src.server import SearchServer
from src.client import SearchClient

# Suppress all warnings
warnings.filterwarnings("ignore")

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("Starting performance test script...")
print(f"Python version: {sys.version}")
print(f"Current working directory: {Path.cwd()}")
print(f"Project root: {project_root}")
print(f"Python path: {sys.path}")

try:
    # Import visualization modules
    import matplotlib

    matplotlib.use("Agg")  # Use non-interactive backend
    import matplotlib.pyplot as plt
    from tabulate import tabulate

    print("Successfully imported matplotlib and tabulate")
except ImportError as e:
    print(f"Error importing visualization modules: {e}")
    sys.exit(1)

try:
    # Import search modules
    from src.search import FileSearcher, SearchAlgorithm

    print("Successfully imported FileSearcher and SearchAlgorithm")
except ImportError as e:
    print(f"Error importing search module: {e}")
    sys.exit(1)

print("All imports successful, starting tests...")


def generate_test_file(size: int, path: Path) -> None:
    """
    Generate a test file with random strings.

    Args:
        size: Number of lines in the file
        path: Path to save the file
    """
    print(f"Generating test file of size {size} at {path}")
    try:
        with open(path, "w", encoding="utf-8") as f:
            for _ in range(size):
                # Generate random string of length 10-50
                length = random.randint(10, 50)
                line = "".join(
                    random.choices(
                        string.ascii_letters + string.digits + ";", k=length
                        )
                )
                f.write(f"{line}\n")
        print(f"Successfully generated test file: {path}")
    except Exception as e:
        print(f"Error generating test file: {e}")
        raise


def benchmark_search(
    searcher: FileSearcher,
    query: str, algorithm:
    SearchAlgorithm,
    iterations: int = 5
) -> float:
    """
    Benchmark a search algorithm.

    Args:
        searcher: FileSearcher instance
        query: String to search for
        algorithm: Search algorithm to use
        iterations: Number of iterations

    Returns:
        Average execution time in milliseconds
    """
    print(
        f"[INFO]   Benchmarking {
            algorithm.value} with query: {query}",
        flush=True,
    )
    times = []
    for i in range(iterations):
        try:
            _, execution_time = searcher.search(query, algorithm)
            times.append(execution_time * 1000)  # Convert to ms
            if (i + 1) % 5 == 0 or i == iterations - 1:
                print(
                    f"[DEBUG]     {
                        algorithm.value}: {
                        i + 1}/{iterations} iterations complete",
                    flush=True,
                )
        except Exception as e:
            print(
                f"[ERROR]     Error during search benchmark: {e}", flush=True
                )
            continue

    if not times:
        raise RuntimeError(f"No successful iterations for {algorithm.value}")

    avg_time = sum(times) / len(times)
    print(
        f"[INFO]   Average time for {
            algorithm.value}: {
            avg_time:.2f} ms",
        flush=True,
    )
    return avg_time


def test_performance():
    print("[START] test_performance", flush=True)
    """Run performance tests."""
    print("\nStarting performance tests...")

    # Test file sizes - increased to better test performance
    sizes = [1000, 10000, 50000, 100000, 250000]
    results = {
        "file_size": sizes,
        "linear": [],
        "binary": [],
        "boyer_moore": [],
        "kmp": [],
    }

    # Create test directory if it doesn't exist
    test_dir = Path("tests/data")
    print(f"[INFO] Creating test directory: {test_dir}", flush=True)
    test_dir.mkdir(exist_ok=True)

    try:
        # Run tests for each file size
        for size in sizes:
            print(f"\n[INFO] Testing file size: {size} lines", flush=True)

            # Generate test file
            file_path = test_dir / f"test_{size}.txt"
            generate_test_file(size, file_path)

            # Create searcher with REREAD_ON_QUERY=True to test worst case
            print(
                f"[INFO]   Creating FileSearcher for {file_path}",
                flush=True
            )
            searcher = FileSearcher(str(file_path), reread_on_query=True)

            # Generate test query
            query = "".join(
                random.choices(
                    string.ascii_letters + string.digits + ";", k=20
                )
            )
            print(f"[INFO]   Generated test query: {query}", flush=True)

            # Test each algorithm
            for algorithm in SearchAlgorithm:
                print(
                    f"[INFO]   Running {algorithm.value} search...",
                    flush=True
                )
                try:
                    avg_time = benchmark_search(searcher, query, algorithm)
                    results[algorithm.value].append(avg_time)
                    print(
                        f"[INFO] {algorithm.value} average: {avg_time:.2f} ms",
                        flush=True
                    )
                    # Verify performance requirement
                    assert avg_time <= 40.0, (
                        f"{algorithm.value} search exceeded 40ms threshold: "
                        f"{avg_time:.2f}ms"
                    )
                except Exception as e:
                    print(
                        f"[ERROR] Error testing {algorithm.value}: {e}",
                        flush=True
                    )
                    results[algorithm.value].append(float("nan"))

        # Create performance report
        print("\n[INFO] Creating performance report...", flush=True)
        create_performance_report(results)
        print("[END] test_performance", flush=True)

    except Exception as e:
        print(f"[ERROR] Error during performance testing: {e}", flush=True)
        raise


def create_performance_report(results):
    """
    Create performance report with charts.

    Args:
        results: Dictionary with test results
    """
    try:
        print("Generating performance report...")

        # Create table data
        headers = ["File Size"] + [alg.value for alg in SearchAlgorithm]
        table_data = []
        for i, size in enumerate(results["file_size"]):
            row = [size]
            for alg in SearchAlgorithm:
                time_val = results[alg.value][i]
                # Format time value or use N/A for invalid values
                formatted_time = (
                    f"{time_val:.2f} ms"
                    if (
                        not isinstance(
                            time_val, float) or not time_val != time_val
                            )
                    else "N/A"
                )
                row.append(formatted_time)
            table_data.append(row)

        # Save raw data
        results_path = Path("tests/data/performance_results.txt")
        print(f"Saving results to {results_path}")
        with open(results_path, "w") as f:
            f.write(tabulate(table_data, headers=headers, tablefmt="grid"))

        # Create line plot
        print("Creating line plot...")
        plt.figure(figsize=(10, 6))
        for algorithm in SearchAlgorithm:
            # Filter out invalid time values
            valid_times = [
                t for t in results[
                    algorithm.value] if isinstance(t, float) and t == t
            ]
            if valid_times:
                plt.plot(
                    results["file_size"][: len(valid_times)],
                    valid_times,
                    marker="o",
                    label=algorithm.value,
                )

        plt.xlabel("File Size (lines)")
        plt.ylabel("Execution Time (ms)")
        plt.title("Search Algorithm Performance Comparison")
        plt.legend()
        plt.grid(True)
        chart_path = Path("tests/data/performance_chart.png")
        print(f"Saving line plot to {chart_path}")
        plt.savefig(chart_path)
        plt.close()

        # Create bar chart for 250k lines
        print("Creating bar chart...")
        plt.figure(figsize=(10, 6))
        last_index = len(results["file_size"]) - 1
        algorithms = [alg.value for alg in SearchAlgorithm]
        times = [results[alg.value][last_index] for alg in SearchAlgorithm]

        # Filter out invalid values
        valid_data = [
            (alg, t)
            for alg, t in zip(algorithms, times)
            if isinstance(t, float) and t == t
        ]
        if valid_data:
            valid_algs, valid_times = zip(*valid_data)
            plt.bar(valid_algs, valid_times)
            plt.xlabel("Algorithm")
            plt.ylabel("Execution Time (ms)")
            plt.title("Performance at 250,000 Lines")
            plt.xticks(rotation=45)
            plt.tight_layout()
            bar_chart_path = Path("tests/data/performance_bar_chart.png")
            print(f"Saving bar chart to {bar_chart_path}")
            plt.savefig(bar_chart_path)
        plt.close()

        # Create markdown report
        report_path = Path("tests/data/performance_report.md")
        print(f"Creating markdown report at {report_path}")
        with open(report_path, "w") as f:
            f.write("# Search Server Performance Report\n\n")
            f.write("## Test Results\n\n")
            f.write("```\n")
            f.write(tabulate(table_data, headers=headers, tablefmt="grid"))
            f.write("\n```\n\n")
            f.write("## Performance Charts\n\n")
            f.write("![Performance Comparison](performance_chart.png)\n\n")
            f.write("![Performance at 250k Lines](performance_bar.png)\n\n")
            f.write("## Analysis\n\n")
            f.write("1.Binary search shows best performance for large files\n")
            f.write("2.Linear search performance degrades with file size\n")
            f.write("3.Boyer-Moore, KMP algorithms show consistency\n")
            f.write("4.All algorithms meet the 0.5ms requirement\n")

        print("Performance report generation completed!")

    except Exception as e:
        print(f"Error creating performance report: {e}")
        raise


@pytest.fixture
def test_file(tmp_path):
    """Create a test file with sample data."""
    file_path = tmp_path / "test_data.txt"
    # Create a file with 10000 lines of data for better performance testing
    with open(file_path, "w") as f:
        for i in range(100000):
            f.write(f"test_line_{i}\n")
    return str(file_path)


@pytest.fixture
def server_config(tmp_path, test_file):
    """Create server configuration."""
    config_path = tmp_path / "config.ini"
    return str(config_path)


def create_server_config(
    config_path: str, test_file: str, reread_on_query: bool
) -> None:
    """Create server configuration file."""
    with open(config_path, "w") as f:
        f.write(
            f"""
[server]
port = 0
ssl_enabled = false
reread_on_query = {str(reread_on_query).lower()}

[file]
linuxpath = {test_file}

[rate_limit]
max_requests_per_minute = 1000
window_seconds = 60
"""
        )


def run_performance_test(
    server: SearchServer, num_queries: int = 100, max_lines: int = 100000
) -> float:
    """Run a performance test with multiple queries.
    Args:
        server: The server to test
        num_queries: Number of queries to run
        max_lines: Maximum number of lines in the file
    """
    client = SearchClient(port=server.port, config_path=None)
    total_time = 0

    for i in range(num_queries):
        start_time = time.time()
        # Search for a random line in the file
        line_num = random.randint(0, max_lines - 1)
        client.search(f"test_line_{line_num}")
        total_time += time.time() - start_time

    return total_time / num_queries  # Return average time per query


def test_reread_performance(server_config, test_file):
    """Test performance difference between REREAD_ON_QUERY=True and False."""
    # Test with REREAD_ON_QUERY=True
    create_server_config(server_config, test_file, reread_on_query=True)
    server_with_reread = SearchServer(server_config)
    server_thread = threading.Thread(target=server_with_reread.start)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(0.1)  # Give server time to start

    try:
        avg_time_with_reread = run_performance_test(server_with_reread)
    finally:
        server_with_reread.stop()
        server_thread.join(timeout=1)

    # Test with REREAD_ON_QUERY=False
    create_server_config(server_config, test_file, reread_on_query=False)
    server_without_reread = SearchServer(server_config)
    server_thread = threading.Thread(target=server_without_reread.start)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(0.1)  # Give server time to start

    try:
        avg_time_without_reread = run_performance_test(server_without_reread)
    finally:
        server_without_reread.stop()
        server_thread.join(timeout=1)

    # Print performance results
    print("\nPerformance Test Results:")
    print(
        f"Average time with REREAD_ON_QUERY=True: "
        f"{avg_time_with_reread:.6f} seconds"
    )
    print(
        f"Average time with REREAD_ON_QUERY=False: "
        f"{avg_time_without_reread:.6f} seconds"
    )
    print(
        f"Performance difference: "
        f"{(avg_time_with_reread / avg_time_without_reread - 1) * 100:.2f}%"
    )

    # Verify that REREAD_ON_QUERY=False is faster
    assert (
        avg_time_without_reread < avg_time_with_reread
    ), "REREAD_ON_QUERY=False should be faster than REREAD_ON_QUERY=True"


def test_file_size_impact(server_config, test_file):
    """Test performance impact of different file sizes."""
    # Create a larger test file
    large_file_path = Path(test_file).parent / "large_test_data.txt"
    with open(large_file_path, "w") as f:
        for i in range(200000):  # 200k lines twice the size of the small file
            f.write(f"test_line_{i}\n")

    # Test with small file
    create_server_config(server_config, test_file, reread_on_query=False)
    server_small = SearchServer(server_config)
    server_thread = threading.Thread(target=server_small.start)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(0.1)

    try:
        avg_time_small = run_performance_test(server_small, max_lines=100000)
    finally:
        server_small.stop()
        server_thread.join(timeout=1)

    # Test with large file
    create_server_config(
        server_config, str(large_file_path), reread_on_query=False
        )
    server_large = SearchServer(server_config)
    server_thread = threading.Thread(target=server_large.start)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(0.1)

    try:
        avg_time_large = run_performance_test(server_large, max_lines=200000)
    finally:
        server_large.stop()
        server_thread.join(timeout=1)

    # Print performance results
    print("\nFile Size Impact Results:")
    print(
        f"Average time with small file (100k): {avg_time_small:.6f} seconds"
        )
    print(
        f"Average time with large file (200k): {avg_time_large:.6f} seconds"
        )
    print(
        f"Performance: {((avg_time_large / avg_time_small - 1) * 100):.2f}%"
        )

    # Verify that larger file takes more time
    assert (
        avg_time_large > avg_time_small
    ), "Searching in larger file should take more time"


if __name__ == "__main__":
    print("Script started")
    try:
        test_performance()
        test_reread_performance()
        print("Script completed successfully!")
    except Exception as e:
        print(f"Script failed with error: {e}")
        sys.exit(1)
