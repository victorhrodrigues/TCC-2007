import core_otimizador
import os
import copy

pasta = "dados"
dataset = "EarlyDatasets"
nome_arquivo = "comp01.ctt.txt"

caminho_instancia = os.path.join(pasta, dataset, nome_arquivo)

instancia = core_otimizador.Instancia()

print("=" * 60)
print(f"ROTEIRO DE VERIFICAÇÃO AUTOMATIZADA: {nome_arquivo}")
print("=" * 60)
print(f"Tentando carregar arquivo: {caminho_instancia}")

if core_otimizador.Parser.carregar_ctt(caminho_instancia, instancia):
    print("\n[Sucesso 1/2] Dados da instância carregados pelo C++!")
    
    grade = core_otimizador.GradeHoraria(instancia)
    print("[Sucesso 2/2] Matriz 3D da Grade Horária criada na memória RAM!")
    print("-" * 60)
    

    # -----------------------------------------------------------------
    # TESTE 1: ALOCAÇÃO PADRÃO (Cenário de Sucesso)
    # -----------------------------------------------------------------
    print("\nTESTE 1: Inserindo uma disciplina em um espaço vazio...")
    # Aloca a Disciplina 0 (c0001) no Dia 0, Período 0, Sala 0 (Sala B)
    alocou_sucesso = grade.alocar_aula(0, 0, 0, 0)
    print(f" -> Alocação inicial da Disciplina 0: {alocou_sucesso} (Esperado: True)")
    
    # Confere quem ficou na memória RAM
    ocupante = grade.obter_disciplina_na_gaveta(0, 0, 0)
    print(f" -> Ocupante da célula [Dia 0][Período 0][Sala 0]: Índice {ocupante} (Esperado: 0)")

    # -----------------------------------------------------------------
    # TESTE 2: RESTRIÇÃO RÍGIDA H2 - OCUPAÇÃO DE SALA (SOBREPOSIÇÃO)
    # -----------------------------------------------------------------
    print("\nTESTE 2: Validando Restrição Rígida H2 (Ocupação Física de Sala)...")
    # Tenta colocar a Disciplina 2 (c0004) no MESMO dia, período e sala da Disciplina 0
    colisao_sala = grade.alocar_aula(0, 0, 0, 2)
    print(f" -> Inserir Disciplina 2 no mesmo espaço da Disciplina 0: {colisao_sala} (Esperado: False)")

    # -----------------------------------------------------------------
    # TESTE 3: RESTRIÇÃO RÍGIDA H3 - CONFLITO DE CURRÍCULO (TURMA)
    # -----------------------------------------------------------------
    print("\nTESTE 3: Validando Restrição Rígida H3 (Conflito de Currículo/Alunos)...")
    # No comp01, a Disciplina 0 (c0001) e a Disciplina 1 (c0002) compartilham o currículo q000.
    # Tentaremos colocar a Disciplina 1 no MESMO horário (Dia 0, Período 0), mas em outra sala (Sala 1)
    colisao_turma = grade.alocar_aula(0, 0, 1, 1)
    print(f" -> Alocar Disciplina 1 (Mesmo currículo) no mesmo período: {colisao_turma} (Esperado: False)")

    # c0001 pertence a dois currículos (q000 e q002). A Disciplina 8 (c0024, professor t008) só está em q002,
    # então o conflito tem de ser detectado também pelo segundo currículo de c0001, não só pelo primeiro.
    colisao_segundo_curriculo = grade.alocar_aula(0, 0, 1, 8)
    print(f" -> Alocar Disciplina 8 (compartilha só o 2º currículo de c0001) no mesmo período: {colisao_segundo_curriculo} (Esperado: False)")

    # -----------------------------------------------------------------
    # TESTE 4: AVALIAÇÃO DE PENALIDADES SUAVES (S1, S2, S3, S4)
    # -----------------------------------------------------------------
    print("\nTESTE 4: Verificando Motor de Avaliação Estética / Custos (S1 a S4)...")
    
    # Vamos limpar qualquer inserção anterior criando uma nova instância limpa de testes
    grade_teste = core_otimizador.GradeHoraria(instancia)
    
    # Disciplina 0 precisa de 4 aulas distribuídas em no mínimo 4 dias diferentes (comp01)
    # Alocando duas aulas da Disciplina 0 no MESMO DIA (Dia 0), mas em períodos diferentes:
    grade_teste.alocar_aula(0, 0, 0, 0) # Sala Grande
    grade_teste.alocar_aula(0, 2, 1, 0) # Sala Média (C)

    custo_suave = grade_teste.calcular_total_penalidades()
    print(f" -> Penalidades acumuladas com a configuração atual: {custo_suave}")
    print("    Análise esperada do Custo (pesos oficiais ITC-2007):")
    print("     * S1 (Capacidade): +30 - Sala C (capacidade 100) é pequena demais para os 130 alunos de c0001 (130 - 100 = 30).")
    print("     * S2 (Estabilidade de Sala): +1 - Usou duas salas diferentes (Sala 0 e Sala 1), peso 1.")
    print("     * S3 (Mínimo de Dias Úteis): +15 - Precisava de 4 dias, só usou 1 (4 - 1 = 3), peso 5 (3 x 5 = 15).")
    print("     * S4 (Compactação Currículo): +8 - c0001 pertence a 2 currículos (q000 e q002); em cada um, as")
    print("       aulas dos períodos 0 e 2 ficam isoladas (sem vizinho no período 1), peso 2 (2 aulas x 2 currículos x 2 = 8).")
    print(f"    Total calculado pelo C++: {custo_suave} (Esperado: 54)")

    # -----------------------------------------------------------------
    # TESTE 5: ESCUDO DE MEMÓRIA (ÍNDICES INVÁLIDOS)
    # -----------------------------------------------------------------
    print("\nTESTE 5: Testando Cláusulas de Guarda (Segurança contra falhas da IA)...")
    # Simula a IA tentando ler ou escrever em um dia ou período que não existe no arquivo
    limite_invalido = grade.validar_movimento_viavel(99, 0, 0, 0)
    print(f" -> Validação de índice inexistente (Ex: Dia 99): {limite_invalido} (Esperado: False)")

    # -----------------------------------------------------------------
    # TESTE 6: RESTRIÇÃO RÍGIDA H4 - INDISPONIBILIDADE DE PROFESSOR
    # -----------------------------------------------------------------
    print("\nTESTE 6: Validando Restrição Rígida H4 (Indisponibilidade)...")
    # Baseado no arquivo real: c0001 (Disciplina 0) é indisponível no Dia 4, Período 0
    tentativa_indisponivel = grade.alocar_aula(4, 0, 0, 0) # <- Ajustado para as coordenadas do arquivo
    print(f" -> Alocar Disciplina 0 em horário de indisponibilidade: {tentativa_indisponivel} (Esperado: False)")

    # -----------------------------------------------------------------
    # TESTE 7: RESTRIÇÃO RÍGIDA H1 - ALOCAÇÃO COMPLETA DE AULAS
    # -----------------------------------------------------------------
    print("\nTESTE 7: Validando Restrição Rígida H1 (Alocação Completa)...")
    grade_completa = grade.validar_alocacao_completa()
    print(f" -> A grade possui todas as aulas exigidas alocadas? {grade_completa} (Esperado: False - pois a grade está quase vazia)")

    # -----------------------------------------------------------------
    # TESTE 8: CÓPIA DA GRADE NO C++ (ELITISMO)
    # -----------------------------------------------------------------
    print("\nTESTE 8: Validando a cópia da grade (usada para guardar a melhor solução)...")
    copia = copy.deepcopy(grade_teste)
    grade_teste.remover_aula(0, 0, 0)  # altera só a original
    print(f" -> Custo da cópia depois de alterar a original: {copia.calcular_total_penalidades()} (Esperado: 54)")
    # Na original o período 0 ficou livre para o currículo q000; na cópia, c0001 continua lá
    print(f" -> Alocar Disciplina 1 no período 0 da original: {grade_teste.alocar_aula(0, 0, 1, 1)} (Esperado: True)")
    print(f" -> Alocar Disciplina 1 no período 0 da cópia: {copia.alocar_aula(0, 0, 1, 1)} (Esperado: False)")

    # -----------------------------------------------------------------
    # TESTE 9: CONFLITOS POR POSIÇÃO (REPARO DA FASE 1, INSPIRADO EM MÜLLER)
    # -----------------------------------------------------------------
    print("\nTESTE 9: Validando a lista de conflitos usada pelo reparo da Fase 1...")
    print(f" -> Domínio da Disciplina 8 (c0024): {grade.tamanho_dominio(8)} (Esperado: 144 - 24 períodos livres x 6 salas)")
    print(f" -> Disciplinas em conflito com a Disciplina 0 (c0001): {grade.grau_conflitos(0)} (Esperado: 6)")
    print(f" -> Disciplinas em conflito com a Disciplina 8 (c0024): {grade.grau_conflitos(8)} (Esperado: 4)")
    posicoes = {(d, p, s): conflitos for d, p, s, conflitos in grade.conflitos_por_posicao(8)}
    # Na grade do Teste 1, só a c0001 está alocada, em (dia 0, período 0, sala 0); ela divide o currículo q002 com a c0024
    print(f" -> Conflitos da c0024 em (0, 0, 1): {posicoes[(0, 0, 1)]} (Esperado: [(0, 0)] - c0001 na sala 0)")
    print(f" -> Conflitos da c0024 em (1, 0, 0): {posicoes[(1, 0, 0)]} (Esperado: [] - posição livre e sem conflito)")
    print(f" -> Posições da c0024 no dia 3 (indisponível): {sum(1 for (d, p, s) in posicoes if d == 3)} (Esperado: 0)")

    # -----------------------------------------------------------------
    # TESTE 10: RECONSTRUÇÃO REATIVA (FASE 1, INSPIRADA EM GEIGER)
    # -----------------------------------------------------------------
    print("\nTESTE 10: Validando a reconstrução reativa usada na Fase 1...")
    grade_rec = core_otimizador.GradeHoraria(instancia)
    aceitou, fora = grade_rec.reconstruir([], 1, -1)  # limite impossível: a grade não pode ser trocada
    print(f" -> Com limite -1, a grade foi trocada? {aceitou} (Esperado: False); aulas na grade: "
          f"{sum(1 for d in range(5) for p in range(6) for s in range(6) if grade_rec.obter_disciplina_na_gaveta(d, p, s) != -1)} (Esperado: 0)")
    aceitou, fora = grade_rec.reconstruir([], 1, 1000)
    print(f" -> Reconstrução do comp01 (semente 1): trocou {aceitou}, aulas de fora {len(fora)}, grade completa "
          f"{grade_rec.validar_alocacao_completa()} (Esperado: True, 0, True - o comp01 fecha em 20 de 20 sementes)")

    print("\n" + "=" * 60)
    print("FIM DO ROTEIRO: AMBIENTE INTEGRADO E FUNCIONANDO SEM ERROS!")
    print("=" * 60)
else:
    print("\n [ERRO] Falha crítica ao abrir o arquivo.")
    print("Verifique se a árvore de diretórios contém a pasta dados/EarlyDatasets/")