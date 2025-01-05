"""
邮件服务
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema
from pydantic import EmailStr

from ..core.config import settings

# 配置日志
logger = logging.getLogger(__name__)

# 邮件配置
email_conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_TLS=settings.MAIL_TLS,
    MAIL_SSL=settings.MAIL_SSL,
    USE_CREDENTIALS=True,
)


class EmailService:
    def __init__(self):
        self.fastmail = FastMail(email_conf)

    async def send_verification_email(
        self, email: str, username: str, verification_code: str
    ):
        """发送验证邮件"""
        try:
            message = MessageSchema(
                subject="验证您的邮箱",
                recipients=[email],
                body=f"""
                尊敬的 {username}：
                
                感谢您注册我们的系统。请使用以下验证码完成邮箱验证：
                
                {verification_code}
                
                此验证码将在24小时后过期。
                
                如果这不是您的操作，请忽略此邮件。
                
                祝好，
                系统团队
                """,
                subtype="plain",
            )

            await self.fastmail.send_message(message)
            logger.info(f"验证邮件已发送至 {email}")

        except Exception as e:
            logger.error(f"发送验证邮件失败: {str(e)}")
            raise

    async def send_registration_approved_email(
        self,
        email: str,
        username: str,
        is_temporary: bool,
        valid_until: Optional[datetime] = None,
    ):
        """发送注册批准邮件"""
        try:
            body = f"""
            尊敬的 {username}：
            
            您的注册申请已被批准。您现在可以使用您的用户名和密码登录系统。
            
            """

            if is_temporary:
                body += f"""
                请注意，这是一个临时账户，将在 {valid_until.strftime('%Y-%m-%d %H:%M:%S')} 过期。
                """

            body += """
            如果您有任何问题，请联系系统管理员。
            
            祝好，
            系统团队
            """

            message = MessageSchema(
                subject="注册申请已批准", recipients=[email], body=body, subtype="plain"
            )

            await self.fastmail.send_message(message)
            logger.info(f"注册批准邮件已发送至 {email}")

        except Exception as e:
            logger.error(f"发送注册批准邮件失败: {str(e)}")
            raise

    async def send_registration_rejected_email(
        self, email: str, username: str, remarks: Optional[str] = None
    ):
        """发送注册拒绝邮件"""
        try:
            body = f"""
            尊敬的 {username}：
            
            很抱歉，您的注册申请未能通过审核。
            """

            if remarks:
                body += f"""
                
                拒绝原因：
                {remarks}
                """

            body += """
            
            如果您认为这是一个错误，请联系系统管理员。
            
            祝好，
            系统团队
            """

            message = MessageSchema(
                subject="注册申请未通过", recipients=[email], body=body, subtype="plain"
            )

            await self.fastmail.send_message(message)
            logger.info(f"注册拒绝邮件已发送至 {email}")

        except Exception as e:
            logger.error(f"发送注册拒绝邮件失败: {str(e)}")
            raise

    async def send_password_reset_email(
        self, email: str, username: str, reset_code: str
    ):
        """发送密码重置邮件"""
        try:
            message = MessageSchema(
                subject="密码重置请求",
                recipients=[email],
                body=f"""
                尊敬的 {username}：
                
                我们收到了您的密码重置请求。请使用以下验证码重置您的密码：
                
                {reset_code}
                
                此验证码将在1小时后过期。
                
                如果这不是您的操作，请立即联系系统管理员。
                
                祝好，
                系统团队
                """,
                subtype="plain",
            )

            await self.fastmail.send_message(message)
            logger.info(f"密码重置邮件已发送至 {email}")

        except Exception as e:
            logger.error(f"发送密码重置邮件失败: {str(e)}")
            raise

    async def send_account_expiring_notification(
        self, email: str, username: str, expire_date: datetime
    ):
        """发送账户即将过期通知"""
        try:
            message = MessageSchema(
                subject="账户即将过期提醒",
                recipients=[email],
                body=f"""
                尊敬的 {username}：
                
                您的账户将在 {expire_date.strftime('%Y-%m-%d %H:%M:%S')} 过期。
                
                如需延长使用期限，请联系系统管理员。
                
                祝好，
                系统团队
                """,
                subtype="plain",
            )

            await self.fastmail.send_message(message)
            logger.info(f"账户过期提醒已发送至 {email}")

        except Exception as e:
            logger.error(f"发送账户过期提醒失败: {str(e)}")
            raise
