import React from 'react';
import { Form, Input, Button, Card, Switch, InputNumber, Select } from 'antd';

const { Option } = Select;

const Settings: React.FC = () => {
  const [form] = Form.useForm();

  const handleSubmit = (values: any) => {
    console.log('表单值:', values);
  };

  return (
    <div>
      <h1>系统设置</h1>
      <Card>
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{
            serverHost: 'localhost',
            serverPort: 8000,
            logLevel: 'info',
            maxDevices: 100,
            enableMetrics: true,
            deviceTimeout: 30,
            backupInterval: 24,
          }}
        >
          <h3>服务器设置</h3>
          <Form.Item
            name="serverHost"
            label="服务器地址"
            rules={[{ required: true, message: '请输入服务器地址' }]}
          >
            <Input />
          </Form.Item>
          
          <Form.Item
            name="serverPort"
            label="服务器端口"
            rules={[{ required: true, message: '请输入服务器端口' }]}
          >
            <InputNumber min={1} max={65535} style={{ width: '100%' }} />
          </Form.Item>

          <h3>日志设置</h3>
          <Form.Item
            name="logLevel"
            label="日志级别"
            rules={[{ required: true, message: '请选择日志级别' }]}
          >
            <Select>
              <Option value="debug">Debug</Option>
              <Option value="info">Info</Option>
              <Option value="warning">Warning</Option>
              <Option value="error">Error</Option>
            </Select>
          </Form.Item>

          <h3>设备设置</h3>
          <Form.Item
            name="maxDevices"
            label="最大设备数"
            rules={[{ required: true, message: '请输入最大设备数' }]}
          >
            <InputNumber min={1} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="deviceTimeout"
            label="设备超时时间(秒)"
            rules={[{ required: true, message: '请输入设备超时时间' }]}
          >
            <InputNumber min={1} style={{ width: '100%' }} />
          </Form.Item>

          <h3>系统设置</h3>
          <Form.Item
            name="enableMetrics"
            label="启用监控"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>

          <Form.Item
            name="backupInterval"
            label="备份间隔(小时)"
            rules={[{ required: true, message: '请输入备份间隔' }]}
          >
            <InputNumber min={1} max={168} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit">
              保存设置
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
};

export default Settings; 