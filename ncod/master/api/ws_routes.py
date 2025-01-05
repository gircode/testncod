from typing import Dict
from datetime import datetime
from flask import Blueprint
from flask_socketio import (
    SocketIO, emit, join_room, leave_room,
    rooms, disconnect
)
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..device_manager import DeviceManager
from ..slave_manager import SlaveManager
from ..utils.logger import get_logger

logger = get_logger(__name__)
ws = Blueprint('ws', __name__)
socketio = SocketIO()


@socketio.on('connect')
@jwt_required()
def handle_connect() -> None:
    """处理客户端连接"""
    try:
        user_id = get_jwt_identity()
        join_room(f'user_{user_id}')
        logger.info(f"User {user_id} connected")
        emit('connect_response', {'status': 'connected'})
        
    except Exception as e:
        logger.error(f"Connection failed: {e}")
        disconnect()


@socketio.on('disconnect')
def handle_disconnect() -> None:
    """处理客户端断开连接"""
    try:
        user_rooms = rooms()
        for room in user_rooms:
            if room.startswith('user_'):
                user_id = room.split('_')[1]
                logger.info(f"User {user_id} disconnected")
                leave_room(room)
                
    except Exception as e:
        logger.error(f"Disconnect error: {e}")


@socketio.on('subscribe_device')
@jwt_required()
def handle_subscribe_device(data: Dict) -> None:
    """订阅设备状态更新"""
    try:
        device_id = data.get('device_id')
        if not device_id:
            emit('error', {'message': 'Missing device ID'})
            return
            
        device = DeviceManager().get_device(device_id)
        if not device:
            emit('error', {'message': 'Device not found'})
            return
            
        room = f'device_{device_id}'
        join_room(room)
        logger.info(f"Subscribed to device {device_id}")
        emit('subscribe_response', {
            'status': 'subscribed',
            'device': device
        })
        
    except Exception as e:
        logger.error(f"Subscribe device failed: {e}")
        emit('error', {'message': 'Internal server error'})


@socketio.on('unsubscribe_device')
@jwt_required()
def handle_unsubscribe_device(data: Dict) -> None:
    """取消订阅设备状态更新"""
    try:
        device_id = data.get('device_id')
        if not device_id:
            emit('error', {'message': 'Missing device ID'})
            return
            
        room = f'device_{device_id}'
        leave_room(room)
        logger.info(f"Unsubscribed from device {device_id}")
        emit('unsubscribe_response', {
            'status': 'unsubscribed',
            'device_id': device_id
        })
        
    except Exception as e:
        logger.error(f"Unsubscribe device failed: {e}")
        emit('error', {'message': 'Internal server error'})


@socketio.on('subscribe_slave')
@jwt_required()
def handle_subscribe_slave(data: Dict) -> None:
    """订阅从服务器状态更新"""
    try:
        slave_id = data.get('slave_id')
        if not slave_id:
            emit('error', {'message': 'Missing slave ID'})
            return
            
        slave = SlaveManager().get_slave(slave_id)
        if not slave:
            emit('error', {'message': 'Slave not found'})
            return
            
        room = f'slave_{slave_id}'
        join_room(room)
        logger.info(f"Subscribed to slave {slave_id}")
        emit('subscribe_response', {
            'status': 'subscribed',
            'slave': slave
        })
        
    except Exception as e:
        logger.error(f"Subscribe slave failed: {e}")
        emit('error', {'message': 'Internal server error'})


@socketio.on('unsubscribe_slave')
@jwt_required()
def handle_unsubscribe_slave(data: Dict) -> None:
    """取消订阅从服务器状态更新"""
    try:
        slave_id = data.get('slave_id')
        if not slave_id:
            emit('error', {'message': 'Missing slave ID'})
            return
            
        room = f'slave_{slave_id}'
        leave_room(room)
        logger.info(f"Unsubscribed from slave {slave_id}")
        emit('unsubscribe_response', {
            'status': 'unsubscribed',
            'slave_id': slave_id
        })
        
    except Exception as e:
        logger.error(f"Unsubscribe slave failed: {e}")
        emit('error', {'message': 'Internal server error'})


def broadcast_device_update(device_id: int, data: Dict) -> None:
    """广播设备状态更新"""
    try:
        room = f'device_{device_id}'
        socketio.emit('device_update', data, room=room)
        logger.info(f"Broadcasted device update: {device_id}")
        
    except Exception as e:
        logger.error(f"Broadcast device update failed: {e}")


def broadcast_slave_update(slave_id: int, data: Dict) -> None:
    """广播从服务器状态更新"""
    try:
        room = f'slave_{slave_id}'
        socketio.emit('slave_update', data, room=room)
        logger.info(f"Broadcasted slave update: {slave_id}")
        
    except Exception as e:
        logger.error(f"Broadcast slave update failed: {e}")


def broadcast_system_message(message: str, level: str = 'info') -> None:
    """广播系统消息"""
    try:
        data = {
            'message': message,
            'level': level,
            'timestamp': datetime.utcnow().isoformat()
        }
        socketio.emit('system_message', data, broadcast=True)
        logger.info(f"Broadcasted system message: {message}")
        
    except Exception as e:
        logger.error(f"Broadcast system message failed: {e}")


def notify_user(user_id: int, message: str, level: str = 'info') -> None:
    """发送用户通知"""
    try:
        room = f'user_{user_id}'
        data = {
            'message': message,
            'level': level,
            'timestamp': datetime.utcnow().isoformat()
        }
        socketio.emit('user_notification', data, room=room)
        logger.info(f"Sent notification to user {user_id}")
        
    except Exception as e:
        logger.error(f"Send user notification failed: {e}") 