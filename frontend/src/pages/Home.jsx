import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { motosService, checklistsService, analyticsService } from '../services/api'
import { handleApiError } from '../utils/errorHandler'
import { showToast } from '../components/Toast'
import './Home.css'

function Home() {
  const [stats, setStats] = useState({
    totalMotos: 0,
    totalChecklists: 0,
    custoTotal: 0,
    checklistsPendentes: 0,
  })
  const [checklistsRecentes, setChecklistsRecentes] = useState([])
  const [motosRecentes, setMotosRecentes] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    carregarDados()
  }, [])

  const carregarDados = async () => {
    try {
      const [motosRes, checklistsRes, analyticsRes] = await Promise.all([
        motosService.listar(),
        checklistsService.listar({ ordenar_por: 'data', limit: 10 }),
        analyticsService.obter(),
      ])

      const todosChecklists = await checklistsService.listar()
      const checklistsPendentes = todosChecklists.data?.filter(c => 
        !c.finalizado && c.total_pendente > 0
      ).length || 0

      // Ordena checklists por data (mais recente primeiro)
      const checklistsOrdenados = (checklistsRes.data || []).sort((a, b) => {
        const dataA = new Date(a.data_revisao)
        const dataB = new Date(b.data_revisao)
        return dataB - dataA
      })

      // Pega as últimas 5 motos (ou todas se tiver menos)
      const motos = motosRes.data || []
      const motosOrdenadas = motos.slice(0, 5)

      setStats({
        totalMotos: motos.length,
        totalChecklists: todosChecklists.data?.length || 0,
        custoTotal: analyticsRes.data?.resumo_custos?.soma || 0,
        checklistsPendentes,
      })
      setChecklistsRecentes(checklistsOrdenados.slice(0, 5))
      setMotosRecentes(motosOrdenadas)
    } catch (error) {
      const errorMsg = handleApiError(error)
      console.error('Erro ao carregar dados:', error)
      showToast(`Erro ao carregar dados: ${errorMsg}`, 'error')
      setStats({
        totalMotos: 0,
        totalChecklists: 0,
        custoTotal: 0,
        checklistsPendentes: 0,
      })
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

  if (loading) {
    return <div className="loading">Carregando dashboard...</div>
  }

  return (
    <div className="home">
      <div className="hero">
        <h1>🔧 SGO</h1>
        <p>Sistema de Gerenciamento de Oficinas</p>
      </div>

      {/* Estatísticas Principais */}
      <div className="stats-grid">
        <Link to="/motos" className="stat-card stat-card-link">
          <div className="stat-icon">🏍️</div>
          <div className="stat-content">
            <h3>{stats.totalMotos}</h3>
            <p>Motos Cadastradas</p>
          </div>
          <div className="stat-footer">Ver todas →</div>
        </Link>

        <Link to="/checklists" className="stat-card stat-card-link">
          <div className="stat-icon">📋</div>
          <div className="stat-content">
            <h3>{stats.totalChecklists}</h3>
            <p>Checklists de Revisão</p>
          </div>
          <div className="stat-footer">Ver todos →</div>
        </Link>

        <Link 
          to="/checklists?status_item=pendente" 
          className="stat-card stat-card-link stat-card-warning"
        >
          <div className="stat-icon">⚠️</div>
          <div className="stat-content">
            <h3>{stats.checklistsPendentes}</h3>
            <p>Checklists Pendentes</p>
          </div>
          <div className="stat-footer">Ver pendentes →</div>
        </Link>

        <Link to="/analytics" className="stat-card stat-card-link">
          <div className="stat-icon">💰</div>
          <div className="stat-content">
            <h3>R$ {stats.custoTotal.toFixed(2)}</h3>
            <p>Valor Total das Revisões</p>
          </div>
          <div className="stat-footer">Ver analytics →</div>
        </Link>
      </div>

      {/* Ações Rápidas */}
      <div className="quick-actions">
        <h2>⚡ Ações Rápidas</h2>
        <div className="actions-grid">
          <Link to="/motos" className="action-card action-primary">
            <span className="action-icon">➕</span>
            <h3>Cadastrar Nova Moto</h3>
            <p>Adicione uma nova moto ao sistema</p>
          </Link>
          <Link to="/checklists" className="action-card action-primary">
            <span className="action-icon">📝</span>
            <h3>Criar Checklist</h3>
            <p>Registre uma nova revisão</p>
          </Link>
          <Link to="/motos" className="action-card">
            <span className="action-icon">🔍</span>
            <h3>Buscar Moto</h3>
            <p>Encontre uma moto cadastrada</p>
          </Link>
          <Link to="/analytics" className="action-card">
            <span className="action-icon">📊</span>
            <h3>Ver Analytics</h3>
            <p>Analise estatísticas e custos</p>
          </Link>
        </div>
      </div>

      {/* Conteúdo em duas colunas */}
      <div className="dashboard-content">
        {/* Checklists Recentes */}
        <div className="dashboard-section">
          <div className="section-header">
            <h2>📜 Checklists Recentes</h2>
            <Link to="/checklists" className="section-link">Ver todos →</Link>
          </div>
          {checklistsRecentes.length === 0 ? (
            <div className="empty-section">
              <p>Nenhum checklist registrado ainda.</p>
              <Link to="/checklists" className="btn-link">Criar Primeiro Checklist</Link>
            </div>
          ) : (
            <div className="recent-list">
              {checklistsRecentes.map((checklist) => (
                <Link
                  key={checklist.id}
                  to={`/checklists/${checklist.id}`}
                  className="recent-item"
                >
                  <div className="recent-item-header">
                    <div>
                      <h4>{checklist.moto?.modelo || 'Moto'}</h4>
                      <p className="recent-placa">{checklist.moto?.placa || 'N/A'}</p>
                    </div>
                    <div className="recent-badges">
                      <span className="badge-km">{checklist.km_atual?.toLocaleString('pt-BR')} km</span>
                      {checklist.custo_total_estimado > 0 && (
                        <span className="badge-custo">R$ {checklist.custo_total_estimado.toFixed(2)}</span>
                      )}
                    </div>
                  </div>
                  <div className="recent-item-footer">
                    <span className="recent-date">📅 {formatarData(checklist.data_revisao)}</span>
                    <div className="recent-stats">
                      {checklist.total_pendente > 0 && (
                        <span className="stat-badge stat-pending">
                          ⏳ {checklist.total_pendente} pendente{checklist.total_pendente > 1 ? 's' : ''}
                        </span>
                      )}
                      {checklist.total_necessita_troca > 0 && (
                        <span className="stat-badge stat-warning">
                          ⚠️ {checklist.total_necessita_troca} necessita{checklist.total_necessita_troca > 1 ? 'm' : ''} troca
                        </span>
                      )}
                      {checklist.total_concluido > 0 && (
                        <span className="stat-badge stat-success">
                          ✅ {checklist.total_concluido} concluído{checklist.total_concluido > 1 ? 's' : ''}
                        </span>
                      )}
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* Motos Recentes */}
        <div className="dashboard-section">
          <div className="section-header">
            <h2>🏍️ Motos Cadastradas</h2>
            <Link to="/motos" className="section-link">Ver todas →</Link>
          </div>
          {motosRecentes.length === 0 ? (
            <div className="empty-section">
              <p>Nenhuma moto cadastrada ainda.</p>
              <Link to="/motos" className="btn-link">Cadastrar Primeira Moto</Link>
            </div>
          ) : (
            <div className="recent-list">
              {motosRecentes.map((moto) => (
                <Link
                  key={moto.placa}
                  to={`/motos/${encodeURIComponent(moto.placa)}`}
                  className="recent-item"
                >
                  <div className="recent-item-header">
                    <div>
                      <h4>{moto.modelo}</h4>
                      <p className="recent-placa">{moto.placa}</p>
                    </div>
                    <div className="recent-badges">
                      <span className="badge-info">{moto.marca}</span>
                      <span className="badge-info">{moto.ano}</span>
                    </div>
                  </div>
                  <div className="recent-item-footer">
                    <span className="recent-details">
                      {moto.cilindradas}cc • {moto.categoria}
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Home
