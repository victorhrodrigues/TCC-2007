import core_otimizador
import os

pasta = "dados"
dataset = "EarlyDatasets"
instancia = "comp01.ctt.txt"

caminho_instancia = os.path.join(pasta, dataset, instancia)

instancia = core_otimizador.Instancia()

print(f"Tentando carregar: {caminho_instancia}")
if core_otimizador.Parser.carregar_ctt(caminho_instancia, instancia):
    print("\n[Sucesso 1/2] Dados da instância carregados pelo C++!")
    
    grade = core_otimizador.GradeHoraria(instancia)
    print("[Sucesso 2/2] Matriz 3D da Grade Horária criada na memória RAM!")
    
    alocou = grade.alocar_aula(0, 0, 0, 0)
    print(f"\nTentativa de alocação estrutural: {alocou}")
    
    tentativa_invalida = grade.alocar_aula(0, 0, 0, 1)
    print(f"Tentativa de colocar outra matéria na mesma sala/horário: {tentativa_invalida} (Esperado: False)")
    
    disciplina_alocada = grade.obter_disciplina_na_gaveta(0, 0, 0)
    print(f"Quem está ocupando a gaveta [0][0][0]? Índice da Disciplina: {disciplina_alocada}")

    print(f"Total de penalidades iniciais da grade: {grade.calcular_total_penalidades()}")

else:
    print("[Erro] Falha ao carregar o arquivo. Verifique o caminho ou a estrutura.")