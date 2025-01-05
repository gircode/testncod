"""Init Db模块"""

import datetime
import json
import logging
import sys
from pathlib import Path

import bcrypt

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from database import db_manager
from models.user import Base, User

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_admin_user(session):
    """创建管理员用户"""
    try:
        # 检查是否已存在管理员用户
        admin = session.query(User).filter(User.username == "admin").first()
        if admin:
            logger.info("Admin user already exists")
            return

        # 创建密码哈希
        password = "Admin123!@#"
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode(), salt)

        # 创建管理员用户
        admin = User(
            username="admin",
            password=hashed.decode(),
            name="系统管理员",
            email="admin@example.com",
            role="admin",
            permissions=["read", "write", "delete", "admin"],
            is_active=True,
            password_changed_at=datetime.datetime.utcnow(),
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow(),
        )

        session.add(admin)
        session.commit()
        logger.info("Admin user created successfully")

    except Exception as e:
        logger.error(f"Failed to create admin user: {e}")
        session.rollback()
        raise


def init_database():
    """初始化数据库"""
    try:
        # 创建所有表
        Base.metadata.create_all(db_manager.engine)
        logger.info("Database tables created successfully")

        # 创建管理员用户
        with db_manager.get_session() as session:
            create_admin_user(session)

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    finally:
        db_manager.cleanup()


if __name__ == "__main__":
    try:
        init_database()
        logger.info("Database initialization completed successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        sys.exit(1)
