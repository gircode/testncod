import { http } from '@/utils/http';

export interface ConfigCreate {
  name: string;
  channel: string;
  config: Record<string, any>;
  description?: string;
}

export interface ConfigUpdate {
  name?: string;
  config?: Record<string, any>;
  description?: string;
}

export const notifyConfigApi = {
  // 创建通知配置
  createConfig(data: ConfigCreate) {
    return http.post('/api/v1/notify-configs', data);
  },

  // 获取通知配置
  getConfigs(params?: {
    channel?: string;
  }) {
    return http.get('/api/v1/notify-configs', { params });
  },

  // 更新通知配置
  updateConfig(configId: string, data: ConfigUpdate) {
    return http.put(`/api/v1/notify-configs/${configId}`, data);
  },

  // 删除通知配置
  deleteConfig(configId: string) {
    return http.delete(`/api/v1/notify-configs/${configId}`);
  }
};

// 通知渠道配置模板
export const CHANNEL_TEMPLATES = {
  email: {
    host: '',
    port: 465,
    username: '',
    password: '',
    sender: '',
    to_list: []
  },
  sms: {
    api_url: '',
    token: '',
    sign: '',
    template: '',
    phone_list: []
  },
  webhook: {
    url: '',
    headers: {},
    template: ''
  },
  dingtalk: {
    webhook: '',
    secret: '',
    at_mobiles: []
  },
  wecom: {
    webhook: '',
    agent_id: '',
    corp_id: '',
    corp_secret: '',
    to_user: '@all'
  }
};

// 通知渠道
export const NOTIFY_CHANNELS = [
  { value: 'email', label: '邮件', icon: 'mail' },
  { value: 'sms', label: '短信', icon: 'mobile' },
  { value: 'webhook', label: 'Webhook', icon: 'api' },
  { value: 'dingtalk', label: '钉钉', icon: 'dingding' },
  { value: 'wecom', label: '企业微信', icon: 'wechat' }
];

// 通知渠道表单配置
export const CHANNEL_FORMS = {
  email: [
    { label: 'SMTP服务器', key: 'host', type: 'input', required: true },
    { label: '端口', key: 'port', type: 'number', required: true },
    { label: '用户名', key: 'username', type: 'input', required: true },
    { label: '密码', key: 'password', type: 'password', required: true },
    { label: '发件人', key: 'sender', type: 'input', required: true },
    { label: '收件人', key: 'to_list', type: 'select', mode: 'tags', required: true }
  ],
  sms: [
    { label: 'API地址', key: 'api_url', type: 'input', required: true },
    { label: '访问令牌', key: 'token', type: 'password', required: true },
    { label: '签名', key: 'sign', type: 'input', required: true },
    { label: '模板ID', key: 'template', type: 'input', required: true },
    { label: '手机号码', key: 'phone_list', type: 'select', mode: 'tags', required: true }
  ],
  webhook: [
    { label: 'Webhook地址', key: 'url', type: 'input', required: true },
    { label: '请求头', key: 'headers', type: 'json', required: false },
    { label: '消息模板', key: 'template', type: 'textarea', required: false }
  ],
  dingtalk: [
    { label: 'Webhook地址', key: 'webhook', type: 'input', required: true },
    { label: '加签密钥', key: 'secret', type: 'password', required: false },
    { label: '@手机号码', key: 'at_mobiles', type: 'select', mode: 'tags', required: false }
  ],
  wecom: [
    { label: 'Webhook地址', key: 'webhook', type: 'input', required: true },
    { label: '应用ID', key: 'agent_id', type: 'input', required: true },
    { label: '企业ID', key: 'corp_id', type: 'input', required: true },
    { label: '应用密钥', key: 'corp_secret', type: 'password', required: true },
    { label: '接收人', key: 'to_user', type: 'input', required: true }
  ]
}; 