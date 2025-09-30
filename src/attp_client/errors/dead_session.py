class DeadSessionError(Exception):
    def __init__(self, organization_id: int) -> None:
        super().__init__()
        self.organization_id = organization_id
    
    def __str__(self) -> str:
        return f"Cannot perform any actions over dead ATTP session (organization_id={self.organization_id})"