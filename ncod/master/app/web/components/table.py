"""
表格组件
"""
from typing import Any, Callable, Dict, List, Optional

from pywebio.output import put_buttons, put_html, put_loading
from pywebio.pin import pin, put_input, put_select


def create_table(
    headers: List[str],
    data: List[Dict[str, Any]],
    actions: Optional[List[Dict[str, Any]]] = None,
    page_size: int = 10,
    search: bool = True,
    sort: bool = True,
) -> None:
    """创建数据表格

    Args:
        headers: 表头列表
        data: 数据列表
        actions: 操作按钮列表，每项包含text和callback
        page_size: 每页显示的行数
        search: 是否显示搜索框
        sort: 是否支持排序
    """
    table_id = "data-table"

    # 创建搜索框
    if search:
        put_input("search", type="text", label="搜索", placeholder="输入关键字搜索...")

    # 创建表格头部
    header_html = "<thead><tr>"
    for header in headers:
        if sort:
            header_html += f"""
            <th class="sortable" onclick="sortTable('{table_id}', \
                 {headers.index(header)})">
                {header}
                <span class="sort-icon">⇅</span>
            </th>
            """
        else:
            header_html += f"<th>{header}</th>"
    if actions:
        header_html += "<th>操作</th>"
    header_html += "</tr></thead>"

    # 创建表格主体
    body_html = "<tbody>"
    for row in data:
        body_html += "<tr>"
        for header in headers:
            body_html += f"<td>{row.get(header, '')}</td>"
        if actions:
            body_html += "<td>"
            for action in actions:
                body_html += f"""
                <button class="btn btn-sm btn-{action.get('type', 'primary')} me-1"
                        onclick="handleAction('{action['text']}', {row['id']})">
                    {action['text']}
                </button>
                """
            body_html += "</td>"
        body_html += "</tr>"
    body_html += "</tbody>"

    # 创建分页控件
    total_pages = (len(data) + page_size - 1) // page_size
    pagination_html = """
    <div class="d-flex justify-content-between align-items-center mt-3">
        <div class="datatable-info">
            显示 {start} 到 {end}，共 {total} 条记录
        </div>
        <nav>
            <ul class="pagination mb-0">
    """

    for i in range(total_pages):
        active = "active" if i == 0 else ""
        pagination_html += f"""
        <li class="page-item {active}">
            <a class="page-link" href="#" onclick="changePage('{table_id}', {i})">{i \
            1}</a>
        </li>
        """

    pagination_html += """
            </ul>
        </nav>
    </div>
    """

    # 组合所有HTML
    table_html = f"""
    <div class="table-responsive">
        <table id="{table_id}" class="table table-striped table-hover">
            {header_html}
            {body_html}
        </table>
        {pagination_html}
    </div>
    """

    # 添加JavaScript函数
    js_code = """
    <script>
    function sortTable(tableId, colIndex) {
        const table = document.getElementById(tableId);
        const rows = Array.from(table.rows).slice(1);
        const isAsc = table.rows[0].cells[colIndex].classList.contains('asc');
        
        rows.sort((a, b) => {
            const aVal = a.cells[colIndex].textContent;
            const bVal = b.cells[colIndex].textContent;
            return isAsc ? bVal.localeCompare(aVal) : aVal.localeCompare(bVal);
        });
        
        rows.forEach(row => table.tBodies[0].appendChild(row));
        
        // 更新排序图标
        const headers = table.rows[0].cells;
        for (let i = 0; i < headers.length; i++) {
            headers[i].classList.remove('asc', 'desc');
        }
        table.rows[0].cells[colIndex].classList.add(isAsc ? 'desc' : 'asc');
    }
    
    function handleAction(action, rowId) {
        // 这里需要与PyWebIO交互，触发回调函数
        window.parent.postMessage({
            type: 'table_action',
            action: action,
            row_id: rowId
        }, '*');
    }
    
    function changePage(tableId, pageNum) {
        const table = document.getElementById(tableId);
        const rows = table.tBodies[0].rows;
        const pageSize = 10;  // 与Python代码中的page_size保持一致
        
        for (let i = 0; i < rows.length; i++) {
            rows[i].style.display = 
                (i >= pageNum * pageSize && i < (pageNum + 1) * pageSize) ? '' : 'none';
        }
        
        // 更新分页按钮状态
        const pagination = table.parentElement.querySelector('.pagination');
        const pages = pagination.getElementsByTagName('li');
        for (let i = 0; i < pages.length; i++) {
            pages[i].classList.remove('active');
        }
        pages[pageNum].classList.add('active');
        
        // 更新显示信息
        const info = table.parentElement.querySelector('.datatable-info');
        const total = rows.length;
        const start = pageNum * pageSize + 1;
        const end = Math.min((pageNum + 1) * pageSize, total);
        info.textContent = `显示 ${start} 到 ${end}，共 ${total} 条记录`;
    }
    
    // 初始化第一页
    window.onload = function() {
        changePage('${table_id}', 0);
    };
    </script>
    
    <style>
    .sortable {
        cursor: pointer;
    }
    .sort-icon {
        display: inline-block;
        width: 12px;
        height: 12px;
        margin-left: 5px;
    }
    th.asc .sort-icon::after {
        content: '↑';
    }
    th.desc .sort-icon::after {
        content: '↓';
    }
    </style>
    """

    put_html(table_html + js_code)


def create_crud_table(
    model: str,
    headers: List[str],
    data: List[Dict[str, Any]],
    create_form: Optional[Dict[str, Any]] = None,
    edit_form: Optional[Dict[str, Any]] = None,
    delete_confirm: bool = True,
    page_size: int = 10,
) -> None:
    """创建CRUD表格

    Args:
        model: 模型名称
        headers: 表头列表
        data: 数据列表
        create_form: 创建表单配置
        edit_form: 编辑表单配置
        delete_confirm: 是否显示删除确认
        page_size: 每页显示的行数
    """
    # 创建按钮
    if create_form:
        put_buttons(
            [{"label": f"新建{model}", "value": "create", "color": "primary"}],
            onclick=lambda _: show_create_form(create_form),
        )

    # 创建表格
    actions = [
        {
            "text": "编辑",
            "type": "primary",
            "callback": lambda row_id: show_edit_form(edit_form, row_id),
        }
    ]

    if delete_confirm:
        actions.append(
            {
                "text": "删除",
                "type": "danger",
                "callback": lambda row_id: show_delete_confirm(model, row_id),
            }
        )

    create_table(headers, data, actions, page_size)


def show_create_form(form_config: Dict[str, Any]) -> None:
    """显示创建表单"""
    with put_loading():
        for field in form_config["fields"]:
            if field["type"] == "select":
                put_select(
                    name=field["name"], label=field["label"], options=field["options"]
                )
            else:
                put_input(
                    name=field["name"],
                    type=field["type"],
                    label=field["label"],
                    placeholder=field.get("placeholder", ""),
                )

        put_buttons(
            [
                {"label": "保存", "value": "save", "color": "primary"},
                {"label": "取消", "value": "cancel", "color": "secondary"},
            ],
            onclick=lambda val: handle_form_action(val, form_config),
        )


def show_edit_form(form_config: Dict[str, Any], row_id: int) -> None:
    """显示编辑表单"""
    with put_loading():
        # 获取数据
        data = form_config["get_data"](row_id)

        for field in form_config["fields"]:
            value = data.get(field["name"])
            if field["type"] == "select":
                put_select(
                    name=field["name"],
                    label=field["label"],
                    options=field["options"],
                    value=value,
                )
            else:
                put_input(
                    name=field["name"],
                    type=field["type"],
                    label=field["label"],
                    value=value,
                    placeholder=field.get("placeholder", ""),
                )

        put_buttons(
            [
                {"label": "保存", "value": "save", "color": "primary"},
                {"label": "取消", "value": "cancel", "color": "secondary"},
            ],
            onclick=lambda val: handle_form_action(val, form_config, row_id),
        )


def show_delete_confirm(model: str, row_id: int) -> None:
    """显示删除确认对话框"""
    put_html(
        f"""
    <div class="modal fade" id="deleteModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">确认删除</h5>
                    <button type="button" class="btn-close" \
                         data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    确定要删除这条{model}记录吗？此操作不可恢复。
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" \
                         data-bs-dismiss="modal">取消</button>
                    <button type="button" class="btn btn-danger" \
                         onclick="handleDelete({row_id})">
                        确定删除
                    </button>
                </div>
            </div>
        </div>
    </div>
    """
    )


def handle_form_action(
    action: str, form_config: Dict[str, Any], row_id: Optional[int] = None
) -> None:
    """处理表单动作"""
    if action == "save":
        # 获取表单数据
        data = {field["name"]: pin[field["name"]] for field in form_config["fields"]}

        # 保存数据
        if row_id is None:
            form_config["on_create"](data)
        else:
            form_config["on_edit"](row_id, data)

    # 关闭表单
    put_html('<script>$("#formModal").modal("hide");</script>')