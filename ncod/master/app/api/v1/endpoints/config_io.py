"""
配置导入导出接口
"""

import csv
import io
import json
import logging
from typing import Any, Dict, List, Optional

from app.core.deps import get_current_active_user, get_db
from app.core.security import check_admin_permission
from app.models.auth import User
from app.models.config import Config
from app.schemas.config import ConfigCreate
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
logger = logging.getLogger(__name__)


def convert_value(value: str, type_name: str) -> Any:
    """转换值类型"""
    try:
        if type_name == "int":
            return int(value)
        elif type_name == "float":
            return float(value)
        elif type_name == "bool":
            return value.lower() in ("true", "1", "yes", "on")
        else:
            return value
    except Exception as e:
        logger.error("值转换失败: %s", str(e))
        raise ValueError(f"无法将值 '{value}' 转换为 {type_name} 类型") from e


@router.post("/configs/import")
async def import_configs(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    file: UploadFile = File(...),
    file_format: str = "json",
    overwrite: bool = False,
) -> Dict[str, List[str]]:
    """导入配置
    Args:
        db: 数据库会话
        current_user: 当前用户
        file: 上传的文件
        file_format: 文件格式，支持json和csv
        overwrite: 是否覆盖已存在的配置
    Returns:
        导入结果
    """
    await check_admin_permission(current_user)
    content = await file.read()
    try:
        if file_format == "json":
            configs = json.loads(content)
        elif file_format == "csv":
            text = content.decode("utf-8")
            reader = csv.DictReader(io.StringIO(text))
            configs = list(reader)
        else:
            raise HTTPException(status_code=400, detail="不支持的文件格式")
        imported = []
        skipped = []
        for config_data in configs:
            if not all(k in config_data for k in ["key", "value", "group"]):
                skipped.append(f"配置 {config_data.get('key', '未知')} 缺少必要字段")
                continue
            config = ConfigCreate(
                key=config_data["key"],
                value=config_data["value"],
                group=config_data["group"],
                description=config_data.get("description"),
                is_secret=bool(config_data.get("is_secret", False)),
            )
            existing = await db.execute(select(Config).where(Config.key == config.key))
            existing = existing.scalar_one_or_none()
            if existing and not overwrite:
                skipped.append(f"配置 {config.key} 已存在")
                continue
            if existing:
                for field, value in config.dict(exclude_unset=True).items():
                    setattr(existing, field, value)
                imported.append(f"更新配置 {config.key}")
            else:
                db_config = Config(**config.dict())
                db.add(db_config)
                imported.append(f"创建配置 {config.key}")
        await db.commit()
        return {"imported": imported, "skipped": skipped}
    except Exception as e:
        logger.error("导入配置失败: %s", str(e))
        raise HTTPException(status_code=500, detail="导入配置失败") from e


@router.get("/configs/export")
async def export_configs(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    file_format: str = "json",
    group: Optional[str] = None,
    is_secret: Optional[bool] = None,
) -> StreamingResponse:
    """导出配置
    Args:
        db: 数据库会话
        current_user: 当前用户
        file_format: 文件格式，支持json和csv
        group: 配置组
        is_secret: 是否为敏感配置
    Returns:
        配置文件流
    """
    await check_admin_permission(current_user)
    query = select(Config)
    if group:
        query = query.where(Config.group == group)
    if is_secret is not None:
        query = query.where(Config.is_secret == is_secret)
    result = await db.execute(query)
    configs = result.scalars().all()
    try:
        if file_format == "json":
            data = [
                {
                    "key": config.key,
                    "value": config.value,
                    "description": config.description,
                    "group": config.group,
                    "is_secret": config.is_secret,
                }
                for config in configs
            ]
            content = json.dumps(data, ensure_ascii=False, indent=2)
            media_type = "application/json"
            filename = "configs.json"
        elif file_format == "csv":
            output = io.StringIO()
            writer = csv.DictWriter(
                output, fieldnames=["key", "value", "description", "group", "is_secret"]
            )
            writer.writeheader()
            for config in configs:
                writer.writerow(
                    {
                        "key": config.key,
                        "value": config.value,
                        "description": config.description or "",
                        "group": config.group,
                        "is_secret": str(config.is_secret),
                    }
                )
            content = output.getvalue()
            media_type = "text/csv"
            filename = "configs.csv"
        else:
            raise HTTPException(status_code=400, detail="不支持的文件格式")
        return StreamingResponse(
            iter([content.encode()]),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        logger.error("导出配置失败: %s", str(e))
        raise HTTPException(status_code=500, detail="导出配置失败") from e
