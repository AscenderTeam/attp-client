class SerializationError(Exception):
    def __init__(self, detail: str) -> None:
        self.detail = detail
    
    def __str__(self) -> str:
        return f"Serialization fault: {self.detail}"