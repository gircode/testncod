"""角色服务"""

from typing import Dict, List, Optional, Tuple
from ncod.core.logger import setup_logger
from ncod.core.db.transaction import transaction_manager
from ncod.master.models.role import Role
from ncod.master.models.permission import Permission

logger = setup_logger("role_service")


class RoleService:
    """角色服务"""

    def __init__(self):
        self.transaction = transaction_manager

    async def create_role(self, data: Dict) -> Tuple[bool, str, Optional[Role]]:
        """创建角色"""
        try:
            async with self.transaction.transaction() as session:
                # 检查角色名是否存在
                if await Role.get_by_name(session, data["name"]):
                    return False, "Role name already exists", None

                # 创建角色
                role = Role(
                    name=data["name"],
                    description=data.get("description"),
                    is_system=data.get("is_system", False),
                )

                # 添加权限
                if "permissions" in data:
                    perms = []
                    for perm_code in data["permissions"]:
                        perm = await Permission.get_by_code(session, perm_code)
                        if perm:
                            perms.append(perm)
                    role.permissions = perms

                session.add(role)
                await session.commit()
                await session.refresh(role)

                return True, "Role created successfully", role
        except Exception as e:
            logger.error(f"Error creating role: {e}")
            return False, str(e), None

    async def update_role(
        self, role_id: str, data: Dict
    ) -> Tuple[bool, str, Optional[Role]]:
        """更新角色"""
        try:
            async with self.transaction.transaction() as session:
                role = await session.get(Role, role_id)
                if not role:
                    return False, "Role not found", None

                # 检查角色名是否重复
                if "name" in data:
                    existing = await Role.get_by_name(session, data["name"])
                    if existing and existing.id != role_id:
                        return False, "Role name already exists", None
                    role.name = data["name"]

                if "description" in data:
                    role.description = data["description"]

                # 更新权限
                if "permissions" in data:
                    perms = []
                    for perm_code in data["permissions"]:
                        perm = await Permission.get_by_code(session, perm_code)
                        if perm:
                            perms.append(perm)
                    role.permissions = perms

                await session.commit()
                await session.refresh(role)

                return True, "Role updated successfully", role
        except Exception as e:
            logger.error(f"Error updating role: {e}")
            return False, str(e), None

    async def delete_role(self, role_id: str) -> Tuple[bool, str]:
        """删除角色"""
        try:
            async with self.transaction.transaction() as session:
                role = await session.get(Role, role_id)
                if not role:
                    return False, "Role not found"

                if role.is_system:
                    return False, "Cannot delete system role"

                await session.delete(role)
                await session.commit()

                return True, "Role deleted successfully"
        except Exception as e:
            logger.error(f"Error deleting role: {e}")
            return False, str(e)

    async def get_role(self, role_id: str) -> Optional[Dict]:
        """获取角色"""
        try:
            async with self.transaction.transaction() as session:
                role = await session.get(Role, role_id)
                return role.to_dict() if role else None
        except Exception as e:
            logger.error(f"Error getting role: {e}")
            return None

    async def list_roles(self, include_system: bool = True) -> List[Dict]:
        """获取角色列表"""
        try:
            async with self.transaction.transaction() as session:
                query = select(Role)
                if not include_system:
                    query = query.where(Role.is_system == False)
                result = await session.execute(query)
                roles = result.scalars().all()
                return [role.to_dict() for role in roles]
        except Exception as e:
            logger.error(f"Error listing roles: {e}")
            return []

    async def get_role_permissions(self, role_name: str) -> List[str]:
        """获取角色权限"""
        try:
            async with self.transaction.transaction() as session:
                role = await Role.get_by_name(session, role_name)
                if not role:
                    return []
                return [p.code for p in role.permissions]
        except Exception as e:
            logger.error(f"Error getting role permissions: {e}")
            return []


# 创建全局角色服务实例
role_service = RoleService()
