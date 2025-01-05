"""从服务器配置"""

import os


class Config:
    # 主服务器配置
    MASTER_URL = 'https://localhost:5000'
    SSL_VERIFY = True  # 是否验证SSL证书
    
    # VirtualHere配置
    VH_SERVER_PATH = '/usr/local/bin/vhusbhub'
    VH_CONFIG_PATH = '/etc/virtualhere/config.ini'
    
    # 日志配置
    LOG_PATH = 'logs'
    LOG_FILE = os.path.join(LOG_PATH, 'slave.log')
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # 设备监控配置
    UPDATE_INTERVAL = 30  # 设备状态上报间隔(秒)
    RETRY_INTERVAL = 60   # 注册失败重试间隔(秒)
    
    # SSL/TLS配置
    SSL_CERT = 'certs/client.pem'
    SSL_KEY = 'certs/client.key'
    CA_CERT = 'certs/ca.pem'
