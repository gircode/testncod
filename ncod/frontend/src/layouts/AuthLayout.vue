<!-- 认证页面布局 -->
<template>
  <div class="auth-container">
    <router-view></router-view>
  </div>
</template>

<style lang="less" scoped>
.auth-container {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #2d3a4b;
  overflow: auto;
}
</style>