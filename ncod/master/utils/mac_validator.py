from typing import Optional

def get_client_mac_address() -> Optional[str]:
    """获取客户端MAC地址"""
    try:
        # 从请求头中获取MAC地址
        from flask import request
        mac_address = request.headers.get('X-Client-MAC')
        
        if not mac_address:
            logger.warning("No MAC address in request headers")
            return None
            
        # 验证MAC地址格式
        if not is_valid_mac(mac_address):
            logger.warning(f"Invalid MAC address format: {mac_address}")
            return None
            
        return mac_address.lower()
        
    except Exception as e:
        logger.error(f"Failed to get client MAC address: {e}")
        return None 