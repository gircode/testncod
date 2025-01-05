/// <reference types="element-plus/global" />

import type { App } from 'vue'

declare module 'element-plus' {
  const ElementPlus: {
    install(app: App, options?: { locale: any }): void
  }
  export default ElementPlus

  export const ElMessage: {
    success(message: string): void
    error(message: string): void
    warning(message: string): void
    info(message: string): void
  }

  export const ElMessageBox: {
    confirm(message: string, title?: string, options?: any): Promise<void>
    alert(message: string, title?: string, options?: any): Promise<void>
  }

  export interface ElForm {
    validate(callback?: (valid: boolean) => void): Promise<boolean>
    validateField(props: string | string[], callback?: (valid: boolean) => void): void
    resetFields(): void
    scrollToField(prop: string): void
    clearValidate(props?: string | string[]): void
  }
}

declare module '@element-plus/icons-vue' {
  export const DataLine: any
  export const Histogram: any
  export const Cpu: any
  export const Loading: any
  export const More: any
  export const Connection: any
  export const Timer: any
  export const UploadFilled: any
  export const DownloadFilled: any
  export const Search: any
  export const Refresh: any
  export const Operation: any
  export const Download: any
  export const Monitor: any
  export const CircleCheck: any
  export const Warning: any
  export const CircleClose: any
  export const Setting: any
  export const HomeFilled: any
  export const User: any
  export const OfficeBuilding: any
  export const Plus: any
  export const Upload: any
}

declare module 'element-plus/es/locale' {
  export interface Language {
    name: string
    el: {
      colorpicker: Record<string, string>
      datepicker: Record<string, string>
      dialog: Record<string, string>
      form: Record<string, string>
      message: Record<string, string>
      messagebox: Record<string, string>
      pagination: Record<string, string>
      select: Record<string, string>
      table: Record<string, string>
      tree: Record<string, string>
      upload: Record<string, string>
      [key: string]: any
    }
  }

  export const zhCn: Language
} 