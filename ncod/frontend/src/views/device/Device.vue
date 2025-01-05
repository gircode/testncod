<template>
  <div class="device-management">
    <a-card>
      <template #title>设备管理</template>
      <template #extra>
        <a-space>
          <a-select
            v-model:value="filterOrg"
            style="width: 200px"
            placeholder="选择组织"
            allow-clear
            @change="handleOrgChange"
          >
            <a-select-option
              v-for="org in organizations"
              :key="org.id"
              :value="org.id"
            >
              {{ org.name }}
            </a-select-option>
          </a-select>
          <a-button
            type="primary"
            @click="showCreateModal"
            v-permission="'device:create'"
          >
            添加设备
          </a-button>
        </a-space>
      </template>

      <a-table
        :columns="columns"
        :data-source="devices"
        :loading="loading"
        row-key="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'is_active'">
            <a-tag :color="record.is_active ? 'success' : 'error'">
              {{ record.is_active ? '在线' : '离线' }}
            </a-tag>
          </template>
          <template v-if="column.key === 'action'">
            <a-space>
              <a-button
                type="link"
                @click="showEditModal(record)"
                v-permission="'device:update'"
              >
                编辑
              </a-button>
              <a-popconfirm
                title="确定要删除这个设备吗？"
                @confirm="handleDelete(record.id)"
                v-permission="'device:delete'"
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

    <!-- 创建/编辑设备弹窗 -->
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
          label="设备名称"
          name="name"
        >
          <a-input v-model:value="formState.name" />
        </a-form-item>

        <a-form-item
          label="MAC地址"
          name="mac_address"
        >
          <a-input v-model:value="formState.mac_address" />
        </a-form-item>

        <a-form-item
          label="IP地址"
          name="ip_address"
        >
          <a-input v-model:value="formState.ip_address" />
        </a-form-item>

        <a-form-item
          label="所属组织"
          name="organization_id"
        >
          <a-select
            v-model:value="formState.organization_id"
            placeholder="请选择组织"
            allow-clear
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
          label="从服务器"
          name="slave_id"
        >
          <a-select
            v-model:value="formState.slave_id"
            placeholder="请选择从服务器"
            allow-clear
          >
            <a-select-option
              v-for="slave in slaves"
              :key="slave.id"
              :value="slave.id"
            >
              {{ slave.name }}
            </a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item
          label="描述"
          name="description"
        >
          <a-textarea v-model:value="formState.description" />
        </a-form-item>

        <a-form-item
          label="状态"
          name="is_active"
          v-if="editingDeviceId"
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
import { deviceApi } from '@/api/device';
import { organizationApi } from '@/api/organization';
import { slaveApi } from '@/api/slave';
import { formatDate } from '@/utils/date';

export default defineComponent({
  name: 'DeviceManagement',
  setup() {
    const loading = ref(false);
    const devices = ref<any[]>([]);
    const organizations = ref<any[]>([]);
    const slaves = ref<any[]>([]);
    const filterOrg = ref<string>();
    const modalVisible = ref(false);
    const modalTitle = ref('');
    const editingDeviceId = ref('');
    const formState = ref({
      name: '',
      mac_address: '',
      ip_address: '',
      description: '',
      organization_id: undefined,
      slave_id: undefined,
      is_active: true
    });

    const columns = [
      {
        title: '设备名称',
        dataIndex: 'name',
        key: 'name'
      },
      {
        title: 'MAC地址',
        dataIndex: 'mac_address',
        key: 'mac_address'
      },
      {
        title: 'IP地址',
        dataIndex: 'ip_address',
        key: 'ip_address'
      },
      {
        title: '状态',
        dataIndex: 'is_active',
        key: 'is_active'
      },
      {
        title: '创建时间',
        dataIndex: 'created_at',
        key: 'created_at',
        render: (text: string) => formatDate(text)
      },
      {
        title: '操作',
        key: 'action'
      }
    ];

    const rules = {
      name: [{ required: true, message: '请输入设备名称' }],
      mac_address: [{ required: true, message: '请输入MAC地址' }]
    };

    const loadDevices = async () => {
      try {
        loading.value = true;
        const params = filterOrg.value ? { organization_id: filterOrg.value } : {};
        const data = await deviceApi.listDevices(params);
        devices.value = data;
      } catch (error) {
        message.error('加载设备列表失败');
      } finally {
        loading.value = false;
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

    const loadSlaves = async () => {
      try {
        const data = await slaveApi.listSlaves();
        slaves.value = data;
      } catch (error) {
        message.error('加载从服务器列表失败');
      }
    };

    const handleOrgChange = () => {
      loadDevices();
    };

    const showCreateModal = () => {
      modalTitle.value = '创建设备';
      editingDeviceId.value = '';
      formState.value = {
        name: '',
        mac_address: '',
        ip_address: '',
        description: '',
        organization_id: filterOrg.value,
        slave_id: undefined,
        is_active: true
      };
      modalVisible.value = true;
    };

    const showEditModal = async (device: any) => {
      try {
        modalTitle.value = '编辑设备';
        editingDeviceId.value = device.id;
        formState.value = {
          name: device.name,
          mac_address: device.mac_address,
          ip_address: device.ip_address,
          description: device.description,
          organization_id: device.organization_id,
          slave_id: device.slave_id,
          is_active: device.is_active
        };
        modalVisible.value = true;
      } catch (error) {
        message.error('加载设备信息失败');
      }
    };

    const handleModalOk = async () => {
      try {
        if (editingDeviceId.value) {
          await deviceApi.updateDevice(
            editingDeviceId.value,
            formState.value
          );
          message.success('设备更新成功');
        } else {
          await deviceApi.createDevice(formState.value);
          message.success('设备创建成功');
        }
        modalVisible.value = false;
        loadDevices();
      } catch (error) {
        message.error('操作失败');
      }
    };

    const handleModalCancel = () => {
      modalVisible.value = false;
    };

    const handleDelete = async (deviceId: string) => {
      try {
        await deviceApi.deleteDevice(deviceId);
        message.success('设备删除成功');
        loadDevices();
      } catch (error) {
        message.error('删除失败');
      }
    };

    onMounted(() => {
      loadDevices();
      loadOrganizations();
      loadSlaves();
    });

    return {
      loading,
      devices,
      organizations,
      slaves,
      filterOrg,
      columns,
      modalVisible,
      modalTitle,
      formState,
      rules,
      handleOrgChange,
      showCreateModal,
      showEditModal,
      handleModalOk,
      handleModalCancel,
      handleDelete,
      formatDate
    };
  }
});
</script>

<style lang="less" scoped>
.device-management {
  padding: 24px;

  .ant-card {
    margin-bottom: 24px;
  }
}
</style> 