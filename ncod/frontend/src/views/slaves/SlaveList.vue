<!-- 从机管理页面 -->
<template>
  <div class="slave-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <h2>从服务器管理</h2>
          </div>
          <div class="header-right">
            <el-button-group>
              <el-button type="primary" @click="showAddDialog" :icon="Plus">
                添加从服务器
              </el-button>
              <el-button :loading="loading" @click="loadSlaves" :icon="Refresh">
                刷新
              </el-button>
            </el-button-group>
          </div>
        </div>
      </template>

      <div class="table-container">
        <el-table
          v-loading="loading"
          :data="slaveList"
          border
          stripe
          highlight-current-row
        >
          <el-table-column prop="name" label="名称" min-width="150" />
          <el-table-column prop="ip" label="IP地址" min-width="150" />
          <el-table-column prop="port" label="端口" width="100" />
          <el-table-column prop="status" label="状态" width="120">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)">
                {{ getStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="lastSeen" label="最后在线时间" min-width="180">
            <template #default="{ row }">
              {{ formatDate(row.lastSeen) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="280" fixed="right">
            <template #default="{ row }">
              <el-button-group>
                <el-tooltip content="编辑服务器" placement="top">
                  <el-button type="primary" @click="showEditDialog(row)" :icon="Edit" />
                </el-tooltip>
                <el-tooltip :content="row.status === 'online' ? '停止服务' : '启动服务'" placement="top">
                  <el-button 
                    :type="row.status === 'online' ? 'warning' : 'success'"
                    @click="handleToggleStatus(row)"
                    :icon="row.status === 'online' ? VideoPlay : VideoPause"
                  />
                </el-tooltip>
                <el-tooltip content="删除服务器" placement="top">
                  <el-button type="danger" @click="handleDelete(row)" :icon="Delete" />
                </el-tooltip>
              </el-button-group>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>

    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑从服务器' : '添加从服务器'"
      width="500px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="100px"
        @submit.prevent="handleSubmit"
        status-icon
      >
        <el-form-item label="名称" prop="name">
          <el-input
            v-model="form.name"
            placeholder="请输入服务器名称"
            maxlength="50"
            show-word-limit
            clearable
          />
        </el-form-item>
        <el-form-item label="IP地址" prop="ip">
          <el-input
            v-model="form.ip"
            placeholder="请输入IP地址"
            clearable
          />
        </el-form-item>
        <el-form-item label="端口" prop="port">
          <el-input-number
            v-model="form.port"
            :min="1"
            :max="65535"
            placeholder="请输入端口号"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="submitLoading">
            确定
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete, Refresh, Warning, VideoPlay, VideoPause } from '@element-plus/icons-vue'
import type { FormInstance, FormRules, TagProps } from 'element-plus'

interface Slave {
    id: string
    name: string
    ip: string
    port: number
    status: 'online' | 'offline' | 'error'
    lastSeen: string
}

interface SlaveForm {
    name: string
    ip: string
    port: number
}

const formRef = ref<FormInstance>()
const loading = ref(false)
const submitLoading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const currentSlave = ref<Slave | null>(null)

const form = ref<SlaveForm>({
    name: '',
    ip: '',
    port: 8001
})

const formRules: FormRules = {
    name: [
        { required: true, message: '请输入名称', trigger: 'blur' },
        { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
    ],
    ip: [
        { required: true, message: '请输入IP地址', trigger: 'blur' },
        { pattern: /^(\d{1,3}\.){3}\d{1,3}$/, message: 'IP地址格式不正确', trigger: 'blur' }
    ],
    port: [
        { required: true, message: '请输入端口号', trigger: 'blur' },
        { type: 'number', min: 1, max: 65535, message: '端口号范围为1-65535', trigger: 'blur' }
    ]
}

// 模拟数据
const mockSlaves: Slave[] = [
    {
        id: '1',
        name: '从服务器1',
        ip: '192.168.1.101',
        port: 8001,
        status: 'online',
        lastSeen: new Date().toISOString()
    },
    {
        id: '2',
        name: '从服务器2',
        ip: '192.168.1.102',
        port: 8002,
        status: 'offline',
        lastSeen: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString()
    },
    {
        id: '3',
        name: '从服务器3',
        ip: '192.168.1.103',
        port: 8003,
        status: 'error',
        lastSeen: new Date(Date.now() - 30 * 60 * 1000).toISOString()
    }
]

const slaveList = ref<Slave[]>(mockSlaves)

const getStatusType = (status: string): TagProps['type'] => {
    const typeMap: Record<string, TagProps['type']> = {
        online: 'success',
        offline: 'info',
        error: 'danger'
    }
    return typeMap[status] || 'info'
}

const getStatusText = (status: string) => {
    const textMap: Record<string, string> = {
        online: '在线',
        offline: '离线',
        error: '错误'
    }
    return textMap[status] || status
}

const formatDate = (date: string) => {
    return new Date(date).toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    })
}

const loadSlaves = async () => {
    loading.value = true
    try {
        // 模拟API延迟
        await new Promise(resolve => setTimeout(resolve, 500))
        slaveList.value = mockSlaves
        ElMessage.success('加载成功')
    } catch (error) {
        ElMessage.error('加载失败')
        console.error(error)
    } finally {
        loading.value = false
    }
}

const showAddDialog = () => {
    isEdit.value = false
    currentSlave.value = null
    form.value = {
        name: '',
        ip: '',
        port: 8001
    }
    dialogVisible.value = true
}

const showEditDialog = (slave: Slave) => {
    isEdit.value = true
    currentSlave.value = slave
    form.value = {
        name: slave.name,
        ip: slave.ip,
        port: slave.port
    }
    dialogVisible.value = true
}

const handleSubmit = async () => {
    if (!formRef.value) return
    
    await formRef.value.validate(async (valid) => {
        if (valid) {
            submitLoading.value = true
            try {
                // 模拟API延迟
                await new Promise(resolve => setTimeout(resolve, 500))
                
                if (isEdit.value && currentSlave.value) {
                    // 编辑现有从服务器
                    Object.assign(currentSlave.value, {
                        ...form.value
                    })
                } else {
                    // 添加新从服务器
                    const newSlave: Slave = {
                        id: String(Date.now()),
                        ...form.value,
                        status: 'offline',
                        lastSeen: new Date().toISOString()
                    }
                    slaveList.value.push(newSlave)
                }
                
                ElMessage.success(isEdit.value ? '编辑成功' : '添加成功')
                dialogVisible.value = false
                await loadSlaves()
            } catch (error) {
                ElMessage.error(isEdit.value ? '编辑失败' : '添加失败')
                console.error(error)
            } finally {
                submitLoading.value = false
            }
        }
    })
}

const handleDelete = async (slave: Slave) => {
    try {
        await ElMessageBox.confirm(
            `确定要删除从服务器 "${slave.name}" 吗？`,
            '确认删除',
            {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning',
                icon: Warning
            }
        )
        
        loading.value = true
        try {
            // 模拟API延迟
            await new Promise(resolve => setTimeout(resolve, 500))
            const index = slaveList.value.findIndex(s => s.id === slave.id)
            if (index !== -1) {
                slaveList.value.splice(index, 1)
            }
            ElMessage.success('删除成功')
        } catch (error) {
            ElMessage.error('删除失败')
            console.error(error)
        } finally {
            loading.value = false
        }
    } catch {
        // 用户取消操作
    }
}

const handleToggleStatus = async (slave: Slave) => {
    const action = slave.status === 'online' ? '停止' : '启动'
    try {
        await ElMessageBox.confirm(
            `确定要${action}从服务器 "${slave.name}" 吗？`,
            `确认${action}`,
            {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning',
                icon: Warning
            }
        )
        
        loading.value = true
        try {
            // 模拟API延迟
            await new Promise(resolve => setTimeout(resolve, 500))
            slave.status = slave.status === 'online' ? 'offline' : 'online'
            slave.lastSeen = new Date().toISOString()
            ElMessage.success(`${action}成功`)
        } catch (error) {
            ElMessage.error(`${action}失败`)
            console.error(error)
        } finally {
            loading.value = false
        }
    } catch {
        // 用户取消操作
    }
}

// 自动刷新
let refreshTimer: number | null = null

const startAutoRefresh = () => {
    stopAutoRefresh()
    refreshTimer = window.setInterval(() => {
        loadSlaves()
    }, 30000) // 每30秒刷新一次
}

const stopAutoRefresh = () => {
    if (refreshTimer) {
        clearInterval(refreshTimer)
        refreshTimer = null
    }
}

onMounted(() => {
    loadSlaves()
    startAutoRefresh()
})

onUnmounted(() => {
    stopAutoRefresh()
})
</script>

<style scoped>
.slave-list {
    padding: 20px;
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.header-left h2 {
    margin: 0;
    font-size: 18px;
    color: var(--el-text-color-primary);
}

.header-right {
    display: flex;
    gap: 10px;
}

.table-container {
    margin-top: 20px;
}

.dialog-footer {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
}

:deep(.el-tag) {
    text-transform: uppercase;
}

:deep(.el-button-group .el-button--primary) {
    --el-button-hover-text-color: var(--el-color-white);
    --el-button-hover-bg-color: var(--el-color-primary-light-3);
    --el-button-hover-border-color: var(--el-color-primary-light-3);
}

:deep(.el-button-group .el-button--danger) {
    --el-button-hover-text-color: var(--el-color-white);
    --el-button-hover-bg-color: var(--el-color-danger-light-3);
    --el-button-hover-border-color: var(--el-color-danger-light-3);
}

:deep(.el-button-group .el-button--warning) {
    --el-button-hover-text-color: var(--el-color-white);
    --el-button-hover-bg-color: var(--el-color-warning-light-3);
    --el-button-hover-border-color: var(--el-color-warning-light-3);
}

:deep(.el-button-group .el-button--success) {
    --el-button-hover-text-color: var(--el-color-white);
    --el-button-hover-bg-color: var(--el-color-success-light-3);
    --el-button-hover-border-color: var(--el-color-success-light-3);
}
</style>