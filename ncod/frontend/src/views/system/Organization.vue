<template>
  <div class="organization-management">
    <a-row :gutter="16">
      <!-- 组织树 -->
      <a-col :span="8">
        <a-card>
          <template #title>组织架构</template>
          <template #extra>
            <a-button
              type="primary"
              @click="showCreateModal()"
              v-permission="'organization:create'"
            >
              添加组织
            </a-button>
          </template>
          <a-tree
            v-model:selectedKeys="selectedKeys"
            :tree-data="treeData"
            :loading="loading"
            @select="handleSelect"
          >
            <template #title="{ title, key }">
              <a-dropdown>
                <span>{{ title }}</span>
                <template #overlay>
                  <a-menu>
                    <a-menu-item
                      key="add"
                      v-permission="'organization:create'"
                      @click="showCreateModal(key)"
                    >
                      添加子组织
                    </a-menu-item>
                    <a-menu-item
                      key="edit"
                      v-permission="'organization:update'"
                      @click="showEditModal(key)"
                    >
                      编辑组织
                    </a-menu-item>
                    <a-menu-item
                      key="delete"
                      v-permission="'organization:delete'"
                      @click="handleDelete(key)"
                    >
                      删除组织
                    </a-menu-item>
                  </a-menu>
                </template>
              </a-dropdown>
            </template>
          </a-tree>
        </a-card>
      </a-col>

      <!-- 组织详情 -->
      <a-col :span="16">
        <a-card v-if="currentOrg">
          <template #title>组织详情</template>
          <a-descriptions bordered>
            <a-descriptions-item label="组织名称">
              {{ currentOrg.name }}
            </a-descriptions-item>
            <a-descriptions-item label="组织代码">
              {{ currentOrg.code }}
            </a-descriptions-item>
            <a-descriptions-item label="上级组织">
              {{ getParentName(currentOrg.parent_id) }}
            </a-descriptions-item>
            <a-descriptions-item label="创建时间">
              {{ formatDate(currentOrg.created_at) }}
            </a-descriptions-item>
            <a-descriptions-item label="更新时间">
              {{ formatDate(currentOrg.updated_at) }}
            </a-descriptions-item>
            <a-descriptions-item label="描述">
              {{ currentOrg.description || '-' }}
            </a-descriptions-item>
          </a-descriptions>
        </a-card>
      </a-col>
    </a-row>

    <!-- 创建/编辑组织弹窗 -->
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
          label="组织名称"
          name="name"
        >
          <a-input v-model:value="formState.name" />
        </a-form-item>

        <a-form-item
          label="组织代码"
          name="code"
        >
          <a-input v-model:value="formState.code" />
        </a-form-item>

        <a-form-item
          label="上级组织"
          name="parent_id"
        >
          <a-tree-select
            v-model:value="formState.parent_id"
            :tree-data="treeData"
            :disabled="!!editingOrgId"
            allow-clear
            placeholder="请选择上级组织"
          />
        </a-form-item>

        <a-form-item
          label="描述"
          name="description"
        >
          <a-textarea v-model:value="formState.description" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { organizationApi } from '@/api/organization';
import { formatDate } from '@/utils/date';

export default defineComponent({
  name: 'OrganizationManagement',
  setup() {
    const loading = ref(false);
    const treeData = ref<any[]>([]);
    const selectedKeys = ref<string[]>([]);
    const currentOrg = ref<any>(null);
    const modalVisible = ref(false);
    const modalTitle = ref('');
    const editingOrgId = ref('');
    const formState = ref({
      name: '',
      code: '',
      description: '',
      parent_id: undefined
    });

    const rules = {
      name: [{ required: true, message: '请输入组织名称' }],
      code: [{ required: true, message: '请输入组织代码' }]
    };

    const loadOrganizationTree = async () => {
      try {
        loading.value = true;
        const data = await organizationApi.getOrganizationTree();
        treeData.value = formatTreeData(data);
      } catch (error) {
        message.error('加载组织树失败');
      } finally {
        loading.value = false;
      }
    };

    const formatTreeData = (data: any[]) => {
      return data.map(item => ({
        key: item.id,
        title: item.name,
        children: item.children ? formatTreeData(item.children) : undefined,
        ...item
      }));
    };

    const handleSelect = async (selectedKeys: string[]) => {
      if (selectedKeys.length > 0) {
        try {
          const org = await organizationApi.getOrganization(selectedKeys[0]);
          currentOrg.value = org;
        } catch (error) {
          message.error('加载组织详情失败');
        }
      } else {
        currentOrg.value = null;
      }
    };

    const showCreateModal = (parentId?: string) => {
      modalTitle.value = '创建组织';
      editingOrgId.value = '';
      formState.value = {
        name: '',
        code: '',
        description: '',
        parent_id: parentId
      };
      modalVisible.value = true;
    };

    const showEditModal = async (orgId: string) => {
      try {
        const org = await organizationApi.getOrganization(orgId);
        modalTitle.value = '编辑组织';
        editingOrgId.value = orgId;
        formState.value = {
          name: org.name,
          code: org.code,
          description: org.description,
          parent_id: org.parent_id
        };
        modalVisible.value = true;
      } catch (error) {
        message.error('加载组织信息失败');
      }
    };

    const handleModalOk = async () => {
      try {
        if (editingOrgId.value) {
          await organizationApi.updateOrganization(
            editingOrgId.value,
            formState.value
          );
          message.success('组织更新成功');
        } else {
          await organizationApi.createOrganization(formState.value);
          message.success('组织创建成功');
        }
        modalVisible.value = false;
        loadOrganizationTree();
      } catch (error) {
        message.error('操作失败');
      }
    };

    const handleModalCancel = () => {
      modalVisible.value = false;
    };

    const handleDelete = async (orgId: string) => {
      try {
        await organizationApi.deleteOrganization(orgId);
        message.success('组织删除成功');
        loadOrganizationTree();
        if (currentOrg.value?.id === orgId) {
          currentOrg.value = null;
        }
      } catch (error) {
        message.error('删除失败');
      }
    };

    const getParentName = (parentId?: string) => {
      if (!parentId) return '-';
      const findParent = (nodes: any[]): string => {
        for (const node of nodes) {
          if (node.id === parentId) {
            return node.name;
          }
          if (node.children) {
            const name = findParent(node.children);
            if (name) return name;
          }
        }
        return '-';
      };
      return findParent(treeData.value);
    };

    onMounted(() => {
      loadOrganizationTree();
    });

    return {
      loading,
      treeData,
      selectedKeys,
      currentOrg,
      modalVisible,
      modalTitle,
      formState,
      rules,
      handleSelect,
      showCreateModal,
      showEditModal,
      handleModalOk,
      handleModalCancel,
      handleDelete,
      getParentName,
      formatDate
    };
  }
});
</script>

<style lang="less" scoped>
.organization-management {
  padding: 24px;

  .ant-card {
    margin-bottom: 24px;
  }
}
</style> 