from jam.settings import setup_setting


def test_block_production(db_path):
    alice_settings = setup_setting(db_path, 1, port=40000)
