"""Users模块"""

import datetime
import json
import logging
from typing import Dict, List, Optional

from database import db_manager
from models.user import Permission, Role, User
from pywebio.input import input, input_group, select, textarea
from pywebio.output import clear, put_error, put_html, put_loading, toast
from pywebio.session import info as session_info
from pywebio.session import run_js, set_env

logger = logging.getLogger(__name__)


def get_users() -> List[Dict]:
    """获取用户列表"""
    try:
        with db_manager.get_session() as session:
            users = session.query(User).all()
            return [
                {
                    "id": user.id,
                    "username": user.username,
                    "name": user.name,
                    "email": user.email,
                    "role": user.role.name if user.role else None,
                    "status": user.status,
                    "last_login": (
                        user.last_login.strftime("%Y-%m-%d %H:%M:%S")
                        if user.last_login
                        else None
                    ),
                    "created_at": user.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                }
                for user in users
            ]
    except Exception as e:
        logger.error(f"Failed to get users: {e}")
        return []


def get_roles() -> List[Dict]:
    """获取角色列表"""
    try:
        with db_manager.get_session() as session:
            roles = session.query(Role).all()
            return [
                {
                    "id": role.id,
                    "name": role.name,
                    "description": role.description,
                    "permissions": [p.name for p in role.permissions],
                }
                for role in roles
            ]
    except Exception as e:
        logger.error(f"Failed to get roles: {e}")
        return []


async def create_user(user_data: Dict) -> bool:
    """创建新用户"""
    try:
        with db_manager.get_session() as session:
            # 检查用户名是否已存在
            if (
                session.query(User)
                .filter(User.username == user_data["username"])
                .first()
            ):
                return False

            # 创建新用户
            user = User(
                username=user_data["username"],
                name=user_data["name"],
                email=user_data["email"],
                role_id=user_data["role_id"],
                status="active",
                created_at=datetime.datetime.utcnow(),
                updated_at=datetime.datetime.utcnow(),
            )
            user.set_password(user_data["password"])

            session.add(user)
            session.commit()
            return True
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        return False


async def update_user(user_id: int, user_data: Dict) -> bool:
    """更新用户信息"""
    try:
        with db_manager.get_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return False

            user.name = user_data.get("name", user.name)
            user.email = user_data.get("email", user.email)
            user.role_id = user_data.get("role_id", user.role_id)
            user.status = user_data.get("status", user.status)
            user.updated_at = datetime.datetime.utcnow()

            if "password" in user_data:
                user.set_password(user_data["password"])

            session.commit()
            return True
    except Exception as e:
        logger.error(f"Failed to update user: {e}")
        return False


async def delete_user(user_id: int) -> bool:
    """删除用户"""
    try:
        with db_manager.get_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return False

            session.delete(user)
            session.commit()
            return True
    except Exception as e:
        logger.error(f"Failed to delete user: {e}")
        return False


async def users_page():
    """用户管理页面"""
    set_env(title="用户管理")

    # 页面样式
    style = """
    <style>
        .users-page {
            padding: 20px;
            max-width: 1200px;
            margin: 0 auto;
        }
        .users-header {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .users-title {
            font-size: 24px;
            font-weight: 600;
            color: #2c3e50;
        }
        .users-table {
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .table {
            width: 100%;
            border-collapse: collapse;
        }
        .table th,
        .table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e5e7eb;
        }
        .table th {
            background: #f8fafc;
            font-weight: 500;
            color: #64748b;
            font-size: 14px;
        }
        .table tr:hover {
            background: #f8fafc;
        }
        .status-badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 9999px;
            font-size: 12px;
            font-weight: 500;
        }
        .status-active {
            background: #dcfce7;
            color: #16a34a;
        }
        .status-inactive {
            background: #fee2e2;
            color: #dc2626;
        }
        .action-button {
            padding: 8px 16px;
            border-radius: 6px;
            border: none;
            cursor: pointer;
            font-size: 14px;
            transition: background-color 0.3s;
        }
        .create-button {
            background: #3b82f6;
            color: white;
        }
        .create-button:hover {
            background: #2563eb;
        }
        .edit-button {
            background: #f59e0b;
            color: white;
            padding: 4px 8px;
            margin-right: 4px;
        }
        .edit-button:hover {
            background: #d97706;
        }
        .delete-button {
            background: #ef4444;
            color: white;
            padding: 4px 8px;
        }
        .delete-button:hover {
            background: #dc2626;
        }
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 1000;
        }
        .modal-content {
            position: relative;
            background: white;
            margin: 100px auto;
            padding: 20px;
            width: 90%;
            max-width: 500px;
            border-radius: 10px;
        }
        .modal-header {
            margin-bottom: 20px;
        }
        .modal-title {
            font-size: 20px;
            font-weight: 600;
            color: #2c3e50;
        }
        .close {
            position: absolute;
            right: 20px;
            top: 20px;
            font-size: 24px;
            cursor: pointer;
            color: #64748b;
        }
        .form-group {
            margin-bottom: 15px;
        }
        .form-label {
            display: block;
            font-size: 14px;
            color: #64748b;
            margin-bottom: 5px;
        }
        .form-input {
            width: 100%;
            padding: 8px;
            border: 1px solid #e5e7eb;
            border-radius: 6px;
            font-size: 14px;
        }
        .form-input:focus {
            outline: none;
            border-color: #3b82f6;
            box-shadow: 0 0 0 2px rgba(59,130,246,0.1);
        }
        .form-select {
            width: 100%;
            padding: 8px;
            border: 1px solid #e5e7eb;
            border-radius: 6px;
            font-size: 14px;
            background-color: white;
        }
        .modal-footer {
            margin-top: 20px;
            text-align: right;
        }
        .cancel-button {
            background: #e5e7eb;
            color: #374151;
            margin-right: 10px;
        }
        .cancel-button:hover {
            background: #d1d5db;
        }
    </style>
    """

    # 获取用户列表和角色列表
    users = get_users()
    roles = get_roles()

    # 渲染页面
    clear()
    put_html(style)

    put_html(
        f"""
    <div class="users-page">
        <div class="users-header">
            <div class="users-title">用户管理</div>
            <button class="action-button create-button" \
                 onclick="showCreateModal()">创建用户</button>
        </div>
        
        <div class="users-table">
            <table class="table">
                <thead>
                    <tr>
                        <th>用户名</th>
                        <th>姓名</th>
                        <th>邮箱</th>
                        <th>角色</th>
                        <th>状态</th>
                        <th>最后登录</th>
                        <th>创建时间</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
    """
    )

    for user in users:
        status_class = (
            "status-active" if user["status"] == "active" else "status-inactive"
        )
        put_html(
            f"""
            <tr>
                <td>{user['username']}</td>
                <td>{user['name']}</td>
                <td>{user['email']}</td>
                <td>{user['role']}</td>
                <td><span class="status-badge \
                     {status_class}">{user['status']}</span></td>
                <td>{user['last_login'] or '-'}</td>
                <td>{user['created_at']}</td>
                <td>
                    <button class="action-button edit-button" \
                         onclick="showEditModal({user['id']})">编辑</button>
                    <button class="action-button delete-button" \
                         onclick="deleteUser({user['id']})">删除</button>
                </td>
            </tr>
        """
        )

    put_html(
        """
                </tbody>
            </table>
        </div>
        
        <!-- 创建用户模态框 -->
        <div id="createModal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <div class="modal-title">创建用户</div>
                    <span class="close" onclick="hideCreateModal()">&times;</span>
                </div>
                <div class="form-group">
                    <label class="form-label">用户名</label>
                    <input type="text" class="form-input" id="create_username">
                </div>
                <div class="form-group">
                    <label class="form-label">密码</label>
                    <input type="password" class="form-input" id="create_password">
                </div>
                <div class="form-group">
                    <label class="form-label">姓名</label>
                    <input type="text" class="form-input" id="create_name">
                </div>
                <div class="form-group">
                    <label class="form-label">邮箱</label>
                    <input type="email" class="form-input" id="create_email">
                </div>
                <div class="form-group">
                    <label class="form-label">角色</label>
                    <select class="form-select" id="create_role">
    """
    )

    for role in roles:
        put_html(
            f"""
            <option value="{role['id']}">{role['name']}</option>
        """
        )

    put_html(
        """
                    </select>
                </div>
                <div class="modal-footer">
                    <button class="action-button cancel-button" \
                         onclick="hideCreateModal()">取消</button>
                    <button class="action-button create-button" \
                         onclick="createUser()">创建</button>
                </div>
            </div>
        </div>
        
        <!-- 编辑用户模态框 -->
        <div id="editModal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <div class="modal-title">编辑用户</div>
                    <span class="close" onclick="hideEditModal()">&times;</span>
                </div>
                <input type="hidden" id="edit_user_id">
                <div class="form-group">
                    <label class="form-label">姓名</label>
                    <input type="text" class="form-input" id="edit_name">
                </div>
                <div class="form-group">
                    <label class="form-label">邮箱</label>
                    <input type="email" class="form-input" id="edit_email">
                </div>
                <div class="form-group">
                    <label class="form-label">角色</label>
                    <select class="form-select" id="edit_role">
    """
    )

    for role in roles:
        put_html(
            f"""
            <option value="{role['id']}">{role['name']}</option>
        """
        )

    put_html(
        """
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label">状态</label>
                    <select class="form-select" id="edit_status">
                        <option value="active">激活</option>
                        <option value="inactive">禁用</option>
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label">新密码（留空表示不修改）</label>
                    <input type="password" class="form-input" id="edit_password">
                </div>
                <div class="modal-footer">
                    <button class="action-button cancel-button" \
                         onclick="hideEditModal()">取消</button>
                    <button class="action-button create-button" \
                         onclick="updateUser()">保存</button>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // 显示创建用户模态框
        function showCreateModal() {
            document.getElementById('createModal').style.display = 'block';
        }
        
        // 隐藏创建用户模态框
        function hideCreateModal() {
            document.getElementById('createModal').style.display = 'none';
        }
        
        // 显示编辑用户模态框
        function showEditModal(userId) {
            document.getElementById('edit_user_id').value = userId;
            document.getElementById('editModal').style.display = 'block';
            
            // 获取用户信息并填充表单
            const user = users.find(u => u.id === userId);
            if (user) {
                document.getElementById('edit_name').value = user.name;
                document.getElementById('edit_email').value = user.email;
                document.getElementById('edit_role').value = user.role_id;
                document.getElementById('edit_status').value = user.status;
            }
        }
        
        // 隐藏编辑用户模态框
        function hideEditModal() {
            document.getElementById('editModal').style.display = 'none';
        }
        
        // 创建用户
        function createUser() {
            const userData = {
                username: document.getElementById('create_username').value,
                password: document.getElementById('create_password').value,
                name: document.getElementById('create_name').value,
                email: document.getElementById('create_email').value,
                role_id: parseInt(document.getElementById('create_role').value)
            };
            
            pywebio.call_js_function('create_user', userData).then(success => {
                if (success) {
                    hideCreateModal();
                    location.reload();
                } else {
                    alert('创建用户失败，可能用户名已存在');
                }
            });
        }
        
        // 更新用户
        function updateUser() {
            const userId = parseInt(document.getElementById('edit_user_id').value);
            const userData = {
                name: document.getElementById('edit_name').value,
                email: document.getElementById('edit_email').value,
                role_id: parseInt(document.getElementById('edit_role').value),
                status: document.getElementById('edit_status').value
            };
            
            const password = document.getElementById('edit_password').value;
            if (password) {
                userData.password = password;
            }
            
            pywebio.call_js_function('update_user', userId, userData).then(success => {
                if (success) {
                    hideEditModal();
                    location.reload();
                } else {
                    alert('更新用户失败');
                }
            });
        }
        
        // 删除用户
        function deleteUser(userId) {
            if (confirm('确定要删除该用户吗？')) {
                pywebio.call_js_function('delete_user', userId).then(success => {
                    if (success) {
                        location.reload();
                    } else {
                        alert('删除用户失败');
                    }
                });
            }
        }
    </script>
    """
    )


if __name__ == "__main__":
    users_page()
