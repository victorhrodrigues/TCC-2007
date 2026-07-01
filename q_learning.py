import core_otimizador
import os
import random
import collections

# =====================================================================
# 1. A ESTRUTURA DO AGENTE DE Q-LEARNING
# =====================================================================
class AgenteQLearning:
    def __init__(self, num_acoes=4, alpha=0.1, gamma=0.9, epsilon=1.0, epsilon_decay=0.995, epsilon_min=0.01):
        self.alpha = alpha          
        self.gamma = gamma          
        self.epsilon = epsilon      
        self.epsilon_decay = epsilon_decay  
        self.epsilon_min = epsilon_min      
        self.num_acoes = num_acoes
        
        # Q-Table baseada em dicionário: chave=(viavel, gargalo, estagnado) -> valor=[Q0, Q1, Q2, Q3]
        self.q_table = collections.defaultdict(lambda: [0.0] * num_acoes)
        self.iteracoes_sem_melhora = 0

    def obter_estado(self, grade):
        """ Extrai a representação discreta (S) do ambiente C++ """
        viavel = 1 if grade.validar_alocacao_completa() else 0
        
        total_custo = grade.calcular_total_penalidades()
        if total_custo == 0:
            gargalo = "NENHUM"
        else:
            gargalo = "SUAVE" # Simplificado para o início do loop
            
        estagnado = 1 if self.iteracoes_sem_melhora > 50 else 0
        return (viavel, gargalo, estagnado)

    def escolher_acao(self, estado):
        """ Política Epsilon-Greedy """
        if random.random() < self.epsilon:
            return random.randint(0, self.num_acoes - 1) # Exploração
        
        valores_q = self.q_table[estado]
        max_q = max(valores_q)
        acoes_com_max_q = [i for i, v in enumerate(valores_q) if v == max_q]
        return random.choice(acoes_com_max_q) # Explotação

    def atualizar_politica(self, estado_antigo, acao, recompensa, estado_novo):
        """ Equação de Bellman """
        q_antigo = self.q_table[estado_antigo][acao]
        max_q_futuro = max(self.q_table[estado_novo])
        self.q_table[estado_antigo][acao] = q_antigo + self.alpha * (recompensa + self.gamma * max_q_futuro - q_antigo)

    def decair_epsilon(self):
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

# =====================================================================
# 2. HEURÍSTICAS DE BAIXO NÍVEL (AS AÇÕES DO AGENTE)
# =====================================================================
def aplicar_heuristica_baixo_nivel(acao, grade, instancia):
    """ Modifica a grade aleatoriamente baseado na ação escolhida pela IA """
    # Para o teste inicial, geramos coordenadas estocásticas
    d = random.randint(0, instancia.qtd_dias - 1)
    p = random.randint(0, instancia.periodos_por_dia - 1)
    s = random.randint(0, instancia.qtd_salas - 1)
    disc = random.randint(0, instancia.qtd_disciplinas - 1)

    if acao == 0: # Move-Lecture básico
        if not grade.espaco_esta_livre(d, p, s):
            grade.remover_aula(d, p, s)
        return grade.alocar_aula(d, p, s, disc)
    
    elif acao == 1: # Esqueleto para Resolve-Bottleneck (Müller)
        return False
    elif acao == 2: # Esqueleto para Targeted Soft-Fix (Lü & Hao)
        return False
    elif acao == 3: # Esqueleto para Ruin-and-Recreate (Geiger)
        return False
        
    return False

# =====================================================================
# 3. CONTEXTO DE EXECUÇÃO E LOOP DE TREINO (TESTE)
# =====================================================================
pasta = "dados"
dataset = "EarlyDatasets"
nome_arquivo = "comp01.ctt.txt"
caminho_instancia = os.path.join(pasta, dataset, nome_arquivo)

instancia = core_otimizador.Instancia()

if core_otimizador.Parser.carregar_ctt(caminho_instancia, instancia):
    print("=" * 60)
    print("INICIANDO TREINAMENTO EXPERIMENTAL DO AGENTE Q-LEARNING")
    print("=" * 60)
    
    grade = core_otimizador.GradeHoraria(instancia)
    agente = AgenteQLearning(num_acoes=4)
    
    custo_anterior = grade.calcular_total_penalidades()
    
    # Rodaremos apenas 100 iterações rápidas para testar o fluxo de aprendizado
    for iteracao in range(1, 101):
        estado_atual = agente.obter_estado(grade)
        acao = agente.escolher_acao(estado_atual)
        
        # Tenta aplicar a modificação física no C++
        alterou = aplicar_heuristica_baixo_nivel(acao, grade, instancia)
        
        # Calcula a consequência (Recompensa R)
        custo_novo = grade.calcular_total_penalidades()
        estado_novo = agente.obter_estado(grade)
        
        if alterou:
            if custo_novo < custo_anterior:
                recompensa = 10.0  # IA reduziu penalidades suaves!
            elif custo_novo > custo_anterior:
                recompensa = -5.0  # Piorou o conforto da grade
            else:
                recompensa = 0.0   # Neutro
        else:
            recompensa = -1.0      # Movimento inválido/bloqueado pelo C++
            
        # Agente processa e aprende
        agente.atualizar_politica(estado_atual, acao, recompensa, estado_novo)
        agente.decair_epsilon()
        custo_anterior = custo_novo
        
        if iteracao % 20 == 0:
            print(f"Iteração {iteracao:03d} | Epsilon: {agente.epsilon:.3f} | Custo Atual: {custo_novo}")
            
    print("\n" + "=" * 60)
    print("Tamanho da Q-Table gerada:", len(agente.q_table))
    print("Mapeamento de Estados Aprendidos:")
    for estado, acoes in agente.q_table.items():
        print(f" -> Estado {estado}: Valores Q {acoes}")
    print("=" * 60)