<template>
  <a-modal
    v-model:visible="visible"
    title="系统公告"
    :footer="null"
    width="800px"
    class="system-announcement"
  >
    <div class="announcement-content">
      <div class="welcome-message">
        <h2>欢迎使用 NCOD 设备管理系统</h2>
        <p>全新版本v3.1.0已经发布！</p>
      </div>

      <div class="feature-list">
        <h3>系统主要功能：</h3>
        <a-row :gutter="[16, 16]">
          <a-col :span="8" v-for="feature in features" :key="feature.title">
            <a-card class="feature-card">
              <template #cover>
                <div class="feature-icon">
                  <component :is="feature.icon" />
                </div>
              </template>
              <a-card-meta :title="feature.title">
                <template #description>
                  <div class="feature-description">{{ feature.description }}</div>
                </template>
              </a-card-meta>
            </a-card>
          </a-col>
        </a-row>
      </div>

      <div class="action-footer">
        <a-checkbox v-model:checked="dontShow">不再显示</a-checkbox>
        <a-button type="primary" @click="handleClose">我知道了</a-button>
      </div>
    </div>
  </a-modal>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import {
  DesktopOutlined,
  TeamOutlined,
  SafetyCertificateOutlined,
  ToolOutlined,
  CloudServerOutlined,
  SettingOutlined
} from '@ant-design/icons-vue'

const visible = ref(true)
const dontShow = ref(false)

const features = [
  {
    icon: DesktopOutlined,
    title: '设备管理',
    description: '支持设备状态监控、使用记录查看、设备授权管理等功能'
  },
  {
    icon: TeamOutlined,
    title: '组织架构',
    description: '提供完整的组织架构管理，支持多级部门和用户组管理'
  },
  {
    icon: SafetyCertificateOutlined,
    title: '权限管理',
    description: '细粒度的权限控制，支持角色分配和权限继承'
  },
  {
    icon: CloudServerOutlined,
    title: '服务器管理',
    description: '支持多服务器节点管理，实时监控服务器状态'
  },
  {
    icon: ToolOutlined,
    title: '基础工具',
    description: '提供日志查看、系统监控、性能分析等基础工具'
  },
  {
    icon: SettingOutlined,
    title: '系统设置',
    description: '灵活的系统配置，支持自定义系统参数和告警规则'
  }
]

const handleClose = () => {
  if (dontShow.value) {
    localStorage.setItem('hideAnnouncement', 'true')
  }
  visible.value = false
}

// 检查是否需要显示公告
const shouldShow = !localStorage.getItem('hideAnnouncement')
if (!shouldShow) {
  visible.value = false
}
</script>

<style lang="less" scoped>
.system-announcement {
  :deep(.ant-modal-body) {
    padding: 24px;
  }
}

.announcement-content {
  .welcome-message {
    text-align: center;
    margin-bottom: 32px;

    h2 {
      font-size: 24px;
      color: #1890ff;
      margin-bottom: 8px;
    }

    p {
      font-size: 16px;
      color: #52c41a;
      margin: 0;
    }
  }

  .feature-list {
    h3 {
      font-size: 18px;
      margin-bottom: 24px;
    }
  }

  .feature-card {
    height: 100%;
    transition: all 0.3s;

    &:hover {
      transform: translateY(-4px);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }

    .feature-icon {
      display: flex;
      justify-content: center;
      align-items: center;
      height: 120px;
      background: #f0f5ff;
      font-size: 48px;
      color: #1890ff;
    }

    :deep(.ant-card-meta-title) {
      margin-bottom: 12px;
      font-size: 16px;
      color: #1890ff;
    }

    .feature-description {
      color: #666;
      line-height: 1.5;
    }
  }

  .action-footer {
    margin-top: 32px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
}
</style> 