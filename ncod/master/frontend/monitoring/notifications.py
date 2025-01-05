"""
Monitoring Notifications Module
"""

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional

import requests
import yaml

logger = logging.getLogger(__name__)


class NotificationChannel:
    """Base class for notification channels"""

    def __init__(self, name: str, type: str):
        """Initialize notification channel"""
        self.name = name
        self.type = type

    def send(self, subject: str, message: str, **kwargs):
        """Send notification"""
        raise NotImplementedError

    def to_dict(self) -> Dict[str, Any]:
        """Convert channel to dictionary"""
        return {"name": self.name, "type": self.type}


class EmailChannel(NotificationChannel):
    """Email notification channel"""

    def __init__(
        self,
        name: str,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        from_address: str,
        to_addresses: List[str],
        use_tls: bool = True,
    ):
        """Initialize email channel"""
        super().__init__(name, "email")
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_address = from_address
        self.to_addresses = to_addresses
        self.use_tls = use_tls

    def send(self, subject: str, message: str, **kwargs):
        """Send email notification"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg["From"] = self.from_address
            msg["To"] = ", ".join(self.to_addresses)
            msg["Subject"] = subject

            # Add message body
            msg.attach(MIMEText(message, "plain"))

            # Connect to SMTP server
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)

            logger.info(f"Sent email notification to {', '.join(self.to_addresses)}")

        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            raise

    def to_dict(self) -> Dict[str, Any]:
        """Convert channel to dictionary"""
        return {
            **super().to_dict(),
            "smtp_host": self.smtp_host,
            "smtp_port": self.smtp_port,
            "username": self.username,
            "from_address": self.from_address,
            "to_addresses": self.to_addresses,
            "use_tls": self.use_tls,
        }


class SlackChannel(NotificationChannel):
    """Slack notification channel"""

    def __init__(
        self, name: str, webhook_url: str, channel: str, username: str = "NCOD Monitor"
    ):
        """Initialize Slack channel"""
        super().__init__(name, "slack")
        self.webhook_url = webhook_url
        self.channel = channel
        self.username = username

    def send(self, subject: str, message: str, **kwargs):
        """Send Slack notification"""
        try:
            # Prepare payload
            payload = {
                "channel": self.channel,
                "username": self.username,
                "text": f"*{subject}*\n{message}",
                "icon_emoji": ":warning:",
            }

            # Send request
            response = requests.post(self.webhook_url, json=payload)
            response.raise_for_status()

            logger.info(f"Sent Slack notification to channel {self.channel}")

        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            raise

    def to_dict(self) -> Dict[str, Any]:
        """Convert channel to dictionary"""
        return {
            **super().to_dict(),
            "webhook_url": self.webhook_url,
            "channel": self.channel,
            "username": self.username,
        }


class WebhookChannel(NotificationChannel):
    """Webhook notification channel"""

    def __init__(
        self,
        name: str,
        url: str,
        method: str = "POST",
        headers: Optional[Dict[str, str]] = None,
        template: Optional[Dict[str, Any]] = None,
    ):
        """Initialize webhook channel"""
        super().__init__(name, "webhook")
        self.url = url
        self.method = method
        self.headers = headers or {}
        self.template = template or {}

    def send(self, subject: str, message: str, **kwargs):
        """Send webhook notification"""
        try:
            # Prepare payload using template
            payload = {
                **self.template,
                "subject": subject,
                "message": message,
                **kwargs,
            }

            # Send request
            response = requests.request(
                method=self.method, url=self.url, headers=self.headers, json=payload
            )
            response.raise_for_status()

            logger.info(f"Sent webhook notification to {self.url}")

        except Exception as e:
            logger.error(f"Failed to send webhook notification: {e}")
            raise

    def to_dict(self) -> Dict[str, Any]:
        """Convert channel to dictionary"""
        return {
            **super().to_dict(),
            "url": self.url,
            "method": self.method,
            "headers": self.headers,
            "template": self.template,
        }


class NotificationManager:
    """Class for managing monitoring notifications"""

    def __init__(self):
        """Initialize notification manager"""
        self.channels: Dict[str, NotificationChannel] = {}

    def add_channel(self, channel: NotificationChannel):
        """Add notification channel"""
        self.channels[channel.name] = channel

    def remove_channel(self, name: str):
        """Remove notification channel"""
        if name in self.channels:
            del self.channels[name]

    def get_channel(self, name: str) -> Optional[NotificationChannel]:
        """Get notification channel by name"""
        return self.channels.get(name)

    def send_notification(
        self, subject: str, message: str, channels: Optional[List[str]] = None, **kwargs
    ):
        """Send notification to specified channels"""
        channels = channels or list(self.channels.keys())

        for channel_name in channels:
            channel = self.get_channel(channel_name)
            if channel:
                try:
                    channel.send(subject, message, **kwargs)
                except Exception as e:
                    logger.error(
                        f"Failed to send notification via channel {channel_name}: {e}"
                    )

    def save_config(self, output_dir: str):
        """Save notification configuration to file"""
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "notification_config.yml")

        config = {
            "channels": {
                name: channel.to_dict() for name, channel in self.channels.items()
            }
        }

        with open(output_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False)

        return output_path

    def load_config(self, config_path: str):
        """Load notification configuration from file"""
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        for name, channel_config in config.get("channels", {}).items():
            channel_type = channel_config.get("type")

            if channel_type == "email":
                channel = EmailChannel(
                    name=name,
                    smtp_host=channel_config["smtp_host"],
                    smtp_port=channel_config["smtp_port"],
                    username=channel_config["username"],
                    password=channel_config["password"],
                    from_address=channel_config["from_address"],
                    to_addresses=channel_config["to_addresses"],
                    use_tls=channel_config.get("use_tls", True),
                )
            elif channel_type == "slack":
                channel = SlackChannel(
                    name=name,
                    webhook_url=channel_config["webhook_url"],
                    channel=channel_config["channel"],
                    username=channel_config.get("username", "NCOD Monitor"),
                )
            elif channel_type == "webhook":
                channel = WebhookChannel(
                    name=name,
                    url=channel_config["url"],
                    method=channel_config.get("method", "POST"),
                    headers=channel_config.get("headers"),
                    template=channel_config.get("template"),
                )
            else:
                logger.warning(f"Unknown channel type: {channel_type}")
                continue

            self.add_channel(channel)

    def get_yaml(self) -> str:
        """Get configuration as YAML string"""
        config = {
            "channels": {
                name: channel.to_dict() for name, channel in self.channels.items()
            }
        }
        return yaml.dump(config, default_flow_style=False)

    def get_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary"""
        return {
            "channels": {
                name: channel.to_dict() for name, channel in self.channels.items()
            }
        }
