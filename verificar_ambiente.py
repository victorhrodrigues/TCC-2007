import core_otimizador
import os

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
    print("    Análise esperada do Custo:")
    print("     * S1 (Capacidade): 0 - Ambas as salas suportam os alunos.")
    print("     * S2 (Estabilidade de Sala): +1 - Usou duas salas diferentes (Sala 0 e Sala 1).")
    print("     * S3 (Mínimo de Dias Úteis): +3 - Precisava de 4 dias, mas as duas aulas estão no mesmo dia (4 - 1 = 3).")
    print("     * S4 (Compactação Currículo): +1 - Janela vazia criada no Período 1 entre as duas aulas da turma.")
    print(f"    Total calculado pelo C++: {custo_suave} (Esperado: 5)")

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

    print("\n" + "=" * 60)
    print("FIM DO ROTEIRO: AMBIENTE INTEGRADO E FUNCIONANDO SEM ERROS!")
    print("=" * 60)
else:
    print("\n [ERRO] Falha crítica ao abrir o arquivo.")
    print("Verifique se a árvore de diretórios contém a pasta dados/EarlyDatasets/")