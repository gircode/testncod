<template>
  <div class="monitoring-page">
    <h2>监控面板</h2>
    <div class="stats-cards">
      <div class="stat-card">
        <h3>在线设备</h3>
        <div class="stat-value">5</div>
      </div>
      <div class="stat-card">
        <h3>离线设备</h3>
        <div class="stat-value">2</div>
      </div>
      <div class="stat-card">
        <h3>从服务器</h3>
        <div class="stat-value">3</div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
// 监控页面的逻辑代码
</script>

<style lang="scss" scoped>
.monitoring-page {
  h2 {
    margin: 0 0 20px;
    color: #333;
  }
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.stat-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  
  h3 {
    margin: 0 0 10px;
    color: #666;
    font-size: 16px;
  }
  
  .stat-value {
    font-size: 36px;
    font-weight: bold;
    color: #409eff;
  }
}
</style> 