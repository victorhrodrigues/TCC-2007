import core_otimizador 
import os

# criar depois um loop para tentar automatizar a aplicação da solução para todas as intâncias
pasta = "dados"
dataset = "EarlyDatasets"
instancia = "comp01.ctt.txt" 

caminho_instancia = os.path.join(pasta, dataset, instancia)

instancia = core_otimizador.Instancia()

print(f"Tentando carregar: {caminho_instancia}")
if core_otimizador.Parser.carregar_ctt(caminho_instancia, instancia):
    print("\n[Sucesso] Instância carregada pelo C++!")
    print(f"Nome do Cenário: {instancia.nome}")
    print(f"Dias: {instancia.qtd_dias} | Períodos por dia: {instancia.periodos_por_dia}")
    print(f"Total de disciplinas lidas: {len(instancia.disciplinas)}")
    print(f"Total de salas lidas: {len(instancia.salas)}")
    
    # Teste de integridade dos dados lidos
    print(f"\nPrimeira Disciplina: {instancia.disciplinas[0].id} (Aulas: {instancia.disciplinas[0].num_aulas})")
    print(f"Primeira Sala: {instancia.salas[0].id} (Capacidade: {instancia.salas[0].capacidade})")
else:
    print("[Erro] Falha ao carregar o arquivo.")