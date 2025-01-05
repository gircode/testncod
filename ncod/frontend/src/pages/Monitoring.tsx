import React, { useEffect, useState } from 'react';
import { Card, Row, Col, Statistic, Table, Alert } from 'antd';
import { Line } from '@ant-design/plots';
import { useWebSocket } from '../hooks/useWebSocket';

interface MonitoringData {
  cpu_usage: number;
  memory_usage: number;
  network_usage: number;
  storage_usage: number;
  device_count: number;
  active_connections: number;
}

const Monitoring: React.FC = () => {
  const [data, setData] = useState<MonitoringData | null>(null);
  const [alerts, setAlerts] = useState<string[]>([]);
  const [chartData, setChartData] = useState<any[]>([]);
  
  // 连接WebSocket
  const { lastMessage } = useWebSocket('monitoring');
  
  useEffect(() => {
    if (lastMessage) {
      const message = JSON.parse(lastMessage.data);
      if (message.type === 'metrics') {
        setData(message.data);
        // 更新图表数据
        setChartData(prev => [...prev, {
          time: new Date().toISOString(),
          value: message.data.cpu_usage,
          type: 'CPU'
        }, {
          time: new Date().toISOString(),
          value: message.data.memory_usage,
          type: 'Memory'
        }].slice(-50)); // 保留最近50个数据点
      } else if (message.type === 'alert') {
        setAlerts(prev => [...prev, message.data].slice(-5)); // 保留最近5条告警
      }
    }
  }, [lastMessage]);
  
  const chartConfig = {
    data: chartData,
    xField: 'time',
    yField: 'value',
    seriesField: 'type',
    yAxis: {
      label: {
        formatter: (v: string) => `${v}%`,
      },
    },
    smooth: true,
  };
  
  return (
    <div>
      <h1>系统监控</h1>
      
      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="CPU使用率"
              value={data?.cpu_usage || 0}
              suffix="%"
              precision={2}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="内存使用率"
              value={data?.memory_usage || 0}
              suffix="%"
              precision={2}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="设备数量"
              value={data?.device_count || 0}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="活跃连接"
              value={data?.active_connections || 0}
            />
          </Card>
        </Col>
      </Row>
      
      {/* 性能图表 */}
      <Card title="性能趋势" style={{ marginBottom: 24 }}>
        <Line {...chartConfig} />
      </Card>
      
      {/* 告警信息 */}
      <Card title="最新告警">
        {alerts.map((alert, index) => (
          <Alert
            key={index}
            message={alert}
            type="warning"
            showIcon
            style={{ marginBottom: 8 }}
          />
        ))}
      </Card>
    </div>
  );
};

export default Monitoring; 