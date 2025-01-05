"""Login模块"""

import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, Optional

import streamlit as st

from ..utils.auth import authenticate_user, create_session
from ..utils.performance import (
    PerformanceMonitor,
    measure_time,
    monitor_page_load,
    performance_monitor,
)
from ..utils.theme import apply_theme


class LoginPage:
    def __init__(self):
        self.theme = apply_theme()
        self.max_attempts = 5
        self.lockout_duration = 300  # 5分钟
        self._init_session_state()

    def _init_session_state(self):
        """初始化会话状态"""
        if "login_attempts" not in st.session_state:
            st.session_state.login_attempts = 0
        if "lockout_until" not in st.session_state:
            st.session_state.lockout_until = None

    @monitor_page_load("login")
    def render(self):
        """渲染登录页面"""
        st.title("系统登录")

        # 检查是否被锁定
        if self._is_locked_out():
            self._render_lockout_message()
            return

        # 登录表单
        with st.form("login_form"):
            username = st.text_input("用户名")
            password = st.text_input("密码", type="password")
            submit = st.form_submit_button("登录")

            if submit:
                self._handle_login(username, password)

        # 显示性能指标
        self._show_performance_metrics()

    def _is_locked_out(self) -> bool:
        """检查是否被���定"""
        if st.session_state.lockout_until is None:
            return False

        if datetime.now() > st.session_state.lockout_until:
            st.session_state.lockout_until = None
            st.session_state.login_attempts = 0
            return False

        return True

    def _render_lockout_message(self):
        """显示锁定消息"""
        remaining_time = (st.session_state.lockout_until - datetime.now()).seconds
        st.error(
            f"由于多次登录失败，账户已被临时锁定。请在 {remaining_time} 秒后重试。"
        )

    @measure_time
    def _handle_login(self, username: str, password: str):
        """处理登录请求"""
        try:
            if not username or not password:
                st.error("请输入用户名和密码")
                return

            # 密码哈希
            password_hash = hashlib.sha256(password.encode()).hexdigest()

            # 验证用户
            if self._authenticate_user(username, password_hash):
                self._login_success(username)
            else:
                self._login_failure()

        except Exception as e:
            performance_monitor.record_error()
            st.error(f"登录过程中发生错误: {str(e)}")

    @measure_time
    def _authenticate_user(self, username: str, password_hash: str) -> bool:
        """验证用户凭据"""
        try:
            result = authenticate_user(username, password_hash)
            if result:
                return True
            return False
        except Exception as e:
            performance_monitor.record_error()
            return False

    def _login_success(self, username: str):
        """处理登录成功"""
        st.success("登录成功！正在跳转...")
        st.session_state.login_attempts = 0
        create_session(username)
        time.sleep(1)
        st.experimental_rerun()

    def _login_failure(self):
        """处理登录失败"""
        st.session_state.login_attempts += 1

        if st.session_state.login_attempts >= self.max_attempts:
            st.session_state.lockout_until = datetime.now() + timedelta(
                seconds=self.lockout_duration
            )
            st.error(f"登录失败次数过多，账户已被锁定 {self.lockout_duration/60} 分钟")
        else:
            remaining_attempts = self.max_attempts - st.session_state.login_attempts
            st.error(f"用户名或密码错误。还剩 {remaining_attempts} 次尝试机会")

    def _show_performance_metrics(self):
        """显示性能指标"""
        metrics = performance_monitor.get_metrics()
        with st.expander("登录页面性能指标"):
            cols = st.columns(3)
            cols[0].metric("平均响应时间", f"{metrics['avg_response_time']:.2f}ms")
            cols[1].metric("成功率", f"{100 - metrics['error_rate']:.1f}%")
            cols[2].metric("内存使用", f"{metrics['memory_usage']:.1f}%")


# 创建登录页面实例
login_page = LoginPage()

# 渲染页面
if __name__ == "__main__":
    login_page.render()
