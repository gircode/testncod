import { createProdMockServer } from 'vite-plugin-mock/es/createProdMockServer'
import apiMock from './mock/api'

export function setupProdMockServer() {
  createProdMockServer([
    ...apiMock
  ])
} 