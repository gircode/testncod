<template>
    <div class="slaves-view">
        <el-container>
            <el-header>
                <h2>从服务器管理</h2>
            </el-header>
            <el-main>
                <el-row :gutter="20">
                    <el-col :span="24">
                        <el-card>
                            <template #header>
                                <div class="card-header">
                                    <span>从服务器列表</span>
                                    <el-button type="primary" @click="handleAddSlave">添加从服务器</el-button>
                                </div>
                            </template>
                            <el-table :data="slaves" style="width: 100%">
                                <el-table-column prop="id" label="服务器ID" width="180" />
                                <el-table-column prop="name" label="服务器名称" width="180" />
                                <el-table-column prop="ip" label="IP地址" width="150" />
                                <el-table-column prop="port" label="端口" width="100" />
                                <el-table-column prop="status" label="状态">
                                    <template #default="scope">
                                        <el-tag :type="scope.row.status === 'online' ? 'success' : 'danger'">
                                            {{ scope.row.status === 'online' ? '在线' : '离线' }}
                                        </el-tag>
                                    </template>
                                </el-table-column>
                                <el-table-column prop="lastHeartbeat" label="最后心跳时间" />
                                <el-table-column prop="deviceCount" label="设备数量" width="100" />
                                <el-table-column label="操作" width="250">
                                    <template #default="scope">
                                        <el-button size="small" @click="handleEdit(scope.row)">编辑</el-button>
                                        <el-button size="small"
                                            :type="scope.row.status === 'online' ? 'warning' : 'success'"
                                            @click="handleToggleStatus(scope.row)">
                                            {{ scope.row.status === 'online' ? '停止' : '启动' }}
                                        </el-button>
                                        <el-button size="small" type="danger"
                                            @click="handleDelete(scope.row)">删除</el-button>
                                    </template>
                                </el-table-column>
                            </el-table>
                        </el-card>
                    </el-col>
                </el-row>
            </el-main>
        </el-container>

        <!-- 添加/编辑从服务器对话框 -->
        <el-dialog :title="dialogTitle" v-model="dialogVisible" width="500px">
            <el-form :model="slaveForm" label-width="100px">
                <el-form-item label="服务器名称">
                    <el-input v-model="slaveForm.name" />
                </el-form-item>
                <el-form-item label="IP地址">
                    <el-input v-model="slaveForm.ip" />
                </el-form-item>
                <el-form-item label="端口">
                    <el-input-number v-model="slaveForm.port" :min="1" :max="65535" />
                </el-form-item>
                <el-form-item label="最大设备数">
                    <el-input-number v-model="slaveForm.maxDevices" :min="1" :max="1000" />
                </el-form-item>
                <el-form-item label="描述">
                    <el-input v-model="slaveForm.description" type="textarea" :rows="3" />
                </el-form-item>
            </el-form>
            <template #footer>
                <span class="dialog-footer">
                    <el-button @click="dialogVisible = false">取消</el-button>
                    <el-button type="primary" @click="handleSaveSlave">确定</el-button>
                </span>
            </template>
        </el-dialog>
    </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface Slave {
    id: string
    name: string
    ip: string
    port: number
    status: 'online' | 'offline'
    lastHeartbeat: string
    deviceCount: number
    maxDevices: number
    description: string
}

const slaves = ref<Slave[]>([
    {
        id: 'SLV001',
        name: '从服务器1',
        ip: '192.168.1.101',
        port: 8001,
        status: 'online',
        lastHeartbeat: '2024-12-31 12:00:00',
        deviceCount: 5,
        maxDevices: 100,
        description: '负责A区域设备管理'
    },
    {
        id: 'SLV002',
        name: '从服务器2',
        ip: '192.168.1.102',
        port: 8002,
        status: 'offline',
        lastHeartbeat: '2024-12-31 11:30:00',
        deviceCount: 3,
        maxDevices: 100,
        description: '负责B区域设备管理'
    }
])

const dialogVisible = ref(false)
const dialogTitle = ref('')
const slaveForm = ref({
    id: '',
    name: '',
    ip: '',
    port: 8000,
    maxDevices: 100,
    description: ''
})

const handleAddSlave = () => {
    dialogTitle.value = '添加从服务器'
    slaveForm.value = {
        id: '',
        name: '',
        ip: '',
        port: 8000,
        maxDevices: 100,
        description: ''
    }
    dialogVisible.value = true
}

const handleEdit = (row: Slave) => {
    dialogTitle.value = '编辑从服务器'
    slaveForm.value = { ...row }
    dialogVisible.value = true
}

const handleToggleStatus = (row: Slave) => {
    console.log('切换服务器状态:', row)
}

const handleDelete = (row: Slave) => {
    console.log('删除从服务器:', row)
}

const handleSaveSlave = () => {
    console.log('保存从服务器:', slaveForm.value)
    dialogVisible.value = false
}
</script>

<style scoped>
.slaves-view {
    height: 100%;
}

.el-header {
    background-color: #409EFF;
    color: white;
    line-height: 60px;
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.dialog-footer {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
}
</style>