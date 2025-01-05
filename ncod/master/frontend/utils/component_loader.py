"""
Component Loader Module
"""

import asyncio
import importlib
import logging
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ComponentLoader:
    def __init__(self):
        self._components = {}
        self._loading_stats = defaultdict(
            lambda: {"load_time": 0, "last_loaded": None, "load_count": 0}
        )

    async def load_component(self, component_path: str) -> Any:
        """Load a component by its path"""
        start_time = time.time()

        try:
            if component_path in self._components:
                return self._components[component_path]

            module_path, class_name = component_path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            component = getattr(module, class_name)

            self._components[component_path] = component

            # Update stats
            load_time = time.time() - start_time
            self._loading_stats[component_path].update(
                {
                    "load_time": load_time,
                    "last_loaded": time.time(),
                    "load_count": self._loading_stats[component_path]["load_count"] + 1,
                }
            )

            return component
        except Exception as e:
            logger.error(f"Error loading component {component_path}: {str(e)}")
            raise

    def get_loading_stats(self) -> Dict[str, Dict]:
        """Get component loading statistics"""
        return dict(self._loading_stats)

    def clear_cache(self):
        """Clear the component cache"""
        self._components.clear()
        self._loading_stats.clear()


class Preloader:
    def __init__(self):
        self._preload_config = {}
        self._component_loader = ComponentLoader()

    def configure_preload(self, config: Dict[str, List[str]]):
        """Configure which components to preload for each section"""
        self._preload_config = config

    async def preload_components(self, section: str):
        """Preload components for a specific section"""
        if section not in self._preload_config:
            logger.warning(f"No preload configuration found for section: {section}")
            return

        components = self._preload_config[section]
        tasks = [self._component_loader.load_component(comp) for comp in components]
        await asyncio.gather(*tasks)

    def get_component_loader(self) -> ComponentLoader:
        """Get the component loader instance"""
        return self._component_loader


# Create global instances
component_loader = ComponentLoader()
preloader = Preloader()
