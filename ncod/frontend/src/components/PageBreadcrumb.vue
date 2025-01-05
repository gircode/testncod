<template>
  <el-breadcrumb class="breadcrumb">
    <el-breadcrumb-item v-for="item in breadcrumbItems" :key="item.path">
      <router-link v-if="item.path" :to="item.path">{{ item.title }}</router-link>
      <span v-else>{{ item.title }}</span>
    </el-breadcrumb-item>
  </el-breadcrumb>
</template>

<script lang="ts">
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'

interface BreadcrumbItem {
  title: string
  path?: string
}

export default {
  name: 'PageBreadcrumb',
  setup() {
    const route = useRoute()
    const breadcrumbItems = ref<BreadcrumbItem[]>([])

    // 根据路由生成面包屑
    const generateBreadcrumb = () => {
      const items: BreadcrumbItem[] = []
      const matched = route.matched

      matched.forEach((route) => {
        if (route.meta?.title) {
          items.push({
            title: route.meta.title as string,
            path: route.path
          })
        }
      })

      breadcrumbItems.value = items
    }

    // 监听路由变化
    watch(() => route.path, generateBreadcrumb, { immediate: true })

    return {
      breadcrumbItems
    }
  }
}
</script>

<style scoped>
.breadcrumb {
  margin: 16px 0;
}
</style> 