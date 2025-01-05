"""
Web应用
"""

from flask import Flask
from flask_cors import CORS
from ncod.core.config import Config
from ncod.core.log import Logger

config = Config()
logger = Logger(__name__)


def create_app() -> Flask:
    """创建Flask应用

    Returns:
        Flask应用
    """
    # 创建应用
    app = Flask(__name__)

    # 配置应用
    app.config["SECRET_KEY"] = config.JWT_SECRET_KEY
    app.config["CORS_ORIGINS"] = config.CORS_ORIGINS

    # 启用CORS
    CORS(app)

    # 注册蓝图
    from ncod.master.app.web.routes import web_bp

    app.register_blueprint(web_bp)

    # 注册错误处理器
    register_error_handlers(app)

    # 注册请求处理器
    register_request_handlers(app)

    return app


def register_error_handlers(app: Flask):
    """注册错误处理器

    Args:
        app: Flask应用
    """

    @app.errorhandler(404)
    def not_found_error(error):
        """404错误处理器"""
        logger.error(f"404错误: {str(error)}")
        return {"error": "Not Found"}, 404

    @app.errorhandler(500)
    def internal_error(error):
        """500错误处理器"""
        logger.error(f"500错误: {str(error)}")
        return {"error": "Internal Server Error"}, 500


def register_request_handlers(app: Flask):
    """注册请求处理器

    Args:
        app: Flask应用
    """

    @app.before_request
    def before_request():
        """请求前处理器"""
        logger.info("开始处理请求")

    @app.after_request
    def after_request(response):
        """请求后处理器"""
        logger.info("请求处理完成")
        return response
