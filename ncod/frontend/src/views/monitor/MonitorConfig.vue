<template>
    <div class="monitor-config">
        <a-card>
            <template #title>监控配置</template>
            <template #extra>
                <a-button type="primary" @click="showCreateModal" v-permission="'monitor:write'">
                    添加配置
                </a-button>
            </template>

            <!-- 配置列表 -->
            <a-table :columns="columns" :data-source="configs" :loading="loading" row-key="id">
                <template #bodyCell="{ column, record }">
                    <template v-if="column.key === 'enabled'">
                        <a-switch v-model:checked="record.enabled"
                            @change="(checked) => handleStatusChange(record, checked)"
                            :disabled="!hasPermission('monitor:write')" />
                    </template>
                    <template v-if="column.key === 'threshold'">
                        {{ record.threshold }}{{ getMetricUnit(record.metric_type) }}
                    </template>
                    <template v-if="column.key === 'alert_levels'">
                        <a-tag v-for="(level, key) in record.alert_levels" :key="key" :color="getAlertColor(key)">
                            {{ key }}: {{ level }}
                        </a-tag>
                    </template>
                    <template v-if="column.key === 'action'">
                        <a-space>
                            <a-button type="link" @click="showEditModal(record)" v-permission="'monitor:write'">
                                编辑
                            </a-button>
                        </a-space>
                    </template>
                </template>
            </a-table>
        </a-card>

        <!-- 配置表单弹窗 -->
        <a-modal v-model:visible="modalVisible" :title="modalTitle" @ok="handleModalOk" @cancel="handleModalCancel">
            <a-form ref="formRef" :model="formState" :rules="rules" :label-col="{ span: 6 }"
                :wrapper-col="{ span: 16 }">
                <a-form-item label="指标类型" name="metric_type">
                    <a-select v-model:value="formState.metric_type" placeholder="请选择指标类型" :disabled="!!formState.id">
                        <a-select-option v-for="type in metricTypes" :key="type.value" :value="type.value">
                            {{ type.label }}
                        </a-select-option>
                    </a-select>
                </a-form-item>

                <a-form-item label="启用状态" name="enabled">
                    <a-switch v-model:checked="formState.enabled" />
                </a-form-item>

                <a-form-item label="阈值" name="threshold">
                    <a-input-number v-model:value="formState.threshold" :min="0" :max="100"
                        :addonAfter="getMetricUnit(formState.metric_type)" />
                </a-form-item>

                <a-form-item label="采集间隔(秒)" name="interval">
                    <a-input-number v-model:value="formState.interval" :min="5" :max="3600" />
                </a-form-item>

                <a-form-item label="告警级别" name="alert_levels">
                    <a-space direction="vertical" style="width: 100%">
                        <a-row v-for="level in alertLevels" :key="level.value">
                            <a-col :span="8">
                                <a-tag :color="level.color">{{ level.label }}</a-tag>
                            </a-col>
                            <a-col :span="16">
                                <a-input-number v-model:value="formState.alert_levels[level.value]" :min="0" :max="100"
                                    :addonAfter="getMetricUnit(formState.metric_type)" />
                            </a-col>
                        </a-row>
                    </a-space>
                </a-form-item>

                <a-form-item label="描述" name="description">
                    <a-textarea v-model:value="formState.description" :rows="3" placeholder="请输入配置描述" />
                </a-form-item>
            </a-form>
        </a-modal>
    </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { usePermission } from '@/hooks/usePermission';
import { monitorConfigApi } from '@/api/monitor-config';

interface MonitorConfig {
    id: string;
    name: string;
    type: string;
    interval: number;
    enabled: boolean;
    description?: string;
}

interface FormState {
    id?: string;
    name: string;
    type: string;
    interval: number;
    enabled: boolean;
    description?: string;
}

interface FormRules {
    name: Array<{ required: boolean; message: string }>;
    type: Array<{ required: boolean; message: string }>;
    interval: Array<{ required: boolean; message: string }>;
}

export default defineComponent({
    name: 'MonitorConfig',
    setup() {
        const { hasPermission } = usePermission();
        const loading = ref(false);
        const configs = ref<MonitorConfig[]>([]);
        const modalVisible = ref(false);
        const modalTitle = ref('');
        const formState = ref<FormState>({
            name: '',
            type: '',
            interval: 60,
            enabled: true,
            description: ''
        });

        // 表单校验规则
        const formRules: FormRules = {
            name: [{ required: true, message: '请输入配置名称' }],
            type: [{ required: true, message: '请选择监控类型' }],
            interval: [{ required: true, message: '请输入采集间隔' }]
        };

        // 表格列定义
        const columns = [
            { title: '配置名称', dataIndex: 'name', key: 'name' },
            { title: '指标类型', dataIndex: 'type', key: 'type' },
            { title: '采集间隔', dataIndex: 'interval', key: 'interval' },
            { title: '启用状态', dataIndex: 'enabled', key: 'enabled' },
            { title: '操作', key: 'action', width: 150 }
        ];

        // 监控类型
        const monitorTypes = [
            { value: 'cpu', label: 'CPU使用率' },
            { value: 'memory', label: '内存使用率' },
            { value: 'disk', label: '磁盘使用率' },
            { value: 'network', label: '网络使用率' }
        ];

        // 处理状态切换
        const handleStatusChange = async (record: MonitorConfig, checked: boolean) => {
            try {
                await monitorConfigApi.updateConfig(record.id, {
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
                const res = await monitorConfigApi.getConfigs();
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
                type: '',
                interval: 60,
                enabled: true,
                description: ''
            };
            modalVisible.value = true;
        };

        // 显示编辑弹窗
        const showEditModal = (record: MonitorConfig) => {
            modalTitle.value = '编辑配置';
            formState.value = { ...record };
            modalVisible.value = true;
        };

        // 处理弹窗确认
        const handleModalOk = async () => {
            try {
                const formData = { ...formState.value };
                if (formData.id) {
                    await monitorConfigApi.updateConfig(formData.id, formData);
                } else {
                    await monitorConfigApi.createConfig(formData);
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
        const handleDelete = async (record: MonitorConfig) => {
            try {
                await monitorConfigApi.deleteConfig(record.id);
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
            monitorTypes,
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
.monitor-config {
    padding: 24px;

    .ant-card {
        margin-bottom: 24px;
    }
}
</style>