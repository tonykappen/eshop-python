from datetime import datetime
from pydantic import BaseModel, EmailStr
from uuid import UUID, uuid4

class User(BaseModel):
    id: UUID
    email: EmailStr
    hashed_password: str
    created_at: datetime

    @classmethod
    def create(cls, email: str, hashed_password: str) -> "User":
        return cls(
            id=uuid4(),
            email=email,
            hashed_password=hashed_password,
            created_at=datetime.utcnow(),
        ) 