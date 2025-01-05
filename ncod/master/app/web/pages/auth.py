"""
认证页面
"""

from typing import Any, Dict

from pywebio.output import put_html, put_loading
from pywebio.pin import pin, put_input

from ...core.auth import authenticate_user, create_access_token
from ..components.form import create_form
from ..components.notification import show_error, show_success


def login_page() -> None:
    """登录页面"""
    # 创建登录表单
    put_html(
        """
    <div class="container">
        <div class="row justify-content-center align-items-center min-vh-100">
            <div class="col-md-6 col-lg-4">
                <div class="card shadow-sm">
                    <div class="card-body p-5">
                        <h3 class="text-center mb-4">主服务器管理系统</h3>
    """
    )

    create_form(
        fields=[
            {
                "name": "username",
                "type": "text",
                "label": "用户名",
                "required": True,
                "placeholder": "请输入用户名",
            },
            {
                "name": "password",
                "type": "password",
                "label": "密码",
                "required": True,
                "placeholder": "请输入密码",
            },
        ],
        on_submit=handle_login,
        submit_text="登录",
    )

    put_html(
        """
                    </div>
                </div>
            </div>
        </div>
    </div>
    """
    )


async def handle_login(data: Dict[str, Any]) -> None:
    """处理登录请求

    Args:
        data: 表单数据
    """
    try:
        with put_loading():
            # 验证用户
            user = await authenticate_user(data["username"], data["password"])
            if not user:
                show_error("用户名或密码错误")
                return

            # 创建访问令牌
            access_token = create_access_token({"sub": user.username})

            # 保存令牌到会话
            pin["access_token"] = access_token

            show_success("登录成功")

            # 重定向到首页
            put_html('<script>window.location.href = "/";</script>')

    except Exception as e:
        show_error(f"登录失败: {str(e)}")


def logout_page() -> None:
    """退出登录页面"""
    try:
        # 清除会话数据
        pin["access_token"] = None

        show_success("已退出登录")

        # 重定向到登录页
        put_html('<script>window.location.href = "/login";</script>')

    except Exception as e:
        show_error(f"退出失败: {str(e)}")


def register_page() -> None:
    """注册页面"""
    put_html(
        """
    <div class="container">
        <div class="row justify-content-center align-items-center min-vh-100">
            <div class="col-md-6">
                <div class="card shadow-sm">
                    <div class="card-body p-5">
                        <h3 class="text-center mb-4">注册账号</h3>
    """
    )

    create_form(
        fields=[
            {
                "name": "username",
                "type": "text",
                "label": "用户名",
                "required": True,
                "placeholder": "请输入用户名",
            },
            {
                "name": "password",
                "type": "password",
                "label": "密码",
                "required": True,
                "placeholder": "请输入密码",
            },
            {
                "name": "confirm_password",
                "type": "password",
                "label": "确认密码",
                "required": True,
                "placeholder": "请再次输入密码",
            },
            {
                "name": "email",
                "type": "email",
                "label": "邮箱",
                "required": True,
                "placeholder": "请输入邮箱",
            },
        ],
        on_submit=handle_register,
        submit_text="注册",
    )

    put_html(
        """
                    </div>
                </div>
            </div>
        </div>
    </div>
    """
    )


async def handle_register(data: Dict[str, Any]) -> None:
    """处理注册请求

    Args:
        data: 表单数据
    """
    try:
        # 验证密码
        if data["password"] != data["confirm_password"]:
            show_error("两次输入的密码不一致")
            return

        with put_loading():
            # 创建用户
            user = await create_user(
                username=data["username"],
                password=data["password"],
                email=data["email"],
            )

            show_success("注册成功，请登录")

            # 重定向到登录页
            put_html('<script>window.location.href = "/login";</script>')

    except Exception as e:
        show_error(f"注册失败: {str(e)}")


def forgot_password_page() -> None:
    """忘记密码页面"""
    put_html(
        """
    <div class="container">
        <div class="row justify-content-center align-items-center min-vh-100">
            <div class="col-md-6">
                <div class="card shadow-sm">
                    <div class="card-body p-5">
                        <h3 class="text-center mb-4">重置密码</h3>
    """
    )

    create_form(
        fields=[
            {
                "name": "email",
                "type": "email",
                "label": "邮箱",
                "required": True,
                "placeholder": "请输入注册时使用的邮箱",
            }
        ],
        on_submit=handle_forgot_password,
        submit_text="发送重置链接",
    )

    put_html(
        """
                    </div>
                </div>
            </div>
        </div>
    </div>
    """
    )


async def handle_forgot_password(data: Dict[str, Any]) -> None:
    """处理忘记密码请求

    Args:
        data: 表单数据
    """
    try:
        with put_loading():
            # 发送重置密码邮件
            await send_reset_password_email(data["email"])

            show_success("重置密码链接已发送到您的邮箱")

            # 重定向到登录页
            put_html('<script>window.location.href = "/login";</script>')

    except Exception as e:
        show_error(f"发送重置链接失败: {str(e)}")


def reset_password_page(token: str) -> None:
    """重置密码页面

    Args:
        token: 重置密码令牌
    """
    put_html(
        """
    <div class="container">
        <div class="row justify-content-center align-items-center min-vh-100">
            <div class="col-md-6">
                <div class="card shadow-sm">
                    <div class="card-body p-5">
                        <h3 class="text-center mb-4">设置新密码</h3>
    """
    )

    create_form(
        fields=[
            {
                "name": "password",
                "type": "password",
                "label": "新密码",
                "required": True,
                "placeholder": "请输入新密码",
            },
            {
                "name": "confirm_password",
                "type": "password",
                "label": "确认密码",
                "required": True,
                "placeholder": "请再次输入新密码",
            },
        ],
        on_submit=lambda data: handle_reset_password(token, data),
        submit_text="重置密码",
    )

    put_html(
        """
                    </div>
                </div>
            </div>
        </div>
    </div>
    """
    )


async def handle_reset_password(token: str, data: Dict[str, Any]) -> None:
    """处理重置密码请求

    Args:
        token: 重置密码令牌
        data: 表单数据
    """
    try:
        # 验证密码
        if data["password"] != data["confirm_password"]:
            show_error("两次输入的密码不一致")
            return

        with put_loading():
            # 重置密码
            await reset_password(token, data["password"])

            show_success("密码重置成功，请登录")

            # 重定向到登录页
            put_html('<script>window.location.href = "/login";</script>')

    except Exception as e:
        show_error(f"重置密码失败: {str(e)}")
