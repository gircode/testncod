#!/usr/bin/env python3
import os
import sys
import argparse
from alembic.config import Config
from alembic import command


def run_migrations(args):
    """运行数据库迁移"""
    # 获取项目根目录
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    alembic_cfg = Config(os.path.join(project_root, "alembic.ini"))

    try:
        if args.command == "upgrade":
            if args.revision == "head":
                command.upgrade(alembic_cfg, "head")
            else:
                command.upgrade(alembic_cfg, args.revision)
        elif args.command == "downgrade":
            command.downgrade(alembic_cfg, args.revision)
        elif args.command == "current":
            command.current(alembic_cfg)
        elif args.command == "history":
            command.history(alembic_cfg)
        elif args.command == "init":
            command.stamp(alembic_cfg, "head")

        print(f"Successfully executed {args.command}")

    except Exception as e:
        print(f"Error executing migration command: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Database migration tool")
    parser.add_argument(
        "command",
        choices=["upgrade", "downgrade", "current", "history", "init"],
        help="Migration command to execute",
    )
    parser.add_argument(
        "--revision", default="head", help="Revision identifier (default: head)"
    )

    args = parser.parse_args()
    run_migrations(args)


if __name__ == "__main__":
    main()
