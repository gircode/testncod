"""
Slave Server Core Module
"""

import os
import time
import logging
import requests
import json
from datetime import datetime
from virtualhere import VirtualHereClient
from utils.device_monitor import DeviceMonitor
from utils.mac_validator import validate_mac
from config import Config


class SlaveServer:
    def __init__(self):
        self.config = Config()
        self.setup_logging()
        self.vh_client = VirtualHereClient()
        self.device_monitor = DeviceMonitor()
        self.master_url = self.config.MASTER_URL
        self.registered = False
        self.slave_id = None
        
    def setup_logging(self):
        logging.basicConfig(
            filename=self.config.LOG_FILE,
            level=self.config.LOG_LEVEL,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('SlaveServer')
        
    def register_with_master(self):
        try:
            mac_address = validate_mac()
            if not mac_address:
                self.logger.error("Failed to validate MAC address")
                return False
                
            data = {
                'hostname': os.uname()[1],
                'ip_address': self.get_ip_address(),
                'mac_address': mac_address
            }
            
            response = requests.post(
                f"{self.master_url}/api/slave/register",
                json=data,
                verify=self.config.SSL_VERIFY
            )
            
            if response.status_code == 200:
                self.slave_id = response.json()['slave_id']
                self.registered = True
                self.logger.info(f"Successfully registered with master, slave_id: {self.slave_id}")
                return True
            else:
                self.logger.error(f"Registration failed: {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Registration error: {str(e)}")
            return False
            
    def report_device_status(self):
        if not self.registered:
            return
            
        try:
            devices = self.vh_client.get_device_list()
            data = {
                'slave_id': self.slave_id,
                'devices': devices
            }
            
            response = requests.post(
                f"{self.master_url}/api/device/update",
                json=data,
                verify=self.config.SSL_VERIFY
            )
            
            if response.status_code != 200:
                self.logger.error(f"Failed to update device status: {response.text}")
                
        except Exception as e:
            self.logger.error(f"Device status reporting error: {str(e)}")
            
    def run(self):
        while True:
            if not self.registered:
                if not self.register_with_master():
                    time.sleep(self.config.RETRY_INTERVAL)
                    continue
                    
            self.report_device_status()
            time.sleep(self.config.UPDATE_INTERVAL)


if __name__ == '__main__':
    server = SlaveServer()
    server.run()
