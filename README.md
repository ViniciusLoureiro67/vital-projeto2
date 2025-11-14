# 🚀 Projeto 2UP – Oficina Vital (Python + NumPy)

Este é o **Projeto 2UP** da disciplina **Laboratório de Programação (Professor Vital)**.  
O sistema simula uma **oficina mecânica real de motos**, permitindo gerenciar motos, checklists de revisão e análises estatísticas usando **NumPy**.

---

## 📦 Funcionalidades principais

### ✅ **1. Cadastro e gerenciamento de motos**

- Placa
- Marca
- Modelo
- Ano
- Cilindradas

### ✅ **2. Registro de checklists de revisão**

Cada checklist possui:

- Data no formato **dd/mm/aaaa**
- Quilometragem (km)
- Itens revisados:
  - ✔️ Concluído
  - ⏳ Pendente
  - ⚠️ Necessita troca (com custo estimado)

### ✅ **3. Histórico completo das revisões**

- Exibição formatada
- Custos totais por revisão
- Quantidade de itens por status

### ✅ **4. Módulo Analytics (NumPy)**

Com o módulo `OficinaAnalytics`, o sistema calcula:

- Soma total dos custos
- Média, máximo e mínimo
- Distribuição de status dos itens
- Regressão linear com `numpy.polyfit`
- Previsão de custo para uma quilometragem futura

### ✅ **5. Menu interativo no terminal**

Permite:

1. Listar motos
2. Buscar por placa
3. Buscar por modelo
4. Ver histórico de revisões
5. Mostrar analytics

---

## 🧠 Tecnologias utilizadas

- **Python 3**
- **Programação Orientada a Objetos (POO)**
- **NumPy** (Data Science / Scientific Computing)
- **Enum**
- **Listas (Coleções)**
- **Módulos organizados em camadas (MVC-lite)**

---

## 📁 Estrutura do Projeto

```
vitalprojeto2/
│
├── main.py
├── modelo/
│   ├── veiculo.py
│   ├── moto.py
│   ├── checklist.py
│   ├── checklist_item.py
│
├── controle/
│   ├── oficina_controller.py
│
└── analytics/
    ├── oficina_analytics.py
```

---

## ▶️ Como rodar o projeto

1. Instale o NumPy:

```bash
pip install numpy
```

2. Execute o sistema:

```bash
python main.py
```

3. Use o menu interativo:

```
1 - Listar motos cadastradas
2 - Buscar moto por PLACA
3 - Buscar motos por MODELO
4 - Ver histórico de revisões de uma moto
5 - Ver resumo de custos (Analytics)
0 - Sair
```

---

## 📊 Exemplo de saída (trecho)

```
=== Resumo de custos (NumPy) ===
Soma total: R$ 2030.00
Média por revisão: R$ 676.67
Maior custo: R$ 980.00
Menor custo: R$ 450.00

=== Estimativa de custo ===
Coeficiente angular (a): -0.011331
Custo previsto para 35000 km: R$ 533.14
```

---

## 🎓 Requisitos atendidos (Professor Vital)

✔️ Herança  
✔️ Polimorfismo  
✔️ Classes abstratas  
✔️ Coleções  
✔️ Exceções  
✔️ NumPy (arrays, estatísticas, polyfit)  
✔️ Estrutura modular  
✔️ Análise científica + previsão

---

## 👤 Autores

**Vinicius Loureiro**  
Projeto feito para fins acadêmicos e inspirado em necessidades reais de uma oficina de motos.

---
