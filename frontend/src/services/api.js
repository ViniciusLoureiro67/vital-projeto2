import axios from 'axios'

// Usa URL relativa para funcionar com o proxy do Vite
const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

export default api

// Serviços de Motos
export const motosService = {
  listar: (params = {}) => api.get('/motos', { params }),
  buscarPorPlaca: (placa) => api.get(`/motos/${placa}`),
  buscarPorModelo: (termo) => api.get('/motos/buscar/modelo', { params: { termo } }),
  criar: (data) => api.post('/motos', data),
  atualizar: (placa, data) => api.put(`/motos/${placa}`, data),
  deletar: (placa) => api.delete(`/motos/${placa}`),
}

// Serviços de Checklists
export const checklistsService = {
  listar: (params = {}) => api.get('/checklists', { params }),
  buscarPorMoto: (placa) => api.get(`/checklists/moto/${placa}`),
  buscarPorId: (id) => api.get(`/checklists/${id}`),
  criar: (data) => api.post('/checklists', data),
  adicionarItem: (checklistId, data) => {
    return api.post(`/checklists/${checklistId}/itens`, {
      nome: data.nome,
      categoria: data.categoria || 'Geral',
      status: data.status || 'pendente',
      custo_estimado: data.custo_estimado || 0
    })
  },
  atualizarItem: (checklistId, itemIndex, params = {}) => {
    // Constrói a URL com query params
    const queryParams = new URLSearchParams()
    if (params.status) queryParams.append('status', params.status)
    if (params.custo_estimado !== undefined && params.custo_estimado !== null) {
      queryParams.append('custo_estimado', params.custo_estimado)
    }
    const queryString = queryParams.toString()
    const url = `/checklists/${checklistId}/itens/${itemIndex}${queryString ? '?' + queryString : ''}`
    return api.put(url)
  },
  deletar: (id) => api.delete(`/checklists/${id}`),
  atualizarStatus: (id, finalizado, pago, custoReal) => {
    const params = new URLSearchParams()
    if (finalizado !== undefined && finalizado !== null) {
      params.append('finalizado', finalizado.toString())
    }
    if (pago !== undefined && pago !== null) {
      params.append('pago', pago.toString())
    }
    if (custoReal !== undefined && custoReal !== null) {
      params.append('custo_real', custoReal.toString())
    }
    const queryString = params.toString()
    const url = `/checklists/${id}/status${queryString ? '?' + queryString : ''}`
    return api.put(url)
  },
}

// Serviços de Analytics
export const analyticsService = {
  obter: (params = {}) => api.get('/analytics', { params }),
  porCategoria: () => api.get('/analytics/categoria'),
}

// Serviços de Financeiro
export const financeiroService = {
  obterRelatorio: (params = {}) => api.get('/financeiro', { params }),
}

