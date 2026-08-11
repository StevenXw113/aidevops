import request from '@/api/request'

// ====== 云账号 ======
export const getCloudCredentials = (params) => request.get('/multicloud/credentials/', { params })
export const getCloudCredential = (id) => request.get(`/multicloud/credentials/${id}/`)
export const createCloudCredential = (data) => request.post('/multicloud/credentials/', data)
export const updateCloudCredential = (id, data) => request.put(`/multicloud/credentials/${id}/`, data)
export const deleteCloudCredential = (id) => request.delete(`/multicloud/credentials/${id}/`)
export const testCloudConnection = (id) => request.post(`/multicloud/credentials/${id}/test_connection/`)
export const syncCloudAll = (id) => request.post(`/multicloud/credentials/${id}/sync_all/`)

// ====== 云环境 ======
export const getCloudEnvironments = (params) => request.get('/multicloud/environments/', { params })
export const createCloudEnvironment = (data) => request.post('/multicloud/environments/', data)
export const updateCloudEnvironment = (id, data) => request.put(`/multicloud/environments/${id}/`, data)
export const deleteCloudEnvironment = (id) => request.delete(`/multicloud/environments/${id}/`)
export const syncCloudEnvironment = (id) => request.post(`/multicloud/environments/${id}/sync/`)
export const syncCloudCmdb = (id) => request.post(`/multicloud/environments/${id}/sync_cmdb/`)

// ====== 云资源 ======
export const getCloudAssets = (params) => request.get('/multicloud/assets/', { params })

// ====== 总览 / 目录 / 成本 ======
export const getCloudOverview = () => request.get('/multicloud/overview/')
export const getCloudCatalog = () => request.get('/multicloud/catalog/')
export const getCloudCostTrend = (params) => request.get('/multicloud/cost-trend/', { params })
export const getCloudTopology = (params) => request.get('/multicloud/topology/', { params })
export const batchSyncCloud = (data) => request.post('/multicloud/batch-sync/', data)
