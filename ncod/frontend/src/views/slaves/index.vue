<template>
  <div class="slaves-container">
    <a-card class="slaves-card">
      <template #title>从服务器管理</template>
      <template #extra>
        <a-button type="primary" @click="showAddModal">
          <template #icon>
            <plus-outlined />
          </template>
          添加从服务器
        </a-button>
      </template>

      <!-- 搜索表单 -->
      <a-form layout="inline" class="search-form">
        <a-form-item label="服务器名称">
          <a-input
            v-model:value="searchForm.name"
            placeholder="请输入服务器名称"
            allow-clear
          />
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
              <reload-outlined />
            </template>
            重置
          </a-button>
        </a-form-item>
      </a-form>

      <!-- 从服务器列表 -->
      <a-table
        :columns="columns"
        :data-source="slaveList"
        :loading="loading"
        :pagination="pagination"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-tag :color="record.status === 'online' ? 'success' : 'error'">
              {{ record.status === 'online' ? '在线' : '离线' }}
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

    <!-- 添加/编辑从服务器弹窗 -->
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
        <a-form-item name="name" label="服务器名称">
          <a-input v-model:value="formState.name" placeholder="请输入服务器名称" />
        </a-form-item>
        <a-form-item name="host" label="主机地址">
          <a-input v-model:value="formState.host" placeholder="请输入主机地址" />
        </a-form-item>
        <a-form-item name="port" label="端口">
          <a-input-number
            v-model:value="formState.port"
            :min="1"
            :max="65535"
            style="width: 100%"
          />
        </a-form-item>
        <a-form-item name="mac_address" label="MAC地址">
          <a-input
            v-model:value="formState.mac_address"
            placeholder="请输入MAC地址"
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
  ReloadOutlined
} from '@ant-design/icons-vue'

interface SlaveRecord {
  id: number
  name: string
  host: string
  port: number
  status: 'online' | 'offline'
  mac_address: string
  last_heartbeat: string
}

interface SearchForm {
  name: string
  status: 'online' | 'offline' | undefined
}

interface FormState {
  id?: number
  name: string
  host: string
  port: number
  mac_address: string
}

// 搜索表单
const searchForm = reactive<SearchForm>({
  name: '',
  status: undefined
})

// 表格列定义
const columns = [
  {
    title: '服务器名称',
    dataIndex: 'name',
    key: 'name'
  },
  {
    title: '主机地址',
    dataIndex: 'host',
    key: 'host'
  },
  {
    title: '端口',
    dataIndex: 'port',
    key: 'port'
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status'
  },
  {
    title: 'MAC地址',
    dataIndex: 'mac_address',
    key: 'mac_address'
  },
  {
    title: '最后心跳',
    dataIndex: 'last_heartbeat',
    key: 'last_heartbeat'
  },
  {
    title: '操作',
    key: 'action',
    width: 150
  }
]

// 表格数据
const loading = ref(false)
const slaveList = ref<SlaveRecord[]>([])
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0
})

// 表单相关
const modalVisible = ref(false)
const modalTitle = ref('添加从服务器')
const formRef = ref()
const formState = reactive<FormState>({
  name: '',
  host: '',
  port: 8001,
  mac_address: ''
})

const rules = {
  name: [{ required: true, message: '请输入服务器名称', trigger: 'blur' }],
  host: [{ required: true, message: '请输入主机地址', trigger: 'blur' }],
  port: [{ required: true, message: '请输入端口', trigger: 'change' }],
  mac_address: [{ required: true, message: '请输入MAC地址', trigger: 'blur' }]
}

// 事件处理方法
const handleSearch = () => {
  pagination.current = 1
  fetchSlaveList()
}

const handleReset = () => {
  searchForm.name = ''
  searchForm.status = undefined
  handleSearch()
}

const handleTableChange = (pag: { current: number; pageSize: number }) => {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  fetchSlaveList()
}

const showAddModal = () => {
  modalTitle.value = '添加从服务器'
  formState.id = undefined
  formState.name = ''
  formState.host = ''
  formState.port = 8001
  formState.mac_address = ''
  modalVisible.value = true
}

const handleEdit = (record: SlaveRecord) => {
  modalTitle.value = '编辑从服务器'
  Object.assign(formState, record)
  modalVisible.value = true
}

const handleDelete = async (record: SlaveRecord) => {
  try {
    // TODO: 调用删除接口
    message.success('删除成功')
    fetchSlaveList()
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
    fetchSlaveList()
  } catch (error) {
    console.error('表单验证失败:', error)
  }
}

const handleModalCancel = () => {
  modalVisible.value = false
  formRef.value?.resetFields()
}

// 获取从服务器列表
const fetchSlaveList = async () => {
  try {
    loading.value = true
    // TODO: 调用后端接口获取数据
    slaveList.value = [
      {
        id: 1,
        name: '从服务器1',
        host: '192.168.1.101',
        port: 8001,
        status: 'online',
        mac_address: 'CC:DD:EE:FF:00:11',
        last_heartbeat: '2024-01-04 16:30:00'
      },
      {
        id: 2,
        name: '从服务器2',
        host: '192.168.1.102',
        port: 8001,
        status: 'offline',
        mac_address: 'CC:DD:EE:FF:00:22',
        last_heartbeat: '2024-01-04 15:45:00'
      }
    ]
    pagination.total = 2
  } catch (error) {
    message.error('获取从服务器列表失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchSlaveList()
})
</script>

<style lang="less" scoped>
.slaves-container {
  padding: 24px;
  background-color: #f0f2f5;
  min-height: 100%;

  .slaves-card {
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