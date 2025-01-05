"""布局组件"""

from functools import wraps
from typing import Any, Callable, Dict, List, Optional

from pywebio import output, session
from pywebio.output import clear, put_html
from pywebio.session import run_js, use_scope


def page_layout(title: str = "主服务器管理系统"):
    """页面布局装饰器"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> None:
            clear()  # 清除页面内容

            # 设置页面标题
            run_js("document.title = '%s'" % title)

            with use_scope("header"):
                put_html(_get_header_html(title))

            # 创建主内容区域
            with use_scope("main"):
                func(*args, **kwargs)

            # 创建页脚
            with use_scope("footer", clear=True):
                put_html(_get_footer_html())

        return wrapper

    return decorator


def _get_header_html(title: str) -> str:
    """获取页头HTML"""
    return f"""
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container-fluid">
            <a class="navbar-brand" href="/">{title}</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" 
                    data-bs-target="#navbarNav" aria-controls="navbarNav" 
                    aria-expanded="false" aria-label="Toggle navigation">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav me-auto mb-2 mb-lg-0">
                    <li class="nav-item">
                        <a class="nav-link" href="/devices">设备管理</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/monitor">系统监控</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/users">用户管理</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/settings">系统设置</a>
                    </li>
                </ul>
                <ul class="navbar-nav">
                    <li class="nav-item">
                        <a class="nav-link" href="/profile">个人中心</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/logout">退出登录</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>
    """


def _get_footer_html() -> str:
    """获取页脚HTML"""
    return """
    <footer class="footer mt-auto py-3 bg-light">
        <div class="container">
            <span class="text-muted">© 2024 主服务器管理系统</span>
        </div>
    </footer>
    """


def create_card(
    title: str,
    content: Any,
    footer: Optional[Any] = None,
    width: Optional[str] = None,
    class_: Optional[str] = None,
) -> None:
    """创建卡片组件

    Args:
        title: 卡片标题
        content: 卡片内容
        footer: 卡片页脚
        width: 卡片宽度
        class_: 额外的CSS类
    """
    style = f"width: {width};" if width else ""
    card_class = f"card {class_ or ''}"

    put_html(
        f"""
    <div class="{card_class}" style="{style}">
        <div class="card-header">{title}</div>
        <div class="card-body">
            {content if isinstance(content, str) else ''}
        </div>
        {f'<div class="card-footer">{footer}</div>' if footer else ''}
    </div>
    """
    )

    if not isinstance(content, str):
        with use_scope("card-content", clear=True):
            put_html(content)


def create_grid(items: List[Dict[str, Any]], columns: int = 3) -> None:
    """创建网格布局

    Args:
        items: 网格项列表，每项包含title和content
        columns: 列数
    """
    col_width = 12 // columns

    put_html(
        f"""
    <div class="container">
        <div class="row">
    """
    )

    for i, item in enumerate(items):
        put_html(
            f"""
        <div class="col-md-{col_width} mb-4">
            <div class="card h-100">
                <div class="card-header">{item['title']}</div>
                <div class="card-body">
                    {item['content'] if isinstance(item['content'], str) else ''}
                </div>
            </div>
        </div>
        """
        )

        if not isinstance(item["content"], str):
            with use_scope(f"grid-item-{i}", clear=True):
                put_html(item["content"])

    put_html(
        """
        </div>
    </div>
    """
    )


def create_tabs(tabs: List[Dict[str, Any]]) -> None:
    """创建选项卡

    Args:
        tabs: 选项卡列表，每项包含title和content
    """
    put_html(
        """
    <ul class="nav nav-tabs" role="tablist">
    """
    )

    for i, tab in enumerate(tabs):
        active = "active" if i == 0 else ""
        put_html(
            f"""
        <li class="nav-item" role="presentation">
            <button class="nav-link {active}" id="tab-{i}" data-bs-toggle="tab"
                    data-bs-target="#tab-content-{i}" type="button" role="tab"
                    aria-controls="tab-content-{i}" aria-selected="{str(i == \
                         0).lower()}">
                {tab['title']}
            </button>
        </li>
        """
        )

    put_html(
        """
    </ul>
    <div class="tab-content">
    """
    )

    for i, tab in enumerate(tabs):
        active = "show active" if i == 0 else ""
        put_html(
            f"""
        <div class="tab-pane fade {active}" id="tab-content-{i}"
             role="tabpanel" aria-labelledby="tab-{i}">
            {tab['content'] if isinstance(tab['content'], str) else ''}
        </div>
        """
        )

        if not isinstance(tab["content"], str):
            with use_scope(f"tab-content-{i}", clear=True):
                put_html(tab["content"])

    put_html("</div>")
