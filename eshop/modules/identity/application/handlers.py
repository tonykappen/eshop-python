from ..domain.user import User
from ..infrastructure.repository import UserRepository
from ..infrastructure.security import hash_password
from .commands import RegisterUserCommand, RegisterUserResult
from sqlalchemy.exc import IntegrityError
from ..infrastructure.models import UserModel
from datetime import datetime

class RegisterUserHandler:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def handle(self, command: RegisterUserCommand) -> RegisterUserResult:
        # Check for existing user
        existing = await self.repository.get_by_email(command.email)
        if existing:
            raise ValueError("User with this email already exists")
        # Hash password
        hashed = hash_password(command.password)
        # Create SQLAlchemy model
        user_model = UserModel(
            email=command.email,
            hashed_password=hashed,
            created_at=datetime.utcnow(),
        )
        user = await self.repository.add_user(user_model)
        return RegisterUserResult(
            id=str(user.id),
            email=user.email,
            created_at=user.created_at.isoformat(),
        ) 