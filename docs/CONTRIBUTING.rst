Contributing to Documentation
==========================

This guide explains how to write and maintain documentation for the Tessera project.
We use a combination of docstrings and RST files to provide comprehensive documentation.

Documentation Structure
--------------------
Our documentation consists of two main parts:

1. API Documentation (Docstrings):
   - Every module, class, method, and function must have a docstring
   - We use Google-style docstrings
   - Docstrings are processed by Sphinx's autodoc extension

2. Detailed Documentation (RST Files):
   - Located in the `docs/modules/` directory
   - Provides in-depth explanations, examples, and technical details
   - Organized to mirror the package structure

Writing Docstrings
---------------
Follow these guidelines for docstrings:

1. Module Docstrings::

    """
    :mod:`jam.module` --- Module Title
    ================================

    Brief description of the module.

    Core Components:
    * Component1: Description
    * Component2: Description

    Basic Usage::

        from jam.module import Component1

        # Example code
        result = Component1.do_something()
    """

2. Class Docstrings::

    class MyClass:
        """Class description.

        Detailed description of the class functionality.

        Args:
            param1: Description of first parameter
            param2: Description of second parameter

        Attributes:
            attr1: Description of first attribute
            attr2: Description of second attribute

        Examples:
            Basic usage::

                obj = MyClass(param1=1, param2="test")
                result = obj.method()
        """

3. Method/Function Docstrings::

    def my_function(param1: int, param2: str) -> bool:
        """Short description of function.

        Detailed description of what the function does.

        Args:
            param1: Description of first parameter
            param2: Description of second parameter

        Returns:
            Description of return value

        Raises:
            ErrorType: Description of when this error is raised

        Examples:
            Basic usage::

                result = my_function(1, "test")
                assert result is True
        """

Writing RST Documentation
----------------------
For each module, create or update these files:

1. Module Index (`index.rst`)::

    module_name package
    ==================

    Overview
    --------
    Technical description of the module.

    Core Components
    -------------
    * Component1: Description
    * Component2: Description

    Implementation Details
    -------------------
    Detailed technical information.

    Examples
    -------
    Code examples with explanations.

2. Component Documentation::

    component_name module
    ===================

    Technical Details
    --------------
    Implementation specifics.

    Usage Examples
    ------------
    Concrete examples with code.

    Error Handling
    ------------
    Error cases and their handling.

Adding New Documentation
---------------------
When adding a new module:

1. Write comprehensive docstrings in your code
2. Run the documentation generator::

    $ python docs/generate_docs.py

3. Create/edit the RST files in `docs/modules/your/module/`
4. Build and verify the documentation::

    $ cd docs
    $ sphinx-autobuild . _build/html

Documentation Standards
--------------------
1. Technical Focus:
   - Focus on implementation details
   - Provide concrete examples
   - Include error handling cases
   - Show exact byte-level formats where relevant

2. Code Examples:
   - All examples must be runnable
   - Include imports
   - Show expected outputs
   - Cover common use cases

3. Error Handling:
   - Document all possible errors
   - Explain when each error occurs
   - Show how to handle errors properly

4. Type Information:
   - Use type hints consistently
   - Document type constraints
   - Explain type conversions

Building Documentation
-------------------
To build the documentation locally:

1. Install dependencies::

    $ pip install sphinx sphinx-autobuild

2. Build the docs::

    $ cd docs
    $ sphinx-autobuild . _build/html

3. View at http://localhost:8000

Remember to:
- Keep docstrings focused and technical
- Provide detailed RST documentation
- Include runnable examples
- Document error cases
- Maintain type information 