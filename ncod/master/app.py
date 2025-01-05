"""主应用入口"""

from typing import Optional, Any
from flask import Flask, Response
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from .models import db
from .api.routes import api
from .api.ws_routes import ws, socketio
from .config_manager import ConfigManager
from .scheduler_manager import SchedulerManager
from .utils.logger import setup_logger

config = ConfigManager()
logger = setup_logger(__name__)


def create_app(test_config: Optional[dict] = None) -> Flask:
    """创建Flask应用实例"""
    app = Flask(__name__)
    
    # 加载配置
    if test_config is None:
        app.config.from_object('config.Config')
    else:
        app.config.update(test_config)
    
    # 初始化扩展
    CORS(app)
    db.init_app(app)
    Migrate(app, db)
    JWTManager(app)
    socketio.init_app(app)
    
    # 注册蓝图
    app.register_blueprint(api, url_prefix='/api')
    app.register_blueprint(ws, url_prefix='/ws')
    
    # 初始化数据库
    with app.app_context():
        db.create_all()
    
    # 启动任务调度器
    scheduler = SchedulerManager()
    scheduler.start()
    
    @app.before_first_request
    def before_first_request() -> None:
        """首次请求前的初始化"""
        logger.info("Initializing application...")
        
        # 验证配置
        if not config.validate():
            logger.error("Invalid configuration")
            raise RuntimeError("Invalid configuration")
    
    @app.before_request
    def before_request() -> None:
        """每次请求前的处理"""
        pass
    
    @app.after_request
    def after_request(response: Response) -> Response:
        """每次请求后的处理"""
        return response
    
    @app.teardown_appcontext
    def teardown_appcontext(error: Optional[Exception]) -> None:
        """应用上下文销毁时的处理"""
        if error:
            logger.error(f"Application error: {error}")
    
    @app.errorhandler(404)
    def not_found_error(error: Any) -> tuple[dict, int]:
        """404错误处理"""
        return {
            'error': 'Not found'
        }, 404
    
    @app.errorhandler(500)
    def internal_error(error: Any) -> tuple[dict, int]:
        """500错误处理"""
        logger.error(f"Server error: {error}")
        return {
            'error': 'Internal server error'
        }, 500
    
    return app
