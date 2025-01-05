import React from 'react';
import { Card, Row, Col, Statistic } from 'antd';
import { 
  DesktopOutlined, 
  UserOutlined, 
  CheckCircleOutlined,
  WarningOutlined 
} from '@ant-design/icons';

const Dashboard: React.FC = () => {
  return (
    <div>
      <h1>仪表盘</h1>
      <Row gutter={16}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总设备数"
              value={42}
              prefix={<DesktopOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="在线设备"
              value={35}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="离线设备"
              value={7}
              prefix={<WarningOutlined />}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="活跃用户"
              value={12}
              prefix={<UserOutlined />}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard; 