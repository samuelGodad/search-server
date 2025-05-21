"""
Tests for search functionality.
"""

import pytest
from src.search import FileSearcher, SearchAlgorithm
import tempfile
import os


@pytest.fixture
def test_file(tmp_path):
    """Create a temporary test file."""
    file_content = """line1
line2
line3
test string
another line
search test
hello world"""
    file_path = tmp_path / "test.txt"
    file_path.write_text(file_content)
    return str(file_path)


def test_search_existing_string(test_file):
    """Test searching for an existing string."""
    searcher = FileSearcher(test_file)
    found, execution_time = searcher.search("test string")

    assert found is True
    assert execution_time >= 0


def test_search_nonexistent_string(test_file):
    """Test searching for a nonexistent string."""
    searcher = FileSearcher(test_file)
    found, execution_time = searcher.search("nonexistent")

    assert found is False
    assert execution_time >= 0


def test_search_with_null_bytes(test_file):
    """Test searching with null bytes in the query."""
    searcher = FileSearcher(test_file)
    found, _ = searcher.search("test string\x00\x00")

    assert found is True


def test_reread_on_query(test_file):
    """Test reread on query functionality."""
    searcher = FileSearcher(test_file, reread_on_query=True)

    # First search
    found1, _ = searcher.search("test string")
    assert found1 is True

    # Modify file
    with open(test_file, "w") as f:
        f.write("new content\n")

    # Second search should see the new content
    found2, _ = searcher.search("new content")
    assert found2 is True


def test_nonexistent_file():
    """Test handling of nonexistent file."""
    searcher = FileSearcher("nonexistent.txt")
    with pytest.raises(FileNotFoundError):
        searcher._load_file()


def test_binary_search(test_file):
    """Test binary search algorithm."""
    searcher = FileSearcher(test_file)
    found, execution_time = searcher.search(
        "test string", SearchAlgorithm.BINARY)

    assert found is True
    assert execution_time >= 0


def test_boyer_moore_search(test_file):
    """Test Boyer-Moore search algorithm."""
    searcher = FileSearcher(test_file)
    found, execution_time = searcher.search(
        "test string", SearchAlgorithm.BOYER_MOORE)

    assert found is True
    assert execution_time >= 0


def test_kmp_search(test_file):
    """Test Knuth-Morris-Pratt search algorithm."""
    searcher = FileSearcher(test_file)
    found, execution_time = searcher.search(
        "test string", SearchAlgorithm.KNUTH_MORRIS_PRATT
    )

    assert found is True
    assert execution_time >= 0


def test_benchmark(test_file):
    """Test benchmarking functionality."""
    searcher = FileSearcher(test_file)
    results = searcher.benchmark("test string", iterations=10)

    assert isinstance(results, dict)
    assert all(alg.value in results for alg in SearchAlgorithm)
    assert all(isinstance(time_ms, float) for time_ms in results.values())
    assert all(time_ms >= 0 for time_ms in results.values())


def test_search_algorithms_consistency(test_file):
    """Test that all algorithms return consistent results."""
    searcher = FileSearcher(test_file)
    query = "test string"

    results = []
    for algorithm in SearchAlgorithm:
        found, _ = searcher.search(query, algorithm)
        results.append(found)

    # All algorithms should return the same result
    assert all(result == results[0] for result in results)


def test_empty_query(test_file):
    """Test searching with empty query."""
    searcher = FileSearcher(test_file)

    for algorithm in SearchAlgorithm:
        found, _ = searcher.search("", algorithm)
        assert found is True  # Empty string should match any line


def test_whitespace_handling(test_file):
    """Test handling of whitespace in queries."""
    searcher = FileSearcher(test_file)

    # Test with leading/trailing whitespace
    found1, _ = searcher.search("  test string  ")
    assert found1 is True

    # Test with internal whitespace
    found2, _ = searcher.search("test  string")
    assert found2 is False  # Should not match "test string"


@pytest.fixture
def sample_file():
    """Create a temporary file with test data."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("normal line\n")
        f.write("line with spaces  \n")
        f.write("line with\ttabs\n")
        f.write("line with special chars !@#$%^&*()\n")
        f.write("line with unicode: 你好\n")
        f.write("line with numbers: 12345\n")
        f.write("line with mixed: abc123!@#\n")
    yield f.name
    os.unlink(f.name)


def test_special_characters(sample_file):
    """Test search with special characters."""
    searcher = FileSearcher(sample_file)

    # Test with special characters
    assert searcher.search("line with special chars !@#$%^&*()")[0]
    assert searcher.search("line with mixed: abc123!@#")[0]

    # Test with unicode
    assert searcher.search("line with unicode: 你好")[0]

    # Test with numbers
    assert searcher.search("line with numbers: 12345")[0]


def test_whitespace_handling_sample_file(sample_file):
    """Test search with different types of whitespace in file lines."""
    searcher = FileSearcher(sample_file)

    # Test with trailing spaces
    assert searcher.search("line with spaces")[0]

    # Test with tabs
    assert searcher.search("line with\ttabs")[0]


def test_partial_match_prevention(sample_file):
    """Test that partial matches are not allowed."""
    searcher = FileSearcher(sample_file)

    # These should not match
    assert not searcher.search("normal")[0]  # Partial word
    assert not searcher.search("line with")[0]  # Partial line
    assert not searcher.search("123")[0]  # Partial number
    assert not searcher.search("你好")[0]  # Partial unicode


def test_empty_and_null_handling(sample_file):
    """Test handling of empty and null queries."""
    searcher = FileSearcher(sample_file)

    # Empty string should return True
    assert searcher.search("")[0]

    # String with only whitespace should return True
    assert searcher.search("   ")[0]

    # String with null bytes should be handled
    assert searcher.search("normal line\x00")[0]


def test_all_algorithms_consistency(sample_file):
    """Test that all algorithms give consistent results."""
    searcher = FileSearcher(sample_file)
    test_queries = [
        "normal line",
        "line with spaces",
        "line with\ttabs",
        "line with special chars !@#$%^&*()",
        "line with unicode: 你好",
        "line with numbers: 12345",
        "line with mixed: abc123!@#",
    ]

    for query in test_queries:
        results = []
        for algorithm in SearchAlgorithm:
            result, _ = searcher.search(query, algorithm)
            results.append(result)

        # All algorithms should give the same result
        assert all(r == results[0] for r in results)
