"""
Frontend pages package
"""

from .dashboard import Dashboard
from .device_dashboard import DeviceDashboard
from .login import LoginPage
from .settings import SettingsPage

__all__ = ["Dashboard", "DeviceDashboard", "LoginPage", "SettingsPage"]
