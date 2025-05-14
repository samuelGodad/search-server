"""
Tests for search functionality.
"""
import pytest
from src.search import FileSearcher


@pytest.fixture
def test_file(tmp_path):
    """Create a temporary test file."""
    file_content = """line1
line2
line3
test string
another line"""
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
    with open(test_file, 'w') as f:
        f.write("new content\n")
    
    # Second search should see the new content
    found2, _ = searcher.search("new content")
    assert found2 is True


def test_nonexistent_file():
    """Test handling of nonexistent file."""
    searcher = FileSearcher("nonexistent.txt")
    with pytest.raises(FileNotFoundError):
        searcher._load_file() 