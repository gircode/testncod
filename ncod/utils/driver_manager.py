"""驱动管理模块"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
import aiohttp
import aiofiles
import tempfile
import zipfile

from ncod.utils.logger import logger
from ncod.utils.config import settings
from ncod.utils.cache import redis_cache


class DriverManager:
    """驱动管理器"""

    def __init__(self):
        self.driver_dir = settings.DATA_DIR / "drivers"
        self.driver_dir.mkdir(parents=True, exist_ok=True)
        self.driver_cache: Dict[str, Dict] = {}

    async def install_driver(
        self, vendor_id: str, product_id: str, force: bool = False
    ) -> bool:
        """安装设备驱动

        Args:
            vendor_id: 厂商ID
            product_id: 产品ID
            force: 是否强制安装

        Returns:
            bool: 是否安装成功
        """
        try:
            # 检查驱动是否已安装
            if not force and self._is_driver_installed(vendor_id, product_id):
                logger.info(f"驱动已安装: {vendor_id}:{product_id}")
                return True

            # 获取驱动信息
            driver_info = await self._get_driver_info(vendor_id, product_id)
            if not driver_info:
                logger.error(f"未找到驱动: {vendor_id}:{product_id}")
                return False

            # 下载驱动
            driver_path = await self._download_driver(driver_info)
            if not driver_path:
                return False

            # 安装驱动
            success = await self._install_driver_package(driver_path)
            if success:
                logger.info(f"驱动安装成功: {vendor_id}:{product_id}")
                # 缓存驱动信息
                await self._cache_driver_info(vendor_id, product_id, driver_info)
            return success

        except Exception as e:
            logger.error(f"驱动安装失败: {e}")
            return False

    def _is_driver_installed(self, vendor_id: str, product_id: str) -> bool:
        """检查驱动是否已安装"""
        try:
            if sys.platform == "win32":
                # 使用Windows驱动管理工具检查
                cmd = [
                    "pnputil.exe",
                    "/enum-drivers",
                    f"*VID_{vendor_id}&PID_{product_id}*",
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)
                return "No driver packages found." not in result.stdout
            else:
                # 检查Linux模块是否加载
                cmd = ["lsmod"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                return any(
                    f"usb:{vendor_id}:{product_id}" in line
                    for line in result.stdout.splitlines()
                )
        except Exception as e:
            logger.error(f"检查驱动安装状态失败: {e}")
            return False

    async def _get_driver_info(self, vendor_id: str, product_id: str) -> Optional[Dict]:
        """获取驱动信息"""
        try:
            # 先从缓存获取
            cache_key = f"driver_info:{vendor_id}:{product_id}"
            cached_info = await redis_cache.get(cache_key)
            if cached_info:
                return cached_info

            # 从驱动数据库获取
            async with aiohttp.ClientSession() as session:
                url = settings.DRIVER_DB_URL
                params = {"vendor_id": vendor_id, "product_id": product_id}
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        driver_info = await response.json()
                        # 缓存驱动信息
                        await redis_cache.set(
                            cache_key, driver_info, expire=3600  # 1小时
                        )
                        return driver_info
            return None

        except Exception as e:
            logger.error(f"获取驱动信息失败: {e}")
            return None

    async def _download_driver(self, driver_info: Dict) -> Optional[Path]:
        """下载驱动文件"""
        try:
            download_url = driver_info["download_url"]
            file_name = download_url.split("/")[-1]
            target_path = self.driver_dir / file_name

            if target_path.exists():
                return target_path

            async with aiohttp.ClientSession() as session:
                async with session.get(download_url) as response:
                    if response.status == 200:
                        async with aiofiles.open(target_path, "wb") as f:
                            await f.write(await response.read())
                        return target_path
            return None

        except Exception as e:
            logger.error(f"下载驱动失败: {e}")
            return None

    async def _install_driver_package(self, driver_path: Path) -> bool:
        """安装驱动包"""
        try:
            if sys.platform == "win32":
                return await self._install_windows_driver(driver_path)
            else:
                return await self._install_linux_driver(driver_path)
        except Exception as e:
            logger.error(f"安装驱动包失败: {e}")
            return False

    async def _install_windows_driver(self, driver_path: Path) -> bool:
        """安装Windows驱动"""
        try:
            # 解压驱动包
            with tempfile.TemporaryDirectory() as temp_dir:
                with zipfile.ZipFile(driver_path, "r") as zip_ref:
                    zip_ref.extractall(temp_dir)

                # 安装驱动
                inf_file = next(Path(temp_dir).glob("*.inf"))
                cmd = ["pnputil.exe", "/add-driver", str(inf_file), "/install"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                return result.returncode == 0

        except Exception as e:
            logger.error(f"安装Windows驱动失败: {e}")
            return False

    async def _install_linux_driver(self, driver_path: Path) -> bool:
        """安装Linux驱动"""
        try:
            # 解压驱动包
            with tempfile.TemporaryDirectory() as temp_dir:
                with zipfile.ZipFile(driver_path, "r") as zip_ref:
                    zip_ref.extractall(temp_dir)

                # 编译并安装驱动
                build_script = Path(temp_dir) / "build.sh"
                if build_script.exists():
                    cmd = ["bash", str(build_script)]
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode == 0:
                        # 加载驱动模块
                        module_name = next(Path(temp_dir).glob("*.ko")).stem
                        cmd = ["modprobe", module_name]
                        result = subprocess.run(cmd, capture_output=True, text=True)
                        return result.returncode == 0
            return False

        except Exception as e:
            logger.error(f"安装Linux驱动失败: {e}")
            return False

    async def _cache_driver_info(
        self, vendor_id: str, product_id: str, driver_info: Dict
    ):
        """缓存驱动信息"""
        try:
            # 更新内存缓存
            cache_key = f"{vendor_id}:{product_id}"
            self.driver_cache[cache_key] = driver_info

            # 更新Redis缓存
            await redis_cache.set(
                f"driver_info:{cache_key}", driver_info, expire=3600  # 1小时
            )
        except Exception as e:
            logger.error(f"缓存驱动信息失败: {e}")

    async def uninstall_driver(self, vendor_id: str, product_id: str) -> bool:
        """卸载设备驱动

        Args:
            vendor_id: 厂商ID
            product_id: 产品ID

        Returns:
            bool: 是否卸载成功
        """
        try:
            if sys.platform == "win32":
                # 卸载Windows驱动
                cmd = [
                    "pnputil.exe",
                    "/delete-driver",
                    f"*VID_{vendor_id}&PID_{product_id}*",
                    "/uninstall",
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)
                success = result.returncode == 0
            else:
                # 卸载Linux驱动模块
                module_name = f"usb_{vendor_id}_{product_id}"
                cmd = ["modprobe", "-r", module_name]
                result = subprocess.run(cmd, capture_output=True, text=True)
                success = result.returncode == 0

            if success:
                logger.info(f"驱动卸载成功: {vendor_id}:{product_id}")
                # 清除缓存
                cache_key = f"{vendor_id}:{product_id}"
                self.driver_cache.pop(cache_key, None)
                await redis_cache.delete(f"driver_info:{cache_key}")

            return success

        except Exception as e:
            logger.error(f"驱动卸载失败: {e}")
            return False

    def get_installed_drivers(self) -> List[Dict]:
        """获取已安装的驱动列表"""
        try:
            if sys.platform == "win32":
                # 获取Windows已安装驱动
                cmd = ["pnputil.exe", "/enum-drivers"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                drivers = []
                current_driver = {}

                for line in result.stdout.splitlines():
                    if line.startswith("Published Name:"):
                        if current_driver:
                            drivers.append(current_driver)
                        current_driver = {}
                    elif ":" in line:
                        key, value = line.split(":", 1)
                        current_driver[key.strip()] = value.strip()

                if current_driver:
                    drivers.append(current_driver)
                return drivers

            else:
                # 获取Linux已加载模块
                cmd = ["lsmod"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                return [
                    {"name": line.split()[0]}
                    for line in result.stdout.splitlines()[1:]
                    if "usb" in line
                ]

        except Exception as e:
            logger.error(f"获取已安装驱动列表失败: {e}")
            return []


# 创建全局驱动管理器实例
driver_manager = DriverManager()
