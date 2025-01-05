"""组织服务"""

from typing import Dict, List, Optional, Tuple
from ncod.core.logger import setup_logger
from ncod.core.db.transaction import transaction_manager
from ncod.master.models.organization import Organization

logger = setup_logger("organization_service")


class OrganizationService:
    """组织服务"""

    def __init__(self):
        self.transaction = transaction_manager

    async def create_organization(
        self, data: Dict
    ) -> Tuple[bool, str, Optional[Organization]]:
        """创建组织"""
        try:
            async with self.transaction.transaction() as session:
                # 检查代码是否存在
                if await Organization.get_by_code(session, data["code"]):
                    return False, "Organization code already exists", None

                # 检查父组织
                if "parent_id" in data:
                    parent = await session.get(Organization, data["parent_id"])
                    if not parent:
                        return False, "Parent organization not found", None

                # 创建组织
                org = Organization(
                    name=data["name"],
                    code=data["code"],
                    description=data.get("description"),
                    parent_id=data.get("parent_id"),
                )

                session.add(org)
                await session.commit()
                await session.refresh(org)

                return True, "Organization created successfully", org
        except Exception as e:
            logger.error(f"Error creating organization: {e}")
            return False, str(e), None

    async def update_organization(
        self, org_id: str, data: Dict
    ) -> Tuple[bool, str, Optional[Organization]]:
        """更新组织"""
        try:
            async with self.transaction.transaction() as session:
                org = await session.get(Organization, org_id)
                if not org:
                    return False, "Organization not found", None

                # 检查代码是否重复
                if "code" in data:
                    existing = await Organization.get_by_code(session, data["code"])
                    if existing and existing.id != org_id:
                        return False, "Organization code already exists", None
                    org.code = data["code"]

                if "name" in data:
                    org.name = data["name"]
                if "description" in data:
                    org.description = data["description"]

                # 检查父组织
                if "parent_id" in data:
                    if data["parent_id"] == org_id:
                        return False, "Cannot set self as parent", None
                    if data["parent_id"]:
                        parent = await session.get(Organization, data["parent_id"])
                        if not parent:
                            return False, "Parent organization not found", None
                    org.parent_id = data["parent_id"]

                await session.commit()
                await session.refresh(org)

                return True, "Organization updated successfully", org
        except Exception as e:
            logger.error(f"Error updating organization: {e}")
            return False, str(e), None

    async def delete_organization(self, org_id: str) -> Tuple[bool, str]:
        """删除组织"""
        try:
            async with self.transaction.transaction() as session:
                org = await session.get(Organization, org_id)
                if not org:
                    return False, "Organization not found"

                # 检查是否有子组织
                children = await Organization.get_children(session, org_id)
                if children:
                    return False, "Cannot delete organization with children"

                await session.delete(org)
                await session.commit()

                return True, "Organization deleted successfully"
        except Exception as e:
            logger.error(f"Error deleting organization: {e}")
            return False, str(e)

    async def get_organization(self, org_id: str) -> Optional[Dict]:
        """获取组织"""
        try:
            async with self.transaction.transaction() as session:
                org = await session.get(Organization, org_id)
                return org.to_dict() if org else None
        except Exception as e:
            logger.error(f"Error getting organization: {e}")
            return None

    async def list_organizations(self, parent_id: Optional[str] = None) -> List[Dict]:
        """获取组织列表"""
        try:
            async with self.transaction.transaction() as session:
                if parent_id:
                    orgs = await Organization.get_children(session, parent_id)
                else:
                    orgs = await Organization.get_root_organizations(session)
                return [org.to_dict() for org in orgs]
        except Exception as e:
            logger.error(f"Error listing organizations: {e}")
            return []

    async def get_organization_tree(self, org_id: Optional[str] = None) -> List[Dict]:
        """获取组织树"""
        try:
            async with self.transaction.transaction() as session:
                if org_id:
                    orgs = [await session.get(Organization, org_id)]
                else:
                    orgs = await Organization.get_root_organizations(session)

                tree = []
                for org in orgs:
                    if not org:
                        continue
                    node = org.to_dict()
                    children = await self.get_organization_tree(org.id)
                    if children:
                        node["children"] = children
                    tree.append(node)

                return tree
        except Exception as e:
            logger.error(f"Error getting organization tree: {e}")
            return []


# 创建全局组织服务实例
organization_service = OrganizationService()
