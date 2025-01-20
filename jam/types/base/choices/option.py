from typing import Any, Type
from jam.types.base.choices.choice import Choice, decodable_choice
from jam.types.base.null import Null, Nullable
from jam.utils.codec.codable import Codable
from jam.utils.codec.json.json_serializable import JsonSerializable

class Option(Choice):
    """
    An option is a choice that can be either None or a value.
    """
    def __init__(self, initial: Codable = Null):
        super().__init__(initial)

    @classmethod
    def from_json(cls, data: Any) -> 'Option':
        """Create from JSON representation."""
        if data is None:
            return cls(Nullable())
        value = cls.types[1].from_json(data)
        return cls(value)
    
    def to_json(self) -> Any:
        """Convert to JSON representation."""
        if isinstance(self.value, Null):
            return None
        return JsonSerializable.to_json(self.value)

def decodable_option(optional_type: Type[Codable]) -> Type[Option]:
    return decodable_choice([Nullable, optional_type])