from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from .models import UserModel
from uuid import UUID

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_user(self, user: UserModel):
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_by_email(self, email: str):
        result = await self.session.execute(select(UserModel).where(UserModel.email == email))
        return result.scalars().first() 