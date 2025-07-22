from pydantic import BaseModel, EmailStr

class RegisterUserCommand(BaseModel):
    email: EmailStr
    password: str

class RegisterUserResult(BaseModel):
    id: str
    email: EmailStr
    created_at: str 