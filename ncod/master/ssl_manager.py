import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, Tuple
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from .utils.logger import get_logger
from .config_manager import ConfigManager

logger = get_logger(__name__)
config = ConfigManager()


class SSLManager:
    _instance: Optional['SSLManager'] = None
    _cert_dir: str = 'certs'
    
    def __new__(cls) -> 'SSLManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        self._ensure_cert_dir()
    
    def _ensure_cert_dir(self) -> None:
        """确保证书目录存在"""
        try:
            os.makedirs(self._cert_dir, exist_ok=True)
            logger.debug(f"Certificate directory ensured: {self._cert_dir}")
            
        except Exception as e:
            logger.error(f"Failed to create certificate directory: {e}")
            raise
    
    def _generate_key_pair(
        self,
        key_size: int = 2048
    ) -> Tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
        """生成RSA密钥对"""
        try:
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=key_size,
                backend=default_backend()
            )
            public_key = private_key.public_key()
            return private_key, public_key
            
        except Exception as e:
            logger.error(f"Failed to generate key pair: {e}")
            raise
    
    def generate_self_signed_cert(
        self,
        common_name: str,
        country: str = 'CN',
        state: str = 'Beijing',
        locality: str = 'Beijing',
        org_name: str = 'NCOD',
        org_unit: str = 'IT',
        valid_days: int = 365,
        key_size: int = 2048
    ) -> bool:
        """生成自签名证书"""
        try:
            # 生成密钥对
            private_key, public_key = self._generate_key_pair(key_size)
            
            # 生成证书
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, country),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, state),
                x509.NameAttribute(NameOID.LOCALITY_NAME, locality),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, org_name),
                x509.NameAttribute(
                    NameOID.ORGANIZATIONAL_UNIT_NAME,
                    org_unit
                ),
                x509.NameAttribute(NameOID.COMMON_NAME, common_name)
            ])
            
            cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                public_key
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.utcnow()
            ).not_valid_after(
                datetime.utcnow() + timedelta(days=valid_days)
            ).add_extension(
                x509.SubjectAlternativeName([
                    x509.DNSName(common_name)
                ]),
                critical=False
            ).sign(private_key, hashes.SHA256(), default_backend())
            
            # 保存私钥
            key_path = os.path.join(self._cert_dir, f"{common_name}.key")
            with open(key_path, 'wb') as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
                
            # 保存证书
            cert_path = os.path.join(self._cert_dir, f"{common_name}.crt")
            with open(cert_path, 'wb') as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))
                
            logger.info(
                f"Self-signed certificate generated: {cert_path}"
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to generate self-signed certificate: {e}")
            return False
    
    def verify_certificate(self, cert_path: str) -> bool:
        """验证证书有效性"""
        try:
            if not os.path.exists(cert_path):
                logger.error(f"Certificate not found: {cert_path}")
                return False
                
            with open(cert_path, 'rb') as f:
                cert_data = f.read()
                cert = x509.load_pem_x509_certificate(
                    cert_data,
                    default_backend()
                )
                
            now = datetime.utcnow()
            if now < cert.not_valid_before:
                logger.error("Certificate is not yet valid")
                return False
                
            if now > cert.not_valid_after:
                logger.error("Certificate has expired")
                return False
                
            logger.info(f"Certificate is valid: {cert_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to verify certificate: {e}")
            return False
    
    def get_cert_info(self, cert_path: str) -> Optional[Dict[str, Any]]:
        """获取证书信息"""
        try:
            if not os.path.exists(cert_path):
                logger.error(f"Certificate not found: {cert_path}")
                return None
                
            with open(cert_path, 'rb') as f:
                cert_data = f.read()
                cert = x509.load_pem_x509_certificate(
                    cert_data,
                    default_backend()
                )
                
            subject = cert.subject
            issuer = cert.issuer
            
            return {
                'subject': {
                    'common_name': subject.get_attributes_for_oid(
                        NameOID.COMMON_NAME
                    )[0].value,
                    'country': subject.get_attributes_for_oid(
                        NameOID.COUNTRY_NAME
                    )[0].value,
                    'state': subject.get_attributes_for_oid(
                        NameOID.STATE_OR_PROVINCE_NAME
                    )[0].value,
                    'locality': subject.get_attributes_for_oid(
                        NameOID.LOCALITY_NAME
                    )[0].value,
                    'organization': subject.get_attributes_for_oid(
                        NameOID.ORGANIZATION_NAME
                    )[0].value,
                    'org_unit': subject.get_attributes_for_oid(
                        NameOID.ORGANIZATIONAL_UNIT_NAME
                    )[0].value
                },
                'issuer': {
                    'common_name': issuer.get_attributes_for_oid(
                        NameOID.COMMON_NAME
                    )[0].value,
                    'organization': issuer.get_attributes_for_oid(
                        NameOID.ORGANIZATION_NAME
                    )[0].value
                },
                'serial_number': cert.serial_number,
                'not_valid_before': cert.not_valid_before,
                'not_valid_after': cert.not_valid_after,
                'is_valid': self.verify_certificate(cert_path)
            }
            
        except Exception as e:
            logger.error(f"Failed to get certificate info: {e}")
            return None
    
    def list_certificates(self) -> Dict[str, Any]:
        """列出所有证书"""
        try:
            certs = {}
            
            for file in os.listdir(self._cert_dir):
                if file.endswith('.crt'):
                    cert_path = os.path.join(self._cert_dir, file)
                    cert_info = self.get_cert_info(cert_path)
                    if cert_info:
                        certs[file] = cert_info
                        
            return certs
            
        except Exception as e:
            logger.error(f"Failed to list certificates: {e}")
            return {}
    
    def delete_certificate(self, common_name: str) -> bool:
        """删除证书"""
        try:
            cert_path = os.path.join(self._cert_dir, f"{common_name}.crt")
            key_path = os.path.join(self._cert_dir, f"{common_name}.key")
            
            if not os.path.exists(cert_path):
                logger.error(f"Certificate not found: {cert_path}")
                return False
                
            os.remove(cert_path)
            if os.path.exists(key_path):
                os.remove(key_path)
                
            logger.info(f"Certificate deleted: {common_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete certificate: {e}")
            return False
    
    def clean_expired_certs(self) -> bool:
        """清理过期证书"""
        try:
            certs = self.list_certificates()
            
            for cert_file, cert_info in certs.items():
                if not cert_info['is_valid']:
                    common_name = cert_info['subject']['common_name']
                    self.delete_certificate(common_name)
                    
            logger.info("Expired certificates cleaned")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clean expired certificates: {e}")
            return False 