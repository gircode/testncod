import { http } from '@/utils/http';

export interface OrganizationCreate {
  name: string;
  code: string;
  description?: string;
  parent_id?: string;
}

export interface OrganizationUpdate {
  name?: string;
  code?: string;
  description?: string;
  parent_id?: string;
}

export const organizationApi = {
  // 创建组织
  createOrganization(data: OrganizationCreate) {
    return http.post('/api/v1/organizations', data);
  },

  // 更新组织
  updateOrganization(orgId: string, data: OrganizationUpdate) {
    return http.put(`/api/v1/organizations/${orgId}`, data);
  },

  // 删除组织
  deleteOrganization(orgId: string) {
    return http.delete(`/api/v1/organizations/${orgId}`);
  },

  // 获取组织
  getOrganization(orgId: string) {
    return http.get(`/api/v1/organizations/${orgId}`);
  },

  // 获取组织列表
  listOrganizations(parentId?: string) {
    return http.get('/api/v1/organizations', {
      params: { parent_id: parentId }
    });
  },

  // 获取组织树
  getOrganizationTree(orgId?: string) {
    return http.get('/api/v1/organizations/tree', {
      params: { org_id: orgId }
    });
  }
}; 