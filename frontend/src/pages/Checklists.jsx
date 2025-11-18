import { useEffect, useState } from 'react'
import { Link, useSearchParams, useNavigate } from 'react-router-dom'
import { checklistsService, motosService } from '../services/api'
import { handleApiError } from '../utils/errorHandler'
import { showToast } from '../components/Toast'
import './Checklists.css'

function Checklists() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [checklists, setChecklists] = useState([])
  const [motos, setMotos] = useState([])
  const [loading, setLoading] = useState(true)
  const [filtroPlaca, setFiltroPlaca] = useState('')
  const [filtroFinalizado, setFiltroFinalizado] = useState(null) // null = todos, true = finalizados, false = não finalizados
  const [filtroPago, setFiltroPago] = useState(null) // null = todos, true = pagos, false = não pagos
  const [buscaMoto, setBuscaMoto] = useState('')
  const [mostrarBusca, setMostrarBusca] = useState(false)
  const [motosFiltradas, setMotosFiltradas] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState({
    placa_moto: '',
    km_atual: '',
    data_revisao: new Date().toISOString().split('T')[0],
  })

  useEffect(() => {
    // Lê placa da URL se existir
    const placaFromUrl = searchParams.get('placa')
    const criarFromUrl = searchParams.get('criar')
    
    if (placaFromUrl) {
      const placaDecoded = decodeURIComponent(placaFromUrl)
      setFiltroPlaca(placaDecoded)
      // Preenche o formulário também
      setFormData(prev => ({ ...prev, placa_moto: placaDecoded }))
      // Abre o formulário automaticamente se o parâmetro criar=true estiver na URL
      if (criarFromUrl === 'true') {
        setShowForm(true)
        // Scroll suave até o formulário após um pequeno delay
        setTimeout(() => {
          const formElement = document.querySelector('.checklist-form')
          if (formElement) {
            formElement.scrollIntoView({ behavior: 'smooth', block: 'start' })
          }
        }, 100)
      }
    }
    carregarDados()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (filtroPlaca) {
      carregarChecklistsPorMoto()
    } else {
      carregarChecklists()
    }
  }, [filtroPlaca, filtroFinalizado, filtroPago])

  const carregarDados = async () => {
    try {
      const [checklistsRes, motosRes] = await Promise.all([
        checklistsService.listar(),
        motosService.listar(),
      ])
      setChecklists(checklistsRes.data || [])
      setMotos(motosRes.data || [])
      setMotosFiltradas(motosRes.data || [])
    } catch (error) {
      const errorMsg = handleApiError(error)
      console.error('Erro ao carregar dados:', error)
      console.error('Mensagem:', errorMsg)
      showToast(`Erro ao carregar dados: ${errorMsg}`, 'error')
    } finally {
      setLoading(false)
    }
  }

  // Busca inteligente de motos (local)
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

  // Fechar busca ao clicar fora
  useEffect(() => {
    if (!mostrarBusca) return

    const handleClickOutside = (event) => {
      const searchBox = document.querySelector('.search-box')
      const searchToggle = document.querySelector('.btn-search-toggle')
      
      if (searchBox && searchToggle && 
          !searchBox.contains(event.target) && 
          !searchToggle.contains(event.target)) {
        setMostrarBusca(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [mostrarBusca])

  const carregarChecklists = async () => {
    try {
      const params = {}
      if (filtroFinalizado !== null) params.finalizado = filtroFinalizado
      if (filtroPago !== null) params.pago = filtroPago
      const response = await checklistsService.listar(params)
      setChecklists(response.data || [])
    } catch (error) {
      const errorMsg = handleApiError(error)
      console.error('Erro ao carregar checklists:', error)
      showToast(`Erro ao carregar checklists: ${errorMsg}`, 'error')
    }
  }

  const carregarChecklistsPorMoto = async () => {
    try {
      const response = await checklistsService.buscarPorMoto(filtroPlaca)
      setChecklists(response.data || [])
    } catch (error) {
      const errorMsg = handleApiError(error)
      console.error('Erro ao carregar checklists:', error)
      console.error('Mensagem:', errorMsg)
    }
  }

  const handleSubmitChecklist = async (e) => {
    e.preventDefault()
    try {
      const data = {
        placa_moto: formData.placa_moto,
        km_atual: parseInt(formData.km_atual),
        data_revisao: formData.data_revisao || undefined,
      }
      const response = await checklistsService.criar(data)
      console.log('Checklist criado:', response.data)
      
      const checklistId = response.data.id
      if (checklistId) {
        // Redireciona para a página de detalhes do checklist criado
        showToast(
          `Checklist criado com sucesso! Redirecionando...`,
          'success',
          2000
        )
        setTimeout(() => {
          navigate(`/checklists/${checklistId}`)
        }, 500)
      } else {
        showToast(
          `Checklist criado com sucesso! ${response.data.moto.modelo} - ${response.data.moto.placa}`,
          'success'
        )
        setShowForm(false)
        setFormData({
          placa_moto: '',
          km_atual: '',
          data_revisao: new Date().toISOString().split('T')[0],
        })
        carregarDados()
      }
    } catch (error) {
      const errorMsg = handleApiError(error)
      console.error('Erro ao criar checklist:', error)
      showToast(`Erro ao criar checklist: ${errorMsg}`, 'error')
    }
  }

  if (loading) {
    return <div className="loading">Carregando checklists...</div>
  }

  return (
    <div className="checklists-page">
      <div className="page-header">
        <h1>📋 Checklists de Revisão</h1>
        <div className="header-actions">
          <div className="search-container">
            <button
              onClick={() => setMostrarBusca(!mostrarBusca)}
              className="btn-search-toggle"
              title="Buscar moto"
            >
              🔍 {mostrarBusca ? 'Fechar Busca' : 'Buscar Moto'}
            </button>
            
            {mostrarBusca && (
              <div className="search-box">
                <input
                  type="text"
                  value={buscaMoto}
                  onChange={(e) => setBuscaMoto(e.target.value)}
                  placeholder="Buscar por placa, modelo ou marca..."
                  className="search-input"
                  autoFocus
                />
                {buscaMoto && (
                  <button
                    onClick={() => {
                      setBuscaMoto('')
                      setFiltroPlaca('')
                    }}
                    className="btn-clear-search"
                    title="Limpar busca"
                  >
                    ✖️
                  </button>
                )}
                
                {buscaMoto && motosFiltradas.length > 0 && (
                  <div className="search-results">
                    {motosFiltradas.slice(0, 5).map((moto) => (
                      <div
                        key={moto.placa}
                        className="search-result-item"
                        onClick={() => {
                          setFiltroPlaca(moto.placa)
                          setBuscaMoto('')
                          setMostrarBusca(false)
                          showToast(`Filtrando por: ${moto.placa} - ${moto.modelo}`, 'info', 2000)
                        }}
                      >
                        <div className="result-placa">{moto.placa}</div>
                        <div className="result-info">
                          <strong>{moto.modelo}</strong> - {moto.marca}
                        </div>
                        <div className="result-details">
                          {moto.ano} • {moto.cilindradas}cc • {moto.categoria}
                        </div>
                      </div>
                    ))}
                    {motosFiltradas.length > 5 && (
                      <div className="search-result-more">
                        + {motosFiltradas.length - 5} moto(s) encontrada(s)
                      </div>
                    )}
                  </div>
                )}
                
                {buscaMoto && motosFiltradas.length === 0 && (
                  <div className="search-results">
                    <div className="search-result-empty">
                      Nenhuma moto encontrada para "{buscaMoto}"
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
          
          <div className="filtros-container">
            <div className="filtro">
              <label>Filtrar por placa:</label>
              <select
                value={filtroPlaca}
                onChange={(e) => setFiltroPlaca(e.target.value)}
                className="select-filtro"
              >
                <option value="">Todas as motos</option>
                {motos.map((moto) => (
                  <option key={moto.placa} value={moto.placa}>
                    {moto.placa} - {moto.modelo}
                  </option>
                ))}
              </select>
            </div>
            
            <div className="filtro">
              <label>Status:</label>
              <select
                value={filtroFinalizado === null ? '' : filtroFinalizado ? 'finalizado' : 'pendente'}
                onChange={(e) => {
                  const value = e.target.value
                  setFiltroFinalizado(value === '' ? null : value === 'finalizado')
                }}
                className="select-filtro"
              >
                <option value="">Todos</option>
                <option value="pendente">⏳ Em Andamento</option>
                <option value="finalizado">✅ Finalizados</option>
              </select>
            </div>
            
            <div className="filtro">
              <label>Pagamento:</label>
              <select
                value={filtroPago === null ? '' : filtroPago ? 'pago' : 'nao-pago'}
                onChange={(e) => {
                  const value = e.target.value
                  setFiltroPago(value === '' ? null : value === 'pago')
                }}
                className="select-filtro"
              >
                <option value="">Todos</option>
                <option value="pago">💰 Pagos</option>
                <option value="nao-pago">💳 Não Pagos</option>
              </select>
            </div>
          </div>
          
          <button onClick={() => setShowForm(!showForm)} className="btn-primary">
            {showForm ? 'Cancelar' : '+ Novo Checklist'}
          </button>
        </div>
      </div>

      {showForm && (
        <form onSubmit={handleSubmitChecklist} className="checklist-form">
          <h2>Criar Novo Checklist</h2>
          <div className="form-grid">
            <div className="form-group">
              <label>Moto (Placa) *</label>
              <select
                value={formData.placa_moto}
                onChange={(e) => setFormData({ ...formData, placa_moto: e.target.value })}
                required
                className="moto-select"
              >
                <option value="">Selecione uma moto</option>
                {motos.map((moto) => (
                  <option key={moto.placa} value={moto.placa}>
                    {moto.placa} - {moto.modelo} ({moto.marca})
                  </option>
                ))}
              </select>
              {motos.length === 0 && (
                <small style={{ color: '#dc3545', marginTop: '0.5rem', display: 'block' }}>
                  ⚠️ Nenhuma moto cadastrada. Cadastre uma moto primeiro em "Motos".
                </small>
              )}
            </div>
            <div className="form-group">
              <label>Quilometragem Atual (km) *</label>
              <input
                type="number"
                value={formData.km_atual}
                onChange={(e) => setFormData({ ...formData, km_atual: e.target.value })}
                placeholder="15000"
                min="0"
                required
              />
            </div>
            <div className="form-group">
              <label>Data da Revisão</label>
              <input
                type="date"
                value={formData.data_revisao}
                onChange={(e) => setFormData({ ...formData, data_revisao: e.target.value })}
              />
            </div>
          </div>
          <button type="submit" className="btn-primary">Criar Checklist</button>
          <p className="form-note">
            * Um checklist padrão será criado com todos os itens de revisão pendentes.
            Você poderá atualizar o status de cada item depois.
          </p>
        </form>
      )}

      {checklists.length === 0 ? (
        <div className="empty-state">
          <p>Nenhum checklist encontrado.</p>
        </div>
      ) : (
        <div className="checklists-list">
          {checklists.map((checklist) => (
            <div key={checklist.id} className="checklist-card">
              <div className="checklist-header">
                <div>
                  <h3>{checklist.moto.modelo} - {checklist.moto.placa}</h3>
                  <p className="checklist-date">📅 {checklist.data_formatada}</p>
                  <div className="checklist-status-badges">
                    <span className={`status-badge-mini ${checklist.finalizado ? 'finalizado' : 'pendente'}`}>
                      {checklist.finalizado ? '✅ Finalizado' : '⏳ Em Andamento'}
                    </span>
                    <span className={`status-badge-mini ${checklist.pago ? 'pago' : 'nao-pago'}`}>
                      {checklist.pago ? '💰 Pago' : '💳 Não Pago'}
                    </span>
                  </div>
                </div>
                <div className="checklist-km">
                  <span>🚗 {checklist.km_atual.toLocaleString()} km</span>
                </div>
              </div>
              
              <Link 
                to={`/checklists/${checklist.id}`} 
                className="btn-ver-checklist"
              >
                🔍 Ver e Editar Checklist
              </Link>
              
              <div className="checklist-stats">
                <div className="stat">
                  <span className="stat-value">{checklist.total_concluido}</span>
                  <span className="stat-label">Concluídos</span>
                </div>
                <div className="stat">
                  <span className="stat-value">{checklist.total_pendente}</span>
                  <span className="stat-label">Pendentes</span>
                </div>
                <div className="stat">
                  <span className="stat-value">{checklist.total_necessita_troca}</span>
                  <span className="stat-label">Necessita Troca</span>
                </div>
                <div className="stat stat-custo">
                  <span className="stat-value">R$ {checklist.custo_total_estimado.toFixed(2)}</span>
                  <span className="stat-label">Valor da Revisão</span>
                </div>
              </div>

              <div className="checklist-items">
                <h4>Itens ({checklist.itens.length})</h4>
                <div className="items-list">
                  {checklist.itens.slice(0, 5).map((item, idx) => (
                    <div key={idx} className="item-row">
                      <span className="item-nome">{item.nome}</span>
                      <span className={`item-status status-${item.status}`}>
                        {item.status === 'concluido' && '✅'}
                        {item.status === 'pendente' && '⏳'}
                        {item.status === 'necessita_troca' && '⚠️'}
                        {item.status === 'ignorado' && '🚫'}
                        {item.status === 'concluido' ? 'OK' : item.status === 'necessita_troca' ? 'Troca' : item.status === 'ignorado' ? 'Ignorado' : 'Pendente'}
                      </span>
                      {item.custo_estimado > 0 && (
                        <span className="item-custo">R$ {item.custo_estimado.toFixed(2)}</span>
                      )}
                    </div>
                  ))}
                  {checklist.itens.length > 5 && (
                    <p className="more-items">+ {checklist.itens.length - 5} itens...</p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default Checklists

