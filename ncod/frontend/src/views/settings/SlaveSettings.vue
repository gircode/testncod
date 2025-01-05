<template>
    <div class="slave-settings">
        <el-card>
            <template #header>
                <div class="card-header">
                    <div class="header-left">
                        <h2>从服务器设置</h2>
                    </div>
                    <div class="header-right">
                        <el-select v-model="selectedSlave" placeholder="选择从服务器" style="width: 200px">
                            <el-option
                                v-for="slave in slaveList"
                                :key="slave.id"
                                :label="slave.name"
                                :value="slave.id"
                            />
                        </el-select>
                    </div>
                </div>
            </template>

            <div v-if="selectedSlave" class="settings-content">
                <el-form
                    ref="formRef"
                    :model="form"
                    :rules="formRules"
                    label-width="140px"
                >
                    <el-form-item label="服务器名称" prop="name">
                        <el-input v-model="form.name" />
                    </el-form-item>

                    <el-form-item label="IP地址" prop="ip">
                        <el-input v-model="form.ip" />
                    </el-form-item>

                    <el-form-item label="端口" prop="port">
                        <el-input-number v-model="form.port" :min="1" :max="65535" />
                    </el-form-item>

                    <el-form-item label="最大连接数" prop="maxConnections">
                        <el-input-number v-model="form.maxConnections" :min="1" :max="1000" />
                    </el-form-item>

                    <el-form-item label="心跳间隔(秒)" prop="heartbeatInterval">
                        <el-input-number v-model="form.heartbeatInterval" :min="1" :max="60" />
                    </el-form-item>

                    <el-form-item label="日志级别" prop="logLevel">
                        <el-select v-model="form.logLevel" style="width: 100%">
                            <el-option label="DEBUG" value="debug" />
                            <el-option label="INFO" value="info" />
                            <el-option label="WARNING" value="warning" />
                            <el-option label="ERROR" value="error" />
                        </el-select>
                    </el-form-item>

                    <el-form-item label="自动重连" prop="autoReconnect">
                        <el-switch v-model="form.autoReconnect" />
                    </el-form-item>

                    <el-form-item label="重连间隔(秒)" prop="reconnectInterval" v-if="form.autoReconnect">
                        <el-input-number v-model="form.reconnectInterval" :min="1" :max="60" />
                    </el-form-item>

                    <el-form-item label="设备黑名单" prop="deviceBlacklist">
                        <el-select
                            v-model="form.deviceBlacklist"
                            multiple
                            filterable
                            allow-create
                            default-first-option
                            placeholder="输入设备ID并回车"
                            style="width: 100%"
                        />
                    </el-form-item>

                    <el-form-item label="备注" prop="description">
                        <el-input
                            v-model="form.description"
                            type="textarea"
                            :rows="3"
                        />
                    </el-form-item>

                    <el-form-item>
                        <el-button type="primary" @click="handleSubmit" :loading="loading">
                            保存设置
                        </el-button>
                        <el-button @click="resetForm">
                            重置
                        </el-button>
                    </el-form-item>
                </el-form>

                <el-divider />

                <div class="danger-zone">
                    <h3>危险操作</h3>
                    <div class="danger-actions">
                        <el-button type="danger" @click="handleRestart">
                            重启服务
                        </el-button>
                        <el-button type="danger" @click="handleClearLogs">
                            清理日志
                        </el-button>
                        <el-button type="danger" @click="handleResetConfig">
                            重置配置
                        </el-button>
                    </div>
                </div>
            </div>
            <el-empty v-else description="请选择从服务器" />
        </el-card>
    </div>
</template>

<script lang="ts" setup>
import { ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Warning } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'

interface Slave {
    id: string
    name: string
    ip: string
    port: number
}

interface SlaveSettings {
    name: string
    ip: string
    port: number
    maxConnections: number
    heartbeatInterval: number
    logLevel: string
    autoReconnect: boolean
    reconnectInterval: number
    deviceBlacklist: string[]
    description: string
}

const formRef = ref<FormInstance>()
const loading = ref(false)
const selectedSlave = ref<string>('')

// 模拟数据
const mockSlaveList: Slave[] = [
    { id: '1', name: '从服务器1', ip: '192.168.1.101', port: 8001 },
    { id: '2', name: '从服务器2', ip: '192.168.1.102', port: 8002 },
    { id: '3', name: '从服务器3', ip: '192.168.1.103', port: 8003 }
]

const mockSettings: SlaveSettings = {
    name: '从服务器1',
    ip: '192.168.1.101',
    port: 8001,
    maxConnections: 100,
    heartbeatInterval: 5,
    logLevel: 'info',
    autoReconnect: true,
    reconnectInterval: 10,
    deviceBlacklist: ['USB001', 'USB002'],
    description: '测试服务器'
}

const slaveList = ref<Slave[]>(mockSlaveList)
const form = ref<SlaveSettings>({ ...mockSettings })

const formRules: FormRules = {
    name: [
        { required: true, message: '请输入服务器名称', trigger: 'blur' },
        { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
    ],
    ip: [
        { required: true, message: '请输入IP地址', trigger: 'blur' },
        { pattern: /^(\d{1,3}\.){3}\d{1,3}$/, message: 'IP地址格式不正确', trigger: 'blur' }
    ],
    port: [
        { required: true, message: '请输入端口号', trigger: 'blur' },
        { type: 'number', min: 1, max: 65535, message: '端口号范围为1-65535', trigger: 'blur' }
    ],
    maxConnections: [
        { required: true, message: '请输入最大连接数', trigger: 'blur' },
        { type: 'number', min: 1, max: 1000, message: '最大连接数范围为1-1000', trigger: 'blur' }
    ],
    heartbeatInterval: [
        { required: true, message: '请输入心跳间隔', trigger: 'blur' },
        { type: 'number', min: 1, max: 60, message: '心跳间隔范围为1-60秒', trigger: 'blur' }
    ],
    logLevel: [
        { required: true, message: '请选择日志级别', trigger: 'change' }
    ],
    reconnectInterval: [
        { required: true, message: '请输入重连间隔', trigger: 'blur' },
        { type: 'number', min: 1, max: 60, message: '重连间隔范围为1-60秒', trigger: 'blur' }
    ]
}

const handleSubmit = async () => {
    if (!formRef.value) return
    
    await formRef.value.validate(async (valid) => {
        if (valid) {
            loading.value = true
            try {
                // 模拟API延迟
                await new Promise(resolve => setTimeout(resolve, 500))
                ElMessage.success('保存成功')
            } catch (error) {
                ElMessage.error('保存失败')
                console.error(error)
            } finally {
                loading.value = false
            }
        }
    })
}

const resetForm = () => {
    if (!formRef.value) return
    formRef.value.resetFields()
}

const handleRestart = async () => {
    try {
        await ElMessageBox.confirm(
            '确定要重启从服务器吗？这将导致所有连接断开。',
            '确认重启',
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
            ElMessage.success('重启成功')
        } catch (error) {
            ElMessage.error('重启失败')
            console.error(error)
        } finally {
            loading.value = false
        }
    } catch {
        // 用户取消操作
    }
}

const handleClearLogs = async () => {
    try {
        await ElMessageBox.confirm(
            '确定要清理所有日志吗？此操作不可恢复。',
            '确认清理',
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
            ElMessage.success('清理成功')
        } catch (error) {
            ElMessage.error('清理失败')
            console.error(error)
        } finally {
            loading.value = false
        }
    } catch {
        // 用户取消操作
    }
}

const handleResetConfig = async () => {
    try {
        await ElMessageBox.confirm(
            '确定要重置所有配置吗？这将恢复到默认设置。',
            '确认重置',
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
            form.value = { ...mockSettings }
            ElMessage.success('重置成功')
        } catch (error) {
            ElMessage.error('重置失败')
            console.error(error)
        } finally {
            loading.value = false
        }
    } catch {
        // 用户取消操作
    }
}

// 监听从服务器选择变化
watch(selectedSlave, async (newValue: string) => {
    if (newValue) {
        loading.value = true
        try {
            // 模拟API延迟
            await new Promise(resolve => setTimeout(resolve, 500))
            form.value = { ...mockSettings }
        } catch (error) {
            ElMessage.error('加载设置失败')
            console.error(error)
        } finally {
            loading.value = false
        }
    }
})
</script>

<style scoped>
.slave-settings {
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
}

.header-right {
    display: flex;
    gap: 10px;
}

.settings-content {
    margin-top: 20px;
    max-width: 800px;
}

.danger-zone {
    margin-top: 20px;
}

.danger-zone h3 {
    color: #f56c6c;
    margin-bottom: 20px;
}

.danger-actions {
    display: flex;
    gap: 20px;
}
</style> 