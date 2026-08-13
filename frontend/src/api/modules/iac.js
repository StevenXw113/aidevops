import request from '@/api/request'

// ====== Terraform 方案 ======
export const getIaCStacks = (params) => request.get('/iac/stacks/', { params })
export const getIaCStack = (id) => request.get(`/iac/stacks/${id}/`)
export const createIaCStack = (data) => request.post('/iac/stacks/', data)
export const updateIaCStack = (id, data) => request.put(`/iac/stacks/${id}/`, data)
export const deleteIaCStack = (id) => request.delete(`/iac/stacks/${id}/`)
export const downloadIaCStack = (id) => request.get(`/iac/stacks/${id}/download/`, { responseType: 'blob' })
export const getIaCStackExecutions = (id) => request.get(`/iac/stacks/${id}/executions/`)
export const executeIaCStack = (id, data) => request.post(`/iac/stacks/${id}/execute/`, data)
export const syncIaCStackCmdb = (id) => request.post(`/iac/stacks/${id}/sync_cmdb/`)

// ====== 目录与渲染 ======
export const getIaCCatalog = () => request.get('/iac/catalog/')
export const getIaCRegions = (params) => request.get('/iac/regions/', { params })
export const renderIaCTerraform = (data) => request.post('/iac/render/', data)
export const downloadIaCBundle = (data) => request.post('/iac/bundle/', data, { responseType: 'blob' })
