import React, { useState } from 'react';
import { Table, Button, Space, Tag, Modal, Form, Input, Select } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';

interface Device {
  id: string;
  name: string;
  type: string;
  status: 'online' | 'offline' | 'error';
  lastHeartbeat: string;
}

const { Option } = Select;

const Devices: React.FC = () => {
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [form] = Form.useForm();
  
  const columns = [
    {
      title: '设备名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '设备类型',
      dataIndex: 'type',
      key: 'type',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        let color = status === 'online' ? 'green' : status === 'offline' ? 'default' : 'red';
        return <Tag color={color}>{status.toUpperCase()}</Tag>;
      },
    },
    {
      title: '最后心跳',
      dataIndex: 'lastHeartbeat',
      key: 'lastHeartbeat',
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: Device) => (
        <Space size="middle">
          <Button 
            type="primary" 
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Button 
            danger 
            icon={<DeleteOutlined />}
            onClick={() => handleDelete(record)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ];

  const handleAdd = () => {
    setIsModalVisible(true);
  };

  const handleEdit = (record: Device) => {
    form.setFieldsValue(record);
    setIsModalVisible(true);
  };

  const handleDelete = (record: Device) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除设备 ${record.name} 吗？`,
      okText: '确认',
      cancelText: '取消',
      onOk: () => {
        console.log('删除设备:', record);
      },
    });
  };

  const handleModalOk = () => {
    form.validateFields().then(values => {
      console.log('表单值:', values);
      setIsModalVisible(false);
      form.resetFields();
    });
  };

  return (
    <div>
      <h1>设备管理</h1>
      <Button
        type="primary"
        icon={<PlusOutlined />}
        onClick={handleAdd}
        style={{ marginBottom: 16 }}
      >
        添加设备
      </Button>
      <Table columns={columns} dataSource={[]} rowKey="id" />
      
      <Modal
        title="设备信息"
        open={isModalVisible}
        onOk={handleModalOk}
        onCancel={() => setIsModalVisible(false)}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label="设备名称"
            rules={[{ required: true, message: '请输入设备名称' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="type"
            label="设备类型"
            rules={[{ required: true, message: '请选择设备类型' }]}
          >
            <Select>
              <Option value="usb">USB设备</Option>
              <Option value="serial">串口设备</Option>
              <Option value="network">网络设备</Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Devices; 