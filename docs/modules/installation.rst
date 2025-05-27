Installation
============

This guide will help you set up your development environment for working with Tessera.

Prerequisites
------------

* Python 3.11 or higher
* Poetry (Python dependency management tool)
* Git

System Dependencies
----------------

Before installing Tessera, ensure you have the following system dependencies:

1. Python 3.11+::

    # On macOS using brew
    brew install python@3.11

    # On Ubuntu/Debian
    sudo apt install python3.11 python3.11-dev

2. Poetry::

    curl -sSL https://install.python-poetry.org | python3 -

Installation Steps
---------------

1. Clone the Repository::

    git clone https://github.com/chainscore/tessera.git
    cd tessera

2. Install Dependencies::

    poetry install

This will install all required packages including:

* Core Dependencies:
    - aiohappyeyeballs==2.4.4
    - aiohttp==3.11.11
    - aiosignal==1.3.2
    - annotated-types==0.7.0
    - astroid==2.15.8

* Development Dependencies:
    - pytest==7.3.1
    - pytest-cov==6.0.0
    - flake8==4.0.1
    - black==23.12.1
    - isort==5.13.2
    - pre-commit==4.0.1
    - sphinx==8.1.3

3. Set Up Pre-commit Hooks::

    poetry run pre-commit install

Development Environment
--------------------

1. Activate Poetry Shell::

    poetry shell

2. Run Tests::

    pytest

3. Format Code::

    black .
    isort .

4. Lint Code::

    flake8

IDE Setup
--------

For the best development experience, we recommend:

1. VS Code with these extensions:
    * Python
    * Pylance
    * Black Formatter
    * isort

2. PyCharm with:
    * Poetry plugin
    * Black plugin
    * isort plugin

Troubleshooting
-------------

Common Issues:

1. Poetry Installation::

    # If poetry install fails, try:
    poetry update
    poetry install --no-cache

2. Python Version::

    # Verify Python version:
    python --version
    
    # If wrong version:
    poetry env use python3.11

3. Dependencies::

    # Clear poetry cache:
    poetry cache clear . --all 