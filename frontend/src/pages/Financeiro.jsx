import { useEffect, useState } from 'react'
import { financeiroService } from '../services/api'
import { handleApiError } from '../utils/errorHandler'
import { showToast } from '../components/Toast'
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import './Financeiro.css'

const COLORS = ['#667eea', '#43e97b', '#fa709a', '#4facfe', '#f093fb']

function Financeiro() {
  const [relatorio, setRelatorio] = useState(null)
  const [loading, setLoading] = useState(true)
  const [tipoPeriodo, setTipoPeriodo] = useState('mes')
  const [dataReferencia, setDataReferencia] = useState(new Date().toISOString().split('T')[0])
  const [dataInicio, setDataInicio] = useState('')
  const [dataFim, setDataFim] = useState('')
  const [modoFiltro, setModoFiltro] = useState('periodo') // 'periodo' ou 'custom'

  useEffect(() => {
    carregarRelatorio()
  }, [tipoPeriodo, dataReferencia, dataInicio, dataFim, modoFiltro])

  const carregarRelatorio = async () => {
    try {
      setLoading(true)
      const params = {}
      
      if (modoFiltro === 'periodo') {
        params.tipo_periodo = tipoPeriodo
        params.data_referencia = dataReferencia
      } else {
        if (dataInicio) params.data_inicio = dataInicio
        if (dataFim) params.data_fim = dataFim
      }
      
      const response = await financeiroService.obterRelatorio(params)
      setRelatorio(response.data)
    } catch (error) {
      const errorMsg = handleApiError(error)
      console.error('Erro ao carregar relatório financeiro:', error)
      showToast(`Erro ao carregar relatório: ${errorMsg}`, 'error')
    } finally {
      setLoading(false)
    }
  }

  const formatarMoeda = (valor) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(valor)
  }

  const formatarData = (dataStr) => {
    if (!dataStr) return ''
    const data = new Date(dataStr)
    return data.toLocaleDateString('pt-BR')
  }

  if (loading) {
    return <div className="loading">Carregando relatório financeiro...</div>
  }

  if (!relatorio) {
    return <div className="empty-state">Nenhum dado disponível para o período selecionado.</div>
  }

  // Dados para gráficos
  const dadosComparacao = [
    { name: 'Receitas', valor: relatorio.receitas, cor: '#43e97b' },
    { name: 'Custos', valor: relatorio.custos, cor: '#fa709a' },
    { name: 'Lucro', valor: relatorio.lucro, cor: '#667eea' }
  ].filter(item => item.valor > 0)

  const dadosPagamento = [
    { name: 'Pagos', value: relatorio.checklists_pagos, cor: '#43e97b' },
    { name: 'Não Pagos', value: relatorio.checklists_nao_pagos, cor: '#fa709a' }
  ].filter(item => item.value > 0)

  return (
    <div className="financeiro-page">
      <h1>💰 Controle Financeiro</h1>

      {/* Filtros */}
      <div className="filtros-financeiro">
        <div className="filtro-tipo">
          <label>
            <input
              type="radio"
              value="periodo"
              checked={modoFiltro === 'periodo'}
              onChange={(e) => setModoFiltro(e.target.value)}
            />
            Filtrar por Período
          </label>
          <label>
            <input
              type="radio"
              value="custom"
              checked={modoFiltro === 'custom'}
              onChange={(e) => setModoFiltro(e.target.value)}
            />
            Período Personalizado
          </label>
        </div>

        {modoFiltro === 'periodo' ? (
          <div className="filtros-periodo">
            <div className="filtro-group">
              <label>Tipo de Período:</label>
              <select
                value={tipoPeriodo}
                onChange={(e) => setTipoPeriodo(e.target.value)}
                className="select-filtro"
              >
                <option value="dia">📅 Hoje</option>
                <option value="semana">📆 Esta Semana</option>
                <option value="mes">📅 Este Mês</option>
                <option value="ano">📆 Este Ano</option>
              </select>
            </div>
            <div className="filtro-group">
              <label>Data de Referência:</label>
              <input
                type="date"
                value={dataReferencia}
                onChange={(e) => setDataReferencia(e.target.value)}
                className="input-filtro"
              />
            </div>
          </div>
        ) : (
          <div className="filtros-custom">
            <div className="filtro-group">
              <label>Data Início:</label>
              <input
                type="date"
                value={dataInicio}
                onChange={(e) => setDataInicio(e.target.value)}
                className="input-filtro"
              />
            </div>
            <div className="filtro-group">
              <label>Data Fim:</label>
              <input
                type="date"
                value={dataFim}
                onChange={(e) => setDataFim(e.target.value)}
                className="input-filtro"
              />
            </div>
          </div>
        )}

        {relatorio.periodo && (
          <div className="periodo-info">
            <strong>Período:</strong> {formatarData(relatorio.periodo.data_inicio)} até {formatarData(relatorio.periodo.data_fim)}
          </div>
        )}
      </div>

      {/* Cards de Métricas Principais */}
      <div className="metricas-grid">
        <div className="metrica-card receitas">
          <div className="metrica-icon">💰</div>
          <div className="metrica-content">
            <h3>{formatarMoeda(relatorio.receitas)}</h3>
            <p>Receitas (Entradas)</p>
            <small>Checklists pagos</small>
          </div>
        </div>

        <div className="metrica-card custos">
          <div className="metrica-icon">💸</div>
          <div className="metrica-content">
            <h3>{formatarMoeda(relatorio.custos)}</h3>
            <p>Custos (Saídas)</p>
            <small>Total de custos reais</small>
          </div>
        </div>

        <div className={`metrica-card lucro ${relatorio.lucro >= 0 ? 'lucro-positivo' : 'lucro-negativo'}`}>
          <div className="metrica-icon">{relatorio.lucro >= 0 ? '📈' : '📉'}</div>
          <div className="metrica-content">
            <h3>{formatarMoeda(relatorio.lucro)}</h3>
            <p>Lucro Líquido</p>
            <small>Receitas - Custos</small>
          </div>
        </div>

        <div className="metrica-card servicos">
          <div className="metrica-icon">🔧</div>
          <div className="metrica-content">
            <h3>{relatorio.quantidade_servicos}</h3>
            <p>Serviços Realizados</p>
            <small>Total de checklists</small>
          </div>
        </div>

        <div className="metrica-card motos">
          <div className="metrica-icon">🏍️</div>
          <div className="metrica-content">
            <h3>{relatorio.quantidade_motos}</h3>
            <p>Motos Atendidas</p>
            <small>Motos únicas no período</small>
          </div>
        </div>

        <div className="metrica-card ticket">
          <div className="metrica-icon">🎫</div>
          <div className="metrica-content">
            <h3>{formatarMoeda(relatorio.ticket_medio)}</h3>
            <p>Ticket Médio</p>
            <small>Receita média por serviço</small>
          </div>
        </div>
      </div>

      {/* Gráficos */}
      <div className="graficos-section">
        <div className="grafico-card">
          <h2>Comparação: Receitas vs Custos vs Lucro</h2>
          {dadosComparacao.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={dadosComparacao}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip formatter={(value) => formatarMoeda(value)} />
                <Bar dataKey="valor" fill="#667eea">
                  {dadosComparacao.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.cor} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="grafico-vazio">Sem dados para exibir</div>
          )}
        </div>

        <div className="grafico-card">
          <h2>Status de Pagamento</h2>
          {dadosPagamento.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={dadosPagamento}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {dadosPagamento.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.cor} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="grafico-vazio">Sem dados para exibir</div>
          )}
        </div>
      </div>

      {/* Detalhamento */}
      <div className="detalhamento-section">
        <h2>📊 Detalhamento</h2>
        <div className="detalhamento-grid">
          <div className="detalhe-card">
            <h4>Checklists Pagos</h4>
            <p className="detalhe-valor">{relatorio.checklists_pagos}</p>
            <small>Total de {relatorio.quantidade_servicos} serviços</small>
          </div>
          <div className="detalhe-card">
            <h4>Checklists Não Pagos</h4>
            <p className="detalhe-valor">{relatorio.checklists_nao_pagos}</p>
            <small>Aguardando pagamento</small>
          </div>
          <div className="detalhe-card">
            <h4>Taxa de Pagamento</h4>
            <p className="detalhe-valor">
              {relatorio.quantidade_servicos > 0
                ? ((relatorio.checklists_pagos / relatorio.quantidade_servicos) * 100).toFixed(1)
                : 0}%
            </p>
            <small>Percentual de serviços pagos</small>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Financeiro

