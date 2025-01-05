"""
图表组件
"""

import json
from typing import Any, Dict, List, Optional

from pywebio.output import put_html


def create_line_chart(
    title: str,
    data: List[Dict[str, Any]],
    x_field: str,
    y_field: str,
    width: str = "100%",
    height: str = "400px",
) -> None:
    """创建折线图

    Args:
        title: 图表标题
        data: 数据列表
        x_field: X轴字段名
        y_field: Y轴字段名
        width: 图表宽度
        height: 图表高度
    """
    chart_id = f"chart_{hash(title)}"

    # 准备数据
    x_data = [item[x_field] for item in data]
    y_data = [item[y_field] for item in data]

    # 创建图表
    js_code = f"""
    <div id="{chart_id}" style="width: {width}; height: {height};"></div>
    <script>
        var chart = echarts.init(document.getElementById('{chart_id}'));
        var option = {{
            title: {{
                text: '{title}',
                left: 'center'
            }},
            tooltip: {{
                trigger: 'axis'
            }},
            xAxis: {{
                type: 'category',
                data: {json.dumps(x_data)}
            }},
            yAxis: {{
                type: 'value'
            }},
            series: [{{
                data: {json.dumps(y_data)},
                type: 'line',
                smooth: true
            }}]
        }};
        chart.setOption(option);
        
        // 自适应大小
        window.addEventListener('resize', function() {{
            chart.resize();
        }});
    </script>
    """

    put_html(js_code)


def create_bar_chart(
    title: str,
    data: List[Dict[str, Any]],
    x_field: str,
    y_field: str,
    width: str = "100%",
    height: str = "400px",
) -> None:
    """创建柱状图

    Args:
        title: 图表标题
        data: 数据列表
        x_field: X轴字段名
        y_field: Y轴字段名
        width: 图表宽度
        height: 图表高度
    """
    chart_id = f"chart_{hash(title)}"

    # 准备数据
    x_data = [item[x_field] for item in data]
    y_data = [item[y_field] for item in data]

    # 创建图表
    js_code = f"""
    <div id="{chart_id}" style="width: {width}; height: {height};"></div>
    <script>
        var chart = echarts.init(document.getElementById('{chart_id}'));
        var option = {{
            title: {{
                text: '{title}',
                left: 'center'
            }},
            tooltip: {{
                trigger: 'axis'
            }},
            xAxis: {{
                type: 'category',
                data: {json.dumps(x_data)}
            }},
            yAxis: {{
                type: 'value'
            }},
            series: [{{
                data: {json.dumps(y_data)},
                type: 'bar'
            }}]
        }};
        chart.setOption(option);
        
        // 自适应大小
        window.addEventListener('resize', function() {{
            chart.resize();
        }});
    </script>
    """

    put_html(js_code)


def create_pie_chart(
    title: str,
    data: List[Dict[str, Any]],
    name_field: str,
    value_field: str,
    width: str = "100%",
    height: str = "400px",
) -> None:
    """创建饼图

    Args:
        title: 图表标题
        data: 数据列表
        name_field: 名称字段
        value_field: 值字段
        width: 图表宽度
        height: 图表高度
    """
    chart_id = f"chart_{hash(title)}"

    # 准备数据
    pie_data = [{"name": item[name_field], "value": item[value_field]} for item in data]

    # 创建图表
    js_code = f"""
    <div id="{chart_id}" style="width: {width}; height: {height};"></div>
    <script>
        var chart = echarts.init(document.getElementById('{chart_id}'));
        var option = {{
            title: {{
                text: '{title}',
                left: 'center'
            }},
            tooltip: {{
                trigger: 'item',
                formatter: '{{b}}: {{c}} ({{d}}%)'
            }},
            legend: {{
                orient: 'vertical',
                left: 'left'
            }},
            series: [{{
                type: 'pie',
                radius: '50%',
                data: {json.dumps(pie_data)},
                emphasis: {{
                    itemStyle: {{
                        shadowBlur: 10,
                        shadowOffsetX: 0,
                        shadowColor: 'rgba(0, 0, 0, 0.5)'
                    }}
                }}
            }}]
        }};
        chart.setOption(option);
        
        // 自适应大小
        window.addEventListener('resize', function() {{
            chart.resize();
        }});
    </script>
    """

    put_html(js_code)


def create_gauge_chart(
    title: str,
    value: float,
    min_value: float = 0,
    max_value: float = 100,
    width: str = "100%",
    height: str = "400px",
) -> None:
    """创建仪表盘

    Args:
        title: 图表标题
        value: 当前值
        min_value: 最小值
        max_value: 最大值
        width: 图表宽度
        height: 图表高度
    """
    chart_id = f"chart_{hash(title)}"

    # 创建图表
    js_code = f"""
    <div id="{chart_id}" style="width: {width}; height: {height};"></div>
    <script>
        var chart = echarts.init(document.getElementById('{chart_id}'));
        var option = {{
            title: {{
                text: '{title}',
                left: 'center'
            }},
            tooltip: {{
                formatter: '{{b}}: {{c}}%'
            }},
            series: [{{
                type: 'gauge',
                min: {min_value},
                max: {max_value},
                detail: {{
                    formatter: '{{value}}%'
                }},
                data: [{{
                    value: {value},
                    name: '{title}'
                }}]
            }}]
        }};
        chart.setOption(option);
        
        // 自适应大小
        window.addEventListener('resize', function() {{
            chart.resize();
        }});
    </script>
    """

    put_html(js_code)


def create_dashboard(
    charts: List[Dict[str, Any]],
    columns: int = 2,
    width: str = "100%",
    height: str = "300px",
) -> None:
    """创建仪表板

    Args:
        charts: 图表配置列表
        columns: 列数
        width: 图表宽度
        height: 图表高度
    """
    col_width = 12 // columns

    # 创建网格布局
    put_html(
        """
    <div class="container-fluid">
        <div class="row">
    """
    )

    for chart in charts:
        put_html(
            f"""
        <div class="col-md-{col_width} mb-4">
            <div class="card">
                <div class="card-body">
        """
        )

        # 根据图表类型创建不同的图表
        chart_type = chart.get("type", "line")
        if chart_type == "line":
            create_line_chart(
                title=chart["title"],
                data=chart["data"],
                x_field=chart["x_field"],
                y_field=chart["y_field"],
                width=width,
                height=height,
            )
        elif chart_type == "bar":
            create_bar_chart(
                title=chart["title"],
                data=chart["data"],
                x_field=chart["x_field"],
                y_field=chart["y_field"],
                width=width,
                height=height,
            )
        elif chart_type == "pie":
            create_pie_chart(
                title=chart["title"],
                data=chart["data"],
                name_field=chart["name_field"],
                value_field=chart["value_field"],
                width=width,
                height=height,
            )
        elif chart_type == "gauge":
            create_gauge_chart(
                title=chart["title"],
                value=chart["value"],
                min_value=chart.get("min_value", 0),
                max_value=chart.get("max_value", 100),
                width=width,
                height=height,
            )

        put_html(
            """
                </div>
            </div>
        </div>
        """
        )

    put_html(
        """
        </div>
    </div>
    """
    )
