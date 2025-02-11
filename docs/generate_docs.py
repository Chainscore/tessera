#!/usr/bin/env python3
import os
import sys
from pathlib import Path
from typing import List, Set

def clean_docstring(docstring: str) -> str:
    """Clean up docstring formatting issues."""
    if not docstring:
        return ""
    
    # Split into lines and remove empty lines at start/end
    lines = docstring.strip().split('\n')
    
    # Remove common leading whitespace from every line
    def measure_indent(line: str) -> int:
        return len(line) - len(line.lstrip())
    
    # Find minimum indent of non-empty lines
    indents = [measure_indent(line) for line in lines if line.strip()]
    if indents:
        min_indent = min(indents)
        lines = [line[min_indent:] if line.strip() else '' for line in lines]
    
    # Ensure proper spacing around sections
    formatted_lines = []
    for i, line in enumerate(lines):
        if i > 0 and line.strip() and line[0].isalpha() and lines[i-1].strip():
            # Add blank line before new sections
            formatted_lines.append('')
        formatted_lines.append(line)
        if line.strip() and line[-1] == ':':
            # Add blank line after section headers
            formatted_lines.append('')
    
    return '\n'.join(formatted_lines)

def create_sphinx_structure(docs_dir: Path, force: bool = False) -> None:
    """Create basic Sphinx directory structure.
    
    Args:
        docs_dir: Path to the docs directory
        force: If True, overwrite existing files
    """
    # Create required directories
    (docs_dir / '_static').mkdir(parents=True, exist_ok=True)
    (docs_dir / '_templates').mkdir(parents=True, exist_ok=True)
    (docs_dir / '_build').mkdir(parents=True, exist_ok=True)
    (docs_dir / 'modules').mkdir(parents=True, exist_ok=True)

def generate_root_index_rst(docs_dir: Path, force: bool = False) -> None:
    """Generate the root index.rst file if it doesn't exist.
    
    Args:
        docs_dir: Path to the docs directory
        force: If True, overwrite existing file
    """
    index_path = docs_dir / 'index.rst'
    if index_path.exists() and not force:
        print(f"Skipping existing file: {index_path}")
        return

    content = """
Welcome to Tessera Documentation
==============================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   modules/jam/index

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
"""
    with open(index_path, 'w') as f:
        f.write(content.lstrip())

def setup_sphinx_config(docs_dir: Path, force: bool = False) -> None:
    """Generate/update conf.py with necessary settings.
    
    Args:
        docs_dir: Path to the docs directory
        force: If True, overwrite existing file
    """
    conf_path = docs_dir / 'conf.py'
    if conf_path.exists() and not force:
        print(f"Skipping existing file: {conf_path}")
        return

    conf_content = '''
import os
import sys
sys.path.insert(0, os.path.abspath('..'))

project = 'Tessera'
copyright = '2025, Chainscore Labs'
author = 'Chainscore Labs'

# The full version, including alpha/beta/rc tags
release = '0.1.0'

# Add any Sphinx extension module names here
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
]

# Add any paths that contain templates here
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# The theme to use for HTML and HTML Help pages
html_theme = 'alabaster'

# Add any paths that contain custom static files
html_static_path = ['_static']

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = True
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True
napoleon_use_ivar = True
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_type_aliases = None

# AutoDoc settings
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}

# Intersphinx settings
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
}
'''
    with open(conf_path, 'w') as f:
        f.write(conf_content.lstrip())

def generate_package_rst(package_path: Path, display_name: str, doc_path: Path, force: bool = False) -> None:
    """Generate RST content for a package.
    
    Args:
        package_path: The real filesystem path of the package
        display_name: The dotted name of the package
        doc_path: Path where the RST file should be written
        force: If True, overwrite existing file
    """
    index_path = doc_path / 'index.rst'
    if index_path.exists() and not force:
        print(f"Skipping existing file: {index_path}")
        return

    subpackages = []
    submodules = []
    
    for item in package_path.iterdir():
        if item.is_dir() and (item / '__init__.py').exists():
            if not item.name.startswith('_'):
                subpackages.append(item.name)
        elif item.is_file() and item.suffix == '.py' and item.name != '__init__.py':
            if not item.name.startswith('_'):
                submodules.append(item.stem)
    
    subpackages.sort()
    submodules.sort()
    
    content = [
        f'{display_name} package',
        '=' * (len(display_name) + 8),
        ''
    ]
    
    if subpackages:
        content.extend([
            'Subpackages',
            '-----------',
            '',
            '.. toctree::',
            '   :maxdepth: 2',
            ''
        ])
        for pkg in subpackages:
            content.append(f'   {pkg}/index')
        content.append('')
    
    if submodules:
        content.extend([
            'Submodules',
            '----------',
            '',
            '.. toctree::',
            '   :maxdepth: 1',
            ''
        ])
        for mod in submodules:
            content.append(f'   {mod}')
        content.append('')
    
    content.extend([
        'Module Contents',
        '--------------',
        '',
        f'.. automodule:: {display_name}',
        '   :members:',
        '   :undoc-members:',
        '   :show-inheritance:',
        '   :special-members: __init__',
        ''
    ])
    
    with open(index_path, 'w') as f:
        f.write('\n'.join(content))

def generate_module_rst(module_path: Path, display_name: str, doc_path: Path, force: bool = False) -> None:
    """Generate RST content for a module.
    
    Args:
        module_path: The real filesystem path of the module
        display_name: The full dotted module name
        doc_path: Path where the RST file should be written
        force: If True, overwrite existing file
    """
    rst_path = doc_path / f'{module_path.stem}.rst'
    if rst_path.exists() and not force:
        print(f"Skipping existing file: {rst_path}")
        return

    content = [
        f'{display_name} module',
        '=' * (len(display_name) + 7),
        '',
        f'.. automodule:: {display_name}',
        '   :members:',
        '   :undoc-members:',
        '   :show-inheritance:',
        '   :special-members: __init__',
        ''
    ]
    
    with open(rst_path, 'w') as f:
        f.write('\n'.join(content))

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Generate Sphinx documentation structure')
    parser.add_argument('--force', '-f', action='store_true', 
                       help='Force overwrite existing files')
    args = parser.parse_args()

    # Set project_root to be the parent of the docs folder
    project_root = Path(__file__).parent.parent
    docs_dir = project_root / 'docs'
    modules_dir = docs_dir / 'modules'
    modules_dir.mkdir(parents=True, exist_ok=True)
    
    # Create basic Sphinx structure and files
    create_sphinx_structure(docs_dir, args.force)
    generate_root_index_rst(docs_dir, args.force)
    setup_sphinx_config(docs_dir, args.force)
    
    # The source directory is the 'jam' folder in the project root
    src_dir = project_root / 'jam'
    if not src_dir.exists():
        print(f"Error: Source directory not found at {src_dir}")
        print("Please ensure the 'jam' package is in the correct location")
        sys.exit(1)
    
    # Walk through the 'jam' package and generate rst files
    for root, dirs, files in os.walk(src_dir):
        root_path = Path(root)
        # Skip __pycache__ and hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('_')]
        
        # Compute the display name
        if root_path == src_dir:
            pkg_display_name = "jam"
            rel_path_docs = Path("jam")
        else:
            pkg_display_name = "jam." + str(root_path.relative_to(src_dir)).replace(os.sep, '.')
            rel_path_docs = Path("jam") / root_path.relative_to(src_dir)
        
        doc_path = modules_dir / rel_path_docs
        doc_path.mkdir(parents=True, exist_ok=True)
        
        # Generate package index.rst if this is a package
        if (root_path / '__init__.py').exists():
            generate_package_rst(root_path, pkg_display_name, doc_path, args.force)
        
        # Generate rst file for each module
        for file in files:
            if file.endswith('.py') and not file.startswith('_'):
                file_path = root_path / file
                if root_path == src_dir:
                    module_display_name = f"jam.{file[:-3]}"
                else:
                    module_display_name = f"{pkg_display_name}.{file[:-3]}"
                generate_module_rst(file_path, module_display_name, doc_path, args.force)
    
    print("\nDocumentation structure updated!")
    print("\nTo build the documentation:")
    print("1. cd docs")
    print("2. sphinx-autobuild . _build/html")

if __name__ == '__main__':
    main() 