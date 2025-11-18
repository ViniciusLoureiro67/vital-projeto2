import { useEffect, useState } from 'react'
import { 
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer 
} from 'recharts'
import { analyticsService } from '../services/api'
import { handleApiError } from '../utils/errorHandler'
import { showToast } from '../components/Toast'
import './Analytics.css'

const COLORS = ['#667eea', '#f093fb', '#4facfe', '#00f2fe', '#43e97b', '#fa709a']

function Analytics() {
  const [analytics, setAnalytics] = useState(null)
  const [analyticsCategoria, setAnalyticsCategoria] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    carregarAnalytics()
  }, [])

  const carregarAnalytics = async () => {
    try {
      const [res, resCat] = await Promise.all([
        analyticsService.obter(),
        analyticsService.porCategoria(),
      ])
      setAnalytics(res.data)
      setAnalyticsCategoria(resCat.data)
    } catch (error) {
      const errorMsg = handleApiError(error)
      console.error('Erro ao carregar analytics:', error)
      showToast(`Erro ao carregar analytics: ${errorMsg}`, 'error')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="loading">Carregando analytics...</div>
  }

  if (!analytics) {
    return <div className="empty-state">Nenhum dado disponível para análise.</div>
  }

  // Preparar dados para gráficos
  const dadosCustosTempo = analytics.dados_historicos?.dados?.map((d, idx) => ({
    data: d.data_formatada,
    dataFull: d.data,
    index: idx + 1,
    custoEstimado: d.custo_estimado,
    custoReal: d.custo_real || 0,
    km: d.km,
    moto: d.moto
  })) || []

  const dadosKmCusto = analytics.dados_historicos?.dados?.map(d => ({
    km: d.km,
    custoEstimado: d.custo_estimado,
    custoReal: d.custo_real || null
  })).filter(d => d.custoReal !== null) || []

  const dadosStatus = [
    { name: 'Concluídos', value: analytics.distribuicao_status?.concluido || 0, color: '#43e97b' },
    { name: 'Pendentes', value: analytics.distribuicao_status?.pendente || 0, color: '#fbbf24' },
    { name: 'Necessita Troca', value: analytics.distribuicao_status?.necessita_troca || 0, color: '#f87171' }
  ].filter(d => d.value > 0)

  const dadosCustosReais = analytics.resumo_custos_reais?.total_com_custo_real > 0 ? [
    { name: 'Custo Real', value: analytics.resumo_custos_reais?.soma || 0 },
    { name: 'Custo Estimado', value: analytics.resumo_custos?.soma || 0 }
  ] : []

  return (
    <div className="analytics-page">
      <h1>📊 Analytics e Estatísticas</h1>

      {/* Resumo de Custos */}
      <div className="analytics-section">
        <h2>Resumo de Custos Estimados</h2>
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon">💰</div>
            <div className="stat-content">
              <h3>R$ {analytics.resumo_custos?.soma?.toFixed(2) || '0.00'}</h3>
              <p>Valor Total das Revisões</p>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">📈</div>
            <div className="stat-content">
              <h3>R$ {analytics.resumo_custos?.media?.toFixed(2) || '0.00'}</h3>
              <p>Média por Revisão</p>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">⬆️</div>
            <div className="stat-content">
              <h3>R$ {analytics.resumo_custos?.max?.toFixed(2) || '0.00'}</h3>
              <p>Maior Custo</p>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">⬇️</div>
            <div className="stat-content">
              <h3>R$ {analytics.resumo_custos?.min?.toFixed(2) || '0.00'}</h3>
              <p>Menor Custo</p>
            </div>
          </div>
        </div>
      </div>

      {/* Resumo de Custos Reais */}
      {analytics.resumo_custos_reais && analytics.resumo_custos_reais.total_com_custo_real > 0 && (
        <div className="analytics-section">
          <h2>Resumo de Custos Reais</h2>
          <div className="stats-grid">
            <div className="stat-card stat-card-real">
              <div className="stat-icon">💵</div>
              <div className="stat-content">
                <h3>R$ {analytics.resumo_custos_reais.soma?.toFixed(2) || '0.00'}</h3>
                <p>Custo Total das Peças/Produtos</p>
              </div>
            </div>
            <div className="stat-card stat-card-real">
              <div className="stat-icon">📊</div>
              <div className="stat-content">
                <h3>R$ {analytics.resumo_custos_reais.media?.toFixed(2) || '0.00'}</h3>
                <p>Média Real por Revisão</p>
              </div>
            </div>
            <div className="stat-card stat-card-real">
              <div className="stat-icon">📝</div>
              <div className="stat-content">
                <h3>{analytics.resumo_custos_reais.total_com_custo_real}</h3>
                <p>Revisões com Custo Real</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Gráfico: Custos ao Longo do Tempo */}
      {dadosCustosTempo.length > 0 && (
        <div className="analytics-section chart-section">
          <h2>Custos ao Longo do Tempo</h2>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={dadosCustosTempo}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="data" 
                  angle={-45}
                  textAnchor="end"
                  height={80}
                />
                <YAxis />
                <Tooltip 
                  formatter={(value, name) => [
                    `R$ ${value.toFixed(2)}`,
                    name === 'custoEstimado' ? 'Custo Estimado' : 'Custo Real'
                  ]}
                />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="custoEstimado" 
                  stroke="#667eea" 
                  strokeWidth={2}
                  name="Custo Estimado"
                  dot={{ r: 4 }}
                />
                {analytics.resumo_custos_reais?.total_com_custo_real > 0 && (
                  <Line 
                    type="monotone" 
                    dataKey="custoReal" 
                    stroke="#43e97b" 
                    strokeWidth={2}
                    name="Custo Real"
                    dot={{ r: 4 }}
                  />
                )}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Gráfico: Correlação KM vs Custo */}
      {dadosKmCusto.length > 0 && (
        <div className="analytics-section chart-section">
          <h2>Correlação: Quilometragem vs Custo Real</h2>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={dadosKmCusto}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="km" 
                  label={{ value: 'Quilometragem (km)', position: 'insideBottom', offset: -5 }}
                />
                <YAxis 
                  label={{ value: 'Custo (R$)', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip 
                  formatter={(value) => `R$ ${value.toFixed(2)}`}
                  labelFormatter={(label) => `KM: ${label}`}
                />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="custoReal" 
                  stroke="#43e97b" 
                  strokeWidth={2}
                  name="Custo Real"
                  dot={{ r: 5 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Gráfico: Distribuição de Status */}
      {dadosStatus.length > 0 && (
        <div className="analytics-section chart-section">
          <h2>Distribuição de Status dos Itens</h2>
          <div className="charts-row">
            <div className="chart-container half-width">
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={dadosStatus}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {dadosStatus.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="chart-container half-width">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={dadosStatus}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="value" fill="#667eea">
                    {dadosStatus.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* Comparação Custo Real vs Estimado */}
      {dadosCustosReais.length > 0 && (
        <div className="analytics-section chart-section">
          <h2>Comparação: Custo Real vs Estimado</h2>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={dadosCustosReais}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip formatter={(value) => `R$ ${value.toFixed(2)}`} />
                <Legend />
                <Bar dataKey="value" fill="#667eea" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Modelo de Regressão */}
      {analytics.modelo_regressao && (
        <div className="analytics-section">
          <h2>Modelo de Regressão Linear (NumPy polyfit)</h2>
          <div className="regression-info">
            <p><strong>Coeficiente Angular:</strong> {analytics.modelo_regressao.coef_angular?.toFixed(6)}</p>
            <p><strong>Coeficiente Linear:</strong> {analytics.modelo_regressao.coef_linear?.toFixed(2)}</p>
            <p className="regression-formula">
              <strong>Fórmula:</strong> Custo = {analytics.modelo_regressao.coef_angular?.toFixed(6)} × KM + {analytics.modelo_regressao.coef_linear?.toFixed(2)}
            </p>
            {analytics.previsao_custo_km && (
              <p className="previsao">
                <strong>Previsão para 35.000 km:</strong> R$ {analytics.previsao_custo_km.toFixed(2)}
              </p>
            )}
          </div>
        </div>
      )}

      {/* Analytics por Categoria */}
      {analyticsCategoria && Object.keys(analyticsCategoria).length > 0 && (
        <div className="analytics-section">
          <h2>Analytics por Categoria</h2>
          <div className="categoria-grid">
            {Object.entries(analyticsCategoria).map(([categoria, dados]) => (
              <div key={categoria} className="categoria-card">
                <h3>{categoria}</h3>
                <div className="categoria-stats">
                  <p><strong>Motos:</strong> {dados.total_motos}</p>
                  <p><strong>Checklists:</strong> {dados.total_checklists}</p>
                  <p><strong>Valor Total das Revisões:</strong> R$ {dados.resumo_custos?.soma?.toFixed(2) || '0.00'}</p>
                  <p><strong>Média:</strong> R$ {dados.resumo_custos?.media?.toFixed(2) || '0.00'}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default Analytics
