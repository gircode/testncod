"""Roles模块"""

import datetime
import json
import logging
from typing import Dict, List, Optional

from database import db_manager
from models.rbac import PERMISSIONS, Permission, Role
from pywebio.input import input, input_group, select, textarea
from pywebio.output import clear, put_error, put_html, put_loading, toast
from pywebio.session import info as session_info
from pywebio.session import run_js, set_env
from utils.auth import require_permission

logger = logging.getLogger(__name__)


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
                    "permissions": [p.code for p in role.permissions],
                    "created_at": role.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "updated_at": role.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
                }
                for role in roles
            ]
    except Exception as e:
        logger.error(f"Failed to get roles: {e}")
        return []


def get_permissions() -> List[Dict]:
    """获取权限列表"""
    try:
        with db_manager.get_session() as session:
            permissions = session.query(Permission).all()
            return [
                {
                    "id": permission.id,
                    "name": permission.name,
                    "code": permission.code,
                    "description": permission.description,
                    "resource_type": permission.resource_type,
                    "action": permission.action,
                }
                for permission in permissions
            ]
    except Exception as e:
        logger.error(f"Failed to get permissions: {e}")
        return []


async def create_role(role_data: Dict) -> bool:
    """创建角色"""
    try:
        with db_manager.get_session() as session:
            # 检查角色名是否已存在
            if session.query(Role).filter(Role.name == role_data["name"]).first():
                return False

            # 创建角色
            role = Role(
                name=role_data["name"],
                description=role_data["description"],
                created_at=datetime.datetime.utcnow(),
                updated_at=datetime.datetime.utcnow(),
            )
            session.add(role)
            session.commit()

            # 添加权限
            permissions = (
                session.query(Permission)
                .filter(Permission.code.in_(role_data["permissions"]))
                .all()
            )
            role.permissions = permissions
            session.commit()

            return True
    except Exception as e:
        logger.error(f"Failed to create role: {e}")
        return False


async def update_role(role_id: int, role_data: Dict) -> bool:
    """更新角色"""
    try:
        with db_manager.get_session() as session:
            role = session.query(Role).filter(Role.id == role_id).first()
            if not role:
                return False

            # 更新基本信息
            role.name = role_data.get("name", role.name)
            role.description = role_data.get("description", role.description)
            role.updated_at = datetime.datetime.utcnow()

            # 更新权限
            if "permissions" in role_data:
                permissions = (
                    session.query(Permission)
                    .filter(Permission.code.in_(role_data["permissions"]))
                    .all()
                )
                role.permissions = permissions

            session.commit()
            return True
    except Exception as e:
        logger.error(f"Failed to update role: {e}")
        return False


async def delete_role(role_id: int) -> bool:
    """删除角色"""
    try:
        with db_manager.get_session() as session:
            role = session.query(Role).filter(Role.id == role_id).first()
            if not role:
                return False

            session.delete(role)
            session.commit()
            return True
    except Exception as e:
        logger.error(f"Failed to delete role: {e}")
        return False


@require_permission("role:view")
async def roles_page():
    """角色管理页面"""
    set_env(title="角色管理")

    # 页面样式
    style = """
    <style>
        .roles-page {
            padding: 20px;
            max-width: 1200px;
            margin: 0 auto;
        }
        .roles-header {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .roles-title {
            font-size: 24px;
            font-weight: 600;
            color: #2c3e50;
        }
        .roles-table {
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
        .permission-list {
            display: flex;
            flex-wrap: wrap;
            gap: 4px;
        }
        .permission-badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 9999px;
            font-size: 12px;
            font-weight: 500;
            background: #e5e7eb;
            color: #374151;
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
        .permission-group {
            margin-bottom: 15px;
        }
        .permission-group-title {
            font-weight: 500;
            color: #2c3e50;
            margin-bottom: 10px;
        }
        .permission-checkbox {
            display: flex;
            align-items: center;
            margin-bottom: 5px;
        }
        .permission-checkbox input[type="checkbox"] {
            margin-right: 8px;
        }
        .permission-checkbox label {
            font-size: 14px;
            color: #374151;
        }
    </style>
    """

    # 获取角色列表和权限列表
    roles = get_roles()
    permissions = get_permissions()

    # 按资源类型分组权限
    grouped_permissions = {}
    for permission in permissions:
        if permission["resource_type"] not in grouped_permissions:
            grouped_permissions[permission["resource_type"]] = []
        grouped_permissions[permission["resource_type"]].append(permission)

    # 渲染页面
    clear()
    put_html(style)

    put_html(
        f"""
    <div class="roles-page">
        <div class="roles-header">
            <div class="roles-title">角色管理</div>
            <button class="action-button create-button" onclick="showCreateModal()">创建角色</button>
        </div>
        
        <div class="roles-table">
            <table class="table">
                <thead>
                    <tr>
                        <th>角色名称</th>
                        <th>描述</th>
                        <th>权限</th>
                        <th>创建时间</th>
                        <th>更新时间</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
    """
    )

    for role in roles:
        put_html(
            f"""
            <tr>
                <td>{role['name']}</td>
                <td>{role['description']}</td>
                <td>
                    <div class="permission-list">
    """
        )

        for permission in role["permissions"]:
            put_html(
                f"""
                        <span class="permission-badge">{permission}</span>
            """
            )

        put_html(
            f"""
                    </div>
                </td>
                <td>{role['created_at']}</td>
                <td>{role['updated_at']}</td>
                <td>
                    <button class="action-button edit-button" onclick="showEditModal({role['id']})">编辑</button>
                    <button class="action-button delete-button" onclick="deleteRole({role['id']})">删除</button>
                </td>
            </tr>
        """
        )

    put_html(
        """
                </tbody>
            </table>
        </div>
        
        <!-- 创建角色模态框 -->
        <div id="createModal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <div class="modal-title">创建角色</div>
                    <span class="close" onclick="hideCreateModal()">&times;</span>
                </div>
                <div class="form-group">
                    <label class="form-label">角色名称</label>
                    <input type="text" class="form-input" id="create_name">
                </div>
                <div class="form-group">
                    <label class="form-label">描述</label>
                    <input type="text" class="form-input" id="create_description">
                </div>
                <div class="form-group">
                    <label class="form-label">权限</label>
    """
    )

    for resource_type, perms in grouped_permissions.items():
        put_html(
            f"""
                    <div class="permission-group">
                        <div class="permission-group-title">{resource_type}</div>
        """
        )

        for permission in perms:
            put_html(
                f"""
                        <div class="permission-checkbox">
                            <input type="checkbox" id="create_permission_{permission['code']}" value="{permission['code']}">
                            <label for="create_permission_{permission['code']}">{permission['name']} ({permission['description']})</label>
                        </div>
            """
            )

        put_html(
            """
                    </div>
        """
        )

    put_html(
        """
                </div>
                <div class="modal-footer">
                    <button class="action-button cancel-button" onclick="hideCreateModal()">取消</button>
                    <button class="action-button create-button" onclick="createRole()">创建</button>
                </div>
            </div>
        </div>
        
        <!-- 编辑角色模态框 -->
        <div id="editModal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <div class="modal-title">编辑角色</div>
                    <span class="close" onclick="hideEditModal()">&times;</span>
                </div>
                <input type="hidden" id="edit_role_id">
                <div class="form-group">
                    <label class="form-label">角色名称</label>
                    <input type="text" class="form-input" id="edit_name">
                </div>
                <div class="form-group">
                    <label class="form-label">描述</label>
                    <input type="text" class="form-input" id="edit_description">
                </div>
                <div class="form-group">
                    <label class="form-label">权限</label>
    """
    )

    for resource_type, perms in grouped_permissions.items():
        put_html(
            f"""
                    <div class="permission-group">
                        <div class="permission-group-title">{resource_type}</div>
        """
        )

        for permission in perms:
            put_html(
                f"""
                        <div class="permission-checkbox">
                            <input type="checkbox" id="edit_permission_{permission['code']}" value="{permission['code']}">
                            <label for="edit_permission_{permission['code']}">{permission['name']} ({permission['description']})</label>
                        </div>
            """
            )

        put_html(
            """
                    </div>
        """
        )

    put_html(
        """
                </div>
                <div class="modal-footer">
                    <button class="action-button cancel-button" onclick="hideEditModal()">取消</button>
                    <button class="action-button create-button" onclick="updateRole()">保存</button>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // 显示创建角色模态框
        function showCreateModal() {
            document.getElementById('createModal').style.display = 'block';
        }
        
        // 隐藏创建角色模态框
        function hideCreateModal() {
            document.getElementById('createModal').style.display = 'none';
        }
        
        // 显示编辑角色模态框
        function showEditModal(roleId) {
            document.getElementById('edit_role_id').value = roleId;
            document.getElementById('editModal').style.display = 'block';
            
            // 获取角色信息并填充表单
            const role = roles.find(r => r.id === roleId);
            if (role) {
                document.getElementById('edit_name').value = role.name;
                document.getElementById('edit_description').value = role.description;
                
                // 设置权限复选框
                const checkboxes = document.querySelectorAll('[id^="edit_permission_"]');
                checkboxes.forEach(checkbox => {
                    checkbox.checked = role.permissions.includes(checkbox.value);
                });
            }
        }
        
        // 隐藏编辑角色模态框
        function hideEditModal() {
            document.getElementById('editModal').style.display = 'none';
        }
        
        // 创建角色
        function createRole() {
            const permissions = [];
            const checkboxes = document.querySelectorAll('[id^="create_permission_"]');
            checkboxes.forEach(checkbox => {
                if (checkbox.checked) {
                    permissions.push(checkbox.value);
                }
            });
            
            const roleData = {
                name: document.getElementById('create_name').value,
                description: document.getElementById('create_description').value,
                permissions: permissions
            };
            
            pywebio.call_js_function('create_role', roleData).then(success => {
                if (success) {
                    hideCreateModal();
                    location.reload();
                } else {
                    alert('创建角色失败，可能角色名已存在');
                }
            });
        }
        
        // 更新角色
        function updateRole() {
            const roleId = parseInt(document.getElementById('edit_role_id').value);
            
            const permissions = [];
            const checkboxes = document.querySelectorAll('[id^="edit_permission_"]');
            checkboxes.forEach(checkbox => {
                if (checkbox.checked) {
                    permissions.push(checkbox.value);
                }
            });
            
            const roleData = {
                name: document.getElementById('edit_name').value,
                description: document.getElementById('edit_description').value,
                permissions: permissions
            };
            
            pywebio.call_js
