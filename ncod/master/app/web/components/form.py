"""
表单组件
"""

from typing import Any, Callable, Dict, List, Optional

from pywebio.input import file_upload, input, select, textarea
from pywebio.output import put_buttons, put_html, put_loading
from pywebio.pin import pin, put_input, put_select, put_textarea


def create_form(
    fields: List[Dict[str, Any]],
    on_submit: Callable[[Dict[str, Any]], None],
    title: Optional[str] = None,
    submit_text: str = "提交",
    cancel_text: Optional[str] = "取消",
) -> None:
    """创建表单

    Args:
        fields: 表单字段列表
        on_submit: 提交回调函数
        title: 表单标题
        submit_text: 提交按钮文本
        cancel_text: 取消按钮文本
    """
    if title:
        put_html(f"<h3 class='mb-4'>{title}</h3>")

    # 创建表单字段
    for field in fields:
        field_type = field.get("type", "text")

        if field_type == "select":
            put_select(
                name=field["name"],
                label=field["label"],
                options=field["options"],
                value=field.get("value"),
                required=field.get("required", False),
            )
        elif field_type == "textarea":
            put_textarea(
                name=field["name"],
                label=field["label"],
                placeholder=field.get("placeholder", ""),
                value=field.get("value", ""),
                required=field.get("required", False),
            )
        elif field_type == "file":
            put_html(
                f"""
            <div class="mb-3">
                <label class="form-label">{field['label']}</label>
                <input type="file" class="form-control" name="{field['name']}"
                       accept="{field.get('accept', '*')}"
                       {'required' if field.get('required') else ''}>
            </div>
            """
            )
        else:
            put_input(
                name=field["name"],
                type=field_type,
                label=field["label"],
                placeholder=field.get("placeholder", ""),
                value=field.get("value", ""),
                required=field.get("required", False),
            )

    # 创建按钮
    buttons = [{"label": submit_text, "value": "submit", "color": "primary"}]

    if cancel_text:
        buttons.append({"label": cancel_text, "value": "cancel", "color": "secondary"})

    def handle_click(val):
        if val == "submit":
            # 收集表单数据
            data = {}
            for field in fields:
                if field.get("type") == "file":
                    data[field["name"]] = file_upload(
                        label=field["label"], accept=field.get("accept", "*")
                    )
                else:
                    data[field["name"]] = pin[field["name"]]

            # 调用回调函数
            with put_loading():
                on_submit(data)

    put_buttons(buttons, onclick=handle_click)


def create_search_form(
    fields: List[Dict[str, Any]],
    on_search: Callable[[Dict[str, Any]], None],
    search_text: str = "搜索",
    reset_text: str = "重置",
) -> None:
    """创建搜索表单

    Args:
        fields: 搜索字段列表
        on_search: 搜索回调函数
        search_text: 搜索按钮文本
        reset_text: 重置按钮文本
    """
    put_html(
        """
    <div class="card mb-4">
        <div class="card-body">
    """
    )

    # 创建搜索字段
    put_html('<div class="row">')

    for field in fields:
        put_html('<div class="col-md-3 mb-3">')

        field_type = field.get("type", "text")
        if field_type == "select":
            put_select(
                name=field["name"], label=field["label"], options=field["options"]
            )
        else:
            put_input(
                name=field["name"],
                type=field_type,
                label=field["label"],
                placeholder=field.get("placeholder", ""),
            )

        put_html("</div>")

    put_html("</div>")

    # 创建按钮
    def handle_click(val):
        if val == "search":
            # 收集搜索条件
            data = {field["name"]: pin[field["name"]] for field in fields}

            # 调用搜索回调
            with put_loading():
                on_search(data)
        elif val == "reset":
            # 重置表单
            for field in fields:
                pin[field["name"]] = ""

    put_buttons(
        [
            {"label": search_text, "value": "search", "color": "primary"},
            {"label": reset_text, "value": "reset", "color": "secondary"},
        ],
        onclick=handle_click,
    )

    put_html(
        """
        </div>
    </div>
    """
    )


def create_filter_form(
    filters: List[Dict[str, Any]], on_filter: Callable[[Dict[str, Any]], None]
) -> None:
    """创建筛选表单

    Args:
        filters: 筛选条件列表
        on_filter: 筛选回调函数
    """
    put_html(
        """
    <div class="card mb-4">
        <div class="card-header">
            筛选条件
        </div>
        <div class="card-body">
    """
    )

    # 创建筛选条件
    for filter_item in filters:
        if filter_item["type"] == "select":
            put_select(
                name=filter_item["name"],
                label=filter_item["label"],
                options=filter_item["options"],
                multiple=filter_item.get("multiple", False),
            )
        elif filter_item["type"] == "range":
            put_html(
                f"""
            <div class="mb-3">
                <label class="form-label">{filter_item['label']}</label>
                <div class="row">
                    <div class="col">
                        <input type="number" class="form-control" \
                             name="{filter_item['name']}_min"
                               placeholder="最小值">
                    </div>
                    <div class="col">
                        <input type="number" class="form-control" \
                             name="{filter_item['name']}_max"
                               placeholder="最大值">
                    </div>
                </div>
            </div>
            """
            )
        elif filter_item["type"] == "date":
            put_html(
                f"""
            <div class="mb-3">
                <label class="form-label">{filter_item['label']}</label>
                <div class="row">
                    <div class="col">
                        <input type="date" class="form-control" \
                             name="{filter_item['name']}_start">
                    </div>
                    <div class="col">
                        <input type="date" class="form-control" \
                             name="{filter_item['name']}_end">
                    </div>
                </div>
            </div>
            """
            )
        else:
            put_input(
                name=filter_item["name"],
                type=filter_item["type"],
                label=filter_item["label"],
                placeholder=filter_item.get("placeholder", ""),
            )

    # 创建按钮
    def handle_click(val):
        if val == "apply":
            # 收集筛选条件
            data = {}
            for filter_item in filters:
                if filter_item["type"] == "range":
                    data[filter_item["name"]] = {
                        "min": pin[f"{filter_item['name']}_min"],
                        "max": pin[f"{filter_item['name']}_max"],
                    }
                elif filter_item["type"] == "date":
                    data[filter_item["name"]] = {
                        "start": pin[f"{filter_item['name']}_start"],
                        "end": pin[f"{filter_item['name']}_end"],
                    }
                else:
                    data[filter_item["name"]] = pin[filter_item["name"]]

            # 调用筛选回调
            with put_loading():
                on_filter(data)
        elif val == "reset":
            # 重置表单
            for filter_item in filters:
                if filter_item["type"] == "range":
                    pin[f"{filter_item['name']}_min"] = ""
                    pin[f"{filter_item['name']}_max"] = ""
                elif filter_item["type"] == "date":
                    pin[f"{filter_item['name']}_start"] = ""
                    pin[f"{filter_item['name']}_end"] = ""
                else:
                    pin[filter_item["name"]] = ""

    put_buttons(
        [
            {"label": "应用筛选", "value": "apply", "color": "primary"},
            {"label": "重置", "value": "reset", "color": "secondary"},
        ],
        onclick=handle_click,
    )

    put_html(
        """
        </div>
    </div>
    """
    )
