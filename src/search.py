"""
File search functionality module.
"""
import time
from pathlib import Path
from typing import Tuple, Optional, List, Callable
from enum import Enum


class SearchAlgorithm(Enum):
    """Available search algorithms."""
    LINEAR = "linear"
    BINARY = "binary"
    BOYER_MOORE = "boyer_moore"
    KNUTH_MORRIS_PRATT = "kmp"


class FileSearcher:
    """Handles file search operations."""

    def __init__(self, file_path: str, reread_on_query: bool = False) -> None:
        """
        Initialize file searcher.

        Args:
            file_path: Path to the file to search in
            reread_on_query: Whether to reread the file on each query
        """
        self.file_path = Path(file_path)
        self.reread_on_query = reread_on_query
        self._file_contents: Optional[list[str]] = None
        self._sorted_contents: Optional[list[str]] = None
        self._last_read_time: float = 0.0
        self._file_size: int = 0

    def _load_file(self) -> list[str]:
        """
        Load file contents.

        Returns:
            List of lines from the file
        """
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")
        
        # Get file size for monitoring
        self._file_size = self.file_path.stat().st_size
        
        # Read file contents
        with open(self.file_path, 'r', encoding='utf-8') as f:
            contents = [line.strip() for line in f]
        
        # Update last read time
        self._last_read_time = time.time()
        return contents

    def _ensure_file_loaded(self, algorithm: SearchAlgorithm) -> None:
        """
        Ensure file contents are loaded based on reread_on_query setting.
        
        Args:
            algorithm: Current search algorithm
        """
        current_time = time.time()
        
        if self.reread_on_query:
            # Always reload file when reread_on_query is True
            self._file_contents = self._load_file()
            if algorithm == SearchAlgorithm.BINARY:
                self._sorted_contents = sorted(self._file_contents)
        elif self._file_contents is None:
            # Load file if not loaded yet
            self._file_contents = self._load_file()
            if algorithm == SearchAlgorithm.BINARY:
                self._sorted_contents = sorted(self._file_contents)
        elif algorithm == SearchAlgorithm.BINARY and self._sorted_contents is None:
            # Ensure sorted contents for binary search
            self._sorted_contents = sorted(self._file_contents)

    def _linear_search(self, query: str) -> bool:
        """Linear search implementation."""
        # Handle empty query
        if not query:
            return True
            
        # Remove null bytes from query
        query = query.replace('\x00', '')
        
        return any(query == line for line in self._file_contents)

    def _binary_search(self, query: str) -> bool:
        """Binary search implementation."""
        # Handle empty query
        if not query:
            return True
            
        # Remove null bytes from query
        query = query.replace('\x00', '')
        
        if self._sorted_contents is None:
            self._sorted_contents = sorted(self._file_contents)
        
        left, right = 0, len(self._sorted_contents) - 1
        while left <= right:
            mid = (left + right) // 2
            if self._sorted_contents[mid] == query:
                return True
            elif self._sorted_contents[mid] < query:
                left = mid + 1
            else:
                right = mid - 1
        return False

    def _boyer_moore_search(self, query: str) -> bool:
        """Boyer-Moore search implementation."""
        # Handle empty query
        if not query:
            return True
            
        # Remove null bytes from query
        query = query.replace('\x00', '')
        
        def bad_char_heuristic(pattern: str) -> dict:
            bad_char = {}
            for i in range(len(pattern)):
                bad_char[pattern[i]] = i
            return bad_char

        def search_in_text(text: str, pattern: str) -> bool:
            if not pattern:
                return True
            
            bad_char = bad_char_heuristic(pattern)
            m = len(pattern)
            n = len(text)
            s = 0
            
            while s <= n - m:
                j = m - 1
                while j >= 0 and pattern[j] == text[s + j]:
                    j -= 1
                if j < 0:
                    return True
                else:
                    s += max(1, j - bad_char.get(text[s + j], -1))
            return False

        return any(search_in_text(line, query) for line in self._file_contents)

    def _kmp_search(self, query: str) -> bool:
        """Knuth-Morris-Pratt search implementation."""
        # Handle empty query
        if not query:
            return True
            
        # Remove null bytes from query
        query = query.replace('\x00', '')
        
        def compute_lps(pattern: str) -> List[int]:
            lps = [0] * len(pattern)
            length = 0
            i = 1
            
            while i < len(pattern):
                if pattern[i] == pattern[length]:
                    length += 1
                    lps[i] = length
                    i += 1
                else:
                    if length != 0:
                        length = lps[length - 1]
                    else:
                        lps[i] = 0
                        i += 1
            return lps

        def search_in_text(text: str, pattern: str) -> bool:
            if not pattern:
                return True
                
            lps = compute_lps(pattern)
            i = j = 0
            
            while i < len(text):
                if pattern[j] == text[i]:
                    i += 1
                    j += 1
                if j == len(pattern):
                    return True
                elif i < len(text) and pattern[j] != text[i]:
                    if j != 0:
                        j = lps[j - 1]
                    else:
                        i += 1
            return False

        return any(search_in_text(line, query) for line in self._file_contents)

    def search(self, query: str, algorithm: SearchAlgorithm = SearchAlgorithm.BINARY) -> Tuple[bool, float]:
        """
        Search for a string in the file using specified algorithm.

        Args:
            query: String to search for
            algorithm: Search algorithm to use

        Returns:
            Tuple of (bool, float): (True if string is found, execution time in seconds)
        """
        start_time = time.time()
        
        # Strip whitespace and newlines from the query
        query = query.strip()
        
        # Handle empty query
        if not query:
            return True, 0.0
            
        # Remove null bytes from query
        query = query.replace('\x00', '')
        
        # Ensure file is loaded
        self._ensure_file_loaded(algorithm)
        
        # Select search algorithm
        search_func: Callable[[str], bool] = {
            SearchAlgorithm.LINEAR: self._linear_search,
            SearchAlgorithm.BINARY: self._binary_search,
            SearchAlgorithm.BOYER_MOORE: self._boyer_moore_search,
            SearchAlgorithm.KNUTH_MORRIS_PRATT: self._kmp_search
        }[algorithm]
        
        # Perform search
        result = search_func(query)
        end_time = time.time()
        
        return result, end_time - start_time

    def benchmark(self, query: str, iterations: int = 1000) -> dict:
        """
        Benchmark all search algorithms.

        Args:
            query: String to search for
            iterations: Number of iterations for benchmarking

        Returns:
            Dictionary with algorithm names and their average execution times
        """
        results = {}
        
        for algorithm in SearchAlgorithm:
            total_time = 0
            for _ in range(iterations):
                _, execution_time = self.search(query, algorithm)
                total_time += execution_time
            
            results[algorithm.value] = total_time / iterations
            
        return results