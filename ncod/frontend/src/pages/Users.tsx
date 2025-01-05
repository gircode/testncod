import React, { useState } from 'react';
import { Table, Button, Space, Tag, Modal, Form, Input, Select } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';

interface User {
  id: string;
  username: string;
  role: string;
  status: 'active' | 'inactive';
  lastLogin: string;
}

const { Option } = Select;

const Users: React.FC = () => {
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [form] = Form.useForm();

  const columns = [
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
    },
    {
      title: '角色',
      dataIndex: 'role',
      key: 'role',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        let color = status === 'active' ? 'green' : 'red';
        return <Tag color={color}>{status.toUpperCase()}</Tag>;
      },
    },
    {
      title: '最后登录',
      dataIndex: 'lastLogin',
      key: 'lastLogin',
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: User) => (
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

  const handleEdit = (record: User) => {
    form.setFieldsValue(record);
    setIsModalVisible(true);
  };

  const handleDelete = (record: User) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除用户 ${record.username} 吗？`,
      okText: '确认',
      cancelText: '取消',
      onOk: () => {
        console.log('删除用户:', record);
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
      <h1>用户管理</h1>
      <Button
        type="primary"
        icon={<PlusOutlined />}
        onClick={handleAdd}
        style={{ marginBottom: 16 }}
      >
        添加用户
      </Button>
      <Table columns={columns} dataSource={[]} rowKey="id" />

      <Modal
        title="用户信息"
        open={isModalVisible}
        onOk={handleModalOk}
        onCancel={() => setIsModalVisible(false)}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="username"
            label="用户名"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="role"
            label="角色"
            rules={[{ required: true, message: '请选择角色' }]}
          >
            <Select>
              <Option value="admin">管理员</Option>
              <Option value="user">普通用户</Option>
            </Select>
          </Form.Item>
          <Form.Item
            name="status"
            label="状态"
            rules={[{ required: true, message: '请选择状态' }]}
          >
            <Select>
              <Option value="active">激活</Option>
              <Option value="inactive">禁用</Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Users; 