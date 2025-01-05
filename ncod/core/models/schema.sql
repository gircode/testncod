-- 核心数据表结构

-- 用户管理
CREATE TABLE users (
    id UUID PRIMARY KEY,
    username VARCHAR(50) UNIQUE,
    password_hash VARCHAR(255),
    mac_address VARCHAR(17),
    role VARCHAR(20),
    status VARCHAR(20),
    organization_id UUID,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- 组织架构
CREATE TABLE organizations (
    id UUID PRIMARY KEY,
    name VARCHAR(100),
    parent_id UUID,
    level INTEGER,
    path VARCHAR(255)
);

-- 设备管理
CREATE TABLE devices (
    id UUID PRIMARY KEY,
    slave_id UUID,
    vendor_id VARCHAR(10),
    product_id VARCHAR(10),
    serial_number VARCHAR(50),
    status VARCHAR(20),
    last_online TIMESTAMP
);

-- 从服务器管理
CREATE TABLE slaves (
    id UUID PRIMARY KEY,
    hostname VARCHAR(100),
    ip_address VARCHAR(39),
    status VARCHAR(20),
    last_heartbeat TIMESTAMP
); 