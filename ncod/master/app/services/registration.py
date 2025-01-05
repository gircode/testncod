"""
用户注册服务
"""

import logging
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional

from email_validator import EmailNotValidError, validate_email
from fastapi import HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..models.auth import Department, Group, RegistrationRequest, User
from .auth import AuthService
from .email import EmailService

# 配置日志
logger = logging.getLogger(__name__)


class RegistrationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.auth_service = AuthService(db)
        self.email_service = EmailService()

    async def request_registration(
        self,
        username: str,
        email: str,
        password: str,
        department_id: int,
        group_id: int,
        registration_ip: str,
    ) -> RegistrationRequest:
        """申请注册"""
        try:
            # 验证邮箱格式
            email_info = validate_email(email, check_deliverability=False)
            email = email_info.normalized

            # 检查用户名是否已存在
            result = await self.db.execute(
                select(User).where(User.username == username)
            )
            if result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在"
                )

            # 检查邮箱是否已存在
            result = await self.db.execute(select(User).where(User.email == email))
            if result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="邮箱已被使用"
                )

            # 检查部门是否存在
            result = await self.db.execute(
                select(Department).where(Department.id == department_id)
            )
            if not result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="部门不存在"
                )

            # 检查组是否存在
            result = await self.db.execute(select(Group).where(Group.id == group_id))
            if not result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="组不存在"
                )

            # 创建注册申请
            registration_request = RegistrationRequest(
                username=username,
                email=email,
                hashed_password=self.auth_service.get_password_hash(password),
                department_id=department_id,
                group_id=group_id,
                registration_ip=registration_ip,
            )

            self.db.add(registration_request)
            await self.db.commit()
            await self.db.refresh(registration_request)

            # 发送验证邮件
            verification_code = secrets.token_hex(16)
            verification_expires = datetime.utcnow() + timedelta(hours=24)

            registration_request.verification_code = verification_code
            registration_request.verification_code_expires = verification_expires

            await self.db.commit()

            # 发送验证邮件
            await self.email_service.send_verification_email(
                email=email, username=username, verification_code=verification_code
            )

            return registration_request

        except EmailNotValidError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="邮箱格式不正确"
            )
        except Exception as e:
            logger.error(f"注册申请失败: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="注册申请失败"
            )

    async def verify_email(self, request_id: int, verification_code: str) -> bool:
        """验证邮箱"""
        try:
            result = await self.db.execute(
                select(RegistrationRequest).where(RegistrationRequest.id == request_id)
            )
            request = result.scalar_one_or_none()

            if not request:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="注册申请不存在"
                )

            if request.verification_code != verification_code:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="验证码错误"
                )

            if request.verification_code_expires < datetime.utcnow():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="验证码已过期"
                )

            request.email_verified = True
            await self.db.commit()

            return True

        except Exception as e:
            logger.error(f"邮箱验证失败: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="邮箱验证失败"
            )

    async def approve_registration(
        self,
        request_id: int,
        admin_id: int,
        is_temporary: bool = False,
        valid_days: Optional[int] = None,
    ) -> User:
        """批准注册"""
        try:
            result = await self.db.execute(
                select(RegistrationRequest).where(RegistrationRequest.id == request_id)
            )
            request = result.scalar_one_or_none()

            if not request:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="注册申请不存在"
                )

            if not request.email_verified:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="邮箱未验证"
                )

            # 创建用户
            user = User(
                username=request.username,
                email=request.email,
                hashed_password=request.hashed_password,
                department_id=request.department_id,
                group_id=request.group_id,
                is_active=True,
                is_temporary=is_temporary,
                registration_ip=request.registration_ip,
            )

            if is_temporary and valid_days:
                user.valid_until = datetime.utcnow() + timedelta(days=valid_days)

            self.db.add(user)

            # 更新注册申请状态
            request.status = "approved"
            request.processed_by_id = admin_id
            request.processed_time = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(user)

            # 发送通知邮件
            await self.email_service.send_registration_approved_email(
                email=user.email,
                username=user.username,
                is_temporary=is_temporary,
                valid_until=user.valid_until,
            )

            return user

        except Exception as e:
            logger.error(f"批准注册失败: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="批准注册失败"
            )

    async def reject_registration(
        self, request_id: int, admin_id: int, remarks: Optional[str] = None
    ) -> RegistrationRequest:
        """拒绝注册"""
        try:
            result = await self.db.execute(
                select(RegistrationRequest).where(RegistrationRequest.id == request_id)
            )
            request = result.scalar_one_or_none()

            if not request:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="注册申请不存在"
                )

            request.status = "rejected"
            request.processed_by_id = admin_id
            request.processed_time = datetime.utcnow()
            request.remarks = remarks

            await self.db.commit()
            await self.db.refresh(request)

            # 发送通知邮件
            await self.email_service.send_registration_rejected_email(
                email=request.email, username=request.username, remarks=remarks
            )

            return request

        except Exception as e:
            logger.error(f"拒绝注册失败: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="拒绝注册失败"
            )

    async def get_pending_requests(
        self, skip: int = 0, limit: int = 100
    ) -> List[RegistrationRequest]:
        """获取待处理的注册申请"""
        try:
            result = await self.db.execute(
                select(RegistrationRequest)
                .where(RegistrationRequest.status == "pending")
                .offset(skip)
                .limit(limit)
            )
            return result.scalars().all()

        except Exception as e:
            logger.error(f"获取待处理注册申请失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="获取待处理注册申请失败",
            )
