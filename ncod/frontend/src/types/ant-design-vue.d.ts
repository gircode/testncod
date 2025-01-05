declare module 'ant-design-vue' {
  import { App } from 'vue';
  
  export const message: {
    success(content: string): void;
    error(content: string): void;
    warning(content: string): void;
    info(content: string): void;
  };

  export interface FormInstance {
    validate(): Promise<void>;
    validateFields(nameList?: string[]): Promise<void>;
    resetFields(): void;
  }
} 