declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

declare module 'vue-echarts'
declare module '@vue/runtime-core' {
  interface ComponentCustomProperties {
    $echarts: typeof import('echarts')
  }
} 