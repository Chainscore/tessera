from jam.config.logging import Theme, theme_choices

def help_theme():
    """Show help for the --theme option."""
    print("\nAvailable themes for --theme:")
    for theme in Theme:
        print(f"  {theme.name.lower():<10}")

def help_validator_index():
    """Show help for the --validator_index option."""
    ...

def help_temp_db():
    """Show help for the --temp_db flag."""
    ...
