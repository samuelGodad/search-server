"""
File search functionality module.
"""
import time
from pathlib import Path
from typing import Tuple, Optional


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

    def _load_file(self) -> list[str]:
        """
        Load file contents.

        Returns:
            List of lines from the file
        """
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")
        
        with open(self.file_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f]

    def search(self, query: str) -> Tuple[bool, float]:
        """
        Search for a string in the file.

        Args:
            query: String to search for

        Returns:
            Tuple of (found: bool, execution_time: float)
        """
        start_time = time.time()

        if self.reread_on_query or self._file_contents is None:
            self._file_contents = self._load_file()

        # Strip whitespace and newlines from the query
        query = query.strip()
        
        # Check if query exists as a complete line
        found = any(query == line for line in self._file_contents)
        
        execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        return found, execution_time 