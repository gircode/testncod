declare module '@/components/*' {
    import { DefineComponent } from 'vue'
    const component: DefineComponent<Record<string, unknown>, Record<string, unknown>, unknown>
    export default component
}

declare module '@/stores/*' {
    const store: any
    export default store
} 