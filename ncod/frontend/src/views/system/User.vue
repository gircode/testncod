<template>
  <div class="user-management">
    <a-card>
      <template #title>用户管理</template>
      <template #extra>
        <a-button
          type="primary"
          @click="showCreateModal"
          v-permission="'user:create'"
        >
          创建用户
        </a-button>
      </template>

      <a-table
        :columns="columns"
        :data-source="users"
        :loading="loading"
        row-key="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'action'">
            <a-space>
              <a-button
                type="link"
                @click="showEditModal(record)"
                v-permission="'user:update'"
              >
                编辑
              </a-button>
              <a-popconfirm
                title="确定要删除这个用户吗？"
                @confirm="handleDelete(record.id)"
                v-permission="'user:delete'"
              >
                <a-button
                  type="link"
                  danger
                >
                  删除
                </a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 创建/编辑用户弹窗 -->
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
          label="用户名"
          name="username"
          v-if="!editingUserId"
        >
          <a-input v-model:value="formState.username" />
        </a-form-item>

        <a-form-item
          label="邮箱"
          name="email"
        >
          <a-input v-model:value="formState.email" />
        </a-form-item>

        <a-form-item
          label="密码"
          name="password"
          v-if="!editingUserId"
        >
          <a-input-password v-model:value="formState.password" />
        </a-form-item>

        <a-form-item
          label="角色"
          name="roles"
        >
          <a-select
            v-model:value="formState.roles"
            mode="multiple"
            placeholder="请选择角色"
          >
            <a-select-option
              v-for="role in roles"
              :key="role.name"
              :value="role.name"
            >
              {{ role.name }}
            </a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item
          label="组织"
          name="organizations"
        >
          <a-select
            v-model:value="formState.organizations"
            mode="multiple"
            placeholder="请选择组织"
          >
            <a-select-option
              v-for="org in organizations"
              :key="org.id"
              :value="org.id"
            >
              {{ org.name }}
            </a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item
          label="状态"
          name="is_active"
        >
          <a-switch v-model:checked="formState.is_active" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { userApi } from '@/api/user';
import { roleApi } from '@/api/role';
import { organizationApi } from '@/api/organization';

export default defineComponent({
  name: 'UserManagement',
  setup() {
    const loading = ref(false);
    const users = ref([]);
    const roles = ref([]);
    const organizations = ref([]);
    const modalVisible = ref(false);
    const modalTitle = ref('创建用户');
    const editingUserId = ref('');

    const formState = ref({
      username: '',
      email: '',
      password: '',
      roles: [],
      organizations: [],
      is_active: true
    });

    const rules = {
      username: [
        { required: true, message: '请输入用户名' }
      ],
      email: [
        { required: true, message: '请输入邮箱' }
      ],
      password: [
        { required: true, message: '请输入密码' }
      ]
    };

    const columns = [
      {
        title: '用户名',
        dataIndex: 'username',
        key: 'username'
      },
      {
        title: '邮箱',
        dataIndex: 'email',
        key: 'email'
      },
      {
        title: '状态',
        dataIndex: 'is_active',
        key: 'is_active',
        customRender: ({ text }) => text ? '启用' : '禁用'
      },
      {
        title: '操作',
        key: 'action'
      }
    ];

    const loadUsers = async () => {
      try {
        loading.value = true;
        const data = await userApi.listUsers();
        users.value = data;
      } catch (error) {
        message.error('加载用户列表失败');
      } finally {
        loading.value = false;
      }
    };

    const loadRoles = async () => {
      try {
        const data = await roleApi.listRoles();
        roles.value = data;
      } catch (error) {
        message.error('加载角色列表失败');
      }
    };

    const loadOrganizations = async () => {
      try {
        const data = await organizationApi.listOrganizations();
        organizations.value = data;
      } catch (error) {
        message.error('加载组织列表失败');
      }
    };

    const showCreateModal = () => {
      modalTitle.value = '创建用户';
      editingUserId.value = '';
      formState.value = {
        username: '',
        email: '',
        password: '',
        roles: [],
        organizations: [],
        is_active: true
      };
      modalVisible.value = true;
    };

    const showEditModal = (user) => {
      modalTitle.value = '编辑用户';
      editingUserId.value = user.id;
      formState.value = {
        username: user.username,
        email: user.email,
        roles: user.roles,
        organizations: user.organizations,
        is_active: user.is_active
      };
      modalVisible.value = true;
    };

    const handleModalOk = async () => {
      try {
        if (editingUserId.value) {
          await userApi.updateUser(
            editingUserId.value,
            formState.value
          );
          message.success('用户更新成功');
        } else {
          await userApi.createUser(formState.value);
          message.success('用户创建成功');
        }
        modalVisible.value = false;
        loadUsers();
      } catch (error) {
        message.error('操作失败');
      }
    };

    const handleModalCancel = () => {
      modalVisible.value = false;
    };

    const handleDelete = async (userId: string) => {
      try {
        await userApi.deleteUser(userId);
        message.success('用户删除成功');
        loadUsers();
      } catch (error) {
        message.error('删除失败');
      }
    };

    onMounted(() => {
      loadUsers();
      loadRoles();
      loadOrganizations();
    });

    return {
      loading,
      users,
      roles,
      organizations,
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
.user-management {
  padding: 24px;
}
</style> 