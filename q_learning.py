import core_otimizador
import os
import random
import collections


# A ESTRUTURA DO AGENTE DE Q-LEARNING
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

        self.lista_tabu = collections.deque(maxlen=20)

    def obter_estado(self, grade):
        """ Extrai a representação discreta (S) do ambiente C++ """
        # 1. Viabilidade (0 ou 1)
        viavel = 1 if grade.validar_alocacao_completa() else 0
        
        # 2. Gargalo Quantitativo (Discretização do Custo)
        # Vamos dividir o custo em 5 níveis (0 a 4)
        total_custo = grade.calcular_total_penalidades()
        if total_custo == 0: custo_bin = 0
        elif total_custo < 500: custo_bin = 1
        elif total_custo < 1000: custo_bin = 2
        elif total_custo < 1500: custo_bin = 3
        else: custo_bin = 4
            
        # 3. Estagnação
        estagnado = 1 if self.iteracoes_sem_melhora > 50 else 0
        
        return (viavel, custo_bin, estagnado)

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

#  Geração gulosa - tenta preencher a grade o máximo possível e caso sobre aulas passa esse id
def gerar_solucao_inicial_gulosa(grade, instancia):
    print("\n[Fase Construtiva] Gerando solução inicial gulosa...")
    aulas_pendentes = []
    
    # Percorre todas as disciplinas do C++
    for disc_idx in range(instancia.qtd_disciplinas):
        disc = instancia.disciplinas[disc_idx]
        
        # Tenta alocar o número de aulas exigidas para cada disciplina
        for _ in range(disc.num_aulas):
            alocou = False
            for d in range(instancia.qtd_dias):
                for p in range(instancia.periodos_por_dia):
                    for s in range(instancia.qtd_salas):
                        # Se o C++ permitir, aloca
                        if grade.alocar_aula(d, p, s, disc_idx):
                            alocou = True
                            break
                    if alocou: break
                if alocou: break
            
            # Se varreu a grade inteira e não achou vaga viável, vai para a fila
            if not alocou:
                aulas_pendentes.append(disc_idx)
                
    print(f" -> Aulas que ficaram de fora (Violação H1): {len(aulas_pendentes)}")
    return aulas_pendentes

# HEURÍSTICAS DE BAIXO NÍVEL (AS AÇÕES DO AGENTE)
def aplicar_heuristica_baixo_nivel(acao, grade, instancia, aulas_pendentes, agente):
    """ Modifica a grade protegendo a integridade dos dados (Sem vazar aulas) """
    
    if acao == 0: 
        # [A0] MOVE-LECTURE SEGURO
        if aulas_pendentes: return False 
        d1, p1, s1 = random.randint(0, instancia.qtd_dias - 1), random.randint(0, instancia.periodos_por_dia - 1), random.randint(0, instancia.qtd_salas - 1)
        disc_alvo = grade.obter_disciplina_na_gaveta(d1, p1, s1)
        if disc_alvo == -1: return False
        
        d2, p2, s2 = random.randint(0, instancia.qtd_dias - 1), random.randint(0, instancia.periodos_por_dia - 1), random.randint(0, instancia.qtd_salas - 1)
        if grade.espaco_esta_livre(d2, p2, s2):
            grade.remover_aula(d1, p1, s1)
            if grade.alocar_aula(d2, p2, s2, disc_alvo): return True
            else:
                grade.alocar_aula(d1, p1, s1, disc_alvo)
        return False
    
    elif acao == 1: 
        # [A1] RESOLVE-BOTTLENECK (Müller)
        if aulas_pendentes: return False
        melhor_reducao, pior_d, pior_p, pior_s, pior_disc = 0, -1, -1, -1, -1
        custo_atual_base = grade.calcular_total_penalidades()

        for _ in range(10):
            d, p, s = random.randint(0, instancia.qtd_dias - 1), random.randint(0, instancia.periodos_por_dia - 1), random.randint(0, instancia.qtd_salas - 1)
            disc = grade.obter_disciplina_na_gaveta(d, p, s)
            if disc != -1:
                grade.remover_aula(d, p, s)
                reducao = custo_atual_base - grade.calcular_total_penalidades()
                grade.alocar_aula(d, p, s, disc)
                if reducao > melhor_reducao:
                    melhor_reducao, pior_d, pior_p, pior_s, pior_disc = reducao, d, p, s, disc

        if pior_disc == -1 or melhor_reducao == 0: return False

        grade.remover_aula(pior_d, pior_p, pior_s) 
        melhor_custo_destino, melhor_destino = float('inf'), None
        for _ in range(10):
            d_v, p_v, s_v = random.randint(0, instancia.qtd_dias - 1), random.randint(0, instancia.periodos_por_dia - 1), random.randint(0, instancia.qtd_salas - 1)
            if grade.espaco_esta_livre(d_v, p_v, s_v) and grade.alocar_aula(d_v, p_v, s_v, pior_disc):
                custo_teste = grade.calcular_total_penalidades()
                if custo_teste < melhor_custo_destino:
                    melhor_custo_destino, melhor_destino = custo_teste, (d_v, p_v, s_v)
                grade.remover_aula(d_v, p_v, s_v)

        if melhor_destino and melhor_custo_destino < custo_atual_base:
            grade.alocar_aula(*melhor_destino, pior_disc)
            return True
        grade.alocar_aula(pior_d, pior_p, pior_s, pior_disc)
        return False
                
    elif acao == 2: 
        # [A2] RUIN-AND-RECREATE (Geiger)
        if not aulas_pendentes: return False 
        disc_alvo = aulas_pendentes[0] 
        d, p, s = random.randint(0, instancia.qtd_dias - 1), random.randint(0, instancia.periodos_por_dia - 1), random.randint(0, instancia.qtd_salas - 1)
        disc_na_gaveta = grade.obter_disciplina_na_gaveta(d, p, s)
        
        if disc_na_gaveta != -1:
            grade.remover_aula(d, p, s)
            if grade.alocar_aula(d, p, s, disc_alvo):
                aulas_pendentes.pop(0); aulas_pendentes.append(disc_na_gaveta); return True
            grade.alocar_aula(d, p, s, disc_na_gaveta)
            return False
        if grade.alocar_aula(d, p, s, disc_alvo):
            aulas_pendentes.pop(0); return True
        return False
        
    elif acao == 3:
        # [A3] TABU-SWAP
        if aulas_pendentes: return False 
        d1, p1, s1 = random.randint(0, instancia.qtd_dias-1), random.randint(0, instancia.periodos_por_dia-1), random.randint(0, instancia.qtd_salas-1)
        d2, p2, s2 = random.randint(0, instancia.qtd_dias-1), random.randint(0, instancia.periodos_por_dia-1), random.randint(0, instancia.qtd_salas-1)
        disc1, disc2 = grade.obter_disciplina_na_gaveta(d1, p1, s1), grade.obter_disciplina_na_gaveta(d2, p2, s2)
        
        if disc1 == -1 or disc2 == -1 or disc1 == disc2: return False
        movimento = tuple(sorted([disc1, disc2]))
        if movimento in agente.lista_tabu: return False 

        custo_antes = grade.calcular_total_penalidades()
        grade.remover_aula(d1, p1, s1); grade.remover_aula(d2, p2, s2)
        
        if grade.alocar_aula(d1, p1, s1, disc2) and grade.alocar_aula(d2, p2, s2, disc1):
            if grade.calcular_total_penalidades() < custo_antes:
                agente.lista_tabu.append(movimento); return True
                
        grade.remover_aula(d1, p1, s1); grade.remover_aula(d2, p2, s2)
        if disc1 != -1: grade.alocar_aula(d1, p1, s1, disc1)
        if disc2 != -1: grade.alocar_aula(d2, p2, s2, disc2)
        return False

# CONTEXTO DE EXECUÇÃO E LOOP DE TREINO (TESTE)
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
    agente = AgenteQLearning(num_acoes=4, epsilon_decay=0.998)
    
    # 1. GERAÇÃO INICIAL
    aulas_pendentes = gerar_solucao_inicial_gulosa(grade, instancia)
    qtd_pendentes_anterior = len(aulas_pendentes)
    custo_anterior = grade.calcular_total_penalidades() # <--- Captura o custo inicial da grade
    total_exigido = sum(d.num_aulas for d in instancia.disciplinas)
    print(f"Total de aulas exigidas pelo arquivo: {total_exigido}")

    for iteracao in range(1, 10001): 
        estado_atual = agente.obter_estado(grade)
        acao = agente.escolher_acao(estado_atual)
        
        # 2. APLICA A AÇÃO
        alterou = aplicar_heuristica_baixo_nivel(acao, grade, instancia, aulas_pendentes, agente)

        # 3. ATUALIZA AS MÉTRICAS PARA O ÁRBITRO E PARA O PRINT
        qtd_pendentes_novo = len(aulas_pendentes)
        custo_novo = grade.calcular_total_penalidades() # <--- Agora o custo é calculado todo turno!
        estado_novo = agente.obter_estado(grade)
        
        # 4. ÁRBITRO HÍBRIDO (Avalia viabilidade primeiro, estética depois)
        if alterou:
            if estado_atual[0] == 0: # Fase 1 (Grade Inválida)
                if qtd_pendentes_novo < qtd_pendentes_anterior:
                    recompensa = 10.0  
                elif qtd_pendentes_novo > qtd_pendentes_anterior:
                    recompensa = -5.0  
                else:
                    recompensa = 0.0   
            else: # Fase 2 (Grade Válida)
                if custo_novo < custo_anterior:
                    recompensa = 1.0   # BÔNUS: A IA reduziu o custo suave!
                elif custo_novo > custo_anterior:
                    recompensa = -1.0  
                else:
                    recompensa = -0.1  # Punição leve por estagnar
        else:
            recompensa = -1.0      
            
        # 5. APRENDIZADO
        agente.atualizar_politica(estado_atual, acao, recompensa, estado_novo)
        agente.decair_epsilon()
        
        # Salva o estado atual para comparar na próxima iteração
        qtd_pendentes_anterior = qtd_pendentes_novo
        custo_anterior = custo_novo 
        
        # TERMINAL DE ACOMPANHAMENTO (Mantido exatamente como o seu)
        if iteracao % 20 == 0:
            status = "VÁLIDA" if len(aulas_pendentes) == 0 else "INVÁLIDA"
            print(f"Iter {iteracao:04d} | Eps: {agente.epsilon:.3f} | Pendentes: {len(aulas_pendentes)} | Status: {status} | Custo: {custo_novo}")
            
    print("\n" + "=" * 60)
    print("Tamanho da Q-Table gerada:", len(agente.q_table))
    print("Mapeamento de Estados Aprendidos:")
    for estado, acoes in agente.q_table.items():
        print(f" -> Estado {estado}: Valores Q {acoes}")
    print("=" * 60)