from typing import Dict, Tuple
from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..auth import authenticate_user, verify_mac_address
from ..device_manager import DeviceManager
from ..slave_manager import SlaveManager
from ..user_manager import UserManager
from ..log_manager import LogManager
from ..health_manager import HealthManager
from ..utils.logger import get_logger

logger = get_logger(__name__)
api = Blueprint('api', __name__)


@api.route('/auth/login', methods=['POST'])
def login() -> Tuple[Response, int]:
    """用户登录"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        client_type = data.get('client_type', 'web')  # 默认为web登录
        
        if not username or not password:
            return jsonify({
                'error': 'Missing username or password'
            }), 400
            
        # 验证客户端类型
        if client_type not in ['web', 'client']:
            return jsonify({
                'error': 'Invalid client type'
            }), 400
            
        user = authenticate_user(username, password, client_type)
        if not user:
            return jsonify({
                'error': 'Invalid credentials'
            }), 401
            
        return jsonify(user), 200
        
    except Exception as e:
        logger.error(f"Login failed: {e}")
        return jsonify({
            'error': 'Internal server error'
        }), 500


@api.route('/auth/verify-mac', methods=['POST'])
def verify_mac() -> Tuple[Response, int]:
    """验证MAC地址"""
    try:
        data = request.get_json()
        mac_address = data.get('mac_address')
        
        if not mac_address:
            return jsonify({
                'error': 'Missing MAC address'
            }), 400
            
        if verify_mac_address(mac_address):
            return jsonify({
                'status': 'valid'
            }), 200
            
        return jsonify({
            'status': 'invalid'
        }), 401
        
    except Exception as e:
        logger.error(f"MAC verification failed: {e}")
        return jsonify({
            'error': 'Internal server error'
        }), 500


@api.route('/slaves/register', methods=['POST'])
def register_slave() -> Tuple[Response, int]:
    """注册从服务器"""
    try:
        data = request.get_json()
        hostname = data.get('hostname')
        ip_address = data.get('ip_address')
        mac_address = data.get('mac_address')
        
        if not all([hostname, ip_address, mac_address]):
            return jsonify({
                'error': 'Missing required fields'
            }), 400
            
        result = SlaveManager().register_slave(
            hostname=hostname,
            ip_address=ip_address,
            mac_address=mac_address
        )
        
        if result:
            return jsonify(result), 200
            
        return jsonify({
            'error': 'Registration failed'
        }), 400
        
    except Exception as e:
        logger.error(f"Slave registration failed: {e}")
        return jsonify({
            'error': 'Internal server error'
        }), 500


@api.route('/slaves/status', methods=['POST'])
def update_slave_status() -> Tuple[Response, int]:
    """更新从服务器状态"""
    try:
        data = request.get_json()
        slave_id = data.get('slave_id')
        status = data.get('status')
        
        if not all([slave_id, status]):
            return jsonify({
                'error': 'Missing required fields'
            }), 400
            
        if SlaveManager().update_slave_status(slave_id, status):
            return jsonify({
                'status': 'updated'
            }), 200
            
        return jsonify({
            'error': 'Update failed'
        }), 400
        
    except Exception as e:
        logger.error(f"Slave status update failed: {e}")
        return jsonify({
            'error': 'Internal server error'
        }), 500


@api.route('/devices', methods=['GET'])
@jwt_required()
def get_devices() -> Tuple[Response, int]:
    """获取设备列表"""
    try:
        devices = DeviceManager().get_all_devices()
        return jsonify(devices), 200
        
    except Exception as e:
        logger.error(f"Failed to get devices: {e}")
        return jsonify({
            'error': 'Internal server error'
        }), 500


@api.route('/devices/<int:device_id>', methods=['GET'])
@jwt_required()
def get_device(device_id: int) -> Tuple[Response, int]:
    """获取单个设备信息"""
    try:
        device = DeviceManager().get_device(device_id)
        if device:
            return jsonify(device), 200
            
        return jsonify({
            'error': 'Device not found'
        }), 404
        
    except Exception as e:
        logger.error(f"Failed to get device {device_id}: {e}")
        return jsonify({
            'error': 'Internal server error'
        }), 500


@api.route('/devices/<int:device_id>/assign', methods=['POST'])
@jwt_required()
def assign_device(device_id: int) -> Tuple[Response, int]:
    """分配设备"""
    try:
        user_id = get_jwt_identity()
        
        if DeviceManager().assign_device(device_id, user_id):
            return jsonify({
                'status': 'assigned'
            }), 200
            
        return jsonify({
            'error': 'Assignment failed'
        }), 400
        
    except Exception as e:
        logger.error(f"Failed to assign device {device_id}: {e}")
        return jsonify({
            'error': 'Internal server error'
        }), 500


@api.route('/devices/<int:device_id>/release', methods=['POST'])
@jwt_required()
def release_device(device_id: int) -> Tuple[Response, int]:
    """释放设备"""
    try:
        if DeviceManager().release_device(device_id):
            return jsonify({
                'status': 'released'
            }), 200
            
        return jsonify({
            'error': 'Release failed'
        }), 400
        
    except Exception as e:
        logger.error(f"Failed to release device {device_id}: {e}")
        return jsonify({
            'error': 'Internal server error'
        }), 500


@api.route('/users', methods=['GET'])
@jwt_required()
def get_users() -> Tuple[Response, int]:
    """获取用户列表"""
    try:
        users = UserManager().get_all_users()
        return jsonify(users), 200
        
    except Exception as e:
        logger.error(f"Failed to get users: {e}")
        return jsonify({
            'error': 'Internal server error'
        }), 500


@api.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id: int) -> Tuple[Response, int]:
    """获取单个用户信息"""
    try:
        user = UserManager().get_user(user_id)
        if user:
            return jsonify(user), 200
            
        return jsonify({
            'error': 'User not found'
        }), 404
        
    except Exception as e:
        logger.error(f"Failed to get user {user_id}: {e}")
        return jsonify({
            'error': 'Internal server error'
        }), 500


@api.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id: int) -> Tuple[Response, int]:
    """更新用户信息"""
    try:
        data = request.get_json()
        if UserManager().update_user(user_id, data):
            return jsonify({
                'status': 'updated'
            }), 200
            
        return jsonify({
            'error': 'Update failed'
        }), 400
        
    except Exception as e:
        logger.error(f"Failed to update user {user_id}: {e}")
        return jsonify({
            'error': 'Internal server error'
        }), 500


@api.route('/logs', methods=['GET'])
@jwt_required()
def get_logs() -> Tuple[Response, int]:
    """获取系统日志"""
    try:
        hours = request.args.get('hours', default=24, type=int)
        logs = LogManager().get_recent_logs(hours)
        return jsonify(logs), 200
        
    except Exception as e:
        logger.error(f"Failed to get logs: {e}")
        return jsonify({
            'error': 'Internal server error'
        }), 500


@api.route('/health', methods=['GET'])
@jwt_required()
def get_health() -> Tuple[Response, int]:
    """获取系统健康状态"""
    try:
        report = HealthManager().get_full_health_report()
        return jsonify(report), 200
        
    except Exception as e:
        logger.error(f"Failed to get health report: {e}")
        return jsonify({
            'error': 'Internal server error'
        }), 500 