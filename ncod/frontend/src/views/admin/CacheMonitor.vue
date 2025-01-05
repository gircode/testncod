<template>
  <div class="cache-monitor">
    <el-card>
      <template #header>
        <div class="card-header">
          <h3>缓存监控</h3>
          <div class="header-actions">
            <el-button type="primary" @click="handleRefresh">
              <el-icon class="refresh-icon">
                <Refresh />
              </el-icon>
              刷新
            </el-button>
            <el-button type="danger" @click="handleClearCache">
              <el-icon class="delete-icon">
                <Delete />
              </el-icon>
              清理缓存
            </el-button>
          </div>
        </div>
      </template>

      <el-descriptions title="总体统计" :column="4" border>
        <el-descriptions-item label="总大小">
          {{ formatBytes(cacheStats.total.size) }}
        </el-descriptions-item>
        <el-descriptions-item label="键数量">
          {{ cacheStats.total.keys }}
        </el-descriptions-item>
        <el-descriptions-item label="命中次数">
          {{ cacheStats.total.hits }}
        </el-descriptions-item>
        <el-descriptions-item label="命中率">
          {{ formatPercentage(cacheStats.total.hitRate) }}
        </el-descriptions-item>
      </el-descriptions>

      <div class="cache-list">
        <div v-for="(cache, type) in cacheStats.caches" :key="type" class="cache-item">
          <el-card>
            <template #header>
              <div class="cache-header">
                <span>{{ type }}</span>
                <el-button type="danger" link @click="handleClearCache(type)">
                  清理
                </el-button>
              </div>
            </template>

            <el-descriptions :column="2" border>
              <el-descriptions-item label="大小">
                {{ formatBytes(cache.size) }}
              </el-descriptions-item>
              <el-descriptions-item label="键数量">
                {{ cache.keys }}
              </el-descriptions-item>
              <el-descriptions-item label="命中次数">
                {{ cache.hits }}
              </el-descriptions-item>
              <el-descriptions-item label="命中率">
                {{ formatPercentage(cache.hitRate) }}
              </el-descriptions-item>
              <el-descriptions-item label="过期时间">
                {{ formatDurationSeconds(cache.expiryTime) }}
              </el-descriptions-item>
              <el-descriptions-item label="最后清理时间">
                {{ formatDateTime(cache.lastCleanTime) }}
              </el-descriptions-item>
            </el-descriptions>
          </el-card>
        </div>
      </div>
    </el-card>

    <el-dialog v-model="clearDialog.visible" title="清理缓存" width="400px">
      <div class="clear-dialog-content">
        <p v-if="clearDialog.type">
          确定要清理 <strong>{{ clearDialog.type }}</strong> 类型的缓存吗？
        </p>
        <p v-else>确定要清理所有缓存吗？</p>
        <p class="clear-tips">清理后数据将无法恢复</p>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="clearDialog.visible = false">取消</el-button>
          <el-button type="danger" :loading="clearDialog.loading" @click="confirmClearCache">
            确定
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Delete } from '@element-plus/icons-vue'
import { getCacheStats, clearCache, type CacheStats } from '@/api/admin'
import { formatBytes, formatPercentage, formatDurationSeconds, formatDateTime } from '@/utils/format'

const loading = ref(false)
const cacheStats = ref<CacheStats>({
  total: {
    size: 0,
    keys: 0,
    hits: 0,
    misses: 0,
    hitRate: 0
  },
  caches: {}
})

const clearDialog = reactive({
  visible: false,
  loading: false,
  type: ''
})

// 获取缓存统计
const fetchCacheStats = async () => {
  try {
    loading.value = true
    const data = await getCacheStats()
    cacheStats.value = data
  } catch (error) {
    console.error('获取缓存统计失败:', error)
    ElMessage.error('获取缓存统计失败')
  } finally {
    loading.value = false
  }
}

// 刷新数据
const handleRefresh = () => {
  fetchCacheStats()
}

// 清理缓存
const handleClearCache = (type?: string) => {
  clearDialog.type = type || ''
  clearDialog.visible = true
}

// 确认清理缓存
const confirmClearCache = async () => {
  try {
    clearDialog.loading = true
    await clearCache(clearDialog.type || undefined)
    ElMessage.success('缓存清理成功')
    clearDialog.visible = false
    fetchCacheStats()
  } catch (error) {
    console.error('清理缓存失败:', error)
    ElMessage.error('清理缓存失败')
  } finally {
    clearDialog.loading = false
  }
}

// 初始化
fetchCacheStats()
</script>

<style scoped>
.cache-monitor {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.cache-list {
  margin-top: 20px;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 20px;
}

.cache-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.clear-tips {
  color: var(--el-color-danger);
  margin-top: 8px;
  font-size: 14px;
}

.refresh-icon,
.delete-icon {
  margin-right: 4px;
}
</style> 