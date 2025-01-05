<template>
  <div class="approval-list">
    <a-card>
      <template #title>
        <a-space>
          <span>审批流程</span>
          <a-radio-group v-model:value="filterStatus" button-style="solid">
            <a-radio-button value="pending">待审批</a-radio-button>
            <a-radio-button value="approved">已通过</a-radio-button>
            <a-radio-button value="rejected">已拒绝</a-radio-button>
          </a-radio-group>
        </a-space>
      </template>

      <a-table
        :columns="columns"
        :data-source="approvalList"
        :loading="loading"
        :pagination="{
          total: total,
          current: current,
          pageSize: pageSize,
          onChange: handlePageChange
        }"
      >
        <!-- 申请类型 -->
        <template #type="{ text }">
          <a-tag :color="getTypeColor(text)">{{ getTypeText(text) }}</a-tag>
        </template>

        <!-- 状态 -->
        <template #status="{ text }">
          <a-tag :color="getStatusColor(text)">{{ getStatusText(text) }}</a-tag>
        </template>

        <!-- 操作 -->
        <template #action="{ record }">
          <a-space>
            <a-button
              v-if="record.status === 'pending'"
              type="primary"
              size="small"
              @click="handleApprove(record)"
            >
              通过
            </a-button>
            <a-button
              v-if="record.status === 'pending'"
              danger
              size="small"
              @click="handleReject(record)"
            >
              拒绝
            </a-button>
            <a-button size="small" @click="handleViewDetail(record)">
              查看
            </a-button>
          </a-space>
        </template>
      </a-table>
    </a-card>

    <!-- 审批详情弹窗 -->
    <a-modal
      v-model:visible="detailVisible"
      title="审批详情"
      :footer="null"
      width="600px"
    >
      <a-descriptions bordered>
        <a-descriptions-item label="申请人">
          {{ currentDetail?.applicant }}
        </a-descriptions-item>
        <a-descriptions-item label="申请类型">
          {{ getTypeText(currentDetail?.type) }}
        </a-descriptions-item>
        <a-descriptions-item label="申请时间">
          {{ formatTime(currentDetail?.createTime) }}
        </a-descriptions-item>
        <a-descriptions-item label="状态">
          <a-tag :color="getStatusColor(currentDetail?.status)">
            {{ getStatusText(currentDetail?.status) }}
          </a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="申请内容" :span="3">
          {{ currentDetail?.content }}
        </a-descriptions-item>
        <template v-if="currentDetail?.status !== 'pending'">
          <a-descriptions-item label="处理人">
            {{ currentDetail?.handler }}
          </a-descriptions-item>
          <a-descriptions-item label="处理时间">
            {{ formatTime(currentDetail?.handleTime) }}
          </a-descriptions-item>
          <a-descriptions-item label="处理意见">
            {{ currentDetail?.comment }}
          </a-descriptions-item>
        </template>
      </a-descriptions>
    </a-modal>

    <!-- 处理审批弹窗 -->
    <a-modal
      v-model:visible="handleVisible"
      :title="handleType === 'approve' ? '通过审批' : '拒绝审批'"
      @ok="submitHandle"
      :confirmLoading="submitting"
    >
      <a-form :model="handleForm" layout="vertical">
        <a-form-item
          label="处理意见"
          name="comment"
          :rules="[{ required: true, message: '请输入处理意见' }]"
        >
          <a-textarea
            v-model:value="handleForm.comment"
            :rows="4"
            placeholder="请输入处理意见"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { message } from 'ant-design-vue'
import type { TableColumnType } from 'ant-design-vue/es/table'
import { formatTime } from '@/utils/format'

interface ApprovalItem {
  id: number
  type: string
  applicant: string
  content: string
  status: 'pending' | 'approved' | 'rejected'
  createTime: string
  handler?: string
  handleTime?: string
  comment?: string
}

// 表格列定义
const columns: TableColumnType[] = [
  {
    title: '申请类型',
    dataIndex: 'type',
    slots: { customRender: 'type' }
  },
  {
    title: '申请人',
    dataIndex: 'applicant'
  },
  {
    title: '申请时间',
    dataIndex: 'createTime',
    customRender: ({ text }) => formatTime(text)
  },
  {
    title: '状态',
    dataIndex: 'status',
    slots: { customRender: 'status' }
  },
  {
    title: '操作',
    key: 'action',
    slots: { customRender: 'action' }
  }
]

// 列表数据
const approvalList = ref<ApprovalItem[]>([])
const loading = ref(false)
const total = ref(0)
const current = ref(1)
const pageSize = ref(10)
const filterStatus = ref<string>('pending')

// 详情弹窗
const detailVisible = ref(false)
const currentDetail = ref<ApprovalItem>()

// 处理弹窗
const handleVisible = ref(false)
const handleType = ref<'approve' | 'reject'>('approve')
const submitting = ref(false)
const handleForm = ref({
  comment: ''
})

// 获取类型颜色
const getTypeColor = (type: string) => {
  switch (type) {
    case 'device':
      return 'blue'
    case 'permission':
      return 'purple'
    default:
      return 'default'
  }
}

// 获取类型文本
const getTypeText = (type: string) => {
  switch (type) {
    case 'device':
      return '设备申请'
    case 'permission':
      return '权限申请'
    default:
      return '其他申请'
  }
}

// 获取状态颜色
const getStatusColor = (status: string) => {
  switch (status) {
    case 'pending':
      return 'processing'
    case 'approved':
      return 'success'
    case 'rejected':
      return 'error'
    default:
      return 'default'
  }
}

// 获取状态文本
const getStatusText = (status: string) => {
  switch (status) {
    case 'pending':
      return '待审批'
    case 'approved':
      return '已通过'
    case 'rejected':
      return '已拒绝'
    default:
      return '未知'
  }
}

// 获取审批列表
const getApprovalList = async () => {
  loading.value = true
  try {
    // TODO: 调用API获取审批列表
    // const res = await request.get('/api/approvals', {
    //   params: {
    //     status: filterStatus.value,
    //     page: current.value,
    //     pageSize: pageSize.value
    //   }
    // })
    // approvalList.value = res.data.list
    // total.value = res.data.total
  } catch (error) {
    message.error('获取审批列表失败')
  } finally {
    loading.value = false
  }
}

// 处理分页变化
const handlePageChange = (page: number) => {
  current.value = page
  getApprovalList()
}

// 查看详情
const handleViewDetail = (record: ApprovalItem) => {
  currentDetail.value = record
  detailVisible.value = true
}

// 通过审批
const handleApprove = (record: ApprovalItem) => {
  handleType.value = 'approve'
  currentDetail.value = record
  handleVisible.value = true
}

// 拒绝审批
const handleReject = (record: ApprovalItem) => {
  handleType.value = 'reject'
  currentDetail.value = record
  handleVisible.value = true
}

// 提交处理
const submitHandle = async () => {
  if (!currentDetail.value || !handleForm.value.comment) return

  submitting.value = true
  try {
    // TODO: 调用API提交审批处理
    // await request.post(`/api/approvals/${currentDetail.value.id}/${handleType.value}`, {
    //   comment: handleForm.value.comment
    // })
    message.success('处理成功')
    handleVisible.value = false
    getApprovalList()
  } catch (error) {
    message.error('处理失败')
  } finally {
    submitting.value = false
    handleForm.value.comment = ''
  }
}

// 监听状态筛选变化
watch(filterStatus, () => {
  current.value = 1
  getApprovalList()
})

onMounted(() => {
  getApprovalList()
})
</script>

<style scoped>
.approval-list {
  padding: 24px;
}
</style> 