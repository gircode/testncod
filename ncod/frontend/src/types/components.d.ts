import type { DefineComponent } from 'vue'

declare module '*.vue' {
  const component: DefineComponent
  export default component
}

declare module '@/views/*' {
  const component: DefineComponent
  export default component
}

declare module '@/layouts/*' {
  const component: DefineComponent
  export default component
} 