"""
启动脚本
"""

import os
import sys

import click
from dotenv import load_dotenv

# 添加项目根目录到Python路径
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, project_root)

# 加载环境变量
load_dotenv()


@click.group()
def cli():
    """NCOD主服务器命令行工具"""
    pass


@cli.command()
@click.option("--host", default="0.0.0.0", help="监听地址")
@click.option("--port", default=5000, help="监听端口")
@click.option("--debug", is_flag=True, help="调试模式")
def run(host: str, port: int, debug: bool):
    """启动Web服务器"""
    from ncod.master.app import create_app

    app = create_app()
    app.run(host=host, port=port, debug=debug)


@cli.command()
def init_db():
    """初始化数据库"""
    from ncod.core.db import Base, engine

    Base.metadata.create_all(bind=engine)
    click.echo("数据库初始化完成")


@cli.command()
def collect_metrics():
    """收集监控指标"""
    from ncod.core.monitor import Monitor

    monitor = Monitor()
    metrics = monitor.collect_metrics()
    click.echo(f"监控指标: {metrics}")


@cli.command()
def check_alerts():
    """检查告警"""
    from ncod.core.monitor import Monitor

    monitor = Monitor()
    alerts = monitor.check_alerts()
    click.echo(f"告警列表: {alerts}")


if __name__ == "__main__":
    cli()
