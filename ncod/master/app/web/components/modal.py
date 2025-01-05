"""
模态框组件
"""

from typing import Any, Dict, List, Optional

from pywebio.output import put_buttons, put_html, put_loading
from pywebio.pin import pin


def create_modal(
    title: str,
    content: Any,
    size: str = "md",
    footer_buttons: Optional[List[Dict[str, Any]]] = None,
    closable: bool = True,
    centered: bool = True,
    scrollable: bool = False,
) -> None:
    """创建模态框

    Args:
        title: 标题
        content: 内容
        size: 大小（sm/md/lg/xl）
        footer_buttons: 页脚按钮列表
        closable: 是否可关闭
        centered: 是否居中
        scrollable: 是否可滚动
    """
    modal_id = f"modal_{hash(title)}"

    # 创建模态框HTML
    modal_html = f"""
    <div class="modal fade" id="{modal_id}" tabindex="-1" role="dialog"
         aria-labelledby="{modal_id}Label" aria-hidden="true">
        <div class="modal-dialog modal-{size} {'modal-dialog-centered' if centered else \
             ''} 
                {'modal-dialog-scrollable' if scrollable else ''}">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="{modal_id}Label">{title}</h5>
                    {'''
                    <button type="button" class="btn-close" data-bs-dismiss="modal" 
                            aria-label="Close"></button>
                    ''' if closable else ''}
                </div>
                <div class="modal-body">
                    {content if isinstance(content, str) else ''}
                </div>
                {'''
                <div class="modal-footer">
                    {buttons_html}
                </div>
                ''' if footer_buttons else ''}
            </div>
        </div>
    </div>
    """

    # 创建按钮HTML
    if footer_buttons:
        buttons_html = ""
        for button in footer_buttons:
            button_type = button.get("type", "button")
            button_class = f"btn btn-{button.get('color', 'primary')}"
            if button.get("outline"):
                button_class += " btn-outline"
            if button.get("size"):
                button_class += f" btn-{button.get('size')}"

            buttons_html += f"""
            <button type="{button_type}" class="{button_class}"
                    {'data-bs-dismiss="modal"' if button.get('dismiss') else ''}
                    onclick="handleModalAction('{modal_id}', '{button.get('value')}')">
                {button.get('label', 'Button')}
            </button>
            """

    # 添加JavaScript
    js_code = f"""
    <script>
    function handleModalAction(modalId, action) {{
        // 发送消息给PyWebIO
        window.parent.postMessage({{
            type: 'modal_action',
            modal_id: modalId,
            action: action
        }}, '*');
        
        // 关闭模态框
        if (action !== 'cancel') {{
            const modal = bootstrap.Modal.getInstance(document.getElementById(modalId));
            modal.hide();
        }}
    }}
    
    // 显示模态框
    const modal = new bootstrap.Modal(document.getElementById('{modal_id}'));
    modal.show();
    </script>
    """

    # 输出HTML
    put_html(modal_html + js_code)

    # 如果内容不是字符串，在模态框主体中显示内容
    if not isinstance(content, str):
        with put_loading():
            put_html(content)


def create_form_modal(
    title: str,
    fields: List[Dict[str, Any]],
    on_submit: callable,
    size: str = "md",
    submit_text: str = "保存",
    cancel_text: str = "取消",
) -> None:
    """创建表单模态框

    Args:
        title: 标题
        fields: 表单字段列表
        on_submit: 提交回调函数
        size: 大小（sm/md/lg/xl）
        submit_text: 提交按钮文本
        cancel_text: 取消按钮文本
    """
    from .form import create_form

    # 创建表单内容
    form_content = create_form(
        fields=fields,
        on_submit=lambda data: handle_form_submit(data, on_submit),
        submit_text=submit_text,
        cancel_text=cancel_text,
    )

    # 创建模态框
    create_modal(title=title, content=form_content, size=size, closable=True)


def handle_form_submit(data: Dict[str, Any], callback: callable) -> None:
    """处理表单提交

    Args:
        data: 表单数据
        callback: 回调函数
    """
    try:
        with put_loading():
            callback(data)
    except Exception as e:
        from .notification import show_error

        show_error(str(e))


def create_confirm_modal(
    title: str,
    content: str,
    on_confirm: callable,
    confirm_text: str = "确定",
    cancel_text: str = "取消",
    danger: bool = False,
) -> None:
    """创建确认模态框

    Args:
        title: 标题
        content: 内容
        on_confirm: 确认回调函数
        confirm_text: 确认按钮文本
        cancel_text: 取消按钮文本
        danger: 是否为危险操作
    """
    create_modal(
        title=title,
        content=content,
        size="sm",
        footer_buttons=[
            {
                "label": confirm_text,
                "value": "confirm",
                "color": "danger" if danger else "primary",
                "onclick": on_confirm,
            },
            {
                "label": cancel_text,
                "value": "cancel",
                "color": "secondary",
                "dismiss": True,
            },
        ],
        closable=True,
        centered=True,
    )
