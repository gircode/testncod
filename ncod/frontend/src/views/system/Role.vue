<template>
  <div class="role-management">
    <a-card>
      <template #title>角色管理</template>
      <template #extra>
        <a-button
          type="primary"
          @click="showCreateModal"
          v-permission="'role:create'"
        >
          创建角色
        </a-button>
      </template>

      <a-table
        :columns="columns"
        :data-source="roles"
        :loading="loading"
        row-key="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'action'">
            <a-space>
              <a-button
                type="link"
                @click="showEditModal(record)"
                v-permission="'role:update'"
              >
                编辑
              </a-button>
              <a-popconfirm
                title="确定要删除这个角色吗？"
                @confirm="handleDelete(record.id)"
                v-permission="'role:delete'"
              >
                <a-button
                  type="link"
                  danger
                  :disabled="record.is_system"
                >
                  删除
                </a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 创建/编辑角色弹窗 -->
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
      >
        <a-form-item
          label="角色名称"
          name="name"
        >
          <a-input v-model:value="formState.name" />
        </a-form-item>

        <a-form-item
          label="角色描述"
          name="description"
        >
          <a-textarea v-model:value="formState.description" />
        </a-form-item>

        <a-form-item
          label="权限"
          name="permissions"
        >
          <a-select
            v-model:value="formState.permissions"
            mode="multiple"
            placeholder="请选择权限"
          >
            <a-select-option
              v-for="perm in permissions"
              :key="perm.code"
              :value="perm.code"
            >
              {{ perm.name }}
            </a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { roleApi } from '@/api/role';
import { permissionApi } from '@/api/permission';

export default defineComponent({
  name: 'RoleManagement',
  setup() {
    const loading = ref(false);
    const roles = ref([]);
    const permissions = ref([]);
    const modalVisible = ref(false);
    const modalTitle = ref('创建角色');
    const editingRoleId = ref('');

    const formState = ref({
      name: '',
      description: '',
      permissions: []
    });

    const rules = {
      name: [
        { required: true, message: '请输入角色名称' }
      ]
    };

    const columns = [
      {
        title: '角色名称',
        dataIndex: 'name',
        key: 'name'
      },
      {
        title: '描述',
        dataIndex: 'description',
        key: 'description'
      },
      {
        title: '系统角色',
        dataIndex: 'is_system',
        key: 'is_system',
        customRender: ({ text }) => text ? '是' : '否'
      },
      {
        title: '操作',
        key: 'action'
      }
    ];

    const loadRoles = async () => {
      try {
        loading.value = true;
        const data = await roleApi.listRoles();
        roles.value = data;
      } catch (error) {
        message.error('加载角色列表失败');
      } finally {
        loading.value = false;
      }
    };

    const loadPermissions = async () => {
      try {
        const data = await permissionApi.listPermissions();
        permissions.value = data;
      } catch (error) {
        message.error('加载权限列表失败');
      }
    };

    const showCreateModal = () => {
      modalTitle.value = '创建角色';
      editingRoleId.value = '';
      formState.value = {
        name: '',
        description: '',
        permissions: []
      };
      modalVisible.value = true;
    };

    const showEditModal = (role) => {
      modalTitle.value = '编辑角色';
      editingRoleId.value = role.id;
      formState.value = {
        name: role.name,
        description: role.description,
        permissions: role.permissions
      };
      modalVisible.value = true;
    };

    const handleModalOk = async () => {
      try {
        if (editingRoleId.value) {
          await roleApi.updateRole(
            editingRoleId.value,
            formState.value
          );
          message.success('角色更新成功');
        } else {
          await roleApi.createRole(formState.value);
          message.success('角色创建成功');
        }
        modalVisible.value = false;
        loadRoles();
      } catch (error) {
        message.error('操作失败');
      }
    };

    const handleModalCancel = () => {
      modalVisible.value = false;
    };

    const handleDelete = async (roleId: string) => {
      try {
        await roleApi.deleteRole(roleId);
        message.success('角色删除成功');
        loadRoles();
      } catch (error) {
        message.error('删除失败');
      }
    };

    onMounted(() => {
      loadRoles();
      loadPermissions();
    });

    return {
      loading,
      roles,
      permissions,
      columns,
      modalVisible,
      modalTitle,
      formState,
      rules,
      showCreateModal,
      showEditModal,
      handleModalOk,
      handleModalCancel,
      handleDelete
    };
  }
});
</script>

<style lang="less" scoped>
.role-management {
  padding: 24px;
}
</style> 