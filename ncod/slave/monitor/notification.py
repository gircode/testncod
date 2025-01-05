"""通知系统"""

import asyncio
import aiosmtplib
import json
import aiohttp
from email.mime.text import MIMEText
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass
from jinja2 import Environment, FileSystemLoader
from ncod.core.logger import setup_logger
from ncod.core.config import config

logger = setup_logger("notification")

# 初始化模板引擎
template_env = Environment(loader=FileSystemLoader("templates/notifications"))


@dataclass
class NotificationChannel:
    """通知渠道"""

    name: str
    type: str  # email, webhook, sms
    config: Dict
    enabled: bool = True


@dataclass
class NotificationRule:
    """通知规则"""

    name: str
    type: str  # alert, fault, metric
    severity: List[str]
    channels: List[str]
    template: str
    enabled: bool = True


class NotificationService:
    """通知服务"""

    def __init__(self):
        self.channels: Dict[str, NotificationChannel] = {}
        self.rules: Dict[str, NotificationRule] = {}
        self.notification_history: List[Dict] = []
        self.max_history_size = config.notification_history_size
        self._load_config()

    def _load_config(self):
        """加载配置"""
        try:
            # 加载通知渠道
            self.channels = {
                "email": NotificationChannel(
                    name="email",
                    type="email",
                    config={
                        "smtp_server": config.smtp_server,
                        "smtp_port": config.smtp_port,
                        "smtp_user": config.smtp_user,
                        "smtp_password": config.smtp_password,
                        "from_addr": config.notification_email_from,
                        "to_addrs": config.notification_email_to,
                        "use_tls": config.smtp_use_tls,
                    },
                ),
                "webhook": NotificationChannel(
                    name="webhook",
                    type="webhook",
                    config={
                        "url": config.notification_webhook_url,
                        "headers": config.notification_webhook_headers,
                        "timeout": config.webhook_timeout,
                    },
                ),
                "dingtalk": NotificationChannel(
                    name="dingtalk",
                    type="dingtalk",
                    config={
                        "webhook": config.dingtalk_webhook,
                        "secret": config.dingtalk_secret,
                    },
                ),
            }

            # 加载通知规则
            self.rules = {
                "critical_alert": NotificationRule(
                    name="critical_alert",
                    type="alert",
                    severity=["critical"],
                    channels=["email", "webhook", "dingtalk"],
                    template="critical_alert.html",
                ),
                "major_fault": NotificationRule(
                    name="fault",
                    type="fault",
                    severity=["critical", "major"],
                    channels=["email", "dingtalk"],
                    template="fault.html",
                ),
                "warning_alert": NotificationRule(
                    name="warning_alert",
                    type="alert",
                    severity=["warning"],
                    channels=["email"],
                    template="warning_alert.html",
                ),
            }
        except Exception as e:
            logger.error(f"Error loading notification config: {e}")

    async def send_notification(
        self,
        notification_type: str,
        severity: str,
        title: str,
        content: Dict,
        template: Optional[str] = None,
        retry_count: int = 3,
    ) -> bool:
        """发送通知"""
        try:
            # 查找匹配的规则
            matched_rules = [
                rule
                for rule in self.rules.values()
                if (
                    rule.type == notification_type
                    and severity in rule.severity
                    and rule.enabled
                )
            ]

            if not matched_rules:
                return False

            success = False
            for rule in matched_rules:
                # 发送到所有配置的渠道
                for channel_name in rule.channels:
                    channel = self.channels.get(channel_name)
                    if not channel or not channel.enabled:
                        continue

                    # 使用指定模板或规则默认模板
                    template_name = template or rule.template
                    formatted_content = await self._format_content(
                        template_name, title, content
                    )

                    # 重试机制
                    for attempt in range(retry_count):
                        try:
                            if await self._send_to_channel(
                                channel, title, formatted_content
                            ):
                                success = True
                                break
                            await asyncio.sleep(2**attempt)  # 指数退避
                        except Exception as e:
                            logger.error(
                                f"Attempt {attempt + 1} failed for "
                                f"channel {channel.name}: {e}"
                            )

            # 记录通知历史
            self._add_to_history(
                {
                    "type": notification_type,
                    "severity": severity,
                    "title": title,
                    "content": content,
                    "timestamp": datetime.utcnow().isoformat(),
                    "success": success,
                }
            )

            return success
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return False

    def _add_to_history(self, entry: Dict):
        """添加到历史记录"""
        self.notification_history.append(entry)
        # 限制历史记录大小
        if len(self.notification_history) > self.max_history_size:
            self.notification_history = self.notification_history[
                -self.max_history_size :
            ]

    async def _format_content(
        self, template_name: str, title: str, content: Dict
    ) -> str:
        """格式化内容"""
        try:
            template = template_env.get_template(template_name)
            return await asyncio.to_thread(
                template.render,
                title=title,
                content=content,
                timestamp=datetime.utcnow(),
            )
        except Exception as e:
            logger.error(f"Error formatting content: {e}")
            return f"<h2>{title}</h2>" f"<pre>{json.dumps(content, indent=2)}</pre>"

    async def _send_to_channel(
        self, channel: NotificationChannel, title: str, content: str
    ) -> bool:
        """发送到指定渠道"""
        try:
            if channel.type == "email":
                return await self._send_email(channel.config, title, content)
            elif channel.type == "webhook":
                return await self._send_webhook(channel.config, title, content)
            elif channel.type == "dingtalk":
                return await self._send_dingtalk(channel.config, title, content)
            return False
        except Exception as e:
            logger.error(f"Error sending to channel {channel.name}: {e}")
            return False

    async def _send_email(self, config: Dict, title: str, content: str) -> bool:
        """发送邮件"""
        try:
            msg = MIMEText(content, "html", "utf-8")
            msg["Subject"] = title
            msg["From"] = config["from_addr"]
            msg["To"] = ", ".join(config["to_addrs"])

            async with aiosmtplib.SMTP(
                hostname=config["smtp_server"],
                port=config["smtp_port"],
                use_tls=config.get("use_tls", False),
            ) as server:
                if config.get("smtp_user"):
                    await server.login(config["smtp_user"], config["smtp_password"])
                await server.send_message(msg)
            return True
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False

    async def _send_webhook(self, config: Dict, title: str, content: str) -> bool:
        """发送Webhook"""
        try:
            timeout = aiohttp.ClientTimeout(total=config.get("timeout", 10))
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    config["url"],
                    json={"title": title, "content": content},
                    headers=config.get("headers", {}),
                ) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Error sending webhook: {e}")
            return False

    async def _send_dingtalk(self, config: Dict, title: str, content: str) -> bool:
        """发送钉钉通知"""
        try:
            msg = {"msgtype": "markdown", "markdown": {"title": title, "text": content}}
            async with aiohttp.ClientSession() as session:
                async with session.post(config["webhook"], json=msg) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Error sending dingtalk notification: {e}")
            return False

    def get_notification_history(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        types: Optional[List[str]] = None,
        severity: Optional[List[str]] = None,
    ) -> List[Dict]:
        """获取通知历史"""
        try:
            history = self.notification_history

            if start_time:
                history = [
                    n
                    for n in history
                    if datetime.fromisoformat(n["timestamp"]) >= start_time
                ]
            if end_time:
                history = [
                    n
                    for n in history
                    if datetime.fromisoformat(n["timestamp"]) <= end_time
                ]
            if types:
                history = [n for n in history if n["type"] in types]
            if severity:
                history = [n for n in history if n["severity"] in severity]

            return history
        except Exception as e:
            logger.error(f"Error getting notification history: {e}")
            return []


# 创建全局通知服务实例
notification_service = NotificationService()
