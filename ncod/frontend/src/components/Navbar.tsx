import React from 'react';
import { Layout, Menu } from 'antd';
import { Link, useLocation } from 'react-router-dom';
import {
  DashboardOutlined,
  DesktopOutlined,
  UserOutlined,
  SettingOutlined,
  MonitorOutlined,
} from '@ant-design/icons';

const { Sider } = Layout;

const Navbar: React.FC = () => {
  const location = useLocation();
  
  const menuItems = [
    {
      key: '/',
      icon: <DashboardOutlined />,
      label: <Link to="/">仪表盘</Link>,
    },
    {
      key: '/devices',
      icon: <DesktopOutlined />,
      label: <Link to="/devices">设备管理</Link>,
    },
    {
      key: '/users',
      icon: <UserOutlined />,
      label: <Link to="/users">用户管理</Link>,
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: <Link to="/settings">系统设置</Link>,
    },
    {
      key: '/monitoring',
      icon: <MonitorOutlined />,
      label: <Link to="/monitoring">监控面板</Link>,
    },
  ];

  return (
    <Sider
      style={{
        overflow: 'auto',
        height: '100vh',
        position: 'fixed',
        left: 0,
      }}
    >
      <div style={{ height: 32, margin: 16, background: 'rgba(255, 255, 255, 0.2)' }} />
      <Menu
        theme="dark"
        mode="inline"
        selectedKeys={[location.pathname]}
        items={menuItems}
      />
    </Sider>
  );
};

export default Navbar; 