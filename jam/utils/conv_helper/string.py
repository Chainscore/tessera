class StrConversion:
    @staticmethod
    def str_to_bytes(value: str, encoding: str = 'utf-8') -> bytes:
        """Convert string to bytes"""
        return value.encode(encoding)

    @staticmethod
    def bytes_to_str(value: bytes, encoding: str = 'utf-8') -> str:
        """Convert bytes to string"""
        return value.decode(encoding)
