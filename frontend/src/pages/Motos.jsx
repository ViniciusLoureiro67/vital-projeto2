import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motosService } from '../services/api'
import { handleApiError } from '../utils/errorHandler'
import { showToast } from '../components/Toast'
import './Motos.css'

function Motos() {
  const navigate = useNavigate()
  const [motos, setMotos] = useState([])
  const [motosFiltradas, setMotosFiltradas] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editingMoto, setEditingMoto] = useState(null)
  const [buscaMoto, setBuscaMoto] = useState('')
  const [formData, setFormData] = useState({
    placa: '',
    marca: '',
    modelo: '',
    ano: new Date().getFullYear(),
    cilindradas: '',
    categoria: 'NAKED',
  })

  useEffect(() => {
    carregarMotos()
  }, [])

  const carregarMotos = async () => {
    try {
      const response = await motosService.listar()
      console.log('Resposta da API:', response.data)
      const motosData = response.data || []
      setMotos(motosData)
      setMotosFiltradas(motosData)
    } catch (error) {
      const errorMsg = handleApiError(error)
      console.error('Erro ao carregar motos:', error)
      console.error('Mensagem:', errorMsg)
      showToast(`Erro ao carregar motos: ${errorMsg}`, 'error')
      setMotos([])
      setMotosFiltradas([])
    } finally {
      setLoading(false)
    }
  }

  // Busca inteligente de motos
  useEffect(() => {
    if (!buscaMoto || buscaMoto.trim() === '') {
      setMotosFiltradas(motos)
      return
    }

    const termoLower = buscaMoto.toLowerCase().trim()
    const filtradas = motos.filter(moto => {
      const placa = moto.placa?.toLowerCase() || ''
      const modelo = moto.modelo?.toLowerCase() || ''
      const marca = moto.marca?.toLowerCase() || ''
      
      return placa.includes(termoLower) || 
             modelo.includes(termoLower) || 
             marca.includes(termoLower)
    })
    
    setMotosFiltradas(filtradas)
  }, [buscaMoto, motos])

  const handleMotoClick = (placa, e) => {
    // Se clicou em um botão, não navega
    if (e && (e.target.tagName === 'BUTTON' || e.target.closest('button'))) {
      return
    }
    navigate(`/motos/${encodeURIComponent(placa)}`)
  }

  const handleEdit = (moto, e) => {
    e.stopPropagation()
    setEditingMoto(moto)
    setFormData({
      placa: moto.placa,
      marca: moto.marca,
      modelo: moto.modelo,
      ano: moto.ano,
      cilindradas: moto.cilindradas,
      categoria: moto.categoria_enum || moto.categoria,
    })
    setShowForm(false)
  }

  const handleDelete = async (moto, e) => {
    e.stopPropagation()
    if (!window.confirm(`Tem certeza que deseja excluir a moto ${moto.modelo} - ${moto.placa}?\n\nEsta ação não pode ser desfeita e excluirá todos os checklists relacionados.`)) {
      return
    }

    try {
      await motosService.deletar(moto.placa)
      showToast(`Moto ${moto.modelo} - ${moto.placa} excluída com sucesso!`, 'success')
      carregarMotos()
    } catch (error) {
      const errorMsg = handleApiError(error)
      console.error('Erro ao excluir moto:', error)
      showToast(`Erro ao excluir moto: ${errorMsg}`, 'error')
    }
  }

  const handleUpdate = async (e) => {
    e.preventDefault()
    try {
      const dadosEnviar = {
        marca: formData.marca,
        modelo: formData.modelo,
        ano: parseInt(formData.ano),
        cilindradas: parseInt(formData.cilindradas),
        categoria: formData.categoria,
      }
      
      await motosService.atualizar(editingMoto.placa, dadosEnviar)
      showToast(`Moto ${formData.modelo} - ${formData.placa} atualizada com sucesso!`, 'success')
      setEditingMoto(null)
      setFormData({
        placa: '',
        marca: '',
        modelo: '',
        ano: new Date().getFullYear(),
        cilindradas: '',
        categoria: 'NAKED',
      })
      carregarMotos()
    } catch (error) {
      const errorMsg = handleApiError(error)
      console.error('Erro ao atualizar moto:', error)
      showToast(`Erro ao atualizar moto: ${errorMsg}`, 'error')
    }
  }

  const handleCancelEdit = () => {
    setEditingMoto(null)
    setFormData({
      placa: '',
      marca: '',
      modelo: '',
      ano: new Date().getFullYear(),
      cilindradas: '',
      categoria: 'NAKED',
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      // Garante que os tipos estão corretos
      const dadosEnviar = {
        ...formData,
        ano: parseInt(formData.ano),
        cilindradas: parseInt(formData.cilindradas),
      }
      
      console.log('Dados a enviar:', dadosEnviar)
      
      const response = await motosService.criar(dadosEnviar)
      console.log('Moto cadastrada:', response.data)
      
      // Verifica se response.data existe e tem as propriedades esperadas
      const modelo = response.data?.modelo || formData.modelo
      const placa = response.data?.placa || formData.placa
      
      showToast(`Moto cadastrada com sucesso! ${modelo} - ${placa}`, 'success')
      setShowForm(false)
      setEditingMoto(null)
      setFormData({
        placa: '',
        marca: '',
        modelo: '',
        ano: new Date().getFullYear(),
        cilindradas: '',
        categoria: 'NAKED',
      })
      carregarMotos()
    } catch (error) {
      console.error('Erro completo:', error)
      console.error('Error response:', error.response)
      console.error('Error response data:', error.response?.data)
      
      // Tratamento mais robusto do erro
      let mensagemFinal = 'Erro desconhecido ao cadastrar moto'
      
      if (error.response?.data) {
        const data = error.response.data
        
        // Se data é uma string, usa diretamente
        if (typeof data === 'string') {
          mensagemFinal = data
        }
        // Se data é um objeto, tenta extrair a mensagem
        else if (typeof data === 'object') {
          // Erro 422 - Validação do Pydantic
          if (error.response.status === 422 && Array.isArray(data.detail)) {
            const erros = data.detail.map(err => {
              const campo = err.loc ? err.loc.join('.') : 'campo desconhecido'
              const msg = err.msg || 'Erro de validação'
              return `${campo}: ${msg}`
            })
            mensagemFinal = `Erros de validação:\n\n${erros.join('\n')}`
          }
          // Outros erros com detail
          else if (data.detail) {
            if (Array.isArray(data.detail)) {
              mensagemFinal = data.detail.map(d => typeof d === 'string' ? d : JSON.stringify(d)).join('\n')
            } else if (typeof data.detail === 'string') {
              mensagemFinal = data.detail
            } else {
              mensagemFinal = JSON.stringify(data.detail)
            }
          } else if (data.message) {
            mensagemFinal = data.message
          } else {
            mensagemFinal = JSON.stringify(data)
          }
        }
      } else if (error.message) {
        mensagemFinal = error.message
      }
      
      // Mensagem mais específica para erros comuns
      if (mensagemFinal.includes('já cadastrada') || mensagemFinal.includes('já existe')) {
        mensagemFinal = `Esta placa já está cadastrada no sistema.\n\nPlaca: ${formData.placa}\n\nVerifique se você não está tentando cadastrar a mesma moto duas vezes.`
      } else if (mensagemFinal.includes('placa') || mensagemFinal.includes('min_length') || mensagemFinal.includes('6') || mensagemFinal.includes('7')) {
        mensagemFinal = `Placa inválida!\n\n${mensagemFinal}\n\nA placa precisa ter entre 6 e 8 caracteres:\n- Formato antigo: ABC-1234 (7 caracteres)\n- Formato novo: ABC1D23 (7 caracteres)\n- Formato alternativo: ABC321 (6 caracteres)\n\nSua placa "${formData.placa}" tem ${formData.placa.length} caracteres.`
      } else if (mensagemFinal.includes('inválida')) {
        mensagemFinal = `Placa inválida!\n\n${mensagemFinal}\n\nFormato aceito:\n- Antigo: ABC-1234\n- Novo: ABC1D23`
      }
      
      showToast(`Erro ao cadastrar moto: ${mensagemFinal}`, 'error')
    }
  }

  if (loading) {
    return <div className="loading">Carregando motos...</div>
  }

  return (
    <div className="motos-page">
      <div className="page-header">
        <h1>🏍️ Motos Cadastradas</h1>
        <div className="header-actions">
          <div className="search-container">
            <input
              type="text"
              className="search-input-motos"
              placeholder="🔍 Buscar por placa, modelo ou marca..."
              value={buscaMoto}
              onChange={(e) => setBuscaMoto(e.target.value)}
            />
            {buscaMoto && (
              <button
                className="btn-clear-search"
                onClick={() => setBuscaMoto('')}
                title="Limpar busca"
              >
                ✕
              </button>
            )}
          </div>
          <button onClick={() => setShowForm(!showForm)} className="btn-primary">
            {showForm ? 'Cancelar' : '+ Nova Moto'}
          </button>
        </div>
      </div>

      {editingMoto ? (
        <div className="moto-form-container">
          <h2>✏️ Editar Moto</h2>
          <form onSubmit={handleUpdate} className="moto-form">
            <div className="form-grid">
              <div className="form-group">
                <label>Placa *</label>
                <input
                  type="text"
                  value={formData.placa}
                  disabled
                  style={{ background: '#f0f0f0', cursor: 'not-allowed' }}
                />
                <small style={{ color: '#666', fontSize: '0.85rem', marginTop: '0.25rem', display: 'block' }}>
                  A placa não pode ser alterada
                </small>
              </div>
              <div className="form-group">
                <label>Marca *</label>
                <input
                  type="text"
                  value={formData.marca}
                  onChange={(e) => setFormData({ ...formData, marca: e.target.value.toUpperCase() })}
                  placeholder="YAMAHA"
                  required
                />
              </div>
              <div className="form-group">
                <label>Modelo *</label>
                <input
                  type="text"
                  value={formData.modelo}
                  onChange={(e) => setFormData({ ...formData, modelo: e.target.value.toUpperCase() })}
                  placeholder="MT-07"
                  required
                />
              </div>
              <div className="form-group">
                <label>Ano *</label>
                <input
                  type="number"
                  value={formData.ano}
                  onChange={(e) => setFormData({ ...formData, ano: parseInt(e.target.value) })}
                  min="1900"
                  max="2100"
                  required
                />
              </div>
              <div className="form-group">
                <label>Cilindradas (cc) *</label>
                <input
                  type="number"
                  value={formData.cilindradas}
                  onChange={(e) => setFormData({ ...formData, cilindradas: parseInt(e.target.value) })}
                  placeholder="689"
                  min="1"
                  required
                />
              </div>
              <div className="form-group">
                <label>Categoria *</label>
                <select
                  value={formData.categoria}
                  onChange={(e) => setFormData({ ...formData, categoria: e.target.value })}
                  required
                >
                  <option value="NAKED">Naked</option>
                  <option value="ESPORTIVA">Esportiva</option>
                  <option value="CUSTOM">Custom</option>
                  <option value="BIG_TRAIL">Big Trail</option>
                  <option value="CROSS">Cross</option>
                  <option value="OUTROS">Outros</option>
                </select>
              </div>
            </div>
            <div className="form-actions">
              <button type="submit" className="btn-primary">Salvar Alterações</button>
              <button type="button" onClick={handleCancelEdit} className="btn-secondary">Cancelar</button>
            </div>
          </form>
        </div>
      ) : showForm && (
        <form onSubmit={handleSubmit} className="moto-form">
          <h2>Cadastrar Nova Moto</h2>
          <div className="form-grid">
            <div className="form-group">
              <label>Placa *</label>
              <input
                type="text"
                value={formData.placa}
                onChange={(e) => {
                  let valor = e.target.value.toUpperCase().replace(/[^A-Z0-9-]/g, '')
                  // Limita o tamanho
                  if (valor.length > 8) valor = valor.slice(0, 8)
                  setFormData({ ...formData, placa: valor })
                }}
                placeholder="ABC-1234 ou ABC1D23"
                required
                minLength={6}
                maxLength={8}
              />
              <small style={{ color: '#666', fontSize: '0.85rem', marginTop: '0.25rem', display: 'block' }}>
                Formato: ABC-1234 (antigo) ou ABC1D23 (novo) - mínimo 6 caracteres
              </small>
            </div>
            <div className="form-group">
              <label>Marca *</label>
              <input
                type="text"
                value={formData.marca}
                onChange={(e) => setFormData({ ...formData, marca: e.target.value })}
                placeholder="Yamaha"
                required
              />
            </div>
            <div className="form-group">
              <label>Modelo *</label>
              <input
                type="text"
                value={formData.modelo}
                onChange={(e) => setFormData({ ...formData, modelo: e.target.value })}
                placeholder="MT-07"
                required
              />
            </div>
            <div className="form-group">
              <label>Ano *</label>
              <input
                type="number"
                value={formData.ano}
                onChange={(e) => setFormData({ ...formData, ano: parseInt(e.target.value) })}
                min="1900"
                max="2100"
                required
              />
            </div>
            <div className="form-group">
              <label>Cilindradas (cc) *</label>
              <input
                type="number"
                value={formData.cilindradas}
                onChange={(e) => setFormData({ ...formData, cilindradas: parseInt(e.target.value) })}
                placeholder="689"
                min="1"
                required
              />
            </div>
            <div className="form-group">
              <label>Categoria *</label>
              <select
                value={formData.categoria}
                onChange={(e) => setFormData({ ...formData, categoria: e.target.value })}
                required
              >
                <option value="NAKED">Naked</option>
                <option value="ESPORTIVA">Esportiva</option>
                <option value="CUSTOM">Custom</option>
                <option value="BIG_TRAIL">Big Trail</option>
                <option value="CROSS">Cross</option>
                <option value="OUTROS">Outros</option>
              </select>
            </div>
          </div>
          <button type="submit" className="btn-primary">Cadastrar Moto</button>
        </form>
      )}

      {motos.length === 0 ? (
        <div className="empty-state">
          <p>Nenhuma moto cadastrada ainda.</p>
          <button onClick={() => setShowForm(true)} className="btn-primary">
            Cadastrar Primeira Moto
          </button>
        </div>
      ) : motosFiltradas.length === 0 ? (
        <div className="empty-state">
          <p>Nenhuma moto encontrada com "{buscaMoto}".</p>
          <button onClick={() => setBuscaMoto('')} className="btn-primary">
            Limpar Busca
          </button>
        </div>
      ) : (
        <>
          {buscaMoto && (
            <div className="search-results-info">
              <p>Mostrando {motosFiltradas.length} de {motos.length} moto(s)</p>
            </div>
          )}
          <div className="motos-grid">
            {motosFiltradas.map((moto) => (
              <div 
                key={moto.placa} 
                className="moto-card clickable"
                onClick={(e) => handleMotoClick(moto.placa, e)}
              >
                <div className="moto-header">
                  <h3>{moto.modelo}</h3>
                  <span className="moto-placa">{moto.placa}</span>
                </div>
                <div className="moto-details">
                  <p><strong>Marca:</strong> {moto.marca}</p>
                  <p><strong>Ano:</strong> {moto.ano}</p>
                  <p><strong>Cilindradas:</strong> {moto.cilindradas}cc</p>
                  <p><strong>Categoria:</strong> {moto.categoria}</p>
                </div>
                <div className="moto-card-actions">
                  <button 
                    className="btn-edit"
                    onClick={(e) => handleEdit(moto, e)}
                    title="Editar moto"
                  >
                    ✏️ Editar
                  </button>
                  <button 
                    className="btn-delete"
                    onClick={(e) => handleDelete(moto, e)}
                    title="Excluir moto"
                  >
                    🗑️ Excluir
                  </button>
                </div>
                <div className="moto-card-footer">
                  <span className="click-hint">Clique para ver detalhes →</span>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}

export default Motos

