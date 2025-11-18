import { useEffect, useState, useMemo, useRef, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { checklistsService } from '../services/api'
import { handleApiError } from '../utils/errorHandler'
import { gerarPDFChecklist } from '../utils/pdfGenerator'
import { debounce } from '../utils/debounce'
import { showToast } from '../components/Toast'
import './ChecklistDetalhes.css'

function ChecklistDetalhes() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [checklist, setChecklist] = useState(null)
  const [loading, setLoading] = useState(true)
  const [salvando, setSalvando] = useState({}) // Objeto para rastrear itens sendo salvos
  const [mostrarFormNovoItem, setMostrarFormNovoItem] = useState(false)
  const [modoRapido, setModoRapido] = useState(false)
  const [itemFocado, setItemFocado] = useState(null) // Para navegação por teclado
  const [novoItem, setNovoItem] = useState({
    nome: '',
    categoria: 'Geral',
    custo_estimado: ''
  })
  
  // Backup para reverter em caso de erro
  const backupChecklist = useRef(null)

  useEffect(() => {
    carregarChecklist()
  }, [id])

  const carregarChecklist = async () => {
    try {
      const response = await checklistsService.buscarPorId(id)
      setChecklist(response.data)
      backupChecklist.current = JSON.parse(JSON.stringify(response.data)) // Deep copy
    } catch (error) {
      const errorMsg = handleApiError(error)
      console.error('Erro ao carregar checklist:', error)
      showToast(`Erro ao carregar checklist: ${errorMsg}`, 'error')
      navigate('/checklists')
    } finally {
      setLoading(false)
    }
  }

  const atualizarItem = async (itemIndex, status, custo, optimistic = true) => {
    const itemKey = `item-${itemIndex}`
    if (salvando[itemKey]) return
    
    const item = checklist.itens[itemIndex]
    if (!item) return
    
    // Salva backup antes de otimistic update
    if (optimistic && !backupChecklist.current) {
      backupChecklist.current = JSON.parse(JSON.stringify(checklist))
    }
    
    // Optimistic update - atualiza UI imediatamente
    if (optimistic) {
      const novoChecklist = { ...checklist }
      const novoItem = { ...item }
      if (status) novoItem.status = status
      if (custo !== undefined && custo !== null) novoItem.custo_estimado = custo
      
      // Atualiza totais
      const novosItens = [...novoChecklist.itens]
      novosItens[itemIndex] = novoItem
      novoChecklist.itens = novosItens
      
      // Recalcula totais
      novoChecklist.total_concluido = novosItens.filter(i => i.status === 'concluido').length
      novoChecklist.total_pendente = novosItens.filter(i => i.status === 'pendente').length
      novoChecklist.total_necessita_troca = novosItens.filter(i => i.status === 'necessita_troca').length
      novoChecklist.total_ignorado = novosItens.filter(i => i.status === 'ignorado').length
      novoChecklist.custo_total_estimado = novosItens
        .filter(i => i.status === 'necessita_troca')
        .reduce((sum, i) => sum + (i.custo_estimado || 0), 0)
      
      setChecklist(novoChecklist)
    }
    
    setSalvando(prev => ({ ...prev, [itemKey]: true }))
    
    try {
      const params = {}
      if (status) params.status = status
      if (custo !== undefined && custo !== null) params.custo_estimado = custo

      const response = await checklistsService.atualizarItem(
        parseInt(id),
        itemIndex,
        params
      )
      
      // CORREÇÃO DEFINITIVA: Usa dados do servidor para o item modificado, preserva os outros itens
      setChecklist(prevChecklist => {
        const dadosServidor = response.data
        const novoChecklist = { ...prevChecklist }
        
        // Atualiza campos gerais do checklist
        novoChecklist.finalizado = dadosServidor.finalizado
        novoChecklist.pago = dadosServidor.pago
        novoChecklist.custo_real = dadosServidor.custo_real
        novoChecklist.total_concluido = dadosServidor.total_concluido
        novoChecklist.total_pendente = dadosServidor.total_pendente
        novoChecklist.total_necessita_troca = dadosServidor.total_necessita_troca
        novoChecklist.total_ignorado = dadosServidor.total_ignorado
        
        // PRESERVA todos os itens atuais (cópia profunda)
        const novosItens = prevChecklist.itens.map(item => ({ ...item }))
        
        // Atualiza APENAS o item modificado com os dados do servidor (confirma que foi salvo)
        if (dadosServidor.itens && dadosServidor.itens[itemIndex]) {
          // Usa os dados do servidor para o item modificado
          // O servidor retorna o valor que foi salvo no banco
          novosItens[itemIndex] = { ...dadosServidor.itens[itemIndex] }
        }
        
        novoChecklist.itens = novosItens
        
        // Recalcula custo_total_estimado baseado nos itens
        novoChecklist.custo_total_estimado = novosItens
          .filter(i => i.status === 'necessita_troca')
          .reduce((sum, i) => sum + (i.custo_estimado || 0), 0)
        
        backupChecklist.current = JSON.parse(JSON.stringify(novoChecklist))
        return novoChecklist
      })
      showToast('Item atualizado com sucesso', 'success', 2000)
    } catch (error) {
      // Reverte para backup em caso de erro
      if (backupChecklist.current) {
        setChecklist(backupChecklist.current)
      }
      const errorMsg = handleApiError(error)
      console.error('Erro ao atualizar item:', error)
      showToast(`Erro ao atualizar item: ${errorMsg}`, 'error')
    } finally {
      setSalvando(prev => {
        const novo = { ...prev }
        delete novo[itemKey]
        return novo
      })
    }
  }
  
  // Debounced version para custo
  const debouncedAtualizarCusto = useMemo(
    () => debounce((itemIndex, custo) => {
      atualizarItem(itemIndex, null, custo, true)
    }, 500),
    [id]
  )

  const atualizarStatusChecklist = async (finalizado, pago, custoReal) => {
    try {
      // Preserva o custo_real atual se não foi especificado um novo valor
      // Isso garante que o valor não seja perdido ao finalizar ou marcar como pago
      let custoRealParaEnviar = custoReal
      if (custoReal === undefined) {
        // Se não foi especificado um novo valor, preserva o atual
        if (checklist?.custo_real !== null && checklist?.custo_real !== undefined) {
          custoRealParaEnviar = checklist.custo_real
        }
        // Se custoRealParaEnviar ainda for undefined, não envia o parâmetro
      }
      
      // Preserva o custo_total_estimado atual antes de atualizar
      const custoTotalEstimadoAtual = checklist?.custo_total_estimado
      
      const response = await checklistsService.atualizarStatus(id, finalizado, pago, custoRealParaEnviar)
      
      // Faz merge inteligente: preserva TODOS os valores dos itens e atualiza apenas os campos de status
      const dadosServidor = response.data
      const novoChecklist = { ...checklist }
      
      // Atualiza apenas os campos de status do checklist
      novoChecklist.finalizado = dadosServidor.finalizado
      novoChecklist.pago = dadosServidor.pago
      novoChecklist.custo_real = dadosServidor.custo_real
      novoChecklist.total_concluido = dadosServidor.total_concluido
      novoChecklist.total_pendente = dadosServidor.total_pendente
      novoChecklist.total_necessita_troca = dadosServidor.total_necessita_troca
      novoChecklist.total_ignorado = dadosServidor.total_ignorado
      
      // PRESERVA TODOS OS VALORES DOS ITENS - não substitui pelos dados do servidor
      // Isso garante que valores de custo_estimado não sejam perdidos
      if (checklist.itens && checklist.itens.length > 0) {
        // Mantém os itens atuais com seus valores preservados
        novoChecklist.itens = [...checklist.itens]
      } else if (dadosServidor.itens) {
        // Se não temos itens atuais, usa os do servidor
        novoChecklist.itens = dadosServidor.itens
      }
      
      // Recalcula custo_total_estimado baseado nos itens preservados
      if (novoChecklist.itens && novoChecklist.itens.length > 0) {
        novoChecklist.custo_total_estimado = novoChecklist.itens
          .filter(i => i.status === 'necessita_troca')
          .reduce((sum, i) => sum + (i.custo_estimado || 0), 0)
      } else {
        // Se não tem itens, usa o valor do servidor ou o preservado
        novoChecklist.custo_total_estimado = dadosServidor.custo_total_estimado || custoTotalEstimadoAtual || 0
      }
      
      setChecklist(novoChecklist)
      backupChecklist.current = JSON.parse(JSON.stringify(novoChecklist))
      
      if (finalizado !== undefined) {
        showToast(finalizado ? 'Checklist finalizado com sucesso!' : 'Checklist reaberto.', 'success')
      }
      if (pago !== undefined) {
        showToast(pago ? 'Checklist marcado como pago!' : 'Checklist marcado como não pago.', 'success')
      }
      if (custoReal !== undefined) {
        showToast('Custo real atualizado com sucesso!', 'success')
      }
    } catch (error) {
      const errorMsg = handleApiError(error)
      console.error('Erro ao atualizar status:', error)
      showToast(`Erro ao atualizar status: ${errorMsg}`, 'error')
    }
  }
  
  const [editandoCustoReal, setEditandoCustoReal] = useState(false)
  const [custoRealInput, setCustoRealInput] = useState('')
  
  useEffect(() => {
    if (checklist) {
      setCustoRealInput(checklist.custo_real?.toString() || '')
    }
  }, [checklist])
  
  const handleSalvarCustoReal = () => {
    const valor = custoRealInput.trim() === '' ? null : parseFloat(custoRealInput)
    if (valor !== null && (isNaN(valor) || valor < 0)) {
      showToast('Por favor, insira um valor válido (número positivo).', 'error')
      return
    }
    atualizarStatusChecklist(undefined, undefined, valor)
    setEditandoCustoReal(false)
  }

  const handleStatusChange = useCallback((itemIndex, novoStatus) => {
    if (!checklist) return
    const item = checklist.itens[itemIndex]
    if (!item) return
    
    let custo = item.custo_estimado
    
    // Se mudou para "concluido" ou "ignorado", zera o custo
    if (novoStatus === 'concluido' || novoStatus === 'ignorado') {
      custo = 0
    }
    // Se voltou para "pendente", zera o custo
    else if (novoStatus === 'pendente') {
      custo = 0
    }
    // Se mudou para "necessita_troca" e custo é 0, mantém 0 (usuário pode preencher depois)

    // Mapeia status para o formato da API
    const statusMap = {
      'concluido': 'concluido',
      'pendente': 'pendente',
      'necessita_troca': 'necessita_troca',
      'ignorado': 'ignorado'
    }
    
    atualizarItem(itemIndex, statusMap[novoStatus], custo)
  }, [checklist])

  const handleAdicionarItem = async (e) => {
    e.preventDefault()
    if (!novoItem.nome.trim()) {
      showToast('Informe o nome do item', 'warning')
      return
    }

    const itemKey = 'adicionar-item'
    setSalvando(prev => ({ ...prev, [itemKey]: true }))
    try {
      const dadosEnviar = {
        nome: novoItem.nome.trim(),
        categoria: novoItem.categoria || 'Geral',
        status: 'pendente',
        custo_estimado: novoItem.custo_estimado ? parseFloat(novoItem.custo_estimado) : 0
      }
      
      console.log('Adicionando item:', dadosEnviar)
      
      const response = await checklistsService.adicionarItem(id, dadosEnviar)
      console.log('Item adicionado com sucesso:', response.data)
      
      setChecklist(response.data)
      setNovoItem({ nome: '', categoria: 'Geral', custo_estimado: '' })
      setMostrarFormNovoItem(false)
      showToast('Item adicionado com sucesso', 'success')
    } catch (error) {
      console.error('Erro completo ao adicionar item:', error)
      console.error('Response:', error.response)
      const errorMsg = handleApiError(error)
      showToast(`Erro ao adicionar item: ${errorMsg}`, 'error')
    } finally {
      setSalvando(prev => {
        const novo = { ...prev }
        delete novo[itemKey]
        return novo
      })
    }
  }

  const handleCustoChange = (itemIndex, novoCusto) => {
    // Atualiza UI imediatamente (optimistic)
    const novoChecklist = { ...checklist }
    const novoItem = { ...checklist.itens[itemIndex] }
    novoItem.custo_estimado = novoCusto
    const novosItens = [...novoChecklist.itens]
    novosItens[itemIndex] = novoItem
    novoChecklist.itens = novosItens
    novoChecklist.custo_total_estimado = novosItens
      .filter(i => i.status === 'necessita_troca')
      .reduce((sum, i) => sum + (i.custo_estimado || 0), 0)
    setChecklist(novoChecklist)
    
    // Salva com debounce
    debouncedAtualizarCusto(itemIndex, novoCusto)
  }
  
  const handleSalvarCusto = async (itemIndex) => {
    // Evita múltiplas chamadas
    const itemKey = `item-${itemIndex}`
    if (salvando[itemKey]) return
    
    // Cancela o debounce pendente e salva imediatamente
    if (debouncedAtualizarCusto.cancel) {
      debouncedAtualizarCusto.cancel()
    }
    const item = checklist.itens[itemIndex]
    if (item && item.custo_estimado !== undefined && item.custo_estimado !== null) {
      // atualizarItem já mostra a notificação, não precisa mostrar novamente
      await atualizarItem(itemIndex, null, item.custo_estimado, false)
    }
  }
  
  const handleCustoBlur = async (itemIndex, e) => {
    // Evita salvar se o foco foi para o botão de salvar
    if (e?.relatedTarget?.classList?.contains('btn-salvar-custo')) {
      return
    }
    
    // Evita múltiplas chamadas
    const itemKey = `item-${itemIndex}`
    if (salvando[itemKey]) return
    
    // Salva automaticamente quando o campo perde o foco
    // Cancela qualquer debounce pendente
    if (debouncedAtualizarCusto.cancel) {
      debouncedAtualizarCusto.cancel()
    }
    const item = checklist.itens[itemIndex]
    if (item && item.custo_estimado !== undefined && item.custo_estimado !== null) {
      // Salva imediatamente sem debounce
      await atualizarItem(itemIndex, null, item.custo_estimado, false)
    }
  }
  
  // Atalhos de teclado para modo rápido
  useEffect(() => {
    if (!modoRapido || !checklist) return
    
    const handleKeyPress = (e) => {
      if (itemFocado === null) return
      
      // Ignora se estiver digitando em input
      if (e.target.tagName === 'INPUT') return
      
      const itemIndex = itemFocado
      
      switch(e.key) {
        case '1':
          e.preventDefault()
          handleStatusChange(itemIndex, 'concluido')
          break
        case '2':
          e.preventDefault()
          handleStatusChange(itemIndex, 'necessita_troca')
          break
        case '3':
          e.preventDefault()
          handleStatusChange(itemIndex, 'pendente')
          break
        case '4':
          e.preventDefault()
          handleStatusChange(itemIndex, 'ignorado')
          break
        case 'ArrowDown':
          e.preventDefault()
          const proximoIndex = Math.min(itemIndex + 1, checklist.itens.length - 1)
          setItemFocado(proximoIndex)
          break
        case 'ArrowUp':
          e.preventDefault()
          const anteriorIndex = Math.max(itemIndex - 1, 0)
          setItemFocado(anteriorIndex)
          break
        default:
          break
      }
    }
    
    window.addEventListener('keydown', handleKeyPress)
    return () => window.removeEventListener('keydown', handleKeyPress)
  }, [modoRapido, itemFocado, checklist, handleStatusChange])

  if (loading) {
    return <div className="loading">Carregando checklist...</div>
  }

  if (!checklist) {
    return <div className="empty-state">Checklist não encontrado.</div>
  }

  // Agrupa itens por categoria
  const itensPorCategoria = {}
  checklist.itens.forEach((item, idx) => {
    if (!itensPorCategoria[item.categoria]) {
      itensPorCategoria[item.categoria] = []
    }
    itensPorCategoria[item.categoria].push({ ...item, index: idx })
  })

  const getStatusColor = (status) => {
    switch (status) {
      case 'concluido': return '#28a745'
      case 'pendente': return '#ffc107'
      case 'necessita_troca': return '#dc3545'
      case 'ignorado': return '#6c757d'
      default: return '#6c757d'
    }
  }

  const getStatusLabel = (status) => {
    switch (status) {
      case 'concluido': return '✅ OK'
      case 'pendente': return '⏳ PENDENTE'
      case 'necessita_troca': return '⚠️ TROCA'
      case 'ignorado': return '🚫 IGNORADO'
      default: return status.toUpperCase()
    }
  }

  return (
    <div className="checklist-detalhes-page">
      <div className="page-header">
        <button onClick={() => navigate('/checklists')} className="btn-back">
          ← Voltar
        </button>
        <div className="header-content">
          <div>
            <h1>📋 Checklist de Revisão</h1>
            <p className="checklist-info">
              {checklist.moto.modelo} - {checklist.moto.placa} | 
              📅 {checklist.data_formatada} | 
              🚗 {checklist.km_atual.toLocaleString()} km
            </p>
          </div>
          <button 
            onClick={() => gerarPDFChecklist(checklist)}
            className="btn-gerar-pdf"
            title="Gerar PDF do checklist (em breve)"
          >
            📄 Gerar PDF
          </button>
        </div>
      </div>

      {/* Status e Ações do Checklist */}
      <div className="checklist-actions-section">
        <div className="status-info-cards">
          <div className={`status-info-card ${checklist.finalizado ? 'status-finalizado' : 'status-pendente'}`}>
            <div className="status-info-header">
              <span className="status-icon-large">
                {checklist.finalizado ? '✅' : '⏳'}
              </span>
              <div className="status-info-content">
                <h3>{checklist.finalizado ? 'Revisão Finalizada' : 'Revisão em Andamento'}</h3>
                <p>{checklist.finalizado ? 'Esta revisão foi concluída' : 'Esta revisão ainda está em andamento'}</p>
              </div>
            </div>
            {!checklist.finalizado && (
              <button
                onClick={() => atualizarStatusChecklist(true, undefined)}
                className="btn-action-primary"
              >
                Finalizar Revisão
              </button>
            )}
            {checklist.finalizado && (
              <button
                onClick={() => atualizarStatusChecklist(false, undefined)}
                className="btn-action-secondary"
              >
                Reabrir Revisão
              </button>
            )}
          </div>

          <div className={`status-info-card ${checklist.pago ? 'status-pago' : 'status-nao-pago'}`}>
            <div className="status-info-header">
              <span className="status-icon-large">
                {checklist.pago ? '💰' : '💳'}
              </span>
              <div className="status-info-content">
                <h3>{checklist.pago ? 'Pagamento Realizado' : 'Aguardando Pagamento'}</h3>
                <p>{checklist.pago ? 'Esta revisão já foi paga' : 'Esta revisão ainda não foi paga'}</p>
              </div>
            </div>
            <button
              onClick={() => atualizarStatusChecklist(undefined, !checklist.pago)}
              className={checklist.pago ? 'btn-action-secondary' : 'btn-action-success'}
            >
              {checklist.pago ? 'Marcar como Não Pago' : 'Marcar como Pago'}
            </button>
          </div>

          <div className="status-info-card status-custo-real">
            <div className="status-info-header">
              <span className="status-icon-large">💵</span>
              <div className="status-info-content">
                <h3>Custo Real das Peças/Produtos</h3>
                {!editandoCustoReal ? (
                  <p>
                    {checklist.custo_real !== null && checklist.custo_real !== undefined
                      ? `R$ ${checklist.custo_real.toFixed(2)}`
                      : 'Custo real das peças ainda não informado'}
                  </p>
                ) : (
                  <div className="custo-real-input-group">
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={custoRealInput}
                      onChange={(e) => setCustoRealInput(e.target.value)}
                      placeholder="0.00"
                      className="custo-real-input"
                      autoFocus
                    />
                    <span className="custo-real-currency">R$</span>
                  </div>
                )}
              </div>
            </div>
            {!editandoCustoReal ? (
              <button
                onClick={() => setEditandoCustoReal(true)}
                className="btn-action-primary"
              >
                {checklist.custo_real ? 'Editar Custo das Peças' : 'Informar Custo das Peças'}
              </button>
            ) : (
              <div className="custo-real-actions">
                <button
                  onClick={handleSalvarCustoReal}
                  className="btn-action-success"
                >
                  Salvar
                </button>
                <button
                  onClick={() => {
                    setEditandoCustoReal(false)
                    setCustoRealInput(checklist.custo_real?.toString() || '')
                  }}
                  className="btn-action-secondary"
                >
                  Cancelar
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="checklist-summary">
        <div className="summary-card">
          <span className="summary-label">Concluídos</span>
          <span className="summary-value concluido">{checklist.total_concluido}</span>
        </div>
        <div className="summary-card">
          <span className="summary-label">Pendentes</span>
          <span className="summary-value pendente">{checklist.total_pendente}</span>
        </div>
        <div className="summary-card">
          <span className="summary-label">Necessita Troca</span>
          <span className="summary-value necessita-troca">{checklist.total_necessita_troca}</span>
        </div>
        <div className="summary-card">
          <span className="summary-label">Ignorados</span>
          <span className="summary-value ignorado">{checklist.total_ignorado || 0}</span>
        </div>
        <div className="summary-card summary-custo">
          <span className="summary-label">Valor da Revisão</span>
          <span className="summary-value">R$ {checklist.custo_total_estimado.toFixed(2)}</span>
        </div>
      </div>

      <div className="instrucoes">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
          <div>
            <p>💡 <strong>Instruções:</strong> Marque cada item conforme você verifica a moto.</p>
            <p><strong>Estados:</strong> ⏳ Pendente (não verificado) → ✅ OK (verificado e sem problemas) → ⚠️ Troca (precisa manutenção) → 🚫 Ignorado (não será verificado)</p>
            <p><strong>Dica:</strong> Você pode salvar parcialmente e continuar depois. Não é necessário verificar todos os itens.</p>
          </div>
          <button
            onClick={() => {
              setModoRapido(!modoRapido)
              if (!modoRapido) {
                // Foca no primeiro item pendente
                const primeiroPendente = checklist.itens.findIndex(i => i.status === 'pendente')
                setItemFocado(primeiroPendente >= 0 ? primeiroPendente : 0)
                showToast('Modo Rápido ativado! Use 1=OK, 2=Troca, 3=Pendente, 4=Ignorado. Setas para navegar.', 'info', 4000)
              }
            }}
            className={`btn-modo-rapido ${modoRapido ? 'active' : ''}`}
            style={{
              padding: '10px 20px',
              fontSize: '16px',
              fontWeight: 'bold',
              borderRadius: '8px',
              border: '2px solid',
              cursor: 'pointer',
              backgroundColor: modoRapido ? '#28a745' : 'white',
              color: modoRapido ? 'white' : '#28a745',
              borderColor: '#28a745'
            }}
          >
            {modoRapido ? '⚡ Modo Rápido ATIVO' : '⚡ Ativar Modo Rápido'}
          </button>
        </div>
        {modoRapido && (
          <div style={{
            padding: '10px',
            backgroundColor: '#fff3cd',
            borderRadius: '8px',
            marginTop: '10px',
            border: '1px solid #ffc107'
          }}>
            <strong>⌨️ Atalhos do Modo Rápido:</strong>
            <ul style={{ margin: '5px 0', paddingLeft: '20px' }}>
              <li><strong>1</strong> = ✅ OK (Concluído)</li>
              <li><strong>2</strong> = ⚠️ Troca (Necessita troca)</li>
              <li><strong>3</strong> = ⏳ Pendente</li>
              <li><strong>4</strong> = 🚫 Ignorado</li>
              <li><strong>↑↓</strong> = Navegar entre itens</li>
            </ul>
          </div>
        )}
      </div>

      <div className="adicionar-item-section">
        <button 
          onClick={() => setMostrarFormNovoItem(!mostrarFormNovoItem)}
          className="btn-adicionar-item"
          disabled={salvando['adicionar-item']}
        >
          {mostrarFormNovoItem ? '✖️ Cancelar' : '➕ Adicionar Item Customizado'}
        </button>

        {mostrarFormNovoItem && (
          <form onSubmit={handleAdicionarItem} className="form-novo-item">
            <div className="form-row">
              <input
                type="text"
                value={novoItem.nome}
                onChange={(e) => setNovoItem({ ...novoItem, nome: e.target.value })}
                placeholder="Ex: Troca de vela, Ajuste de corrente..."
                required
                className="input-nome-item"
              />
              <select
                value={novoItem.categoria}
                onChange={(e) => setNovoItem({ ...novoItem, categoria: e.target.value })}
                className="select-categoria-item"
              >
                <option value="Geral">Geral</option>
                <option value="Motor">Motor</option>
                <option value="Freios">Freios</option>
                <option value="Pneus">Pneus</option>
                <option value="Suspensão">Suspensão</option>
                <option value="Elétrica">Elétrica</option>
                <option value="Segurança">Segurança</option>
              </select>
              <input
                type="number"
                step="0.01"
                min="0"
                value={novoItem.custo_estimado}
                onChange={(e) => setNovoItem({ ...novoItem, custo_estimado: e.target.value })}
                placeholder="R$ 0,00"
                className="input-custo-item"
              />
              <button type="submit" className="btn-salvar-item" disabled={salvando['adicionar-item']}>
                Salvar
              </button>
            </div>
          </form>
        )}
      </div>

      {Object.entries(itensPorCategoria).map(([categoria, itens]) => {
        // Filtra apenas pendentes no modo rápido
        const itensExibir = modoRapido 
          ? itens.filter(i => i.status === 'pendente')
          : itens
        
        if (modoRapido && itensExibir.length === 0) return null
        
        return (
          <div key={categoria} className="categoria-section">
            <h2 className="categoria-title">{categoria} {modoRapido && `(${itensExibir.length} pendentes)`}</h2>
            <div className="itens-grid">
              {itensExibir.map((item) => (
                <div 
                  key={item.index} 
                  className={`item-card status-${item.status} ${itemFocado === item.index && modoRapido ? 'focado' : ''}`}
                  onClick={() => modoRapido && setItemFocado(item.index)}
                  style={{
                    border: itemFocado === item.index && modoRapido ? '3px solid #007bff' : undefined,
                    boxShadow: itemFocado === item.index && modoRapido ? '0 0 10px rgba(0,123,255,0.5)' : undefined
                  }}
                >
                <div className="item-header">
                  <div className="item-title-wrapper">
                    <h3>{item.nome}</h3>
                  </div>
                  <span 
                    className={`status-badge status-badge-${item.status}`}
                  >
                    {getStatusLabel(item.status)}
                  </span>
                </div>
                
                <div className="item-actions">
                  <div className="status-buttons-container">
                    <div className="status-buttons">
                      <button
                        type="button"
                        className={`btn-status btn-status-pendente ${item.status === 'pendente' ? 'active' : ''}`}
                        onClick={(e) => {
                          e.stopPropagation()
                          handleStatusChange(item.index, 'pendente')
                        }}
                        disabled={salvando[`item-${item.index}`]}
                        title="Ainda não verificado (3)"
                        style={{ color: item.status === 'pendente' ? '#ffffff' : '#2d3748' }}
                      >
                        <span className="btn-icon" style={{ color: 'inherit' }}>⏳</span>
                        <span className="btn-text" style={{ color: 'inherit' }}>Pendente</span>
                        {modoRapido && <span className="btn-shortcut" style={{ color: 'inherit' }}>(3)</span>}
                      </button>
                      <button
                        type="button"
                        className={`btn-status btn-status-ok ${item.status === 'concluido' ? 'active' : ''}`}
                        onClick={(e) => {
                          e.stopPropagation()
                          handleStatusChange(item.index, 'concluido')
                        }}
                        disabled={salvando[`item-${item.index}`]}
                        title="Verificado e sem problemas (1)"
                        style={{ color: item.status === 'concluido' ? '#ffffff' : '#2d3748' }}
                      >
                        <span className="btn-icon" style={{ color: 'inherit' }}>✅</span>
                        <span className="btn-text" style={{ color: 'inherit' }}>OK</span>
                        {modoRapido && <span className="btn-shortcut" style={{ color: 'inherit' }}>(1)</span>}
                      </button>
                      <button
                        type="button"
                        className={`btn-status btn-status-troca ${item.status === 'necessita_troca' ? 'active' : ''}`}
                        onClick={(e) => {
                          e.stopPropagation()
                          handleStatusChange(item.index, 'necessita_troca')
                        }}
                        disabled={salvando[`item-${item.index}`]}
                        title="Precisa de troca/manutenção (2)"
                        style={{ color: item.status === 'necessita_troca' ? '#ffffff' : '#2d3748' }}
                      >
                        <span className="btn-icon" style={{ color: 'inherit' }}>⚠️</span>
                        <span className="btn-text" style={{ color: 'inherit' }}>Troca</span>
                        {modoRapido && <span className="btn-shortcut" style={{ color: 'inherit' }}>(2)</span>}
                      </button>
                      <button
                        type="button"
                        className={`btn-status btn-status-ignorado ${item.status === 'ignorado' ? 'active' : ''}`}
                        onClick={(e) => {
                          e.stopPropagation()
                          handleStatusChange(item.index, 'ignorado')
                        }}
                        disabled={salvando[`item-${item.index}`]}
                        title="Não será verificado nesta revisão (4)"
                        style={{ color: item.status === 'ignorado' ? '#ffffff' : '#2d3748' }}
                      >
                        <span className="btn-icon" style={{ color: 'inherit' }}>🚫</span>
                        <span className="btn-text" style={{ color: 'inherit' }}>Ignorado</span>
                        {modoRapido && <span className="btn-shortcut" style={{ color: 'inherit' }}>(4)</span>}
                      </button>
                    </div>
                  </div>
                  
                  <div className="custo-input-group">
                    <label htmlFor={`custo-${item.index}`}>
                      <span className="label-icon">💰</span>
                      Valor (R$)
                    </label>
                    <div className="custo-input-wrapper">
                      <input
                        id={`custo-${item.index}`}
                        type="number"
                        step="0.01"
                        min="0"
                        value={item.custo_estimado || ''}
                        onChange={(e) => {
                          const valor = parseFloat(e.target.value) || 0
                          handleCustoChange(item.index, valor)
                        }}
                        onBlur={(e) => handleCustoBlur(item.index, e)}
                        placeholder="0,00"
                        disabled={salvando[`item-${item.index}`]}
                        className="input-custo"
                      />
                      <button
                        type="button"
                        onClick={(e) => {
                          e.preventDefault()
                          e.stopPropagation()
                          handleSalvarCusto(item.index)
                        }}
                        disabled={salvando[`item-${item.index}`]}
                        className="btn-salvar-custo"
                        title="Salvar valor"
                      >
                        {salvando[`item-${item.index}`] ? (
                          <span className="spinner"></span>
                        ) : (
                          '💾'
                        )}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
        )
      })}
    </div>
  )
}

export default ChecklistDetalhes


