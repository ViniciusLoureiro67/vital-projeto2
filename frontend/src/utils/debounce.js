/**
 * Função de debounce para limitar chamadas de função
 * Retorna uma função que pode ser cancelada
 */
export function debounce(func, wait) {
  let timeout;
  const executedFunction = function(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
  
  // Adiciona método para cancelar o debounce pendente
  executedFunction.cancel = () => {
    clearTimeout(timeout);
  };
  
  // Adiciona método para executar imediatamente
  executedFunction.flush = (...args) => {
    clearTimeout(timeout);
    func(...args);
  };
  
  return executedFunction;
}

