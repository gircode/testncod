import subprocess
import json
import logging
from typing import List, Dict

class VirtualHereClient:
    def __init__(self):
        self.logger = logging.getLogger('VirtualHereClient')
        
    def execute_command(self, command: str) -> str:
        try:
            result = subprocess.run(
                ['vhui64.exe', '-t', command],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Command execution failed: {e}")
            raise
            
    def get_device_list(self) -> List[Dict]:
        try:
            output = self.execute_command('LIST')
            devices = []
            
            for line in output.split('\n'):
                if not line.strip():
                    continue
                    
                try:
                    vendor_id = line[0:4]
                    product_id = line[5:9]
                    status = 'in_use' if '[IN USE]' in line else 'available'
                    serial = self.get_device_serial(f"{vendor_id}.{product_id}")
                    
                    devices.append({
                        'vendor_id': vendor_id,
                        'product_id': product_id,
                        'status': status,
                        'serial_number': serial
                    })
                    
                except Exception as e:
                    self.logger.error(f"Failed to parse device line: {line}, error: {e}")
                    
            return devices
            
        except Exception as e:
            self.logger.error(f"Failed to get device list: {e}")
            return []
            
    def get_device_serial(self, address: str) -> str:
        try:
            info = self.execute_command(f'DEVICE INFO,{address}')
            for line in info.split('\n'):
                if 'Serial:' in line:
                    return line.split('Serial:')[1].strip()
            return ''
        except:
            return ''
            
    def use_device(self, address: str, password: str = None) -> bool:
        try:
            command = f'USE,{address}'
            if password:
                command += f',{password}'
            result = self.execute_command(command)
            return 'OK' in result
        except:
            return False
            
    def stop_using_device(self, address: str) -> bool:
        try:
            result = self.execute_command(f'STOP USING,{address}')
            return 'OK' in result
        except:
            return False 