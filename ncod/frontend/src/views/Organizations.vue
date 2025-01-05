<template>
  <div class="organizations-container">
    <el-card>
      <template #header>
        <div class="header-content">
          <h2>组织架构管理</h2>
          <el-button type="primary" @click="handleAddOrg">
            添加组织
          </el-button>
        </div>
      </template>
      
      <el-tree
        :data="organizationTree"
        :props="defaultProps"
        node-key="id"
        default-expand-all
      >
        <template #default="{ node, data }">
          <div class="custom-tree-node">
            <span>{{ node.label }}</span>
            <span>
              <el-button
                type="primary"
                link
                @click="handleEdit(data)"
              >
                编辑
              </el-button>
              <el-button
                type="danger"
                link
                @click="handleDelete(node, data)"
              >
                删除
              </el-button>
            </span>
          </div>
        </template>
      </el-tree>
    </el-card>

    <!-- 组织表单对话框 -->
    <el-dialog
      :title="dialogTitle"
      v-model="dialogVisible"
      width="500px"
    >
      <el-form
        :model="orgForm"
        :rules="rules"
        ref="orgFormRef"
        label-width="100px"
      >
        <el-form-item label="名称" prop="name">
          <el-input v-model="orgForm.name" />
        </el-form-item>
        <el-form-item label="编码" prop="code">
          <el-input v-model="orgForm.code" />
        </el-form-item>
        <el-form-item label="上级组织" prop="parent_id">
          <el-tree-select
            v-model="orgForm.parent_id"
            :data="organizationTree"
            :props="{
              label: 'name',
              value: 'id',
              children: 'children'
            }"
            placeholder="请选择上级组织"
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

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useOrganizationStore } from '@/store/organization'
import { ElMessage, ElMessageBox } from 'element-plus'

const organizationStore = useOrganizationStore()
const dialogVisible = ref(false)
const submitting = ref(false)
const isAdd = ref(true)

const organizationTree = computed(() => organizationStore.organizationTree)

const defaultProps = {
  children: 'children',
  label: 'name'
}

const orgForm = reactive({
  id: '',
  name: '',
  code: '',
  parent_id: null as string | null
})

const rules = {
  name: [
    { required: true, message: '请输入组织名称', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入组织编码', trigger: 'blur' }
  ]
}

const dialogTitle = computed(() => isAdd.value ? '添加组织' : '编辑组织')

const handleAddOrg = () => {
  isAdd.value = true
  Object.assign(orgForm, {
    id: '',
    name: '',
    code: '',
    parent_id: null
  })
  dialogVisible.value = true
}

const handleEdit = (data: any) => {
  isAdd.value = false
  Object.assign(orgForm, {
    id: data.id,
    name: data.name,
    code: data.code,
    parent_id: data.parent_id
  })
  dialogVisible.value = true
}

const handleDelete = async (node: any, data: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除组织 ${data.name} 吗？删除后无法恢复！`,
      '警告',
      {
        type: 'warning'
      }
    )
    await organizationStore.deleteOrganization(data.id)
    ElMessage.success('删除成功')
    await refreshOrganizations()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleSubmit = async () => {
  try {
    submitting.value = true
    if (isAdd.value) {
      await organizationStore.createOrganization(orgForm)
      ElMessage.success('组织创建成功')
    } else {
      await organizationStore.updateOrganization(orgForm)
      ElMessage.success('组织更新成功')
    }
    dialogVisible.value = false
    await refreshOrganizations()
  } catch (error: any) {
    ElMessage.error(error.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

const refreshOrganizations = async () => {
  await organizationStore.fetchOrganizationTree()
}

onMounted(() => {
  refreshOrganizations()
})
</script>

<style scoped>
.organizations-container {
  padding: 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.custom-tree-node {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-right: 8px;
}
</style> 