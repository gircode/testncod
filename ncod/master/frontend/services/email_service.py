"""Email Service模块"""

import asyncio
import json
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Dict, List

from jinja2 import Template

logger = logging.getLogger(__name__)


class EmailService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmailService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._load_config()
        self._load_templates()
        self._setup_smtp()

    def _load_config(self):
        """加载配置"""
        try:
            config_path = Path(__file__).parent.parent / "config" / "config.json"
            with open(config_path) as f:
                config = json.load(f)
                self.config = config["email"]
        except Exception as e:
            logger.error(f"Failed to load email config: {e}")
            raise

    def _load_templates(self):
        """加载邮件模板"""
        try:
            template_dir = Path(__file__).parent.parent / "templates" / "email"
            self.templates = {}

            # 密码重置模板
            with open(template_dir / "password_reset.html") as f:
                self.templates["password_reset"] = Template(f.read())

            # 账户锁定通知模板
            with open(template_dir / "account_locked.html") as f:
                self.templates["account_locked"] = Template(f.read())

            # 登录通知模板
            with open(template_dir / "login_notification.html") as f:
                self.templates["login_notification"] = Template(f.read())

        except Exception as e:
            logger.error(f"Failed to load email templates: {e}")
            raise

    def _setup_smtp(self):
        """设置SMTP连接"""
        try:
            if self.config["use_tls"]:
                self.smtp = smtplib.SMTP(
                    self.config["smtp_server"], self.config["smtp_port"]
                )
                self.smtp.starttls()
            else:
                self.smtp = smtplib.SMTP_SSL(
                    self.config["smtp_server"], self.config["smtp_port"]
                )

            self.smtp.login(self.config["smtp_user"], self.config["smtp_password"])

        except Exception as e:
            logger.error(f"Failed to setup SMTP connection: {e}")
            raise

    def _create_message(
        self, to_email: str, subject: str, template_name: str, context: Dict[str, Any]
    ) -> MIMEMultipart:
        """创建邮件消息"""
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = (
                f"{self.config['from_name']} <{self.config['from_address']}>"
            )
            message["To"] = to_email

            template = self.templates[template_name]
            html = template.render(**context)

            part = MIMEText(html, "html")
            message.attach(part)

            return message

        except Exception as e:
            logger.error(f"Failed to create email message: {e}")
            raise

    async def send_password_reset(self, to_email: str, reset_link: str, username: str):
        """发送密码重置邮件"""
        try:
            message = self._create_message(
                to_email=to_email,
                subject="密码重置请求",
                template_name="password_reset",
                context={"reset_link": reset_link, "username": username},
            )

            await self._send_async(message)
            logger.info(f"Password reset email sent to {to_email}")

        except Exception as e:
            logger.error(f"Failed to send password reset email: {e}")
            raise

    async def send_account_locked(self, to_email: str, username: str, unlock_time: str):
        """发送账户锁定通知"""
        try:
            message = self._create_message(
                to_email=to_email,
                subject="账户已被锁定",
                template_name="account_locked",
                context={"username": username, "unlock_time": unlock_time},
            )

            await self._send_async(message)
            logger.info(f"Account locked notification sent to {to_email}")

        except Exception as e:
            logger.error(f"Failed to send account locked notification: {e}")
            raise

    async def send_login_notification(
        self,
        to_email: str,
        username: str,
        ip_address: str,
        user_agent: str,
        location: str,
    ):
        """发送登录通知"""
        try:
            message = self._create_message(
                to_email=to_email,
                subject="新的登录活动",
                template_name="login_notification",
                context={
                    "username": username,
                    "ip_address": ip_address,
                    "user_agent": user_agent,
                    "location": location,
                },
            )

            await self._send_async(message)
            logger.info(f"Login notification sent to {to_email}")

        except Exception as e:
            logger.error(f"Failed to send login notification: {e}")
            raise

    async def _send_async(self, message: MIMEMultipart):
        """异步发送邮件"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.smtp.send_message, message)

    def cleanup(self):
        """清理资源"""
        try:
            self.smtp.quit()
        except Exception as e:
            logger.error(f"Failed to cleanup SMTP connection: {e}")


# 创建全局实例
email_service = EmailService()
