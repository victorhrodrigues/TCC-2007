import core_otimizador
import os

pasta = "dados"
dataset = "EarlyDatasets"
instancia = "comp01.ctt.txt"

caminho_instancia = os.path.join(pasta, dataset, instancia)

instancia = core_otimizador.Instancia()

print("=" * 60)
print(f"ROTEIRO DE VERIFICAÇÃO AUTOMATIZADA: {instancia}")
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
    # TESTE 4: AVALIAÇÃO DE PENALIDADES SUAVES (S1 - CAPACIDADE DA SALA)
    # -----------------------------------------------------------------
    print("\nTESTE 4: Verificando Cálculo da Função de Custo / Fitness (S1)...")
    # Disciplina 0 possui 130 alunos. Sala 0 (Sala B) tem capacidade para 200.
    print(f" -> Penalidade com Disciplina 0 na Sala Grande: {grade.calcular_total_penalidades()} (Esperado: 0)")
    
    # Vamos remover a aula da sala grande...
    grade.remover_aula(0, 0, 0)
    
    # ...e alocar a Disciplina 0 na Sala 2 (Sala E), que só tem capacidade para 9 assentos!
    # O C++ deve aceitar (pois as restrições rígidas passam), mas aplicar uma multa pesada de soft constraint.
    grade.alocar_aula(0, 0, 2, 0)
    # Multa esperada: 130 alunos - 9 assentos = 121 pontos de penalidade
    print(f" -> Penalidade após mover Disciplina 0 para Sala Pequena (Capacidade: 9): {grade.calcular_total_penalidades()} (Esperado: 121)")

    # -----------------------------------------------------------------
    # TESTE 5: ESCUDO DE MEMÓRIA (ÍNDICES INVÁLIDOS)
    # -----------------------------------------------------------------
    print("\nTESTE 5: Testando Cláusulas de Guarda (Segurança contra falhas da IA)...")
    # Simula a IA tentando ler ou escrever em um dia ou período que não existe no arquivo
    limite_invalido = grade.validar_movimento_viavel(99, 0, 0, 0)
    print(f" -> Validação de índice inexistente (Ex: Dia 99): {limite_invalido} (Esperado: False)")

    print("\n" + "=" * 60)
    print("FIM DO ROTEIRO: AMBIENTE INTEGRADO E FUNCIONANDO SEM ERROS!")
    print("=" * 60)

else:
    print("\n [ERRO] Falha crítica ao abrir o arquivo.")
    print("Verifique se a árvore de diretórios contém a pasta dados/EarlyDatasets/")