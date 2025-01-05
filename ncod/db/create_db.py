"""
PostgreSQL数据库初始化脚本
用于创建数据库、用户并设置适当的权限
"""

import os
import psycopg2
from psycopg2 import errors
from ncod.db.config import DB_CONFIG


def create_database() -> None:
    """
    创建PostgreSQL数据库和用户
    - 连接到默认的postgres数据库
    - 创建应用所需的用户（如果不存在）
    - 创建应用数据库（如果不存在）
    - 为用户授予数据库权限
    """
    # 连接到默认的postgres数据库
    conn = psycopg2.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        database="postgres",
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
        client_encoding="utf8",
    )
    conn.autocommit = True
    cur = conn.cursor()

    try:
        # 创建用户
        cur.execute(
            f"""
        DO
        $do$
        BEGIN
           IF NOT EXISTS (
              SELECT FROM pg_catalog.pg_roles
              WHERE rolname = '{DB_CONFIG['user']}') THEN
              CREATE USER {DB_CONFIG['user']} WITH PASSWORD '{DB_CONFIG['password']}';
           END IF;
        END
        $do$;
        """
        )

        # 创建数据库
        cur.execute(
            f"""
        SELECT 'CREATE DATABASE {DB_CONFIG['database']}'
        WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '{DB_CONFIG['database']}')\\gexec
        """
        )

        # 授权
        cur.execute(
            f"""
        GRANT ALL PRIVILEGES ON DATABASE {DB_CONFIG['database']} TO {DB_CONFIG['user']};
        """
        )

        print("Database and user created successfully!")

    except errors.DuplicateDatabase:
        print(f"Database '{DB_CONFIG['database']}' already exists")
    except errors.DuplicateObject:
        print(f"User '{DB_CONFIG['user']}' already exists")
    except errors.InsufficientPrivilege as e:
        print(f"权限错误: {e}")
    except Exception as e:
        print(f"未知错误: {e}")
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    create_database()
