from dataclasses import dataclass, is_dataclass, Field, field
from typing import Any, Dict, Type, TypeVar, Optional, get_type_hints
from .serde import JsonSerde, JsonFieldMetadata

T = TypeVar('T')

def json_field(
    *,
    name: Optional[str] = None,
    skip_if_none: bool = False,
) -> Any:
    """
    Decorator for dataclass fields to customize JSON serialization.
    
    Args:
        name: Custom JSON field name
        skip_if_none: Whether to skip this field when it's None
    """
    # Only include non-None values in metadata
    metadata = {}
    if name is not None:
        metadata['json_name'] = name
    if skip_if_none:
        metadata['skip_if_none'] = skip_if_none
    
    return field(metadata=metadata, default=None)

def json_serializable(cls: Type[T]) -> Type[T]:
    """
    Decorator to make a class JSON serializable.
    
    This decorator:
    1. Makes the class use JsonSerde
    2. For dataclasses, ensures proper field metadata handling
    """
    # If it's not a dataclass, make it one
    if not is_dataclass(cls):
        cls = dataclass(cls)
    
    # Create a new class that includes JsonSerde
    bases = cls.__bases__
    # If not already in the MRO
    if JsonSerde not in cls.__mro__:
        bases = (JsonSerde,) + bases  # Add JsonSerde only if not present
    
    # Create new class dict with all attributes
    namespace = {
        '__module__': cls.__module__,
        '__qualname__': cls.__qualname__,
        '__annotations__': cls.__annotations__,
        '__doc__': cls.__doc__,
    }
    
    # Copy all class attributes
    for name, attr in cls.__dict__.items():
        if name not in ('__dict__', '__weakref__'):
            namespace[name] = attr
    
    # Create the new class
    JsonSerializableClass = type(cls.__name__, bases, namespace)
    
    # Cache type hints
    JsonSerializableClass.__json_type_hints__ = get_type_hints(cls)
    
    return JsonSerializableClass

def json_field_metadata(
    field_name: str,
    *,
    json_name: Optional[str] = None,
    skip_if_none: bool = False,
) -> Dict[str, Any]:
    """
    Create metadata for a JSON field.
    
    Args:
        field_name: Name of the field in the class
        json_name: Custom name to use in JSON
        skip_if_none: Whether to skip this field when it's None
    """
    metadata = {}
    if json_name is not None:
        metadata['json_name'] = json_name
    if skip_if_none:
        metadata['skip_if_none'] = skip_if_none
    return metadata

def with_json_metadata(**field_metadata: Dict[str, Any]):
    """
    Class decorator to add JSON metadata to fields.
    
    Usage:
        @with_json_metadata(
            field1={'name': 'json_field1', 'skip_if_none': True},
            field2={'name': 'json_field2'}
        )
        class MyClass:
            field1: str
            field2: str
    """
    def decorator(cls: Type[T]) -> Type[T]:
        # First make sure it's a dataclass
        if not is_dataclass(cls):
            cls = dataclass(cls)
        
        # Process each field's metadata
        for field_name, metadata in field_metadata.items():
            # Convert metadata to our standard format
            field_meta = {}
            if 'name' in metadata:
                field_meta['json_name'] = metadata['name']
            if metadata.get('skip_if_none', False):
                field_meta['skip_if_none'] = True
            
            # Get the field from __dataclass_fields__
            if field_name in cls.__dataclass_fields__:
                field_obj = cls.__dataclass_fields__[field_name]
                # Update field metadata using object.__setattr__
                object.__setattr__(field_obj, 'metadata', field_meta)
            else:
                raise ValueError(f"Field '{field_name}' not found in dataclass")
        
        return cls
    return decorator 