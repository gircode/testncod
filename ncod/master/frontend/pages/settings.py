"""Settings模块"""

import json
from typing import Any, Dict

import streamlit as st

from ..api.settings import get_settings, update_settings
from ..utils.auth import require_auth
from ..utils.theme import apply_theme
from ..utils.validation import validate_email_settings, validate_monitoring_settings


class SettingsPage:
    def __init__(self):
        self.theme = apply_theme()

    @require_auth
    def render(self):
        """渲染设置页面"""
        st.title("系统设置")

        # 获取当前设置
        settings = self._load_settings()

        # 创建设置选项卡
        tabs = st.tabs(["基本设置", "监控设置", "通知设置", "备份设置", "安全设置"])

        # 基本设置
        with tabs[0]:
            self._render_basic_settings(settings.get("basic", {}))

        # 监控设置
        with tabs[1]:
            self._render_monitoring_settings(settings.get("monitoring", {}))

        # 通知设置
        with tabs[2]:
            self._render_notification_settings(settings.get("notification", {}))

        # 备份设置
        with tabs[3]:
            self._render_backup_settings(settings.get("backup", {}))

        # 安全设置
        with tabs[4]:
            self._render_security_settings(settings.get("security", {}))

    def _load_settings(self) -> Dict[str, Any]:
        """加载系统设置"""
        try:
            return get_settings()
        except Exception as e:
            st.error(f"加载设置失败: {str(e)}")
            return {}

    def _render_basic_settings(self, settings: Dict[str, Any]):
        """渲染基本设置"""
        st.subheader("基本设置")

        with st.form("basic_settings"):
            # 系统名称
            system_name = st.text_input(
                "系统名称",
                value=settings.get("system_name", ""),
                help="显示在页面标题和导航栏中的系统名称",
            )

            # 时区设置
            timezone = st.selectbox(
                "系统时区",
                options=["Asia/Shanghai", "UTC", "America/New_York", "Europe/London"],
                index=(
                    0
                    if not settings.get("timezone")
                    else [
                        "Asia/Shanghai",
                        "UTC",
                        "America/New_York",
                        "Europe/London",
                    ].index(settings.get("timezone"))
                ),
                help="系统使用的时区",
            )

            # 语言设置
            language = st.selectbox(
                "系统语言",
                options=["zh_CN", "en_US"],
                index=(
                    0
                    if not settings.get("language")
                    else ["zh_CN", "en_US"].index(settings.get("language"))
                ),
                help="系统界面语言",
            )

            # 日期格式
            date_format = st.selectbox(
                "日期格式",
                options=["YYYY-MM-DD", "DD/MM/YYYY", "MM/DD/YYYY"],
                index=(
                    0
                    if not settings.get("date_format")
                    else ["YYYY-MM-DD", "DD/MM/YYYY", "MM/DD/YYYY"].index(
                        settings.get("date_format")
                    )
                ),
                help="系统中显示的日期格式",
            )

            # 时间格式
            time_format = st.selectbox(
                "时间格式",
                options=["24小时制", "12小时制"],
                index=(
                    0
                    if not settings.get("time_format")
                    else ["24小时制", "12小时制"].index(settings.get("time_format"))
                ),
                help="系统中显示的时间格式",
            )

            if st.form_submit_button("保存基本设置"):
                try:
                    update_settings(
                        "basic",
                        {
                            "system_name": system_name,
                            "timezone": timezone,
                            "language": language,
                            "date_format": date_format,
                            "time_format": time_format,
                        },
                    )
                    st.success("基本设置已更新")
                except Exception as e:
                    st.error(f"保存设置失败: {str(e)}")

    def _render_monitoring_settings(self, settings: Dict[str, Any]):
        """渲染监控设置"""
        st.subheader("监控设置")

        with st.form("monitoring_settings"):
            # 监控间隔
            interval = st.number_input(
                "监控间隔（秒）",
                min_value=10,
                max_value=3600,
                value=settings.get("interval", 60),
                help="系统收集监控数据的时间间隔",
            )

            # 数据保留时间
            retention = st.number_input(
                "数据保留时间（天）",
                min_value=1,
                max_value=365,
                value=settings.get("retention_days", 30),
                help="监控数据保留的时间",
            )

            # CPU告警阈值
            cpu_threshold = st.slider(
                "CPU使用率告警阈值（%）",
                min_value=0,
                max_value=100,
                value=settings.get("cpu_threshold", 80),
                help="CPU使用率超过此值时触发告警",
            )

            # 内存告警阈值
            memory_threshold = st.slider(
                "内存使用率告警阈值（%）",
                min_value=0,
                max_value=100,
                value=settings.get("memory_threshold", 85),
                help="内存使用率超过此值时触发告警",
            )

            # 磁盘告警阈值
            disk_threshold = st.slider(
                "磁盘使用率告警阈值（%）",
                min_value=0,
                max_value=100,
                value=settings.get("disk_threshold", 85),
                help="磁盘使用率超过此值时触发告警",
            )

            if st.form_submit_button("保存监控设置"):
                try:
                    settings = {
                        "interval": interval,
                        "retention_days": retention,
                        "cpu_threshold": cpu_threshold,
                        "memory_threshold": memory_threshold,
                        "disk_threshold": disk_threshold,
                    }

                    # 验证设置
                    validation = validate_monitoring_settings(settings)
                    if not validation["valid"]:
                        st.error(validation["message"])
                        return

                    update_settings("monitoring", settings)
                    st.success("监控设置已更新")
                except Exception as e:
                    st.error(f"保存设置失败: {str(e)}")

    def _render_notification_settings(self, settings: Dict[str, Any]):
        """渲染通知设置"""
        st.subheader("通知设置")

        with st.form("notification_settings"):
            # 启用邮件通知
            enable_email = st.checkbox(
                "启用邮件通知",
                value=settings.get("enable_email", False),
                help="是否启用邮件通知功能",
            )

            if enable_email:
                # SMTP服务器设置
                smtp_server = st.text_input(
                    "SMTP服务器",
                    value=settings.get("smtp_server", ""),
                    help="SMTP服务器地址",
                )

                smtp_port = st.number_input(
                    "SMTP端口",
                    min_value=1,
                    max_value=65535,
                    value=settings.get("smtp_port", 587),
                    help="SMTP服务器端口",
                )

                use_tls = st.checkbox(
                    "使用TLS",
                    value=settings.get("use_tls", True),
                    help="是否使用TLS加密",
                )

                smtp_username = st.text_input(
                    "SMTP用户名",
                    value=settings.get("smtp_username", ""),
                    help="SMTP服务器用户名",
                )

                smtp_password = st.text_input(
                    "SMTP密码",
                    type="password",
                    value=settings.get("smtp_password", ""),
                    help="SMTP服务器密码",
                )

                sender_email = st.text_input(
                    "发件人邮箱",
                    value=settings.get("sender_email", ""),
                    help="发送通知的邮箱地址",
                )

                recipient_emails = st.text_area(
                    "收件人邮箱",
                    value=settings.get("recipient_emails", ""),
                    help="接收通知的邮箱地址，多个地址请用逗号分隔",
                )

            # 启用钉钉通知
            enable_dingtalk = st.checkbox(
                "启用钉钉通知",
                value=settings.get("enable_dingtalk", False),
                help="是否启用钉钉通知功能",
            )

            if enable_dingtalk:
                webhook_url = st.text_input(
                    "Webhook地址",
                    value=settings.get("webhook_url", ""),
                    help="钉钉机器人的Webhook地址",
                )

                secret = st.text_input(
                    "安全密钥",
                    type="password",
                    value=settings.get("secret", ""),
                    help="钉钉机器人的安全密钥",
                )

            if st.form_submit_button("保存通知设置"):
                try:
                    settings = {
                        "enable_email": enable_email,
                        "enable_dingtalk": enable_dingtalk,
                    }

                    if enable_email:
                        email_settings = {
                            "smtp_server": smtp_server,
                            "smtp_port": smtp_port,
                            "use_tls": use_tls,
                            "smtp_username": smtp_username,
                            "smtp_password": smtp_password,
                            "sender_email": sender_email,
                            "recipient_emails": [
                                email.strip()
                                for email in recipient_emails.split(",")
                                if email.strip()
                            ],
                        }

                        # 验证邮件设置
                        validation = validate_email_settings(email_settings)
                        if not validation["valid"]:
                            st.error(validation["message"])
                            return

                        settings.update(email_settings)

                    if enable_dingtalk:
                        settings.update({"webhook_url": webhook_url, "secret": secret})

                    update_settings("notification", settings)
                    st.success("通知设置已更新")
                except Exception as e:
                    st.error(f"保存设置失败: {str(e)}")

    def _render_backup_settings(self, settings: Dict[str, Any]):
        """渲染备份设置"""
        st.subheader("备份设置")

        with st.form("backup_settings"):
            # 启用自动备份
            enable_backup = st.checkbox(
                "启用自动备份",
                value=settings.get("enable_backup", False),
                help="是否启用自动备份功能",
            )

            if enable_backup:
                # 备份时间
                backup_time = st.time_input(
                    "备份时间",
                    value=settings.get("backup_time", "02:00"),
                    help="每天执行备份的时间",
                )

                # 备份保留时间
                retention_days = st.number_input(
                    "备份保留时间（天）",
                    min_value=1,
                    max_value=365,
                    value=settings.get("retention_days", 30),
                    help="自动备份文件保留的时间",
                )

                # 备份类型
                backup_type = st.selectbox(
                    "备份类型",
                    options=["完整备份", "增量备份"],
                    index=(
                        0
                        if not settings.get("backup_type")
                        else ["完整备份", "增量备份"].index(settings.get("backup_type"))
                    ),
                    help="选择备份类型",
                )

                # 备份目录
                backup_dir = st.text_input(
                    "备份目录",
                    value=settings.get("backup_dir", ""),
                    help="备份文件保存的目录路径",
                )

                # 压缩备份
                compress_backup = st.checkbox(
                    "压缩备份",
                    value=settings.get("compress_backup", True),
                    help="是否压缩备份文件以节省空间",
                )

                # 加密备份
                encrypt_backup = st.checkbox(
                    "加密备份",
                    value=settings.get("encrypt_backup", False),
                    help="是否加密备份文件",
                )

                if encrypt_backup:
                    encryption_key = st.text_input(
                        "加密密钥",
                        type="password",
                        value=settings.get("encryption_key", ""),
                        help="用于加密备份文件的密钥",
                    )

            if st.form_submit_button("保存备份设置"):
                try:
                    settings = {"enable_backup": enable_backup}

                    if enable_backup:
                        settings.update(
                            {
                                "backup_time": backup_time.strftime("%H:%M"),
                                "retention_days": retention_days,
                                "backup_type": backup_type,
                                "backup_dir": backup_dir,
                                "compress_backup": compress_backup,
                                "encrypt_backup": encrypt_backup,
                            }
                        )

                        if encrypt_backup:
                            settings["encryption_key"] = encryption_key

                    update_settings("backup", settings)
                    st.success("备份设置已更新")
                except Exception as e:
                    st.error(f"保存设置失败: {str(e)}")

    def _render_security_settings(self, settings: Dict[str, Any]):
        """渲染安全设置"""
        st.subheader("安全设置")

        with st.form("security_settings"):
            # 密码策略
            st.markdown("#### 密码策略")

            min_password_length = st.number_input(
                "最小密码长度",
                min_value=8,
                max_value=32,
                value=settings.get("min_password_length", 8),
                help="密码的最小长度要求",
            )

            require_uppercase = st.checkbox(
                "要求大写字母",
                value=settings.get("require_uppercase", True),
                help="密码是否必须包含大写字母",
            )

            require_lowercase = st.checkbox(
                "要求小写字母",
                value=settings.get("require_lowercase", True),
                help="密码是否必须包含小写字母",
            )

            require_numbers = st.checkbox(
                "要求数字",
                value=settings.get("require_numbers", True),
                help="密码是否必须包含数字",
            )

            require_special_chars = st.checkbox(
                "要求特殊字符",
                value=settings.get("require_special_chars", True),
                help="密码是否必须包含特殊字符",
            )

            # 登录策略
            st.markdown("#### 登录策略")

            max_login_attempts = st.number_input(
                "最大登录尝试次数",
                min_value=1,
                max_value=10,
                value=settings.get("max_login_attempts", 5),
                help="达到此次数后账户将被锁定",
            )

            lockout_duration = st.number_input(
                "账户锁定时间（分钟）",
                min_value=1,
                max_value=1440,
                value=settings.get("lockout_duration", 30),
                help="账户被锁定的持续时间",
            )

            session_timeout = st.number_input(
                "会话超时时间（分钟）",
                min_value=1,
                max_value=1440,
                value=settings.get("session_timeout", 30),
                help="用户无操作后自动退出的时间",
            )

            # IP白名单
            st.markdown("#### IP白名单")

            enable_ip_whitelist = st.checkbox(
                "启用IP白名单",
                value=settings.get("enable_ip_whitelist", False),
                help="是否启用IP白名单功能",
            )

            if enable_ip_whitelist:
                ip_whitelist = st.text_area(
                    "IP白名单",
                    value=settings.get("ip_whitelist", ""),
                    help="允许访问的IP地址，每行一个",
                )

            if st.form_submit_button("保存安全设置"):
                try:
                    settings = {
                        "min_password_length": min_password_length,
                        "require_uppercase": require_uppercase,
                        "require_lowercase": require_lowercase,
                        "require_numbers": require_numbers,
                        "require_special_chars": require_special_chars,
                        "max_login_attempts": max_login_attempts,
                        "lockout_duration": lockout_duration,
                        "session_timeout": session_timeout,
                        "enable_ip_whitelist": enable_ip_whitelist,
                    }

                    if enable_ip_whitelist:
                        settings["ip_whitelist"] = [
                            ip.strip() for ip in ip_whitelist.split("\n") if ip.strip()
                        ]

                    update_settings("security", settings)
                    st.success("安全设置已更新")
                except Exception as e:
                    st.error(f"保存设置失败: {str(e)}")


# 创建设置页面实例
settings_page = SettingsPage()

# 渲染页面
if __name__ == "__main__":
    settings_page.render()
