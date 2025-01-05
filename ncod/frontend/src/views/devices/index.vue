<template>
  <div class="devices-container">
    <a-card class="devices-card">
      <template #title>设备管理</template>
      <template #extra>
        <a-button type="primary" @click="showAddModal">
          <template #icon>
            <plus-outlined />
          </template>
          添加设备
        </a-button>
      </template>

      <!-- 搜索表单 -->
      <a-form layout="inline" class="search-form">
        <a-form-item label="设备名称">
          <a-input
            v-model:value="searchForm.name"
            placeholder="请输入设备名称"
            allow-clear
          />
        </a-form-item>
        <a-form-item label="设备类型">
          <a-select
            v-model:value="searchForm.type"
            placeholder="请选择设备类型"
            style="width: 120px"
            allow-clear
          >
            <a-select-option value="printer">打印机</a-select-option>
            <a-select-option value="scanner">扫描仪</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="状态">
          <a-select
            v-model:value="searchForm.status"
            placeholder="请选择状态"
            style="width: 120px"
            allow-clear
          >
            <a-select-option value="online">在线</a-select-option>
            <a-select-option value="offline">离线</a-select-option>
            <a-select-option value="in_use">使用中</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item>
          <a-button type="primary" @click="handleSearch">
            <template #icon>
              <search-outlined />
            </template>
            搜索
          </a-button>
          <a-button style="margin-left: 8px" @click="handleReset">
            <template #icon>
              <redo-outlined />
            </template>
            重置
          </a-button>
        </a-form-item>
      </a-form>

      <!-- 设备列表 -->
      <a-table
        :columns="columns"
        :data-source="deviceList"
        :loading="loading"
        :pagination="pagination"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-tag :color="getStatusColor(record.status)">
              {{ getStatusText(record.status) }}
            </a-tag>
          </template>
          <template v-if="column.key === 'action'">
            <a-space>
              <a-button type="link" size="small" @click="handleEdit(record)">
                编辑
              </a-button>
              <a-button
                type="link"
                size="small"
                danger
                @click="handleDelete(record)"
              >
                删除
              </a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 添加/编辑设备弹窗 -->
    <a-modal
      v-model:visible="modalVisible"
      :title="modalTitle"
      @ok="handleModalOk"
      @cancel="handleModalCancel"
    >
      <a-form
        ref="formRef"
        :model="formState"
        :rules="rules"
        label-col="{ span: 6 }"
        wrapper-col="{ span: 16 }"
      >
        <a-form-item name="name" label="设备名称">
          <a-input v-model:value="formState.name" placeholder="请输入设备名称" />
        </a-form-item>
        <a-form-item name="type" label="设备类型">
          <a-select v-model:value="formState.type" placeholder="请选择设备类型">
            <a-select-option value="printer">打印机</a-select-option>
            <a-select-option value="scanner">扫描仪</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item name="slave_id" label="从服务器">
          <a-select
            v-model:value="formState.slave_id"
            placeholder="请选择从服务器"
          >
            <a-select-option
              v-for="slave in slaveList"
              :key="slave.id"
              :value="slave.id"
            >
              {{ slave.name }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item name="description" label="描述">
          <a-textarea
            v-model:value="formState.description"
            placeholder="请输入设备描述"
            :rows="4"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import {
  PlusOutlined,
  SearchOutlined,
  RedoOutlined
} from '@ant-design/icons-vue'

// 搜索表单
const searchForm = reactive({
  name: '',
  type: undefined,
  status: undefined
})

// 表格列定义
const columns = [
  {
    title: '设备名称',
    dataIndex: 'name',
    key: 'name'
  },
  {
    title: '设备类型',
    dataIndex: 'type',
    key: 'type',
    customRender: ({ text }) => {
      const typeMap = {
        printer: '打印机',
        scanner: '扫描仪'
      }
      return typeMap[text] || text
    }
  },
  {
    title: '从服务器',
    dataIndex: 'slave_name',
    key: 'slave_name'
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status'
  },
  {
    title: '描述',
    dataIndex: 'description',
    key: 'description',
    ellipsis: true
  },
  {
    title: '操作',
    key: 'action',
    width: 150
  }
]

// 表格数据
const loading = ref(false)
const deviceList = ref([])
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0
})

// 从服务器列表
const slaveList = ref([])

// 表单相关
const modalVisible = ref(false)
const modalTitle = ref('添加设备')
const formRef = ref()
const formState = reactive({
  id: undefined,
  name: '',
  type: undefined,
  slave_id: undefined,
  description: ''
})

const rules = {
  name: [{ required: true, message: '请输入设备名称', trigger: 'blur' }],
  type: [{ required: true, message: '请选择设备类型', trigger: 'change' }],
  slave_id: [{ required: true, message: '请选择从服务器', trigger: 'change' }]
}

// 状态相关方法
const getStatusColor = (status: string) => {
  const colorMap = {
    online: 'success',
    offline: 'error',
    in_use: 'processing'
  }
  return colorMap[status] || 'default'
}

const getStatusText = (status: string) => {
  const textMap = {
    online: '在线',
    offline: '离线',
    in_use: '使用中'
  }
  return textMap[status] || status
}

// 事件处理方法
const handleSearch = () => {
  pagination.current = 1
  fetchDeviceList()
}

const handleReset = () => {
  searchForm.name = ''
  searchForm.type = undefined
  searchForm.status = undefined
  handleSearch()
}

const handleTableChange = (pag) => {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  fetchDeviceList()
}

const showAddModal = () => {
  modalTitle.value = '添加设备'
  formState.id = undefined
  formState.name = ''
  formState.type = undefined
  formState.slave_id = undefined
  formState.description = ''
  modalVisible.value = true
}

const handleEdit = (record) => {
  modalTitle.value = '编辑设备'
  Object.assign(formState, record)
  modalVisible.value = true
}

const handleDelete = async (record) => {
  try {
    // TODO: 调用删除接口
    message.success('删除成功')
    fetchDeviceList()
  } catch (error) {
    message.error('删除失败')
  }
}

const handleModalOk = async () => {
  try {
    await formRef.value.validate()
    // TODO: 调用保存接口
    message.success(formState.id ? '更新成功' : '添加成功')
    modalVisible.value = false
    fetchDeviceList()
  } catch (error) {
    console.error('表单验证失败:', error)
  }
}

const handleModalCancel = () => {
  modalVisible.value = false
  formRef.value?.resetFields()
}

// 获取设备列表
const fetchDeviceList = async () => {
  try {
    loading.value = true
    // TODO: 调用后端接口获取数据
    deviceList.value = [
      {
        id: 1,
        name: 'USB打印机',
        type: 'printer',
        slave_id: 1,
        slave_name: '从服务器1',
        status: 'online',
        description: '办公室打印机'
      },
      {
        id: 2,
        name: 'USB扫描仪',
        type: 'scanner',
        slave_id: 1,
        slave_name: '从服务器1',
        status: 'in_use',
        description: '文档扫描仪'
      }
    ]
    pagination.total = 2
  } catch (error) {
    message.error('获取设备列表失败')
  } finally {
    loading.value = false
  }
}

// 获取从服务器列表
const fetchSlaveList = async () => {
  try {
    // TODO: 调用后端接口获取数据
    slaveList.value = [
      {
        id: 1,
        name: '从服务器1'
      },
      {
        id: 2,
        name: '从服务器2'
      }
    ]
  } catch (error) {
    message.error('获取从服务器列表失败')
  }
}

onMounted(() => {
  fetchDeviceList()
  fetchSlaveList()
})
</script>

<style lang="less" scoped>
.devices-container {
  padding: 24px;
  background-color: #f0f2f5;
  min-height: 100%;

  .devices-card {
    background-color: transparent;
    
    :deep(.ant-card-head) {
      padding: 0;
      border-bottom: none;
      
      .ant-card-head-title {
        padding: 0 0 16px 0;
        font-size: 20px;
        font-weight: 500;
      }
    }
    
    :deep(.ant-card-body) {
      padding: 0;
    }
  }

  .search-form {
    margin-bottom: 24px;
    padding: 24px;
    background: #fff;
    border-radius: 8px;
  }

  :deep(.ant-card) {
    border-radius: 8px;
    box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.03);
  }

  :deep(.ant-table-wrapper) {
    background: #fff;
    padding: 24px;
    border-radius: 8px;
  }
}
</style> 