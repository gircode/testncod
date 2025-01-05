<template>
  <div class="other-users">
    <el-card>
      <template #header>
        <div class="card-header">
          <div class="search-area">
            <el-input
              v-model="searchQuery"
              placeholder="搜索用户名/姓名/手机号"
              clearable
              @clear="handleSearch"
              style="width: 250px;"
            >
              <template #append>
                <el-button @click="handleSearch">
                  <el-icon><Search /></el-icon>
                </el-button>
              </template>
            </el-input>
            
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              @change="handleSearch"
              style="margin-left: 10px;"
            />
          </div>
          
          <el-button
            type="primary"
            :disabled="!selectedUsers.length"
            @click="handleBatchAssign"
          >
            批量分配
          </el-button>
        </div>
      </template>
      
      <el-table
        v-loading="loading"
        :data="users"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="name" label="姓名" />
        <el-table-column prop="phone" label="手机号" />
        <el-table-column prop="email" label="邮箱" />
        <el-table-column prop="created_at" label="注册时间">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              @click="handleAssign(row)"
            >
              分配
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
    
    <!-- 分配对话框 -->
    <el-dialog
      v-model="assignDialogVisible"
      :title="isMultiple ? '批量分配用户' : '分配用户'"
      width="500px"
    >
      <el-form :model="assignForm" label-width="100px">
        <el-form-item label="目标组织" required>
          <el-cascader
            v-model="assignForm.organizationId"
            :options="organizationOptions"
            :props="{
              value: 'id',
              label: 'name',
              children: 'children',
              checkStrictly: true
            }"
            placeholder="请选择组织"
            clearable
          />
        </el-form-item>
        <el-form-item label="备注">
          <el-input
            v-model="assignForm.remark"
            type="textarea"
            :rows="3"
            placeholder="请输入分配备注"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="assignDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitAssign">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { getOtherUsers, assignUser, batchAssignUsers } from '@/api/user'
import { getOrganizationTree } from '@/api/organization'
import { formatDateTime } from '@/utils/format'
import type { UserInfo, OrganizationTree } from '@/types'
import { Search } from '@element-plus/icons-vue'

const loading = ref(false)
const users = ref<UserInfo[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const selectedUsers = ref<UserInfo[]>([])

const assignDialogVisible = ref(false)
const assignForm = ref({
  organizationId: null as number | null,
  remark: ''
})
const organizationOptions = ref<OrganizationTree[]>([])
const currentUser = ref<UserInfo | null>(null)
const isMultiple = ref(false)

// 搜索相关
const searchQuery = ref('')
const dateRange = ref<[Date, Date] | null>(null)

// 状态映射
const statusMap = {
  pending: { type: 'warning', text: '待分配' },
  approved: { type: 'success', text: '已分配' },
  rejected: { type: 'danger', text: '已拒绝' }
}

const getStatusType = (status: string) => statusMap[status]?.type || 'info'
const getStatusText = (status: string) => statusMap[status]?.text || status

// 加载用户列表
const loadUsers = async () => {
  loading.value = true
  try {
    const response = await getOtherUsers({
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value,
      search: searchQuery.value,
      start_date: dateRange.value?.[0]?.toISOString(),
      end_date: dateRange.value?.[1]?.toISOString()
    })
    users.value = response.data.items
    total.value = response.data.total
  } catch (error) {
    ElMessage.error('获取用户列表失败')
  } finally {
    loading.value = false
  }
}

// 加载组织树
const loadOrganizationTree = async () => {
  try {
    const response = await getOrganizationTree()
    organizationOptions.value = response.data
  } catch (error) {
    ElMessage.error('获取组织结构失败')
  }
}

// 处理分配
const handleAssign = (user: UserInfo) => {
  currentUser.value = user
  isMultiple.value = false
  assignForm.value.organizationId = null
  assignDialogVisible.value = true
}

// 处理批量分配
const handleBatchAssign = () => {
  if (!selectedUsers.value.length) {
    ElMessage.warning('请选择要分配的用户')
    return
  }
  isMultiple.value = true
  assignForm.value.organizationId = null
  assignDialogVisible.value = true
}

// 提交分配
const submitAssign = async () => {
  if (!assignForm.value.organizationId) {
    ElMessage.warning('请选择目标组织')
    return
  }
  
  try {
    if (isMultiple.value) {
      await batchAssignUsers(
        selectedUsers.value.map(u => u.id),
        assignForm.value.organizationId
      )
      ElMessage.success('批量分配成功')
    } else if (currentUser.value) {
      await assignUser(
        currentUser.value.id,
        assignForm.value.organizationId
      )
      ElMessage.success('分配成功')
    }
    
    assignDialogVisible.value = false
    loadUsers()
  } catch (error) {
    ElMessage.error('分配失败')
  }
}

const handleSelectionChange = (selection: UserInfo[]) => {
  selectedUsers.value = selection
}

const handleSizeChange = (val: number) => {
  pageSize.value = val
  loadUsers()
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
  loadUsers()
}

// 处理搜索
const handleSearch = async () => {
  currentPage.value = 1
  await loadUsers()
}

onMounted(() => {
  loadUsers()
  loadOrganizationTree()
})
</script>

<style scoped>
.other-users {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pagination {
  margin-top: 20px;
  text-align: right;
}

.search-area {
  display: flex;
  align-items: center;
}

.el-tag {
  text-transform: capitalize;
}
</style> 