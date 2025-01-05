from ncod.core.db.database import SessionLocal
from ncod.master.models.permission import Role, Permission


def init_roles():
    """初始化系统角色和权限"""
    with SessionLocal() as db:
        # 创建管理员角色
        admin_role = Role(name="admin", description="System Administrator")
        admin_role.permissions = {p.value for p in Permission}

        # 创建设备管理员角色
        device_admin_role = Role(
            name="device_admin", description="Device Administrator"
        )
        device_admin_role.permissions = {
            Permission.DEVICE_VIEW.value,
            Permission.DEVICE_CONNECT.value,
            Permission.DEVICE_MANAGE.value,
        }

        # 创建普通用户角色
        user_role = Role(name="user", description="Normal User")
        user_role.permissions = {
            Permission.DEVICE_VIEW.value,
            Permission.DEVICE_CONNECT.value,
        }

        # 添加角色
        for role in [admin_role, device_admin_role, user_role]:
            existing = db.query(Role).filter_by(name=role.name).first()
            if not existing:
                db.add(role)

        db.commit()
