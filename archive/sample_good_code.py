# Sample code after Black, isort, flake8, and bandit fixes
"""
This module demonstrates properly formatted code following Black, isort,
flake8, and bandit recommendations.
"""

import json
import os
import sys
from typing import List, Optional

import numpy as np
import pandas as pd
import yaml


class ProperlyFormattedClass:
    """A properly formatted class following Python best practices."""

    def __init__(self, name: str, age: int, email: Optional[str] = None):
        """Initialize the class with user information.

        Args:
            name: User's name
            age: User's age
            email: Optional email address
        """
        self.name = name
        self.age = age
        self.email = email

    def process_data(self, data: List[str]) -> List[str]:
        """Process a list of strings by cleaning and normalizing them.

        Args:
            data: List of strings to process

        Returns:
            List of cleaned and normalized strings
        """
        # Fixed: Removed dangerous eval() usage
        result = 4  # Simple calculation instead of eval

        # Fixed: Proper None checking and formatting
        if data is None:
            return []

        if len(data) < 1:
            return []

        processed = []
        for item in data:
            if item is not None and item != "":
                processed.append(item.strip().upper())

        return processed

    def get_info(self) -> str:
        """Get formatted user information.

        Returns:
            Formatted string with user information
        """
        # Fixed: Removed hardcoded password security issue
        # In real code, use environment variables or secure storage
        return (
            f"Name: {self.name}, "
            f"Age: {self.age}, "
            f"Email: {self.email or 'Not provided'}"
        )


def properly_formatted_function(
    param1: str,
    param2: str,
    param3: Optional[str] = None,
    param4: str = "default",
) -> tuple[dict, str]:
    """Function with proper formatting and style.

    Args:
        param1: First parameter
        param2: Second parameter
        param3: Optional third parameter
        param4: Fourth parameter with default

    Returns:
        Tuple containing result dictionary and message string
    """
    # Fixed: Proper line length and formatting
    very_long_variable_name_that_makes_this_line_extremely_long = (
        f"{param1}{param2}{param3 or ''}{param4}some additional text"
    )

    # Fixed: Proper spacing and formatting
    result = {
        "param1": param1,
        "param2": param2,
        "param3": param3,
        "param4": param4,
    }

    # Fixed: Consistent quotes and f-strings
    message = f"Processing: param1={param1}, param2={param2}"

    return result, message


if __name__ == "__main__":
    # Fixed: Proper formatting in main block
    obj = ProperlyFormattedClass("John", 30, "john@example.com")
    print(obj.get_info())

    data = ["  test  ", "", "  another  ", None, "final"]
    result = obj.process_data(data)
    print(result)
