from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.orm import relationship
from ncod.core.db.database import Base


class Slave(Base):
    __tablename__ = "slaves"

    id = Column(Integer, primary_key=True)
    hostname = Column(String(100))
    ip_address = Column(String(50))
    mac_address = Column(String(50))
    capabilities = Column(JSON)
    last_heartbeat = Column(DateTime, default=datetime.utcnow)

    devices = relationship("Device", back_populates="slave")
