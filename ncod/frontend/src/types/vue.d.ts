declare module 'vue' {
  export * from '@vue/runtime-core'
}

declare module '@vue/runtime-core' {
  interface ComponentCustomProperties {
    $message: typeof import('ant-design-vue')['message']
  }
}

export {}; 