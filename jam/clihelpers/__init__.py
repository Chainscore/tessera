from jam.clihelpers.helpertexts import help_theme
# from jam.helptexts.validator_index import help_validator_index
# from jam.helptexts.temp_db import help_temp_db

HELP_TOPICS = {
    "theme": help_theme,
    # "validator_index": help_validator_index,
    # "temp_db": help_temp_db,
}

def show_help_topic(topic: str):
    func = HELP_TOPICS.get(topic.lower())
    if func:
        func()
    else:
        print(f"\nUnknown help topic: {topic}")
        print("Available topics:", ", ".join(HELP_TOPICS))
