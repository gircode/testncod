"""Bulk Operations模块"""

import csv
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
from database import db_manager
from sqlalchemy import text

logger = logging.getLogger(__name__)


class BulkOperations:
    """批量操作工具类"""

    @staticmethod
    def bulk_create(session, model, data: List[Dict]):
        """批量创建记录"""
        try:
            objects = [model(**item) for item in data]
            session.bulk_save_objects(objects)
            session.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to bulk create: {e}")
            session.rollback()
            return False

    @staticmethod
    def bulk_update(session, model, data: List[Dict], key_field: str = "id"):
        """批量更新记录"""
        try:
            # 获取所有ID
            ids = [item[key_field] for item in data]

            # 查询现有记录
            existing = (
                session.query(model).filter(getattr(model, key_field).in_(ids)).all()
            )

            # 更新记录
            for obj in existing:
                item = next(
                    item for item in data if item[key_field] == getattr(obj, key_field)
                )
                for key, value in item.items():
                    if key != key_field:
                        setattr(obj, key, value)

            session.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to bulk update: {e}")
            session.rollback()
            return False

    @staticmethod
    def bulk_delete(session, model, ids: List[int]):
        """批量删除记录"""
        try:
            session.query(model).filter(model.id.in_(ids)).delete(
                synchronize_session=False
            )
            session.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to bulk delete: {e}")
            session.rollback()
            return False


class DataExporter:
    """数据导出工具类"""

    def __init__(self, export_dir: str = "exports"):
        self.export_dir = export_dir
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)

    def _get_export_path(self, name: str, format: str) -> str:
        """获取导出文件路径"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.{format}"
        return os.path.join(self.export_dir, filename)

    def export_to_csv(self, data: List[Dict], name: str) -> Optional[str]:
        """导出为CSV文件"""
        try:
            if not data:
                return None

            filepath = self._get_export_path(name, "csv")

            # 使用pandas导出
            df = pd.DataFrame(data)
            df.to_csv(filepath, index=False, encoding="utf-8")

            return filepath
        except Exception as e:
            logger.error(f"Failed to export to CSV: {e}")
            return None

    def export_to_excel(self, data: List[Dict], name: str) -> Optional[str]:
        """导出为Excel文件"""
        try:
            if not data:
                return None

            filepath = self._get_export_path(name, "xlsx")

            # 使用pandas导出
            df = pd.DataFrame(data)
            df.to_excel(filepath, index=False, engine="openpyxl")

            return filepath
        except Exception as e:
            logger.error(f"Failed to export to Excel: {e}")
            return None

    def export_to_json(self, data: Any, name: str) -> Optional[str]:
        """导出为JSON文件"""
        try:
            filepath = self._get_export_path(name, "json")

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return filepath
        except Exception as e:
            logger.error(f"Failed to export to JSON: {e}")
            return None


class DataImporter:
    """数据导入工具类"""

    @staticmethod
    def import_from_csv(filepath: str) -> List[Dict]:
        """从CSV文件导入数据"""
        try:
            df = pd.read_csv(filepath)
            return df.to_dict("records")
        except Exception as e:
            logger.error(f"Failed to import from CSV: {e}")
            return []

    @staticmethod
    def import_from_excel(filepath: str) -> List[Dict]:
        """从Excel文件导入数据"""
        try:
            df = pd.read_excel(filepath, engine="openpyxl")
            return df.to_dict("records")
        except Exception as e:
            logger.error(f"Failed to import from Excel: {e}")
            return []

    @staticmethod
    def import_from_json(filepath: str) -> Any:
        """从JSON文件导入数据"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to import from JSON: {e}")
            return None


def export_query_results(
    query, format: str = "csv", filename: str = None
) -> Optional[str]:
    """导出查询结果"""
    try:
        # 执行查询
        results = query.all()

        # 转换为字典列表
        data = []
        for row in results:
            if hasattr(row, "_asdict"):
                # 处理元组结果
                data.append(row._asdict())
            elif hasattr(row, "__table__"):
                # 处理ORM模型
                data.append(
                    {
                        column.name: getattr(row, column.name)
                        for column in row.__table__.columns
                    }
                )
            else:
                # 处理其他类型
                data.append(row if isinstance(row, dict) else dict(row))

        # 创建导出器
        exporter = DataExporter()

        # 导出数据
        if format == "csv":
            return exporter.export_to_csv(data, filename or "query_results")
        elif format == "excel":
            return exporter.export_to_excel(data, filename or "query_results")
        elif format == "json":
            return exporter.export_to_json(data, filename or "query_results")
        else:
            raise ValueError(f"Unsupported format: {format}")
    except Exception as e:
        logger.error(f"Failed to export query results: {e}")
        return None


def import_data_to_model(filepath: str, model, format: str = None, **kwargs):
    """导入数据到模型"""
    try:
        # 自动检测格式
        if not format:
            ext = os.path.splitext(filepath)[1].lower()
            if ext == ".csv":
                format = "csv"
            elif ext in [".xlsx", ".xls"]:
                format = "excel"
            elif ext == ".json":
                format = "json"
            else:
                raise ValueError(f"Unsupported file format: {ext}")

        # 创建导入器
        importer = DataImporter()

        # 导入数据
        if format == "csv":
            data = importer.import_from_csv(filepath)
        elif format == "excel":
            data = importer.import_from_excel(filepath)
        elif format == "json":
            data = importer.import_from_json(filepath)
        else:
            raise ValueError(f"Unsupported format: {format}")

        if not data:
            return False

        # 批量创建记录
        with db_manager.get_session() as session:
            return BulkOperations.bulk_create(session, model, data)
    except Exception as e:
        logger.error(f"Failed to import data: {e}")
        return False
