from typing import Type
from jam.types.base.choices.choice import Choice, decodable_choice
from jam.types.base.null import Null, Nullable
from jam.utils.codec.codable import Codable

class Option(Choice):
    """
    An option is a choice that can be either None or a value.
    """

    def __init__(self, initial: Codable = Null):
        super().__init__(initial)

def decodable_option(optional_type: Type[Codable]) -> Type[Option]:
    return decodable_choice([Nullable, optional_type])