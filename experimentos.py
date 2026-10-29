"""
Roda o q_learning.py em várias instâncias e seeds, valida cada solução com o validador
oficial da ITC-2007 e grava CSV com as mesmas colunas do experimentos.ps1 do Müller.

Uso:
    experimentos.bat --config 0                                            # todas as instâncias, seeds 1-10, 65 s
    experimentos.bat --config teste --instancias comp01 --seeds 1 --tempo 5   # teste rápido
    experimentos.bat --config B -- --politica aleatoria                    # repassa opções ao q_learning.py

Execuções já registradas no CSV são puladas: dá para interromper (Ctrl+C) e continuar depois.
"""
import argparse
import csv
import glob
import json
import os
import re
import statistics
import subprocess
import sys

VALIDADOR = os.path.join("..", "Solução Tomas Muller", "cpsolver-itc2007", "doc", "validate", "Win32", "ctt-validator.exe")
COLUNAS = ["configuracao", "grupo", "instancia", "seed", "tempo_limite", "custo", "violacoes_hard",
           "rc", "md", "cc", "rs", "tempo_melhor", "iteracoes", "tempo_viavel"]


def ler_argumentos():
    parser = argparse.ArgumentParser(description="Experimentos do q_learning.py com validação oficial")
    parser.add_argument("--config", required=True, help="rótulo da configuração: 0, 0+R, A, B, C...")
    parser.add_argument("--instancias", default="", help="ex.: comp01,comp05 (padrão: todas do dataset)")
    parser.add_argument("--dataset", default="EarlyDatasets")
    parser.add_argument("--seeds", type=int, default=10, help="roda as seeds 1..N")
    parser.add_argument("--tempo", type=float, default=65.0)
    parser.add_argument("--pasta", default="resultados", help="onde ficam soluções, logs e CSVs")
    parser.add_argument("--validador", default=VALIDADOR)
    parser.add_argument("extras", nargs=argparse.REMAINDER, help="depois de --: opções repassadas ao q_learning.py")
    return parser.parse_args()


def validar(validador, instancia, solucao):
    """ Roda o validador oficial e extrai o custo, as violações rígidas e o custo de cada restrição suave """
    saida = subprocess.run([validador, instancia, solucao], capture_output=True, text=True).stdout
    def numero(padrao):
        m = re.search(padrao, saida)
        return int(m.group(1)) if m else None
    return {
        "custo": numero(r"Total Cost = (\d+)"),
        "violacoes_hard": sum(int(v) for v in re.findall(r"Violations of .* \(hard\) : (\d+)", saida)),
        "rc": numero(r"RoomCapacity \(soft\) : (\d+)"),
        "md": numero(r"MinWorkingDays \(soft\) : (\d+)"),
        "cc": numero(r"CurriculumCompactness \(soft\) : (\d+)"),
        "rs": numero(r"RoomStability \(soft\) : (\d+)"),
    }


def resumir(pasta, tempo):
    """ Por configuração e instância: execuções, quantas viáveis, e melhor/média/desvio/pior custo das viáveis """
    grupos = {}
    with open(os.path.join(pasta, "execucoes.csv"), newline="") as f:
        for linha in csv.DictReader(f):
            if float(linha["tempo_limite"]) == tempo:
                grupos.setdefault((linha["configuracao"], linha["instancia"]), []).append(linha)
    resumo = []
    for (config, inst), execs in sorted(grupos.items()):
        custos = [int(e["custo"]) for e in execs if e["violacoes_hard"] == "0"]
        resumo.append({"configuracao": config, "instancia": inst, "execucoes": len(execs), "viaveis": len(custos),
                       "melhor": min(custos, default=""),
                       "media": round(statistics.mean(custos), 2) if custos else "",
                       "desvio": round(statistics.stdev(custos), 2) if len(custos) > 1 else "",
                       "pior": max(custos, default="")})
    with open(os.path.join(pasta, f"resumo_{tempo:.0f}s.csv"), "w", newline="") as f:
        escritor = csv.DictWriter(f, list(resumo[0]))
        escritor.writeheader()
        escritor.writerows(resumo)
    for r in resumo:
        print(f"{r['configuracao']:>6} {r['instancia']}: {r['viaveis']}/{r['execucoes']} viáveis | "
              f"melhor {r['melhor']} | média {r['media']} | desvio {r['desvio']} | pior {r['pior']}")


def main():
    args = ler_argumentos()
    extras = [a for a in args.extras if a != "--"]

    pasta_dados = os.path.join("dados", args.dataset)
    nomes = sorted(os.path.basename(c).removesuffix(".ctt.txt")
                   for c in glob.glob(os.path.join(pasta_dados, "*.ctt.txt")))
    if args.instancias:
        nomes = [n for n in nomes if n in args.instancias.split(",")]

    pasta_solucoes = os.path.join(args.pasta, f"config_{args.config}", args.dataset)
    os.makedirs(pasta_solucoes, exist_ok=True)
    csv_execucoes = os.path.join(args.pasta, "execucoes.csv")
    feitas = set()
    if os.path.exists(csv_execucoes):
        with open(csv_execucoes, newline="") as f:
            feitas = {(l["configuracao"], l["instancia"], l["seed"], l["tempo_limite"]) for l in csv.DictReader(f)}
    else:
        with open(csv_execucoes, "w", newline="") as f:
            csv.writer(f).writerow(COLUNAS)

    total = len(nomes) * args.seeds
    print(f"config {args.config}: {len(nomes)} instância(s) x {args.seeds} seed(s) x {args.tempo:.0f} s "
          f"(~{total * args.tempo / 60:.0f} min no máximo)")
    n = 0
    for nome in nomes:
        for seed in range(1, args.seeds + 1):
            n += 1
            if (args.config, nome, str(seed), str(args.tempo)) in feitas:
                continue
            print(f"[{n}/{total}] {nome} seed {seed} ... ", end="", flush=True)

            # Cada execução é um processo novo: nada de uma execução vaza para a próxima
            solucao = os.path.join(pasta_solucoes, f"{nome}_seed{seed}.sol")
            comando = [sys.executable, "q_learning.py", nome, "--dataset", args.dataset, "--seed", str(seed),
                       "--tempo", str(args.tempo), "--saida", solucao] + extras
            execucao = subprocess.run(comando, capture_output=True, text=True, encoding="utf-8",
                                      env={**os.environ, "PYTHONIOENCODING": "utf-8"})
            with open(solucao.removesuffix(".sol") + ".log", "w", encoding="utf-8") as f:
                f.write(execucao.stdout + execucao.stderr)
            resumo = next((json.loads(l[len("RESUMO "):]) for l in execucao.stdout.splitlines()
                           if l.startswith("RESUMO ")), None)
            if resumo is None:
                print("falhou (ver o .log)")
                continue

            val = validar(args.validador, os.path.join(pasta_dados, nome + ".ctt.txt"), solucao)
            linha = {"configuracao": args.config, "grupo": args.dataset, "instancia": nome, "seed": seed,
                     "tempo_limite": args.tempo, **val, "tempo_melhor": resumo["tempo_melhor"],
                     "iteracoes": resumo["iteracoes"], "tempo_viavel": resumo["tempo_viavel"]}
            with open(csv_execucoes, "a", newline="") as f:
                csv.DictWriter(f, COLUNAS).writerow(linha)

            aviso = f"  ({val['violacoes_hard']} violações rígidas)" if val["violacoes_hard"] else ""
            # Conferência cruzada (validador oficial x nosso C++) só em grades viáveis: em grades incompletas o
            # validador também cobra a S3 de disciplinas sem nenhuma aula, e esse custo não entra nas estatísticas
            if val["violacoes_hard"] == 0 and val["custo"] != resumo["custo"]:
                aviso += f"  [ATENÇÃO: C++ calculou {resumo['custo']}]"
            print(f"custo {val['custo']}{aviso}")

    resumir(args.pasta, args.tempo)


if __name__ == "__main__":
    main()
