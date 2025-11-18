// Utilitário para tratamento de erros da API
export const handleApiError = (error) => {
  if (error.response) {
    // A requisição foi feita e o servidor respondeu com um status de erro
    console.error('Erro da API:', error.response.status, error.response.data)
    
    const data = error.response.data
    
    // Se data é uma string, retorna diretamente
    if (typeof data === 'string') {
      return data
    }
    
    // Se data é um objeto, tenta extrair a mensagem
    if (typeof data === 'object' && data !== null) {
      // Erro 422 - Validação do Pydantic
      if (error.response.status === 422 && Array.isArray(data.detail)) {
        const erros = data.detail.map(err => {
          const campo = err.loc ? err.loc.slice(1).join('.') : 'campo desconhecido'
          const msg = err.msg || 'Erro de validação'
          return `${campo}: ${msg}`
        })
        return erros.join('\n')
      }
      
      // Outros erros com detail
      if (data.detail) {
        if (Array.isArray(data.detail)) {
          return data.detail.map(d => typeof d === 'string' ? d : JSON.stringify(d)).join('\n')
        } else if (typeof data.detail === 'string') {
          return data.detail
        }
      }
      
      return data.detail || data.message || `Erro ${error.response.status}: ${error.response.statusText}`
    }
    
    return `Erro ${error.response.status}: ${error.response.statusText}`
  } else if (error.request) {
    // A requisição foi feita mas não houve resposta
    console.error('Sem resposta da API:', error.request)
    return 'Não foi possível conectar à API. Verifique se o servidor está rodando em http://127.0.0.1:8000'
  } else {
    // Algo aconteceu na configuração da requisição
    console.error('Erro na requisição:', error.message)
    return error.message || 'Erro desconhecido'
  }
}

