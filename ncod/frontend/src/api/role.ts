import { http } from '@/utils/http';

export interface RoleCreate {
  name: string;
  description?: string;
  permissions: string[];
  is_system?: boolean;
}

export interface RoleUpdate {
  name?: string;
  description?: string;
  permissions?: string[];
}

export const roleApi = {
  // 创建角色
  createRole(data: RoleCreate) {
    return http.post('/api/v1/roles', data);
  },

  // 更新角色
  updateRole(roleId: string, data: RoleUpdate) {
    return http.put(`/api/v1/roles/${roleId}`, data);
  },

  // 删除角色
  deleteRole(roleId: string) {
    return http.delete(`/api/v1/roles/${roleId}`);
  },

  // 获取角色
  getRole(roleId: string) {
    return http.get(`/api/v1/roles/${roleId}`);
  },

  // 获取角色列表
  listRoles(includeSystem: boolean = true) {
    return http.get('/api/v1/roles', {
      params: { include_system: includeSystem }
    });
  }
}; 