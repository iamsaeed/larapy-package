"""
Base Command Class

This module provides the base command class for CLI commands.
"""

import sys
import argparse
from abc import ABC, abstractmethod
from typing import Any, Dict, List


class Command(ABC):
    """Base class for CLI commands."""
    
    name: str = ""
    description: str = ""
    
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            prog=self.name,
            description=self.description
        )
    
    def add_argument(self, *args, **kwargs):
        """Add an argument to the command parser."""
        return self.parser.add_argument(*args, **kwargs)
    
    def parse_args(self, args: List[str] = None) -> Dict[str, Any]:
        """Parse command line arguments."""
        if args is None:
            args = sys.argv[1:]
        
        parsed_args = self.parser.parse_args(args)
        return vars(parsed_args)
    
    @abstractmethod
    def handle(self, **options):
        """
        Handle the command execution.
        
        Args:
            **options: Parsed command options
        """
        pass
    
    def info(self, message: str):
        """Print an info message."""
        print(f"ℹ️  {message}")
    
    def warning(self, message: str):
        """Print a warning message."""
        print(f"⚠️  {message}")
    
    def error(self, message: str):
        """Print an error message."""
        print(f"❌ {message}", file=sys.stderr)
    
    def success(self, message: str):
        """Print a success message."""
        print(f"✅ {message}")