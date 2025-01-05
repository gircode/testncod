<template>
  <div class="users-container">
    <el-card>
      <template #header>
        <div class="header-content">
          <h2>用户管理</h2>
          <el-button type="primary" @click="handleAddUser">
            添加用户
          </el-button>
        </div>
      </template>
      
      <el-table :data="users" v-loading="loading">
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="email" label="邮箱" />
        <el-table-column prop="organization.name" label="所属组织" />
        <el-table-column prop="status" label="状态">
          <template #default="{ row }">
            <el-tag :type="getUserStatusType(row.status)">
              {{ getUserStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_login" label="最后登录时间">
          <template #default="{ row }">
            {{ formatDateTimeString(row.last_login) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250">
          <template #default="{ row }">
            <el-button-group>
              <el-button 
                v-if="row.status === 'pending'"
                type="success" 
                size="small"
                @click="handleApprove(row)"
              >
                批准
              </el-button>
              <el-button 
                v-if="row.status === 'pending'"
                type="danger" 
                size="small"
                @click="handleReject(row)"
              >
                拒绝
              </el-button>
              <el-button
                type="primary"
                size="small"
                @click="handleEdit(row)"
              >
                编辑
              </el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 用户表单对话框 -->
    <el-dialog
      :title="dialogTitle"
      v-model="dialogVisible"
      width="500px"
    >
      <el-form
        :model="userForm"
        :rules="rules"
        ref="userFormRef"
        label-width="100px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="userForm.username" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="userForm.email" />
        </el-form-item>
        <el-form-item label="组织" prop="organization_id">
          <el-tree-select
            v-model="userForm.organization_id"
            :data="organizationTree"
            :props="{
              label: 'name',
              value: 'id',
              children: 'children'
            }"
            placeholder="请选择组织"
          />
        </el-form-item>
        <el-form-item label="密码" prop="password" v-if="isAdd">
          <el-input 
            v-model="userForm.password" 
            type="password"
            show-password
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useUserStore } from '@/store/user'
import { useOrganizationStore } from '@/store/organization'
import { ElMessage, ElMessageBox } from 'element-plus'
import { formatDateTimeString } from '@/utils/format'

const userStore = useUserStore()
const organizationStore = useOrganizationStore()
const loading = ref(false)
const dialogVisible = ref(false)
const submitting = ref(false)
const isAdd = ref(true)

const users = computed(() => userStore.users)
const organizationTree = computed(() => organizationStore.organizationTree)

const userForm = reactive({
  username: '',
  email: '',
  organization_id: null,
  password: ''
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  organization_id: [
    { required: true, message: '请选择组织', trigger: 'change' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur', when: () => isAdd.value }
  ]
}

const dialogTitle = computed(() => isAdd.value ? '添加用户' : '编辑用户')

const getUserStatusType = (status) => {
  const types = {
    'pending': 'warning',
    'approved': 'success',
    'rejected': 'danger'
  }
  return types[status] || 'info'
}

const getUserStatusText = (status) => {
  const texts = {
    'pending': '待审批',
    'approved': '已批准',
    'rejected': '已拒绝'
  }
  return texts[status] || status
}

const handleAddUser = () => {
  isAdd.value = true
  Object.assign(userForm, {
    username: '',
    email: '',
    organization_id: null,
    password: ''
  })
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isAdd.value = false
  Object.assign(userForm, {
    id: row.id,
    username: row.username,
    email: row.email,
    organization_id: row.organization_id
  })
  dialogVisible.value = true
}

const handleSubmit = async () => {
  try {
    submitting.value = true
    if (isAdd.value) {
      await userStore.createUser(userForm)
      ElMessage.success('用户创建成功')
    } else {
      await userStore.updateUser(userForm)
      ElMessage.success('用户更新成功')
    }
    dialogVisible.value = false
    await refreshUsers()
  } catch (error) {
    ElMessage.error(error.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

const handleApprove = async (user) => {
  try {
    await ElMessageBox.confirm(`确定要批准用户 ${user.username} 的注册申请吗？`)
    await userStore.approveUser(user.id)
    ElMessage.success('用户已批准')
    await refreshUsers()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

const handleReject = async (user) => {
  try {
    await ElMessageBox.confirm(`确定要拒绝用户 ${user.username} 的注册申请吗？`)
    await userStore.rejectUser(user.id)
    ElMessage.success('用户已拒绝')
    await refreshUsers()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

const refreshUsers = async () => {
  try {
    loading.value = true
    await userStore.fetchUsers()
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await Promise.all([
    refreshUsers(),
    organizationStore.fetchOrganizationTree()
  ])
})
</script>

<style scoped>
.users-container {
  padding: 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style> 