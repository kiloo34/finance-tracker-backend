from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from .base_repo import CRUDBase
from ..models import User
from ..schemas import UserCreate
from ..core import security

class RepositoryUser(CRUDBase[User, UserCreate, UserCreate]):
    async def get_by_username(self, db: AsyncSession, username: str) -> User | None:
        result = await db.execute(select(self.model).filter(self.model.username == username))
        return result.scalars().first()

    async def get_by_login_identifier(self, db: AsyncSession, identifier: str) -> User | None:
        """Find user by username, email, or phone_number"""
        result = await db.execute(
            select(self.model).filter(
                or_(
                    self.model.username == identifier,
                    self.model.email == identifier,
                    self.model.phone_number == identifier
                )
            )
        )
        return result.scalars().first()
        
    async def create_user(self, db: AsyncSession, obj_in: UserCreate) -> User:
        hashed_password = security.get_password_hash(obj_in.password)
        db_user = self.model(
            username=obj_in.username,
            email=obj_in.email,
            phone_number=obj_in.phone_number,
            hashed_password=hashed_password
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user

user_repo = RepositoryUser(User)
