import core_otimizador
import os
import random
import collections
import copy
import argparse
import time
import json


# AÇÕES QUE PODEM AGIR EM CADA FASE (máscara de ações), indexadas por viavel
ACOES_POR_FASE = {
    0: [2, 5],        # Fase 1 (grade incompleta): reconstrução reativa (Geiger) ou reparo por conflitos (Müller)
    1: [0, 1, 3, 4, 6],  # Fase 2 (grade completa): ações de otimização do custo
}


# A ESTRUTURA DO AGENTE DE Q-LEARNING
class AgenteQLearning:
    def __init__(self, num_acoes=4, alpha=0.1, gamma=0.9, epsilon=1.0, epsilon_min=0.01):
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon_inicial = epsilon
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.num_acoes = num_acoes
        
        # Q-Table baseada em dicionário: chave=(viavel, gargalo, estagnado) -> valor=[Q0, Q1, Q2, Q3]
        self.q_table = collections.defaultdict(lambda: [0.0] * num_acoes)
        self.iteracoes_sem_melhora = 0
        self.custo_referencia = None  # custo da 1ª grade completa: base das faixas da Fase 2

        self.lista_tabu = collections.deque(maxlen=20)
        self.cbs = collections.Counter()  # Conflict-based Statistics (Müller): vezes que cada colocação desalocou cada aula

    def obter_estado(self, grade, qtd_pendentes, custo):
        """ Extrai a representação discreta (S) do ambiente C++ """
        # 1. Viabilidade (0 ou 1)
        viavel = 1 if grade.validar_alocacao_completa() else 0

        # 2. Nível: na Fase 1, quantas aulas faltam; na Fase 2, o custo em relação ao da 1ª grade completa
        if not viavel:
            if qtd_pendentes <= 2: nivel = 1
            elif qtd_pendentes <= 5: nivel = 2
            elif qtd_pendentes <= 10: nivel = 3
            else: nivel = 4
        else:
            if self.custo_referencia is None:
                self.custo_referencia = max(custo, 1)  # 1ª grade completa: início da Fase 2
            razao = custo / self.custo_referencia
            if custo == 0: nivel = 0
            elif razao <= 0.3: nivel = 1
            elif razao <= 0.5: nivel = 2
            else: nivel = 3

        # 3. Estagnação: mais de 50 movimentos sem progresso (na Fase 2, o último episódio inteiro sem melhora)
        estagnado = 1 if self.iteracoes_sem_melhora > 50 else 0

        return (viavel, nivel, estagnado) # trocar estagnado para 0 para testar sem o estado

    def escolher_acao(self, estado):
        """ Política Epsilon-Greedy restrita às ações que podem agir na fase do estado """
        validas = ACOES_POR_FASE[estado[0]]
        if random.random() < self.epsilon:
            return random.choice(validas) # Exploração

        valores_q = self.q_table[estado]
        max_q = max(valores_q[a] for a in validas)
        acoes_com_max_q = [a for a in validas if valores_q[a] == max_q]
        return random.choice(acoes_com_max_q) # Explotação

    def atualizar_politica(self, estado_antigo, acao, recompensa, estado_novo):
        """ Equação de Bellman (o máximo futuro considera só as ações válidas no novo estado) """
        q_antigo = self.q_table[estado_antigo][acao]
        max_q_futuro = max(self.q_table[estado_novo][a] for a in ACOES_POR_FASE[estado_novo[0]])
        self.q_table[estado_antigo][acao] = q_antigo + self.alpha * (recompensa + self.gamma * max_q_futuro - q_antigo)

    def atualizar_epsilon(self, progresso):
        """ Decaimento geométrico pela fração do orçamento já usada: ε_inicial em 0, ε_min em 1 """
        self.epsilon = max(self.epsilon_min,
                           self.epsilon_inicial * (self.epsilon_min / self.epsilon_inicial) ** progresso)

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


def aulas_por_disciplina(grade, instancia):
    """ Para cada disciplina, as posições (d, p, s) das suas aulas, na ordem dia -> período -> sala """
    aulas = collections.defaultdict(list)
    for d, p, s, disc in grade.listar_aulas():  # uma chamada ao C++ em vez de uma por posição
        aulas[disc].append((d, p, s))
    return aulas


def trocar_sala(grade, d, p, s_de, s_para):
    """ No período (d, p), a aula da sala s_de passa para a sala s_para, e o ocupante de s_para, se houver,
    passa para s_de. Sempre viável: H3 e H4 só dependem do período, e a troca mantém a H2.
    Chamar de novo com as salas invertidas desfaz a troca """
    disc = grade.obter_disciplina_na_gaveta(d, p, s_de)
    ocupante = grade.obter_disciplina_na_gaveta(d, p, s_para)
    grade.remover_aula(d, p, s_de)
    ok = True
    if ocupante != -1:
        grade.remover_aula(d, p, s_para)
        ok = grade.alocar_aula(d, p, s_de, ocupante)
    ok = grade.alocar_aula(d, p, s_para, disc) and ok
    if not ok:  # não deveria acontecer; se acontecer, para em vez de perder uma aula em silêncio
        raise RuntimeError(f"troca de sala recusada em ({d}, {p}): sala {s_de} <-> sala {s_para}")


def mover_aula(grade, d, p, s, d2, p2, s2):
    """ Leva a aula de (d, p, s) para (d2, p2, s2); se o destino estiver ocupado, o ocupante vai para (d, p, s).
    O C++ confere H2, H3 e H4 das duas aulas. Devolve True se deu certo; se não, deixa a grade como estava.
    Depois de um movimento que deu certo, chamar com origem e destino invertidos desfaz """
    a = grade.obter_disciplina_na_gaveta(d, p, s)
    b = grade.obter_disciplina_na_gaveta(d2, p2, s2)
    grade.remover_aula(d, p, s)
    if b != -1:
        grade.remover_aula(d2, p2, s2)
    if grade.alocar_aula(d2, p2, s2, a):
        if b == -1 or grade.alocar_aula(d, p, s, b):
            return True
        grade.remover_aula(d2, p2, s2)  # o ocupante não pode ir para a origem: desfaz
    if b != -1:
        grade.alocar_aula(d2, p2, s2, b)
    grade.alocar_aula(d, p, s, a)
    return False

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
        # [A2] RECONSTRUÇÃO REATIVA (Geiger §3.3)
        if not aulas_pendentes: return False
        # Refaz a grade do zero, com as aulas pendentes primeiro; o C++ só troca a grade se não ficarem
        # mais aulas de fora do que agora. A semente vem do gerador do Python (uma seed só por execução)
        aceitou, nao_alocadas = grade.reconstruir(aulas_pendentes, random.getrandbits(32), len(aulas_pendentes))
        if aceitou:
            aulas_pendentes[:] = nao_alocadas
        return aceitou
        
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
        
        # Remove as duas antes de testar
        grade.remover_aula(d1, p1, s1)
        grade.remover_aula(d2, p2, s2)
        
        # Tenta alocar isoladamente (executa ambas e guarda o resultado booleano do C++)
        alocou_disc2 = grade.alocar_aula(d1, p1, s1, disc2)
        alocou_disc1 = grade.alocar_aula(d2, p2, s2, disc1)
        
        if alocou_disc2 and alocou_disc1:
            if grade.calcular_total_penalidades() < custo_antes:
                agente.lista_tabu.append(movimento)
                return True
                
        # Rollback seguro: Só remove o que realmente o C++ conseguiu alocar
        if alocou_disc2: grade.remover_aula(d1, p1, s1)
        if alocou_disc1: grade.remover_aula(d2, p2, s2)
        
        # Devolve para as posições originais
        if disc1 != -1: grade.alocar_aula(d1, p1, s1, disc1)
        if disc2 != -1: grade.alocar_aula(d2, p2, s2, disc2)
        return False
    elif acao == 4:
        # [A4] AÇÃO DE SALA (Room Stability Move de Müller §4.3; ClassToSameRoom e ClassToOtherRoom do QuikFix)
        # Escolhe uma disciplina penalizada em S1 ou S2 e testa pôr todas as suas aulas numa mesma sala, cada
        # aula no seu período, trocando com o ocupante quando a sala estiver ocupada. Só mexe em S1 e S2
        if aulas_pendentes: return False
        aulas = aulas_por_disciplina(grade, instancia)
        penalizadas = [c for c, posicoes in aulas.items()
                       if len({s for _, _, s in posicoes}) > 1                                  # S2: mais de uma sala
                       or any(agente.alunos[c] > agente.capacidade[s] for _, _, s in posicoes)]  # S1: sala pequena
        if not penalizadas: return False
        disc_alvo = random.choice(sorted(penalizadas))

        # Salas candidatas: as que a disciplina já usa (S2) e até 3 outras em que a turma cabe (S1)
        usadas = sorted({s for _, _, s in aulas[disc_alvo]})
        cabem = [s for s in range(instancia.qtd_salas)
                 if s not in usadas and agente.capacidade[s] >= agente.alunos[disc_alvo]]
        candidatas = usadas + random.sample(cabem, min(3, len(cabem)))

        custo_atual_base = grade.calcular_total_penalidades()
        melhor_custo, melhor_sala = custo_atual_base, None
        for s_alvo in candidatas:
            movidas = [(d, p, s) for d, p, s in aulas[disc_alvo] if s != s_alvo]
            for d, p, s in movidas:
                trocar_sala(grade, d, p, s, s_alvo)
            custo_teste = grade.calcular_total_penalidades()
            for d, p, s in movidas:
                trocar_sala(grade, d, p, s_alvo, s)  # desfaz o teste
            if custo_teste < melhor_custo:
                melhor_custo, melhor_sala = custo_teste, s_alvo

        # Só aceita se reduziu o custo
        if melhor_sala is None: return False
        for d, p, s in aulas[disc_alvo]:
            if s != melhor_sala:
                trocar_sala(grade, d, p, s, melhor_sala)
        return True

    elif acao == 5:
        # [A5] REPARO POR CONFLITOS (IFS + CBS, inspirado em Müller §3.1)
        if not aulas_pendentes: return False

        # 1. Variável: uma das aulas pendentes mais difíceis (menor domínio / nº de disciplinas em conflito)
        menor = min(agente.dificuldade[c] for c in aulas_pendentes)
        disc_alvo = random.choice([c for c in aulas_pendentes if agente.dificuldade[c] == menor])

        # 2. Valor: posição permitida (H4) com menos aulas a desalocar, cada conflito pesado pelo histórico (CBS)
        melhor_peso, melhores = float('inf'), []
        for d, p, s, conflitos in grade.conflitos_por_posicao(disc_alvo):
            peso = sum(1 + agente.cbs[(disc_alvo, d, p, s, b, s_b)] for b, s_b in conflitos)
            if peso < melhor_peso:
                melhor_peso, melhores = peso, [(d, p, s, conflitos)]
            elif peso == melhor_peso:
                melhores.append((d, p, s, conflitos))
        if not melhores: return False
        d, p, s, conflitos = random.choice(melhores)

        # 3. Desaloca todas as aulas em conflito (voltam para a fila) e coloca a aula escolhida
        for b, s_b in conflitos:
            grade.remover_aula(d, p, s_b)
            aulas_pendentes.append(b)
        aulas_pendentes.remove(disc_alvo)
        if grade.alocar_aula(d, p, s, disc_alvo):
            for b, s_b in conflitos:
                agente.cbs[(disc_alvo, d, p, s, b, s_b)] += 1  # registra quem foi desalocado por essa colocação
            return True

        # Proteção: se o C++ recusar (não deveria, os conflitos já saíram), desfaz tudo
        aulas_pendentes.append(disc_alvo)
        for b, s_b in conflitos:
            grade.alocar_aula(d, p, s_b, b)
            aulas_pendentes.remove(b)
        return False

    elif acao == 6:
        # [A6] AÇÃO DE PERÍODO (Curriculum Compactness Move e Min Working Days Move de Müller §4.3;
        # CompactCurricula e ClassToAvailablePeriod do QuikFix). Escolhe uma aula com um problema que só se
        # resolve mudando de período (S4, S3 ou S1) e testa levá-la só para os períodos que o resolvem
        if aulas_pendentes: return False
        aulas = aulas_por_disciplina(grade, instancia)
        D, P = instancia.qtd_dias, instancia.periodos_por_dia

        ocupados = collections.defaultdict(set)  # currículo -> períodos (d, p) em que ele tem aula
        for c, posicoes in aulas.items():
            for q in agente.curriculos[c]:
                ocupados[q].update((d, p) for d, p, _ in posicoes)

        alvos = []  # (tipo, aula (d, p, s), disciplina, currículo)
        for c, posicoes in aulas.items():
            dias_c = collections.Counter(d for d, _, _ in posicoes)
            abaixo_do_minimo = len(dias_c) < agente.dias_minimos[c]
            for d, p, s in posicoes:
                for q in agente.curriculos[c]:                      # S4: aula isolada no currículo q
                    if (d, p - 1) not in ocupados[q] and (d, p + 1) not in ocupados[q]:
                        alvos.append(("S4", (d, p, s), c, q))
                if abaixo_do_minimo and dias_c[d] >= 2:             # S3: dia com 2+ aulas da disciplina
                    alvos.append(("S3", (d, p, s), c, None))
                if agente.alunos[c] > agente.capacidade[s]:         # S1: turma maior que a sala
                    alvos.append(("S1", (d, p, s), c, None))
        if not alvos: return False
        tipo, (d, p, s), disc_alvo, q = random.choice(alvos)

        # Períodos de destino que resolvem o problema (fora os que a disciplina já ocupa)
        periodos_disc = {(d2, p2) for d2, p2, _ in aulas[disc_alvo]}
        if tipo == "S4":    # colado em outra aula do currículo q
            outros = ocupados[q] - {(d, p)}
            destinos = {(d2, p2 + k) for d2, p2 in outros for k in (-1, 1) if 0 <= p2 + k < P} - outros
        elif tipo == "S3":  # num dia em que a disciplina não tem aula
            dias = {d2 for d2, _ in periodos_disc}
            destinos = {(d2, p2) for d2 in range(D) if d2 not in dias for p2 in range(P)}
        else:               # S1: qualquer outro período
            destinos = {(d2, p2) for d2 in range(D) for p2 in range(P)}
        destinos -= periodos_disc
        if not destinos: return False

        # Até 10 períodos de destino. Em cada um, as salas vão na ordem de encaixe: primeiro as que comportam a
        # turma (entre elas, as livres antes das que exigem troca, depois as que a disciplina já usa, e a menor);
        # as salas pequenas ficam por último. Vale a 1ª sala em que o movimento é viável, com troca do ocupante
        # se a sala estiver ocupada (o C++ confere H3 e H4 das duas aulas): no máximo 1 avaliação por período
        usadas = {s2 for _, _, s2 in aulas[disc_alvo]}
        turma = agente.alunos[disc_alvo]
        custo_atual_base = grade.calcular_total_penalidades()
        melhor_custo, melhor_destino = custo_atual_base, None
        for d2, p2 in random.sample(sorted(destinos), min(10, len(destinos))):
            # H3 e H4 da aula só dependem do período: com H4 ou com 2+ aulas em conflito, nenhuma sala serve;
            # com uma aula em conflito, só a troca com ela pode dar certo (as outras salas falhariam de qualquer jeito)
            if grade.esta_indisponivel(disc_alvo, d2, p2): continue
            ocupantes = [grade.obter_disciplina_na_gaveta(d2, p2, r) for r in range(instancia.qtd_salas)]
            em_conflito = [r for r, o in enumerate(ocupantes) if o != -1 and o in agente.conflita[disc_alvo]]
            if len(em_conflito) > 1: continue
            ordem_salas = em_conflito or sorted(range(instancia.qtd_salas),
                                                key=lambda r: (max(0, turma - agente.capacidade[r]),  # não estourar a S1
                                                               ocupantes[r] != -1,                    # livre antes de troca
                                                               r not in usadas,                       # S2
                                                               agente.capacidade[r]))                 # a menor que comporta
            for s2 in ordem_salas:
                if mover_aula(grade, d, p, s, d2, p2, s2):
                    custo_teste = grade.calcular_total_penalidades()
                    if not mover_aula(grade, d2, p2, s2, d, p, s):  # desfaz o teste (não deveria falhar)
                        raise RuntimeError(f"não foi possível desfazer o movimento ({d}, {p}, {s}) -> ({d2}, {p2}, {s2})")
                    if custo_teste < melhor_custo:
                        melhor_custo, melhor_destino = custo_teste, (d2, p2, s2)
                    break  # a 1ª sala viável representa o período

        # Só aceita se reduziu o custo
        if melhor_destino is None: return False
        mover_aula(grade, d, p, s, *melhor_destino)
        return True

# PARÂMETROS DA EXECUÇÃO (linha de comando)
def ler_argumentos():
    parser = argparse.ArgumentParser(description="Hiper-heurística com Q-Learning para o CB-CTT (ITC-2007)")
    parser.add_argument("instancia", nargs="?", default="comp01", help="ex.: comp05")
    parser.add_argument("--dataset", default="EarlyDatasets")
    parser.add_argument("--seed", type=int, help="sem valor, sorteia uma e mostra na tela")
    parser.add_argument("--tempo", type=float, default=65.0, help="limite em segundos (benchmark ITC: 65)")
    parser.add_argument("--iteracoes", type=int, help="para por iterações em vez de tempo (execução repetível)")
    parser.add_argument("--saida", help="padrão: resultados/<dataset>/<instancia>_seed<seed>.sol")
    parser.add_argument("--politica", choices=["qlearning", "aleatoria"], default="qlearning",
                        help="aleatoria: escolhe ao acaso entre as ações válidas (ε fixo em 1), para comparação")
    parser.add_argument("--episodio", type=int, default=1,
                        help="Fase 2: movimentos por decisão do agente (1 = decide a cada movimento)")
    return parser.parse_args()

# SAÍDA NO FORMATO DA COMPETIÇÃO
def salvar_solucao_itc(caminho, grade, instancia):
    """ Uma linha 'disciplina sala dia periodo' por aula: o formato lido pelo validador oficial """
    os.makedirs(os.path.dirname(caminho) or ".", exist_ok=True)
    with open(caminho, "w") as arquivo:
        for d in range(instancia.qtd_dias):
            for p in range(instancia.periodos_por_dia):
                for s in range(instancia.qtd_salas):
                    disc = grade.obter_disciplina_na_gaveta(d, p, s)
                    if disc != -1:
                        arquivo.write(f"{instancia.disciplinas[disc].id} {instancia.salas[s].id} {d} {p}\n")

# FUNÇÃO DE RECOMPENSA (proporcional ao progresso)
PENALIDADE_SEM_PROGRESSO = -0.1  # a ação falhou ou não mudou nada: só gastou tempo
LIMITE_FASE2 = 5.0               # teto da Fase 2, abaixo do +10 de uma aula reparada (viabilidade vem primeiro)

def calcular_recompensa(estado, alterou, pend_anterior, pend_novo, custo_anterior, custo_novo):
    """ Retorna (recompensa, houve_progresso) """
    if estado[0] == 0:  # Fase 1 (grade incompleta): progresso = aulas que saíram da fila
        progresso = pend_anterior - pend_novo
        if not alterou or progresso == 0:
            return PENALIDADE_SEM_PROGRESSO, False
        if progresso > 0:
            return 10.0 * progresso, True    # +10 por aula alocada
        return 5.0 * progresso, False        # −5 por aula devolvida à fila

    # Fase 2 (grade completa): progresso = queda percentual do custo
    variacao = 100.0 * (custo_anterior - custo_novo) / max(custo_anterior, 1)
    if not alterou or variacao == 0:
        return PENALIDADE_SEM_PROGRESSO, False
    return max(-LIMITE_FASE2, min(LIMITE_FASE2, variacao)), variacao > 0

# CONTEXTO DE EXECUÇÃO E LOOP DE TREINO
def main():
    args = ler_argumentos()
    inicio = time.perf_counter()  # o relógio conta tudo: leitura, construção gulosa e busca

    # SEMENTE: sorteada uma única vez; toda a aleatoriedade está no Python (o núcleo C++ não sorteia nada)
    seed = args.seed if args.seed is not None else random.randrange(1, 1_000_000)
    random.seed(seed)

    nome = args.instancia.removesuffix(".ctt.txt")
    caminho_instancia = os.path.join("dados", args.dataset, nome + ".ctt.txt")
    caminho_saida = args.saida or os.path.join("resultados", args.dataset, f"{nome}_seed{seed}.sol")
    criterio = f"{args.iteracoes} iterações" if args.iteracoes else f"{args.tempo:.0f} s"

    instancia = core_otimizador.Instancia()
    if not core_otimizador.Parser.carregar_ctt(caminho_instancia, instancia):
        print(f"[ERRO] Não foi possível abrir {caminho_instancia}")
        return

    print("=" * 60)
    print(f"Q-LEARNING | instância {nome} | seed {seed} | parada: {criterio} | política: {args.politica}")
    print("=" * 60)

    grade = core_otimizador.GradeHoraria(instancia)
    agente = AgenteQLearning(num_acoes=7)

    # Dificuldade de cada disciplina para a IFS: domínio pequeno e muitos conflitos = difícil (estática, calculada uma vez)
    agente.dificuldade = [grade.tamanho_dominio(c) / max(1, grade.grau_conflitos(c)) for c in range(instancia.qtd_disciplinas)]

    # Turma de cada disciplina e capacidade de cada sala, usadas pela ação de sala (fixas, lidas uma vez)
    agente.alunos = [d.num_alunos for d in instancia.disciplinas]
    agente.capacidade = [s.capacidade for s in instancia.salas]
    agente.dias_minimos = [d.dias_minimos for d in instancia.disciplinas]  # usado pela ação de período

    # Currículos de cada disciplina (relação N:N, vinda do C++), usados pela ação de período
    agente.curriculos = [grade.curriculos_de(c) for c in range(instancia.qtd_disciplinas)]

    # Disciplinas em conflito com cada uma (mesmo professor ou currículo em comum: H3), para a ação de período
    professor = [d.id_professor for d in instancia.disciplinas]
    agente.conflita = [{o for o in range(instancia.qtd_disciplinas)
                        if professor[o] == professor[c] or set(agente.curriculos[o]) & set(agente.curriculos[c])}
                       for c in range(instancia.qtd_disciplinas)]

    if args.politica == "aleatoria":
        agente.epsilon_inicial = agente.epsilon_min = 1.0  # ε fica em 1 durante toda a execução

    # 1. GERAÇÃO INICIAL
    aulas_pendentes = gerar_solucao_inicial_gulosa(grade, instancia)
    custo_anterior = grade.calcular_total_penalidades()
    total_exigido = sum(d.num_aulas for d in instancia.disciplinas)
    print(f"Total de aulas exigidas pelo arquivo: {total_exigido}")

    # Tamanho dinâmico da Lista Tabu baseado no tamanho da instância
    agente.lista_tabu = collections.deque(maxlen=max(20, int(total_exigido * 0.1)))

    # ELITISMO: melhor grade em ordem lexicográfica (aulas pendentes, custo), como em Geiger (§4.1)
    melhor = (len(aulas_pendentes), custo_anterior)
    melhor_grade = copy.deepcopy(grade)  # cópia feita no C++
    melhor_em = time.perf_counter() - inicio  # segundo em que a melhor solução foi encontrada
    viavel_em = None  # (iteração, segundos) em que a grade ficou completa pela primeira vez
    escolhas = {0: collections.Counter(), 1: collections.Counter()}  # decisões em cada fase (na Fase 2, episódios)
    movimentos_fase2 = collections.Counter()  # Fase 2: movimentos aplicados, por ação
    melhoras_fase2 = collections.Counter()    # Fase 2: movimentos que baixaram o custo, por ação
    proximo_log = 0.05

    # EPISÓDIOS: na Fase 1 cada decisão vale 1 movimento; na Fase 2, --episodio movimentos (Zhang, Ng et al., 2025)
    estado_atual = agente.obter_estado(grade, len(aulas_pendentes), custo_anterior)
    restantes = 0  # movimentos que faltam no episódio atual (0 = hora de decidir)

    iteracao = 0
    while True:
        # CRITÉRIO DE PARADA: fração do orçamento (tempo ou iterações) já usada
        if args.iteracoes:
            progresso = iteracao / args.iteracoes
        else:
            progresso = (time.perf_counter() - inicio) / args.tempo
        if progresso >= 1:
            break
        iteracao += 1

        # 2. DECISÃO: só no início de cada episódio
        if restantes == 0:
            acao = agente.escolher_acao(estado_atual)
            escolhas[estado_atual[0]][acao] += 1
            restantes = args.episodio if estado_atual[0] == 1 else 1
            pend_inicio, custo_inicio, alterou_ep = len(aulas_pendentes), custo_anterior, False

        # 3. APLICA A AÇÃO (um movimento)
        alterou = aplicar_heuristica_baixo_nivel(acao, grade, instancia, aulas_pendentes, agente)
        alterou_ep = alterou_ep or alterou
        restantes -= 1

        # 4. ATUALIZA AS MÉTRICAS a cada movimento (o elitismo não espera o fim do episódio)
        qtd_pendentes_novo = len(aulas_pendentes)
        custo_novo = grade.calcular_total_penalidades()
        if estado_atual[0] == 1:
            movimentos_fase2[acao] += 1
            if custo_novo < custo_anterior:
                melhoras_fase2[acao] += 1

        if (qtd_pendentes_novo, custo_novo) < melhor:
            melhor = (qtd_pendentes_novo, custo_novo)
            melhor_grade = copy.deepcopy(grade)
            melhor_em = time.perf_counter() - inicio
        if qtd_pendentes_novo == 0 and viavel_em is None:
            viavel_em = (iteracao, time.perf_counter() - inicio)

        # 5. FIM DO EPISÓDIO: RECOMPENSA, ESTAGNAÇÃO E APRENDIZADO
        if restantes == 0:
            recompensa, houve_progresso = calcular_recompensa(estado_atual, alterou_ep, pend_inicio,
                                                              qtd_pendentes_novo, custo_inicio, custo_novo)
            if houve_progresso:
                agente.iteracoes_sem_melhora = 0
            else:
                agente.iteracoes_sem_melhora += args.episodio if estado_atual[0] == 1 else 1
            # O estado novo já sai com a estagnação atualizada, e a próxima decisão é tomada nele
            estado_novo = agente.obter_estado(grade, qtd_pendentes_novo, custo_novo)
            agente.atualizar_politica(estado_atual, acao, recompensa, estado_novo)
            agente.atualizar_epsilon(progresso)
            estado_atual = estado_novo

        custo_anterior = custo_novo

        # TERMINAL DE ACOMPANHAMENTO: uma linha a cada 5% do orçamento
        if progresso >= proximo_log:
            proximo_log += 0.05
            status = "VÁLIDA" if qtd_pendentes_novo == 0 else "INVÁLIDA"
            print(f"{time.perf_counter() - inicio:5.1f}s | Iter {iteracao} | Eps: {agente.epsilon:.3f} | "
                  f"Pend: {qtd_pendentes_novo} | Status: {status} | Custo: {custo_novo} | "
                  f"Melhor: pend={melhor[0]} custo={melhor[1]}")

    salvar_solucao_itc(caminho_saida, melhor_grade, instancia)  # única leitura célula a célula

    print("\n" + "=" * 60)
    print(f"FIM | {iteracao} iterações em {time.perf_counter() - inicio:.1f} s | seed {seed}")
    if viavel_em:
        print(f"Grade completa pela primeira vez na iteração {viavel_em[0]} ({viavel_em[1]:.1f} s)")
    else:
        print("A grade nunca ficou completa (H1 violada)")
    print(f"Melhor solução: {melhor[0]} aulas pendentes, custo {melhor[1]}")
    print(f"Solução gravada em {caminho_saida}")
    print("Tamanho da Q-Table gerada:", len(agente.q_table))
    print("Mapeamento de Estados Aprendidos:")
    for estado, acoes in agente.q_table.items():
        print(f" -> Estado {estado}: Valores Q {acoes}")
    print("=" * 60)

    # Última linha: resumo em formato fixo, lido pelo experimentos.py
    print("RESUMO " + json.dumps({
        "instancia": nome, "seed": seed, "iteracoes": iteracao,
        "tempo_total": round(time.perf_counter() - inicio, 2),
        "tempo_melhor": round(melhor_em, 2),
        "tempo_viavel": round(viavel_em[1], 2) if viavel_em else None,
        "pendentes": melhor[0], "custo": melhor[1], "episodio": args.episodio,
        "escolhas_fase1": dict(escolhas[0]), "escolhas_fase2": dict(escolhas[1]),
        "movimentos_fase2": dict(movimentos_fase2), "melhoras_fase2": dict(melhoras_fase2)}))


if __name__ == "__main__":
    main()
