from typing import Optional, TypeVar
from jam.utils.codec.base import Codable
from jam.utils.codec.composite import ChoiceCodec

T = TypeVar('T')

class Option(Codable, Optional):
    """
    An optional value.
    """
    def __init__(self, value: Optional[Codable]):
        self.codec = ChoiceCodec
