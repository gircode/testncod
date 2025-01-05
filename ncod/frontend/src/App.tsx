import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import { Layout } from 'antd';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import Devices from './pages/Devices';
import Users from './pages/Users';
import Settings from './pages/Settings';
import Monitoring from './pages/Monitoring';

const { Content } = Layout;

const App: React.FC = () => {
  return (
    <Router>
      <Layout style={{ minHeight: '100vh' }}>
        <Navbar />
        <Layout>
          <Content style={{ margin: '24px 16px', padding: 24, background: '#fff' }}>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/devices" element={<Devices />} />
              <Route path="/users" element={<Users />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="/monitoring" element={<Monitoring />} />
            </Routes>
          </Content>
        </Layout>
      </Layout>
    </Router>
  );
};

export default App; 