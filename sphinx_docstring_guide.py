"""
Sphinx Docstring Format Guide for ekko Project

This file demonstrates the Sphinx docstring format that we'll use throughout the project.
"""

from collections.abc import Generator
from typing import Any


class ExampleClass:
    """
    A example class demonstrating Sphinx docstring format.
    
    This class shows how to properly document classes, methods, and attributes
    using the Sphinx/reStructuredText format.
    
    :param name: The name of the example
    :type name: str
    :param value: An optional numeric value
    :type value: Optional[int]
    
    :ivar name: Stores the name
    :vartype name: str
    :ivar value: Stores the numeric value
    :vartype value: Optional[int]
    
    :Example:
    
    >>> example = ExampleClass("test", 42)
    >>> example.process()
    'test: 42'
    
    .. note::
       This is a note about the class
       
    .. warning::
       This is a warning about potential issues
    """
    
    def __init__(self, name: str, value: int | None = None):
        """
        Initialize the ExampleClass.
        
        :param name: The name to store
        :type name: str
        :param value: Optional numeric value, defaults to None
        :type value: Optional[int], optional
        """
        self.name = name
        self.value = value
    
    def process(self) -> str:
        """
        Process the stored data and return a formatted string.
        
        :return: A formatted string containing name and value
        :rtype: str
        
        :raises ValueError: If name is empty
        
        :Example:
        
        >>> obj = ExampleClass("test", 42)
        >>> obj.process()
        'test: 42'
        """
        if not self.name:
            raise ValueError("Name cannot be empty")
        return f"{self.name}: {self.value}"
    
    def complex_method(
        self,
        items: list[str],
        options: dict[str, Any] | None = None
    ) -> Generator[str]:
        """
        A complex method with multiple parameters and a generator return type.
        
        :param items: List of items to process
        :type items: List[str]
        :param options: Optional configuration options
        :type options: Optional[Dict[str, Any]]
        
        :yields: Processed items one at a time
        :rtype: Generator[str, None, None]
        
        :raises TypeError: If items is not a list
        :raises KeyError: If required option is missing
        
        .. seealso::
           :meth:`process` - Related processing method
           
        .. versionadded:: 0.2.0
           Added support for options parameter
        """
        if not isinstance(items, list):
            raise TypeError("items must be a list")
            
        for item in items:
            if options and 'prefix' in options:
                yield f"{options['prefix']}{item}"
            else:
                yield item


def standalone_function(text: str, max_length: int = 100) -> str:
    """
    A standalone function demonstrating Sphinx format.
    
    This function truncates text to a maximum length.
    
    :param text: The text to truncate
    :type text: str
    :param max_length: Maximum allowed length, defaults to 100
    :type max_length: int, optional
    
    :return: Truncated text
    :rtype: str
    
    :Example:
    
    >>> standalone_function("Hello world", 5)
    'Hello...'
    """
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


# Conversion mapping from Google/NumPy style to Sphinx
CONVERSION_GUIDE = """
Google Style -> Sphinx Style Conversion:

Args:           -> :param name: description
                   :type name: type

Returns:        -> :return: description
                   :rtype: type

Yields:         -> :yields: description
                   :rtype: type

Raises:         -> :raises ExceptionType: description

Attributes:     -> :ivar name: description
                   :vartype name: type

Example:        -> :Example:
                   
                   >>> code here

Note:           -> .. note::
                      Content here

Warning:        -> .. warning::
                      Content here

See Also:       -> .. seealso::
                      Content here
"""