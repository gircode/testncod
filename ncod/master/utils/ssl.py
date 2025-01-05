import os
import ssl
import logging
from typing import Optional, Tuple
from OpenSSL import crypto
from ..config import Config

logger = logging.getLogger(__name__)

def create_self_signed_cert() -> Tuple[str, str]:
    """创建自签名证书"""
    try:
        # 生成密钥
        key = crypto.PKey()
        key.generate_key(crypto.TYPE_RSA, 2048)
        
        # 创建证书
        cert = crypto.X509()
        cert.get_subject().CN = "localhost"
        cert.set_serial_number(1000)
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(365*24*60*60)  # 有效期1年
        cert.set_issuer(cert.get_subject())
        cert.set_pubkey(key)
        cert.sign(key, 'sha256')
        
        # 保存证书和密钥
        cert_path = Config.SSL_CERTIFICATE
        key_path = Config.SSL_KEY
        
        os.makedirs(os.path.dirname(cert_path), exist_ok=True)
        
        with open(cert_path, "wb") as f:
            f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
            
        with open(key_path, "wb") as f:
            f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key))
            
        logger.info("Self-signed certificate created successfully")
        return cert_path, key_path
        
    except Exception as e:
        logger.error(f"Failed to create self-signed certificate: {e}")
        raise

def get_ssl_context() -> Optional[ssl.SSLContext]:
    """获取SSL上下文"""
    try:
        if not os.path.exists(Config.SSL_CERTIFICATE) or not os.path.exists(Config.SSL_KEY):
            create_self_signed_cert()
            
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(
            certfile=Config.SSL_CERTIFICATE,
            keyfile=Config.SSL_KEY
        )
        context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1  # 禁用不安全的TLS版本
        context.set_ciphers('ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256')
        
        return context
        
    except Exception as e:
        logger.error(f"Failed to create SSL context: {e}")
        return None

def verify_cert(cert_path: str) -> bool:
    """验证证书有效性"""
    try:
        with open(cert_path, 'rb') as f:
            cert_data = f.read()
            
        cert = crypto.load_certificate(crypto.FILETYPE_PEM, cert_data)
        
        # 检查证书是否过期
        from datetime import datetime
        not_after = datetime.strptime(
            cert.get_notAfter().decode('ascii'),
            '%Y%m%d%H%M%SZ'
        )
        if datetime.now() > not_after:
            logger.warning("Certificate has expired")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Certificate verification failed: {e}")
        return False 