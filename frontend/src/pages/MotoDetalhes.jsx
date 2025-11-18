import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { motosService, checklistsService } from '../services/api'
import { handleApiError } from '../utils/errorHandler'
import { showToast } from '../components/Toast'
import './MotoDetalhes.css'

function MotoDetalhes() {
  const { placa } = useParams()
  const navigate = useNavigate()
  const [moto, setMoto] = useState(null)
  const [checklists, setChecklists] = useState([])
  const [loading, setLoading] = useState(true)
  const [editingMoto, setEditingMoto] = useState(false)
  const [formData, setFormData] = useState({
    marca: '',
    modelo: '',
    ano: new Date().getFullYear(),
    cilindradas: '',
    categoria: 'NAKED',
  })

  useEffect(() => {
    carregarDados()
  }, [placa])

  const carregarDados = async () => {
    try {
      setLoading(true)
      const placaDecoded = decodeURIComponent(placa)
      const [motoRes, checklistsRes] = await Promise.all([
        motosService.buscarPorPlaca(placaDecoded),
        checklistsService.buscarPorMoto(placaDecoded).catch(() => ({ data: [] }))
      ])
      
      setMoto(motoRes.data)
      setChecklists(checklistsRes.data || [])
      if (motoRes.data) {
        setFormData({
          marca: motoRes.data.marca,
          modelo: motoRes.data.modelo,
          ano: motoRes.data.ano,
          cilindradas: motoRes.data.cilindradas,
          categoria: motoRes.data.categoria_enum || motoRes.data.categoria,
        })
      }
    } catch (error) {
      const errorMsg = handleApiError(error)
      console.error('Erro ao carregar dados da moto:', error)
      showToast(`Erro ao carregar dados: ${errorMsg}`, 'error')
      navigate('/motos')
    } finally {
      setLoading(false)
    }
  }

  const formatarData = (dataStr) => {
    if (!dataStr) return 'N/A'
    try {
      const data = new Date(dataStr)
      return data.toLocaleDateString('pt-BR')
    } catch {
      return dataStr
    }
  }

  const calcularTotalGasto = () => {
    return checklists.reduce((total, checklist) => {
      return total + (checklist.custo_total_estimado || 0)
    }, 0)
  }

  const obterUltimoServico = () => {
    if (checklists.length === 0) return null
    return checklists.sort((a, b) => {
      const dataA = new Date(a.data_revisao)
      const dataB = new Date(b.data_revisao)
      return dataB - dataA
    })[0]
  }

  const obterProximoKmRevisao = () => {
    if (checklists.length === 0) return null
    const ultimoChecklist = obterUltimoServico()
    if (!ultimoChecklist) return null
    return ultimoChecklist.km_atual + 5000 // Próxima revisão sugerida a cada 5000km
  }

  if (loading) {
    return <div className="loading">Carregando informações da moto...</div>
  }

  if (!moto) {
    return (
      <div className="error-state">
        <p>Moto não encontrada.</p>
        <Link to="/motos" className="btn-primary">Voltar para Motos</Link>
      </div>
    )
  }

  const ultimoServico = obterUltimoServico()
  const proximoKm = obterProximoKmRevisao()
  const totalGasto = calcularTotalGasto()

  const handleEdit = () => {
    setEditingMoto(true)
  }

  const handleCancelEdit = () => {
    setEditingMoto(false)
    if (moto) {
      setFormData({
        marca: moto.marca,
        modelo: moto.modelo,
        ano: moto.ano,
        cilindradas: moto.cilindradas,
        categoria: moto.categoria_enum || moto.categoria,
      })
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
      
      const response = await motosService.atualizar(moto.placa, dadosEnviar)
      setMoto(response.data)
      showToast(`Moto ${formData.modelo} - ${moto.placa} atualizada com sucesso!`, 'success')
      setEditingMoto(false)
    } catch (error) {
      const errorMsg = handleApiError(error)
      console.error('Erro ao atualizar moto:', error)
      showToast(`Erro ao atualizar moto: ${errorMsg}`, 'error')
    }
  }

  const handleDelete = async () => {
    if (!window.confirm(`Tem certeza que deseja excluir a moto ${moto.modelo} - ${moto.placa}?\n\nEsta ação não pode ser desfeita e excluirá todos os checklists relacionados.`)) {
      return
    }

    try {
      await motosService.deletar(moto.placa)
      showToast(`Moto ${moto.modelo} - ${moto.placa} excluída com sucesso!`, 'success')
      navigate('/motos')
    } catch (error) {
      const errorMsg = handleApiError(error)
      console.error('Erro ao excluir moto:', error)
      showToast(`Erro ao excluir moto: ${errorMsg}`, 'error')
    }
  }

  return (
    <div className="moto-detalhes-page">
      <div className="page-header">
        <div>
          <button onClick={() => navigate('/motos')} className="btn-back">
            ← Voltar
          </button>
          <h1>{moto.modelo}</h1>
          <p className="moto-placa-header">{moto.placa}</p>
        </div>
        <div className="header-actions">
          <button onClick={handleEdit} className="btn-edit">
            ✏️ Editar
          </button>
          <button onClick={handleDelete} className="btn-delete">
            🗑️ Excluir
          </button>
          <Link 
            to={`/checklists?placa=${encodeURIComponent(moto.placa)}&criar=true`} 
            className="btn-primary"
          >
            + Novo Checklist
          </Link>
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
                  value={moto.placa}
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
      ) : (
        <div className="moto-info-section">
          <div className="info-card">
            <h2>📋 Informações da Moto</h2>
            <div className="info-grid">
              <div className="info-item">
                <span className="info-label">Marca:</span>
                <span className="info-value">{moto.marca}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Modelo:</span>
                <span className="info-value">{moto.modelo}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Ano:</span>
                <span className="info-value">{moto.ano}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Cilindradas:</span>
                <span className="info-value">{moto.cilindradas}cc</span>
              </div>
              <div className="info-item">
                <span className="info-label">Categoria:</span>
                <span className="info-value">{moto.categoria}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Placa:</span>
                <span className="info-value">{moto.placa}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {!editingMoto && (
        <div className="moto-info-section">
          <div className="stats-cards">
            <div className="stat-card">
              <div className="stat-icon">🔧</div>
              <div className="stat-content">
                <h3>{checklists.length}</h3>
                <p>Serviços Realizados</p>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon">💰</div>
              <div className="stat-content">
                <h3>R$ {totalGasto.toFixed(2)}</h3>
                <p>Total Gasto</p>
              </div>
            </div>
            {ultimoServico && (
              <div className="stat-card">
                <div className="stat-icon">📅</div>
                <div className="stat-content">
                  <h3>{formatarData(ultimoServico.data_revisao)}</h3>
                  <p>Último Serviço</p>
                </div>
              </div>
            )}
            {ultimoServico && (
              <div className="stat-card">
                <div className="stat-icon">📊</div>
                <div className="stat-content">
                  <h3>{ultimoServico.km_atual?.toLocaleString('pt-BR')} km</h3>
                  <p>KM Atual</p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {!editingMoto && (
        <div className="historico-section">
          <h2>📜 Histórico de Serviços</h2>
          {checklists.length === 0 ? (
          <div className="empty-state">
            <p>Nenhum serviço registrado para esta moto ainda.</p>
            <Link 
              to={`/checklists?placa=${encodeURIComponent(moto.placa)}&criar=true`} 
              className="btn-primary"
            >
              Criar Primeiro Checklist
            </Link>
          </div>
        ) : (
          <>
            {proximoKm && (
              <div className="alert-info">
                <strong>💡 Próxima revisão sugerida:</strong> {proximoKm.toLocaleString('pt-BR')} km
              </div>
            )}
            <div className="checklists-list">
              {checklists
                .sort((a, b) => {
                  const dataA = new Date(a.data_revisao)
                  const dataB = new Date(b.data_revisao)
                  return dataB - dataA
                })
                .map((checklist) => (
                  <div key={checklist.id} className="checklist-item">
                    <div className="checklist-item-header">
                      <div>
                        <h3>Revisão #{checklist.id}</h3>
                        <p className="checklist-date">
                          {formatarData(checklist.data_revisao)}
                        </p>
                      </div>
                      <div className="checklist-item-stats">
                        <span className="km-badge">
                          {checklist.km_atual?.toLocaleString('pt-BR')} km
                        </span>
                        {checklist.custo_total_estimado > 0 && (
                          <span className="custo-badge">
                            R$ {checklist.custo_total_estimado.toFixed(2)}
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="checklist-item-details">
                      <div className="checklist-stats-mini">
                        <span>
                          ✅ {checklist.total_concluido || 0} concluídos
                        </span>
                        <span>
                          ⚠️ {checklist.total_necessita_troca || 0} necessitam troca
                        </span>
                        <span>
                          ⏳ {checklist.total_pendente || 0} pendentes
                        </span>
                        {(checklist.total_ignorado || 0) > 0 && (
                          <span>
                            ➖ {checklist.total_ignorado} ignorados
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="checklist-item-actions">
                      <Link
                        to={`/checklists/${checklist.id}`}
                        className="btn-view-checklist"
                      >
                        Ver Detalhes →
                      </Link>
                    </div>
                  </div>
                ))}
            </div>
          </>
          )}
        </div>
      )}
    </div>
  )
}

export default MotoDetalhes

