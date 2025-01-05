"""
配置模板模型
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, Text, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base_class import Base

logger = logging.getLogger(__name__)


class ConfigTemplate(Base):
    """配置模板"""

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    schema: Mapped[Dict] = mapped_column(JSON, nullable=False)
    defaults: Mapped[Optional[Dict]] = mapped_column(JSON)
    validation: Mapped[Optional[Dict]] = mapped_column(JSON)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    updated_at: Mapped[datetime] = mapped_column(DateTime, onupdate=datetime.utcnow)

    # 关系
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])

    def __repr__(self) -> str:
        return f"<ConfigTemplate {self.name}>"


class TemplateManager:
    """模板管理器"""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def create_template(
        self,
        name: str,
        schema: Dict,
        user_id: int,
        description: Optional[str] = None,
        defaults: Optional[Dict] = None,
        validation: Optional[Dict] = None,
    ) -> ConfigTemplate:
        """创建模板"""
        try:
            # 验证schema格式
            if not self._validate_schema(schema):
                raise ValueError("无效的schema格式")

            # 创建模板
            template = ConfigTemplate(
                name=name,
                description=description,
                schema=schema,
                defaults=defaults or {},
                validation=validation or {},
                created_by=user_id,
            )

            self.db.add(template)
            await self.db.commit()
            await self.db.refresh(template)

            return template

        except Exception as e:
            logger.error(f"创建模板失败: {str(e)}")
            await self.db.rollback()
            raise

    async def update_template(
        self,
        name: str,
        user_id: int,
        schema: Optional[Dict] = None,
        description: Optional[str] = None,
        defaults: Optional[Dict] = None,
        validation: Optional[Dict] = None,
    ) -> Optional[ConfigTemplate]:
        """更新模板"""
        try:
            # 获取模板
            template = await self.get_template(name)
            if not template:
                return None

            # 更新字段
            if schema is not None:
                if not self._validate_schema(schema):
                    raise ValueError("无效的schema格式")
                template.schema = schema

            if description is not None:
                template.description = description

            if defaults is not None:
                template.defaults = defaults

            if validation is not None:
                template.validation = validation

            template.updated_by = user_id

            await self.db.commit()
            await self.db.refresh(template)

            return template

        except Exception as e:
            logger.error(f"更新模板失败: {str(e)}")
            await self.db.rollback()
            raise

    async def get_template(self, name: str) -> Optional[ConfigTemplate]:
        """获取模板"""
        try:
            query = select(ConfigTemplate).where(
                ConfigTemplate.name == name, ConfigTemplate.is_active == True
            )
            result = await self.db.execute(query)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"获取模板失败: {str(e)}")
            raise

    async def list_templates(
        self, skip: int = 0, limit: int = 100
    ) -> List[ConfigTemplate]:
        """获取模板列表"""
        try:
            query = (
                select(ConfigTemplate)
                .where(ConfigTemplate.is_active == True)
                .order_by(ConfigTemplate.name)
                .offset(skip)
                .limit(limit)
            )

            result = await self.db.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"获取模板列表失败: {str(e)}")
            raise

    async def delete_template(self, name: str) -> bool:
        """删除模板"""
        try:
            result = await self.db.execute(
                update(ConfigTemplate)
                .where(ConfigTemplate.name == name)
                .values(is_active=False)
            )

            await self.db.commit()
            return result.rowcount > 0

        except Exception as e:
            logger.error(f"删除模板失败: {str(e)}")
            await self.db.rollback()
            raise

    async def validate_config(self, template_name: str, config_data: Dict) -> List[str]:
        """验证配置数据"""
        try:
            # 获取模板
            template = await self.get_template(template_name)
            if not template:
                raise ValueError(f"模板不存在: {template_name}")

            errors = []

            # 验证必填字段
            for field, schema in template.schema.items():
                if schema.get("required", False) and field not in config_data:
                    errors.append(f"缺少必填字段: {field}")

            # 验证字段类型
            for field, value in config_data.items():
                if field not in template.schema:
                    errors.append(f"未知字段: {field}")
                    continue

                schema = template.schema[field]
                if not self._validate_field(value, schema):
                    errors.append(f"字段类型错误: {field}")

            # 验证自定义规则
            if template.validation:
                custom_errors = self._validate_custom_rules(
                    config_data, template.validation
                )
                errors.extend(custom_errors)

            return errors

        except Exception as e:
            logger.error(f"验证配置失败: {str(e)}")
            raise

    def _validate_schema(self, schema: Dict) -> bool:
        """验证schema格式"""
        try:
            required_fields = {"type"}
            allowed_types = {"string", "number", "boolean", "object", "array"}

            for field, definition in schema.items():
                # 检查必填字段
                if not all(f in definition for f in required_fields):
                    return False

                # 检查类型
                if definition["type"] not in allowed_types:
                    return False

            return True

        except Exception:
            return False

    def _validate_field(self, value: Any, schema: Dict) -> bool:
        """验证字段值"""
        try:
            field_type = schema["type"]

            if field_type == "string":
                return isinstance(value, str)
            elif field_type == "number":
                return isinstance(value, (int, float))
            elif field_type == "boolean":
                return isinstance(value, bool)
            elif field_type == "object":
                return isinstance(value, dict)
            elif field_type == "array":
                return isinstance(value, list)

            return False

        except Exception:
            return False

    def _validate_custom_rules(self, config_data: Dict, rules: Dict) -> List[str]:
        """验证自定义规则"""
        errors = []

        try:
            for field, rule in rules.items():
                if field not in config_data:
                    continue

                value = config_data[field]

                # 范围验证
                if "range" in rule:
                    min_val = rule["range"].get("min")
                    max_val = rule["range"].get("max")

                    if min_val is not None and value < min_val:
                        errors.append(f"{field} 小于最小值: {min_val}")
                    if max_val is not None and value > max_val:
                        errors.append(f"{field} 大于最大值: {max_val}")

                # 正则表达式验证
                if "pattern" in rule:
                    import re

                    if not re.match(rule["pattern"], str(value)):
                        errors.append(f"{field} 格式不匹配")

                # 枚举验证
                if "enum" in rule and value not in rule["enum"]:
                    errors.append(f"{field} 值不在允许范围内")

                # 依赖字段验证
                if "dependencies" in rule:
                    for dep in rule["dependencies"]:
                        if dep not in config_data:
                            errors.append(f"{field} 依赖字段缺失: {dep}")

        except Exception as e:
            logger.error(f"验证自定义规则失败: {str(e)}")

        return errors
