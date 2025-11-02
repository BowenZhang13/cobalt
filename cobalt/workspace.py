"""
Workspace management for file operations
"""

from pathlib import Path
from typing import List, Optional, Tuple, Set
import fnmatch
import re


class Workspace:
    """Manages file operations within a workspace"""
    
    def __init__(self, root: Path, ignore_patterns: List[str] = None):
        """
        Initialize workspace
        
        Args:
            root: Root directory of workspace
            ignore_patterns: Patterns to ignore (gitignore-style)
        """
        self.root = Path(root).resolve()
        self.ignore_patterns = ignore_patterns or []
        
        # Add common ignore patterns if not present
        defaults = ['__pycache__', '*.pyc', '.git', '.venv', 'venv', 'node_modules']
        for pattern in defaults:
            if pattern not in self.ignore_patterns:
                self.ignore_patterns.append(pattern)
    
    def should_ignore(self, path: Path) -> bool:
        """
        Check if path should be ignored
        
        Args:
            path: Path to check
            
        Returns:
            True if should be ignored
        """
        relative = path.relative_to(self.root) if path.is_relative_to(self.root) else path
        path_str = str(relative)
        
        for pattern in self.ignore_patterns:
            # Handle directory patterns
            if pattern.endswith('/'):
                if any(part == pattern.rstrip('/') for part in relative.parts):
                    return True
            # Handle glob patterns
            elif fnmatch.fnmatch(path_str, pattern):
                return True
            # Handle exact matches
            elif pattern in path_str:
                return True
        
        return False
    
    def list_files(self, pattern: str = "*", recursive: bool = True) -> List[Path]:
        """
        List files matching pattern
        
        Args:
            pattern: Glob pattern (e.g., "*.py")
            recursive: Search recursively
            
        Returns:
            List of matching file paths
        """
        files = []
        
        if recursive:
            for path in self.root.rglob(pattern):
                if path.is_file() and not self.should_ignore(path):
                    files.append(path)
        else:
            for path in self.root.glob(pattern):
                if path.is_file() and not self.should_ignore(path):
                    files.append(path)
        
        return sorted(files)
    
    def read_file(self, filepath: str) -> Optional[str]:
        """
        Read file content
        
        Args:
            filepath: Relative path from workspace root
            
        Returns:
            File content or None if error
        """
        try:
            full_path = self.root / filepath
            
            # Security check - ensure path is within workspace
            if not full_path.resolve().is_relative_to(self.root):
                raise ValueError(f"Path {filepath} is outside workspace")
            
            return full_path.read_text(encoding='utf-8')
        
        except UnicodeDecodeError:
            try:
                return full_path.read_text(encoding='latin-1')
            except:
                return None
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            return None
    
    def write_file(self, filepath: str, content: str) -> bool:
        """
        Write content to file
        
        Args:
            filepath: Relative path from workspace root
            content: Content to write
            
        Returns:
            True if successful
        """
        try:
            full_path = self.root / filepath
            
            # Security check
            if not full_path.resolve().is_relative_to(self.root):
                raise ValueError(f"Path {filepath} is outside workspace")
            
            # Create parent directories
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            full_path.write_text(content, encoding='utf-8')
            return True
        
        except Exception as e:
            print(f"Error writing {filepath}: {e}")
            return False
    
    def delete_file(self, filepath: str) -> bool:
        """
        Delete a file
        
        Args:
            filepath: Relative path from workspace root
            
        Returns:
            True if successful
        """
        try:
            full_path = self.root / filepath
            
            if not full_path.resolve().is_relative_to(self.root):
                raise ValueError(f"Path {filepath} is outside workspace")
            
            if full_path.exists():
                full_path.unlink()
                return True
            return False
        
        except Exception as e:
            print(f"Error deleting {filepath}: {e}")
            return False
    
    def file_exists(self, filepath: str) -> bool:
        """Check if file exists"""
        full_path = self.root / filepath
        return full_path.exists() and full_path.is_file()
    
    def search_in_files(self, pattern: str, file_pattern: str = "*.py",
                       case_sensitive: bool = False, regex: bool = False) -> List[Tuple[Path, int, str]]:
        """
        Search for pattern in files
        
        Args:
            pattern: Search pattern
            file_pattern: File glob pattern
            case_sensitive: Case-sensitive search
            regex: Use regex matching
            
        Returns:
            List of (filepath, line_number, line_content) tuples
        """
        results = []
        files = self.list_files(file_pattern)
        
        if regex:
            try:
                flags = 0 if case_sensitive else re.IGNORECASE
                compiled_pattern = re.compile(pattern, flags)
            except re.error as e:
                print(f"Invalid regex pattern: {e}")
                return results
        
        for filepath in files:
            try:
                content = self.read_file(str(filepath.relative_to(self.root)))
                if not content:
                    continue
                
                for i, line in enumerate(content.splitlines(), 1):
                    match = False
                    
                    if regex:
                        match = compiled_pattern.search(line) is not None
                    else:
                        search_line = line if case_sensitive else line.lower()
                        search_pattern = pattern if case_sensitive else pattern.lower()
                        match = search_pattern in search_line
                    
                    if match:
                        results.append((filepath, i, line.strip()))
            
            except Exception as e:
                continue
        
        return results
    
    def get_file_info(self, filepath: str) -> Optional[dict]:
        """
        Get file information
        
        Args:
            filepath: Relative path from workspace root
            
        Returns:
            Dictionary with file info or None
        """
        try:
            full_path = self.root / filepath
            
            if not full_path.exists():
                return None
            
            stat = full_path.stat()
            
            return {
                'path': str(filepath),
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'is_file': full_path.is_file(),
                'extension': full_path.suffix
            }
        
        except Exception as e:
            print(f"Error getting file info: {e}")
            return None
    
    def get_tree(self, max_depth: int = 3) -> str:
        """
        Get directory tree representation
        
        Args:
            max_depth: Maximum depth to traverse
            
        Returns:
            Tree string representation
        """
        def build_tree(path: Path, prefix: str = "", depth: int = 0) -> List[str]:
            if depth >= max_depth:
                return []
            
            lines = []
            try:
                items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
                items = [item for item in items if not self.should_ignore(item)]
                
                for i, item in enumerate(items):
                    is_last = i == len(items) - 1
                    current_prefix = "└── " if is_last else "├── "
                    next_prefix = "    " if is_last else "│   "
                    
                    lines.append(f"{prefix}{current_prefix}{item.name}")
                    
                    if item.is_dir():
                        lines.extend(build_tree(item, prefix + next_prefix, depth + 1))
            
            except PermissionError:
                pass
            
            return lines
        
        tree_lines = [str(self.root)]
        tree_lines.extend(build_tree(self.root))
        return "\n".join(tree_lines)
    
    def count_lines(self, file_pattern: str = "*.py") -> dict:
        """
        Count lines in files
        
        Args:
            file_pattern: File glob pattern
            
        Returns:
            Dictionary with statistics
        """
        total_lines = 0
        total_files = 0
        code_lines = 0
        comment_lines = 0
        blank_lines = 0
        
        files = self.list_files(file_pattern)
        
        for filepath in files:
            content = self.read_file(str(filepath.relative_to(self.root)))
            if not content:
                continue
            
            total_files += 1
            lines = content.splitlines()
            total_lines += len(lines)
            
            for line in lines:
                stripped = line.strip()
                if not stripped:
                    blank_lines += 1
                elif stripped.startswith('#'):
                    comment_lines += 1
                else:
                    code_lines += 1
        
        return {
            'total_files': total_files,
            'total_lines': total_lines,
            'code_lines': code_lines,
            'comment_lines': comment_lines,
            'blank_lines': blank_lines
        }
