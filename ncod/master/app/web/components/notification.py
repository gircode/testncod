"""
通知组件
"""

from typing import Optional

from pywebio.output import popup, toast


def show_success(message: str, duration: Optional[int] = 3) -> None:
    """显示成功提示

    Args:
        message: 提示消息
        duration: 显示时长（秒）
    """
    toast(message, color="success", duration=duration)


def show_error(message: str, duration: Optional[int] = 3) -> None:
    """显示错误提示

    Args:
        message: 提示消息
        duration: 显示时长（秒）
    """
    toast(message, color="danger", duration=duration)


def show_warning(message: str, duration: Optional[int] = 3) -> None:
    """显示警告提示

    Args:
        message: 提示消息
        duration: 显示时长（秒）
    """
    toast(message, color="warning", duration=duration)


def show_info(message: str, duration: Optional[int] = 3) -> None:
    """显示信息提示

    Args:
        message: 提示消息
        duration: 显示时长（秒）
    """
    toast(message, color="info", duration=duration)


def show_confirm(
    title: str,
    content: str,
    on_confirm: Optional[callable] = None,
    on_cancel: Optional[callable] = None,
    confirm_text: str = "确定",
    cancel_text: str = "取消",
) -> None:
    """显示确认对话框

    Args:
        title: 标题
        content: 内容
        on_confirm: 确认回调函数
        on_cancel: 取消回调函数
        confirm_text: 确认按钮文本
        cancel_text: 取消按钮文本
    """
    popup(
        title=title,
        content=content,
        size="md",
        buttons=[
            {"label": confirm_text, "value": True, "color": "primary"},
            {"label": cancel_text, "value": False, "color": "secondary"},
        ],
        closable=False,
        callback=lambda val: (
            on_confirm()
            if val and on_confirm
            else on_cancel() if not val and on_cancel else None
        ),
    )


def show_alert(
    title: str, content: str, level: str = "info", closable: bool = True
) -> None:
    """显示警告框

    Args:
        title: 标题
        content: 内容
        level: 警告级别（info/success/warning/danger）
        closable: 是否可关闭
    """
    popup(
        title=title,
        content=f"""
        <div class="alert alert-{level}" role="alert">
            {content}
        </div>
        """,
        size="md",
        closable=closable,
    )
