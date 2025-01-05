<template>
    <div class="notify-config">
        <a-card>
            <template #title>通知配置</template>
            <template #extra>
                <a-button type="primary" @click="showCreateModal" v-permission="'notify:write'">
                    添加配置
                </a-button>
            </template>

            <!-- 配置列表 -->
            <a-table :columns="columns" :data-source="configs" :loading="loading" row-key="id">
                <template #bodyCell="{ column, record }">
                    <template v-if="column.key === 'channel'">
                        <a-tag :icon="getChannelIcon(record.channel)">
                            {{ getChannelLabel(record.channel) }}
                        </a-tag>
                    </template>
                    <template v-if="column.key === 'action'">
                        <a-space>
                            <a-button type="link" @click="showEditModal(record)" v-permission="'notify:write'">
                                编辑
                            </a-button>
                            <a-popconfirm title="确定要删除此配置吗？" @confirm="handleDelete(record)"
                                v-permission="'notify:write'">
                                <a-button type="link" danger>删除</a-button>
                            </a-popconfirm>
                        </a-space>
                    </template>
                </template>
            </a-table>
        </a-card>

        <!-- 配置表单弹窗 -->
        <a-modal v-model:visible="modalVisible" :title="modalTitle" @ok="handleModalOk" @cancel="handleModalCancel"
            width="600px">
            <a-form ref="formRef" :model="formState" :rules="rules" :label-col="{ span: 6 }"
                :wrapper-col="{ span: 16 }">
                <a-form-item label="配置名称" name="name">
                    <a-input v-model:value="formState.name" placeholder="请输入配置名称" />
                </a-form-item>

                <a-form-item label="通知渠道" name="channel">
                    <a-select v-model:value="formState.channel" placeholder="请选择通知渠道" :disabled="!!formState.id"
                        @change="handleChannelChange">
                        <a-select-option v-for="channel in NOTIFY_CHANNELS" :key="channel.value" :value="channel.value">
                            <span>
                                <icon-component :type="channel.icon" />
                                {{ channel.label }}
                            </span>
                        </a-select-option>
                    </a-select>
                </a-form-item>

                <!-- 动态渠道配置表单 -->
                <template v-if="formState.channel">
                    <a-form-item v-for="field in CHANNEL_FORMS[formState.channel]" :key="field.key" :label="field.label"
                        :name="['config', field.key]"
                        :rules="[{ required: field.required, message: `请输入${field.label}` }]">
                        <!-- 输入框 -->
                        <a-input v-if="field.type === 'input'" v-model:value="formState.config[field.key]"
                            :placeholder="`请输入${field.label}`" />

                        <!-- 密码框 -->
                        <a-input-password v-else-if="field.type === 'password'"
                            v-model:value="formState.config[field.key]" :placeholder="`请输入${field.label}`" />

                        <!-- 数字输入框 -->
                        <a-input-number v-else-if="field.type === 'number'" v-model:value="formState.config[field.key]"
                            :placeholder="`请输入${field.label}`" style="width: 100%" />

                        <!-- 多选框 -->
                        <a-select v-else-if="field.type === 'select'" v-model:value="formState.config[field.key]"
                            :mode="field.mode" :placeholder="`请选择${field.label}`" style="width: 100%" />

                        <!-- JSON编辑器 -->
                        <a-textarea v-else-if="field.type === 'json'" v-model:value="formState.config[field.key]"
                            :placeholder="`请输入${field.label} (JSON格式)`" :rows="4" />

                        <!-- 文本域 -->
                        <a-textarea v-else-if="field.type === 'textarea'" v-model:value="formState.config[field.key]"
                            :placeholder="`请输入${field.label}`" :rows="4" />
                    </a-form-item>
                </template>

                <a-form-item label="描述" name="description">
                    <a-textarea v-model:value="formState.description" placeholder="请输入配置描述" :rows="4" />
                </a-form-item>
            </a-form>
        </a-modal>
    </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { usePermission } from '@/hooks/usePermission';
import { notifyConfigApi, NOTIFY_CHANNELS, CHANNEL_FORMS } from '@/api/notify-config';

interface NotifyConfig {
    id: string;
    name: string;
    channel: string;
    config: Record<string, any>;
    enabled: boolean;
    description?: string;
}

interface FormState {
    id?: string;
    name: string;
    channel: string;
    config: Record<string, any>;
    enabled: boolean;
    description?: string;
}

interface FormRules {
    name: Array<{ required: boolean; message: string }>;
    channel: Array<{ required: boolean; message: string }>;
}

export default defineComponent({
    name: 'NotifyConfig',
    setup() {
        const { hasPermission } = usePermission();
        const loading = ref(false);
        const configs = ref<NotifyConfig[]>([]);
        const modalVisible = ref(false);
        const modalTitle = ref('');
        const formState = ref<FormState>({
            name: '',
            channel: '',
            config: {},
            enabled: true,
            description: ''
        });

        // 表单校验规则
        const formRules: FormRules = {
            name: [{ required: true, message: '请输入配置名称' }],
            channel: [{ required: true, message: '请选择通知渠道' }]
        };

        // 表格列定义
        const columns = [
            { title: '配置名称', dataIndex: 'name', key: 'name' },
            { title: '通知渠道', dataIndex: 'channel', key: 'channel' },
            { title: '描述', dataIndex: 'description', key: 'description' },
            { title: '操作', key: 'action', width: 150 }
        ];

        // 处理状态切换
        const handleStatusChange = async (record: NotifyConfig, checked: boolean) => {
            try {
                await notifyConfigApi.updateConfig(record.id, {
                    enabled: checked
                });
                message.success('状态更新成功');
            } catch (error) {
                message.error('状态更新失败');
                record.enabled = !checked;
            }
        };

        // 加载配置列表
        const loadConfigs = async () => {
            try {
                loading.value = true;
                const res = await notifyConfigApi.getConfigs();
                configs.value = res.data.map(config => ({
                    ...config,
                    key: config.id
                }));
            } catch (error) {
                if (error instanceof Error) {
                    message.error(error.message);
                } else {
                    message.error('加载配置失败');
                }
            } finally {
                loading.value = false;
            }
        };

        // 显示创建弹窗
        const showCreateModal = () => {
            modalTitle.value = '添加配置';
            formState.value = {
                name: '',
                channel: '',
                config: {},
                enabled: true,
                description: ''
            };
            modalVisible.value = true;
        };

        // 显示编辑弹窗
        const showEditModal = (record: NotifyConfig) => {
            modalTitle.value = '编辑配置';
            formState.value = { ...record };
            modalVisible.value = true;
        };

        // 处理弹窗确认
        const handleModalOk = async () => {
            try {
                const formData = { ...formState.value };
                if (formData.id) {
                    await notifyConfigApi.updateConfig(formData.id, formData);
                } else {
                    await notifyConfigApi.createConfig(formData);
                }
                message.success('保存成功');
                modalVisible.value = false;
                loadConfigs();
            } catch (error) {
                if (error instanceof Error) {
                    message.error(error.message);
                } else {
                    message.error('保存失败');
                }
            }
        };

        // 处理弹窗取消
        const handleModalCancel = () => {
            modalVisible.value = false;
        };

        // 处理删除
        const handleDelete = async (record: NotifyConfig) => {
            try {
                await notifyConfigApi.deleteConfig(record.id);
                message.success('删除成功');
                loadConfigs();
            } catch (error) {
                message.error('删除失败');
            }
        };

        onMounted(() => {
            loadConfigs();
        });

        return {
            loading,
            configs,
            modalVisible,
            modalTitle,
            formState,
            formRules,
            NOTIFY_CHANNELS,
            CHANNEL_FORMS,
            hasPermission,
            showCreateModal,
            showEditModal,
            handleModalOk,
            handleModalCancel,
            handleStatusChange,
            handleDelete,
            columns
        };
    }
});
</script>

<style lang="less" scoped>
.notify-config {
    padding: 24px;

    .ant-card {
        margin-bottom: 24px;
    }
}
</style>