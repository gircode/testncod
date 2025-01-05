"""用户服务"""

import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from passlib.hash import pbkdf2_sha256
from ncod.core.logger import setup_logger
from ncod.core.db.transaction import transaction_manager
from ncod.master.models.user import User
from ncod.master.models.role import Role
from ncod.master.models.organization import Organization

logger = setup_logger("user_service")


class UserService:
    """用户服务"""

    def __init__(self):
        self.transaction = transaction_manager

    async def create_user(self, data: Dict) -> Tuple[bool, str, Optional[User]]:
        """创建用户"""
        try:
            async with self.transaction.transaction() as session:
                # 检查用户名和邮箱是否已存在
                if await User.get_by_username(session, data["username"]):
                    return False, "Username already exists", None
                if await User.get_by_email(session, data["email"]):
                    return False, "Email already exists", None

                # 创建用户
                user = User(
                    username=data["username"],
                    email=data["email"],
                    password_hash=self._hash_password(data["password"]),
                    mac_address=data.get("mac_address"),
                )

                # 添加角色
                if "roles" in data:
                    roles = await self._get_roles(session, data["roles"])
                    user.roles.extend(roles)

                # 添加组织
                if "organizations" in data:
                    orgs = await self._get_organizations(session, data["organizations"])
                    user.organizations.extend(orgs)

                session.add(user)
                await session.commit()
                await session.refresh(user)

                return True, "User created successfully", user
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return False, str(e), None

    async def update_user(
        self, user_id: str, data: Dict
    ) -> Tuple[bool, str, Optional[User]]:
        """更新用户"""
        try:
            async with self.transaction.transaction() as session:
                user = await session.get(User, user_id)
                if not user:
                    return False, "User not found", None

                # 更新基本信息
                if "email" in data:
                    existing = await User.get_by_email(session, data["email"])
                    if existing and existing.id != user_id:
                        return False, "Email already exists", None
                    user.email = data["email"]

                if "password" in data:
                    user.password_hash = self._hash_password(data["password"])

                if "mac_address" in data:
                    user.mac_address = data["mac_address"]

                if "is_active" in data:
                    user.is_active = data["is_active"]

                # 更新角色
                if "roles" in data:
                    roles = await self._get_roles(session, data["roles"])
                    user.roles = roles

                # 更新组织
                if "organizations" in data:
                    orgs = await self._get_organizations(session, data["organizations"])
                    user.organizations = orgs

                await session.commit()
                await session.refresh(user)

                return True, "User updated successfully", user
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            return False, str(e), None

    async def delete_user(self, user_id: str) -> Tuple[bool, str]:
        """删除用户"""
        try:
            async with self.transaction.transaction() as session:
                user = await session.get(User, user_id)
                if not user:
                    return False, "User not found"

                # 软删除
                user.soft_delete()
                await session.commit()

                return True, "User deleted successfully"
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            return False, str(e)

    async def get_user(self, user_id: str) -> Optional[Dict]:
        """获取用户"""
        try:
            async with self.transaction.transaction() as session:
                user = await session.get(User, user_id)
                return user.to_dict() if user else None
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None

    async def list_users(self, filters: Optional[Dict] = None) -> List[Dict]:
        """获取用户列表"""
        try:
            async with self.transaction.transaction() as session:
                query = select(User)

                if filters:
                    if "organization_id" in filters:
                        query = query.join(User.organizations).where(
                            Organization.id == filters["organization_id"]
                        )
                    if "role" in filters:
                        query = query.join(User.roles).where(
                            Role.name == filters["role"]
                        )
                    if "is_active" in filters:
                        query = query.where(User.is_active == filters["is_active"])

                result = await session.execute(query)
                users = result.scalars().all()
                return [user.to_dict() for user in users]
        except Exception as e:
            logger.error(f"Error listing users: {e}")
            return []

    def _hash_password(self, password: str) -> str:
        """哈希密码"""
        return pbkdf2_sha256.hash(password)

    def verify_password(self, password: str, password_hash: str) -> bool:
        """验证密码"""
        return pbkdf2_sha256.verify(password, password_hash)

    async def _get_roles(self, session, role_names: List[str]) -> List[Role]:
        """获取角色列表"""
        try:
            stmt = select(Role).where(Role.name.in_(role_names))
            result = await session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting roles: {e}")
            return []

    async def _get_organizations(
        self, session, org_ids: List[str]
    ) -> List[Organization]:
        """获取组织列表"""
        try:
            stmt = select(Organization).where(Organization.id.in_(org_ids))
            result = await session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting organizations: {e}")
            return []


# 创建全局用户服务实例
user_service = UserService()
