export interface Organization {
  id: number
  name: string
  code: string
  parent_id?: number
  children?: Organization[]
}

export interface OrganizationTree extends Organization {
  children: OrganizationTree[]
  level: number
  value: number
  label: string
} 