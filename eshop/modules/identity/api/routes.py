from fastapi import APIRouter, Depends, HTTPException, status
from ..application.commands import RegisterUserCommand, RegisterUserResult
from ..application.handlers import RegisterUserHandler
from sqlalchemy.ext.asyncio import AsyncSession
from ..infrastructure.repository import UserRepository
from ..infrastructure.models import UserModel
from eshop.config.db import get_async_session

router = APIRouter()

# Dependency to get handler
async def get_register_user_handler(session: AsyncSession = Depends(get_async_session)):
    repo = UserRepository(session)
    return RegisterUserHandler(repo)

@router.post("/register", response_model=RegisterUserResult, status_code=status.HTTP_201_CREATED)
async def register_user(
    command: RegisterUserCommand,
    handler: RegisterUserHandler = Depends(get_register_user_handler),
):
    try:
        return await handler.handle(command)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) 