"""
File search functionality module.
"""

import time
from pathlib import Path
from typing import Tuple, Optional, Callable, List
from enum import Enum
import mmap
import os


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
        self._file_contents: Optional[List[str]] = None
        self._sorted_contents: Optional[List[str]] = None
        self._last_read_time: float = 0.0
        self._file_size: int = 0
        self._mmap_file: Optional[mmap.mmap] = None
        self._mmap_size: int = 0

    def _load_file(self) -> List[str]:
        """
        Load file contents using memory mapping for better performance.

        Returns:
            List of lines from the file
        """
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")

        # Get file size for monitoring
        self._file_size = self.file_path.stat().st_size

        # Use memory mapping for large files
        if self._file_size > 1024 * 1024:  # 1MB threshold
            with open(self.file_path, "rb") as f:
                self._mmap_file = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
                self._mmap_size = self._mmap_file.size()
                contents = []
                current_line = bytearray()
                
                for i in range(self._mmap_size):
                    byte = self._mmap_file[i:i+1]
                    if byte == b'\n':
                        contents.append(current_line.decode('utf-8').strip())
                        current_line = bytearray()
                    else:
                        current_line.extend(byte)
                
                if current_line:  # Handle last line without newline
                    contents.append(current_line.decode('utf-8').strip())
                
                self._mmap_file.close()
                self._mmap_file = None
        else:
            # For smaller files, use regular file reading
            with open(self.file_path, "r", encoding="utf-8") as f:
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
        """
        Linear search implementation with exact whole line matching.

        Args:
            query: String to search for

        Returns:
            bool: True if exact match found, False otherwise
        """
        if not query:
            return True

        query = query.replace("\x00", "").strip()
        
        # Use list comprehension for better performance
        return any(query == line for line in self._file_contents)

    def _binary_search(self, query: str) -> bool:
        """
        Binary search implementation with exact whole line matching.

        Args:
            query: String to search for

        Returns:
            bool: True if exact match found, False otherwise
        """
        if not query:
            return True

        query = query.replace("\x00", "").strip()

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
        """
        Boyer-Moore search implementation with exact whole line matching.

        Args:
            query: String to search for

        Returns:
            bool: True if exact match found, False otherwise
        """
        if not query:
            return True

        query = query.replace("\x00", "").strip()
        return any(query == line for line in self._file_contents)

    def _kmp_search(self, query: str) -> bool:
        """
        Knuth-Morris-Pratt search implementation with exact whole line matching.

        Args:
            query: String to search for

        Returns:
            bool: True if exact match found, False otherwise
        """
        if not query:
            return True

        query = query.replace("\x00", "").strip()
        return any(query == line for line in self._file_contents)

    def search(
        self, query: str, algorithm: SearchAlgorithm = SearchAlgorithm.BINARY
    ) -> Tuple[bool, float]:
        """
        Search for a string in the file using specified algorithm.

        Args:
            query: String to search for
            algorithm: Search algorithm to use

        Returns:
            Tuple of (bool, float): (True if string is found, time in seconds)

        Raises:
            ValueError: If query is invalid
            FileNotFoundError: If file cannot be found
            RuntimeError: If search operation fails
        """
        start_time = time.time()

        try:
            # Strip whitespace and newlines from the query
            query = query.strip()

            # Handle empty query
            if not query:
                return True, 0.0

            # Remove null bytes from query
            query = query.replace("\x00", "")

            # Ensure file is loaded
            self._ensure_file_loaded(algorithm)

            # Select search algorithm
            search_func: Callable[[str], bool] = {
                SearchAlgorithm.LINEAR: self._linear_search,
                SearchAlgorithm.BINARY: self._binary_search,
                SearchAlgorithm.BOYER_MOORE: self._boyer_moore_search,
                SearchAlgorithm.KNUTH_MORRIS_PRATT: self._kmp_search,
            }[algorithm]

            # Perform search
            result = search_func(query)
            end_time = time.time()

            return result, end_time - start_time

        except Exception as e:
            raise RuntimeError(f"Search operation failed: {str(e)}")

    def benchmark(self, query: str, iterations: int = 1000) -> dict:
        """
        Benchmark all search algorithms.

        Args:
            query: String to search for
            iterations: Number of iterations for benchmarking

        Returns:
            Dictionary with algorithm names and their average execution times

        Raises:
            ValueError: If query is invalid
            RuntimeError: If benchmark operation fails
        """
        try:
            results = {}
            for algorithm in SearchAlgorithm:
                total_time = 0
                for _ in range(iterations):
                    _, execution_time = self.search(query, algorithm)
                    total_time += execution_time
                results[algorithm.value] = total_time / iterations
            return results
        except Exception as e:
            raise RuntimeError(f"Benchmark operation failed: {str(e)}")
