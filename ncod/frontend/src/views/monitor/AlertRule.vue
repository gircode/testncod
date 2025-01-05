<template>
    <div class="alert-rule">
        <a-card>
            <template #title>告警规则</template>
            <template #extra>
                <a-button type="primary" @click="showCreateModal" v-permission="'alert:write'">
                    添加规则
                </a-button>
            </template>

            <!-- 规则列表 -->
            <a-table :columns="columns" :data-source="rules" :loading="loading" row-key="id">
                <template #bodyCell="{ column, record }">
                    <template v-if="column.key === 'metric_type'">
                        {{ getMetricLabel(record.metric_type) }}
                    </template>
                    <template v-if="column.key === 'condition'">
                        {{ getConditionLabel(record.condition) }}
                        {{ record.threshold }}{{ getMetricUnit(record.metric_type) }}
                    </template>
                    <template v-if="column.key === 'level'">
                        <a-tag :color="getAlertColor(record.level)">
                            {{ getAlertLabel(record.level) }}
                        </a-tag>
                    </template>
                    <template v-if="column.key === 'enabled'">
                        <a-switch v-model:checked="record.enabled"
                            @change="(checked) => handleStatusChange(record, checked)"
                            :disabled="!hasPermission('alert:write')" />
                    </template>
                    <template v-if="column.key === 'notify_channels'">
                        <a-tag v-for="channel in record.notify_channels" :key="channel" color="blue">
                            {{ getChannelLabel(channel) }}
                        </a-tag>
                    </template>
                    <template v-if="column.key === 'action'">
                        <a-space>
                            <a-button type="link" @click="showEditModal(record)" v-permission="'alert:write'">
                                编辑
                            </a-button>
                            <a-popconfirm title="确定要删除此规则吗？" @confirm="handleDelete(record)"
                                v-permission="'alert:write'">
                                <a-button type="link" danger>删除</a-button>
                            </a-popconfirm>
                        </a-space>
                    </template>
                </template>
            </a-table>
        </a-card>

        <!-- 规则表单弹窗 -->
        <a-modal v-model:visible="modalVisible" :title="modalTitle" @ok="handleModalOk" @cancel="handleModalCancel">
            <a-form ref="formRef" :model="formState" :rules="formRules" :label-col="{ span: 6 }"
                :wrapper-col="{ span: 16 }">
                <a-form-item label="规则名称" name="name">
                    <a-input v-model:value="formState.name" placeholder="请输入规则名称" />
                </a-form-item>

                <a-form-item label="指标类型" name="metric_type">
                    <a-select v-model:value="formState.metric_type" placeholder="请选择指标类型" :disabled="!!formState.id">
                        <a-select-option v-for="type in METRIC_TYPES" :key="type.value" :value="type.value">
                            {{ type.label }}
                        </a-select-option>
                    </a-select>
                </a-form-item>

                <a-form-item label="告警条件" required>
                    <a-row :gutter="8">
                        <a-col :span="8">
                            <a-form-item name="condition" noStyle>
                                <a-select v-model:value="formState.condition" placeholder="请选择条件">
                                    <a-select-option v-for="cond in CONDITIONS" :key="cond.value" :value="cond.value">
                                        {{ cond.label }}
                                    </a-select-option>
                                </a-select>
                            </a-form-item>
                        </a-col>
                        <a-col :span="16">
                            <a-form-item name="threshold" noStyle>
                                <a-input-number v-model:value="formState.threshold" :min="0" :max="100"
                                    :addonAfter="getMetricUnit(formState.metric_type)" style="width: 100%" />
                            </a-form-item>
                        </a-col>
                    </a-row>
                </a-form-item>

                <a-form-item label="告警级别" name="level">
                    <a-select v-model:value="formState.level" placeholder="请选择告警级别">
                        <a-select-option v-for="level in ALERT_LEVELS" :key="level.value" :value="level.value">
                            <a-tag :color="level.color">{{ level.label }}</a-tag>
                        </a-select-option>
                    </a-select>
                </a-form-item>

                <a-form-item label="通知渠道" name="notify_channels">
                    <a-select v-model:value="formState.notify_channels" mode="multiple" placeholder="请选择通知渠道">
                        <a-select-option v-for="channel in NOTIFY_CHANNELS" :key="channel.value" :value="channel.value">
                            {{ channel.label }}
                        </a-select-option>
                    </a-select>
                </a-form-item>

                <a-form-item label="启用状态" name="enabled">
                    <a-switch v-model:checked="formState.enabled" />
                </a-form-item>

                <a-form-item label="描述" name="description">
                    <a-textarea v-model:value="formState.description" :rows="3" placeholder="请输入规则描述" />
                </a-form-item>
            </a-form>
        </a-modal>
    </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { message, FormInstance } from 'ant-design-vue';
import { usePermission } from '@/hooks/usePermission';
import {
    alertRuleApi,
    AlertRule,
    CONDITIONS,
    ALERT_LEVELS,
    NOTIFY_CHANNELS,
    METRIC_TYPES
} from '@/api/alert-rule';

interface FormRules {
    name: Array<{ required: boolean; message: string }>;
    metric_type: Array<{ required: boolean; message: string }>;
    condition: Array<{ required: boolean; message: string }>;
    threshold: Array<{ required: boolean; message: string }>;
    level: Array<{ required: boolean; message: string }>;
}

// 表单状态接口
interface FormState extends Omit<AlertRule, 'id'> {
    id?: string;
}

// 表格记录接口
interface TableRecord extends AlertRule {
    key: string;
}

export default defineComponent({
    name: 'AlertRule',
    setup() {
        const route = useRoute();
        const deviceId = route.params.id as string;
        const { hasPermission } = usePermission();

        // 状态定义
        const loading = ref(false);
        const rules = ref<AlertRule[]>([]);
        const modalVisible = ref(false);
        const modalTitle = ref('');
        const formRef = ref<FormInstance>();
        const formState = ref<FormState>({
            name: '',
            metric_type: '',
            condition: '',
            threshold: 0,
            level: '',
            enabled: true,
            notify_channels: [],
            description: ''
        });

        // 表格列定义
        const columns = [
            { title: '规则名称', dataIndex: 'name', key: 'name' },
            { title: '指标类型', dataIndex: 'metric_type', key: 'metric_type' },
            { title: '告警条件', dataIndex: 'condition', key: 'condition' },
            { title: '告警级别', dataIndex: 'level', key: 'level' },
            { title: '状态', dataIndex: 'enabled', key: 'enabled' },
            { title: '通知渠道', dataIndex: 'notify_channels', key: 'notify_channels' },
            { title: '操作', key: 'action' }
        ];

        // 表单校验规则
        const formRules: FormRules = {
            name: [{ required: true, message: '请输入规则名称' }],
            metric_type: [{ required: true, message: '请选择指标类型' }],
            condition: [{ required: true, message: '请选择告警条件' }],
            threshold: [{ required: true, message: '请设置阈值' }],
            level: [{ required: true, message: '请选择告警级别' }]
        };

        // 加载规则列表
        const loadRules = async () => {
            try {
                loading.value = true;
                const res = await alertRuleApi.getDeviceRules(deviceId);
                rules.value = res.data.map(rule => ({
                    ...rule,
                    key: rule.id
                }));
            } catch (error) {
                if (error instanceof Error) {
                    message.error(error.message);
                } else {
                    message.error('加载规则失败');
                }
            } finally {
                loading.value = false;
            }
        };

        // 显示创建弹窗
        const showCreateModal = () => {
            modalTitle.value = '添加规则';
            formState.value = {
                name: '',
                metric_type: '',
                condition: '',
                threshold: 80,
                level: '',
                enabled: true,
                notify_channels: [],
                description: ''
            };
            modalVisible.value = true;
        };

        // 显示编辑弹窗
        const showEditModal = (record: TableRecord) => {
            modalTitle.value = '编辑规则';
            formState.value = { ...record };
            modalVisible.value = true;
        };

        // 处理弹窗确认
        const handleModalOk = async () => {
            try {
                if (!formRef.value) {
                    message.error('表单实例不存在');
                    return;
                }

                await formRef.value.validate();
                const formData = { ...formState.value };

                if (formData.id) {
                    await alertRuleApi.updateRule(formData.id, formData);
                } else {
                    await alertRuleApi.createRule(deviceId, formData);
                }

                message.success('保存成功');
                modalVisible.value = false;
                loadRules();
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

        // 处理状态切换
        const handleStatusChange = async (record: AlertRule, checked: boolean) => {
            try {
                await alertRuleApi.updateRule(record.id, {
                    enabled: checked
                });
                message.success('状态更新成功');
            } catch (error) {
                message.error('状态更新失败');
                record.enabled = !checked;
            }
        };

        // 处理删除
        const handleDelete = async (rule: AlertRule) => {
            try {
                await alertRuleApi.deleteRule(rule.id);
                message.success('删除成功');
                loadRules();
            } catch (error) {
                message.error('删除失败');
            }
        };

        // 获取标签和单位
        const getMetricLabel = (type: string): string => {
            return METRIC_TYPES.find(t => t.value === type)?.label || type;
        };

        const getMetricUnit = (type: string): string => {
            return METRIC_TYPES.find(t => t.value === type)?.unit || '';
        };

        const getConditionLabel = (condition: string): string => {
            return CONDITIONS.find(c => c.value === condition)?.label || condition;
        };

        const getAlertLabel = (level: string): string => {
            return ALERT_LEVELS.find(l => l.value === level)?.label || level;
        };

        const getAlertColor = (level: string): string => {
            return ALERT_LEVELS.find(l => l.value === level)?.color || 'blue';
        };

        const getChannelLabel = (channel: string): string => {
            return NOTIFY_CHANNELS.find(c => c.value === channel)?.label || channel;
        };

        onMounted(() => {
            loadRules();
        });

        return {
            loading,
            rules,
            columns,
            modalVisible,
            modalTitle,
            formRef,
            formState,
            formRules,
            CONDITIONS,
            ALERT_LEVELS,
            NOTIFY_CHANNELS,
            METRIC_TYPES,
            hasPermission,
            showCreateModal,
            showEditModal,
            handleModalOk,
            handleModalCancel,
            handleStatusChange,
            handleDelete,
            getMetricLabel,
            getMetricUnit,
            getConditionLabel,
            getAlertLabel,
            getAlertColor,
            getChannelLabel
        };
    }
});
</script>

<style lang="less" scoped>
.alert-rule {
    padding: 24px;

    .ant-card {
        margin-bottom: 24px;
    }
}
</style>