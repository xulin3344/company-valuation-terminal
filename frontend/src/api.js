import axios from 'axios'

const api = axios.create({ baseURL: '/api', timeout: 60000 })

export async function analyze(ticker, market) {
  const { data } = await api.post('/analyze', { ticker, market })
  return data
}

export async function searchStocks(query, market = '') {
  try {
    const { data } = await api.get('/search', { params: { q: query, market } })
    return data?.results || []
  } catch (e) {
    return []
  }
}


export async function recalculate(params) {
  const { data } = await api.post('/recalculate', params)
  return data
}

export async function getCompsPool() {
  const { data } = await api.get('/comps/pool')
  return data
}

export async function saveProject(name, ticker, market, payload, projectId = null) {
  const { data } = await api.post('/projects', { name, ticker, market, payload, project_id: projectId })
  return data
}

export async function listProjects() {
  const { data } = await api.get('/projects')
  return data
}

export async function loadProject(id) {
  const { data } = await api.get(`/projects/${id}`)
  return data
}

export async function deleteProject(id) {
  const { data } = await api.delete(`/projects/${id}`)
  return data
}

export async function exportProject(id) {
  const { data } = await api.get(`/projects/${id}/export`)
  return data
}

export async function exportProjectPDF(id) {
  const { data } = await api.get(`/projects/${id}/export/pdf`, { responseType: 'blob' })
  return data
}

export async function exportAllProjects() {
  const { data } = await api.get('/projects/export-all')
  return data
}

export async function exportAllProjectsPDF() {
  const { data } = await api.get('/projects/export-all/pdf', { responseType: 'blob' })
  return data
}

export async function exportSelectedProjects(ids) {
  const { data } = await api.post('/projects/export-selected', ids, { responseType: 'blob' })
  return data
}

export async function exportDirectPDF(params) {
  const { data } = await api.post('/export/pdf', params, { responseType: 'blob' })
  return data
}