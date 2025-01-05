"""
User service module
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..models.user import User
from ..schemas.user import UserCreate, UserUpdate


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_users(self) -> list[User]:
        result = await self.session.execute(select(User))
        return result.scalars().all()

    async def get_user(self, user_id: int) -> User | None:
        result = await self.session.execute(select(User).filter(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).filter(User.email == email))
        return result.scalar_one_or_none()

    async def create_user(self, user_data: UserCreate) -> User:
        user = User(**user_data.dict())
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update_user(self, user_id: int, user_data: UserUpdate) -> User | None:
        user = await self.get_user(user_id)
        if user:
            for field, value in user_data.dict(exclude_unset=True).items():
                setattr(user, field, value)
            await self.session.commit()
            await self.session.refresh(user)
        return user

    async def delete_user(self, user_id: int) -> bool:
        user = await self.get_user(user_id)
        if user:
            await self.session.delete(user)
            await self.session.commit()
            return True
        return False
