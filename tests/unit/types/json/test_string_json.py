import pytest
from jam.types.base.string import String
from jam.utils.json.serde import JsonDeserializationError
def test_string_json_serialization():
    # Test basic string
    s = String("Hello, World!")
    json_str = s.to_json()
    assert json_str == "Hello, World!"
    assert String.from_json(json_str, ) == s
    
    # Test empty string
    empty = String("")
    json_empty = empty.to_json()
    assert json_empty == ""
    assert String.from_json(json_empty, ) == empty
    
    # Test string with special characters
    special = String("Hello\n\t世界")
    json_special = special.to_json()
    assert json_special == "Hello\n\t世界"
    assert String.from_json(json_special, ) == special
    
    # Test string with emojis
    emoji = String("Hello 👋 World 🌍")
    json_emoji = emoji.to_json()
    assert json_emoji == "Hello 👋 World 🌍"
    assert String.from_json(json_emoji, ) == emoji

def test_string_json_invalid_input():
    # Test with invalid input types
    with pytest.raises(JsonDeserializationError):
        String.from_json(123, )  # Integer instead of str
    
    with pytest.raises(JsonDeserializationError):
        String.from_json(None, )  # None instead of str
    
    with pytest.raises(JsonDeserializationError):
        String.from_json(True, )  # Boolean instead of str
    
    with pytest.raises(JsonDeserializationError):
        String.from_json(["not", "a", "string"], )  # List instead of str

def test_string_json_roundtrip():
    test_strings = [
        "Simple string",
        "",  # Empty string
        "Multi\nline\tstring",  # Control characters
        "Unicode: 你好世界",  # Unicode characters
        "Emoji: 🌟✨🌙",  # Emojis
        "Mixed: Hello 世界 👋"  # Mixed content
    ]
    
    for test_str in test_strings:
        original = String(test_str)
        json_data = original.to_json()
        reconstructed = String.from_json(json_data, )
        assert original == reconstructed
        assert isinstance(reconstructed, String)
        assert str(reconstructed) == test_str 