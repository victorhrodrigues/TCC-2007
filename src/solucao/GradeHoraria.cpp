#include "GradeHoraria.hpp"
#include <iostream>

GradeHoraria::GradeHoraria(const Instancia& instancia) : inst(instancia) {
    // -1 = espaço livre para marcação em sala
    matriz.resize(inst.qtd_dias, 
        std::vector<std::vector<int>>(inst.periodos_por_dia, 
            std::vector<int>(inst.qtd_salas, -1)
        )
    );

    matriz_professor_ocupado.resize(inst.qtd_dias,
        std::vector<std::vector<bool>>(inst.periodos_por_dia,
            std::vector<bool>(inst.qtd_disciplinas, false)
        )
    );

    matriz_curriculo_ocupado.resize(inst.qtd_dias,
        std::vector<std::vector<bool>>(inst.periodos_por_dia,
            std::vector<bool>(inst.qtd_curriculos, false)
        )
    );

    // Mapeia cada disciplina para todos os currículos que a incluem (uma disciplina pode estar em vários)
    curriculos_da_disciplina.resize(inst.qtd_disciplinas);
    for (int q = 0; q < inst.qtd_curriculos; ++q) {
        for (const auto& id_disc : inst.curriculos[q].ids_disciplinas) {
            for (int c = 0; c < inst.qtd_disciplinas; ++c) {
                if (inst.disciplinas[c].id == id_disc) {
                    curriculos_da_disciplina[c].push_back(q);
                    break;
                }
            }
        }
    }

    // Duas disciplinas conflitam (H3) se têm o mesmo professor ou algum currículo em comum
    disciplinas_em_conflito.assign(inst.qtd_disciplinas * inst.qtd_disciplinas, false);
    for (int c = 0; c < inst.qtd_disciplinas; ++c) {
        for (int o = 0; o < inst.qtd_disciplinas; ++o) {
            bool conflito = inst.disciplinas[c].id_professor == inst.disciplinas[o].id_professor;
            for (int q : curriculos_da_disciplina[c]) {
                for (int q2 : curriculos_da_disciplina[o]) {
                    if (q == q2) conflito = true;
                }
            }
            disciplinas_em_conflito[c * inst.qtd_disciplinas + o] = conflito;
        }
    }

    // Períodos indisponíveis por disciplina (H4)
    indisponivel.assign(inst.qtd_disciplinas * inst.qtd_dias * inst.periodos_por_dia, false);
    for (const auto& ind : inst.indisponibilidades) {
        for (int c = 0; c < inst.qtd_disciplinas; ++c) {
            if (inst.disciplinas[c].id == ind.id_disciplina) {
                indisponivel[(c * inst.qtd_dias + ind.dia) * inst.periodos_por_dia + ind.periodo] = true;
                break;
            }
        }
    }
}

bool GradeHoraria::validar_movimento_viavel(int dia, int periodo, int sala_indice, int disciplina_indice) const {
    // Escudo de proteção contra índices inválidos 
    if (dia >= inst.qtd_dias || periodo >= inst.periodos_por_dia || sala_indice >= inst.qtd_salas) {
        return false;
    }
    
    // REGRA H4 - Indisponibilidade 
    std::string id_disciplina_atual = inst.disciplinas[disciplina_indice].id;
    for (const auto& ind : inst.indisponibilidades) { 
        if (ind.dia == dia && ind.periodo == periodo && ind.id_disciplina == id_disciplina_atual) {
            return false; // Bloqueado! Horário marcado como indisponível no arquivo .ctt
        }
    }

    // H2 - A sala já está ocupada nesse horário?
    if (matriz[dia][periodo][sala_indice] != -1) return false;

    // H3 (Professor): O professor dessa disciplina já está dando aula em outro lugar nesse horário
    for (int s = 0; s < inst.qtd_salas; ++s) {
        int o_outro_idx = matriz[dia][periodo][s];
        if (o_outro_idx != -1) {
            if (inst.disciplinas[o_outro_idx].id_professor == inst.disciplinas[disciplina_indice].id_professor) {
                return false; // Conflito de Professor detectado
            }
        }
    }

    // H3 (Currículo): Alunos de qualquer currículo dessa disciplina já estão em outra aula nesse horário
    for (int curr_indice : curriculos_da_disciplina[disciplina_indice]) {
        if (matriz_curriculo_ocupado[dia][periodo][curr_indice]) {
            return false; // Conflito de Currículo detectado
        }
    }

    return true; // Movimento viável
}

bool GradeHoraria::alocar_aula(int dia, int periodo, int sala_indice, int disciplina_indice) {
    // Validar o movimento antes (Centraliza checagem de limites, H2, H3 e H4)
    if (!validar_movimento_viavel(dia, periodo, sala_indice, disciplina_indice)) {
        return false; 
    }

    matriz[dia][periodo][sala_indice] = disciplina_indice;

    for (int curr_indice : curriculos_da_disciplina[disciplina_indice]) {
        matriz_curriculo_ocupado[dia][periodo][curr_indice] = true;
    }

    return true;
}

void GradeHoraria::remover_aula(int dia, int periodo, int sala_indice) {
    // Verifica índice inválido 
    if (dia >= inst.qtd_dias || periodo >= inst.periodos_por_dia || sala_indice >= inst.qtd_salas) {
        return;
    }

    int disciplina_indice = matriz[dia][periodo][sala_indice];

    if (disciplina_indice != -1) {
        for (int curr_indice : curriculos_da_disciplina[disciplina_indice]) {
            matriz_curriculo_ocupado[dia][periodo][curr_indice] = false;
        }

        // Libera o espaço na matriz principal
        matriz[dia][periodo][sala_indice] = -1; 
    }
}

int GradeHoraria::obter_disciplina_na_gaveta(int dia, int periodo, int sala_indice) const {
    return matriz[dia][periodo][sala_indice];
}

bool GradeHoraria::espaco_esta_livre(int dia, int periodo, int sala_indice) const {
    return matriz[dia][periodo][sala_indice] == -1;
}

int GradeHoraria::calcular_total_penalidades() const {
    int penalty = 0;

    // Para S2 (Salas Distintas) e S3 (Dias Distintos) por Disciplina
    std::vector<std::vector<bool>> salas_usadas_por_disc(inst.qtd_disciplinas, std::vector<bool>(inst.qtd_salas, false));
    std::vector<std::vector<bool>> dias_usados_por_disc(inst.qtd_disciplinas, std::vector<bool>(inst.qtd_dias, false));

    // Para S4 (Compactação por Currículo): [Dia][Periodo][Curriculo]
    std::vector<std::vector<std::vector<bool>>> grade_curriculo_ocupada(
        inst.qtd_dias, std::vector<std::vector<bool>>(inst.periodos_por_dia, std::vector<bool>(inst.qtd_curriculos, false))
    );

    // VARREDURA PRINCIPAL DA MATRIZ 3D
    for (int d = 0; d < inst.qtd_dias; ++d) {
        for (int p = 0; p < inst.periodos_por_dia; ++p) {
            for (int s = 0; s < inst.qtd_salas; ++s) {
                int disc_idx = matriz[d][p][s];
                if (disc_idx != -1) {
                    // --- S1: CAPACIDADE DA SALA ---
                    int alunos = inst.disciplinas[disc_idx].num_alunos; 
                    int capacidade = inst.salas[s].capacidade; 
                    if (alunos > capacidade) {
                        penalty += (alunos - capacidade); 
                    }

                    // --- MAPEAMENTO PARA S2 E S3 ---
                    salas_usadas_por_disc[disc_idx][s] = true;
                    dias_usados_por_disc[disc_idx][d] = true;

                    // --- MAPEAMENTO MULTICURRÍCULO PARA S4 ---
                    for (int c : curriculos_da_disciplina[disc_idx]) {
                        grade_curriculo_ocupada[d][p][c] = true;
                    }
                }
            }
        }
    }

    // CÁLCULO DE PENALIDADES DE S2 (ESTABILIDADE DE SALA)
    for (int i = 0; i < inst.qtd_disciplinas; ++i) {
        int qtd_salas_distintas = 0;
        for (int s = 0; s < inst.qtd_salas; ++s) {
            if (salas_usadas_por_disc[i][s]) qtd_salas_distintas++;
        }
        if (qtd_salas_distintas > 1) {
            penalty += (qtd_salas_distintas - 1);
        }
    }

    // CÁLCULO DE PENALIDADES DE S3 (MÍNIMO DE DIAS ÚTEIS)
    for (int i = 0; i < inst.qtd_disciplinas; ++i) {
        int qtd_dias_distintos = 0;
        for (int d = 0; d < inst.qtd_dias; ++d) {
            if (dias_usados_por_disc[i][d]) qtd_dias_distintos++;
        }
        if (qtd_dias_distintos > 0 && qtd_dias_distintos < inst.disciplinas[i].dias_minimos) {
            penalty += 5 * (inst.disciplinas[i].dias_minimos - qtd_dias_distintos); // correção do peso para 5 
        }
    }

    // CÁLCULO DE PENALIDADES DE S4 (COMPACTAÇÃO DO CURRÍCULO)
    // Correção de estrutura de avaliação de restrição S4 inválida
    for (int c = 0; c < inst.qtd_curriculos; ++c) {
        for (int d = 0; d < inst.qtd_dias; ++d) {
            for (int p = 0; p < inst.periodos_por_dia; ++p) {
                if (!grade_curriculo_ocupada[d][p][c]) continue;

                bool vizinho_antes = (p > 0) && grade_curriculo_ocupada[d][p - 1][c];
                bool vizinho_depois = (p < inst.periodos_por_dia - 1) && grade_curriculo_ocupada[d][p + 1][c];

                // Aula isolada: nenhuma aula do mesmo currículo no período imediatamente antes ou depois
                if (!vizinho_antes && !vizinho_depois) {
                    penalty += 2;
                }
            }
        }
    }

    return penalty;
}

bool GradeHoraria::validar_alocacao_completa() const {
    // Cria um vetor de contagem para cada disciplina, inicializado com zero
    std::vector<int> contagem_aulas(inst.qtd_disciplinas, 0);

    // Varre toda a matriz 3D contando quantas vezes cada disciplina aparece alocada
    for (int d = 0; d < inst.qtd_dias; ++d) {
        for (int p = 0; p < inst.periodos_por_dia; ++p) {
            for (int s = 0; s < inst.qtd_salas; ++s) {
                int disc_idx = matriz[d][p][s];
                if (disc_idx != -1) {
                    contagem_aulas[disc_idx]++;
                }
            }
        }
    }

    // Compara se a contagem bate exatamente com o exigido pelo arquivo .ctt
    for (int i = 0; i < inst.qtd_disciplinas; ++i) {
        if (contagem_aulas[i] != inst.disciplinas[i].num_aulas) {
            return false; // Se faltar ou sobrar aula de qualquer disciplina, a grade é inválida (H1 falhou)
        }
    }

    return true; // Todas as disciplinas possuem o número exato de aulas alocadas!
}

// Retorna true se atende H1, H2, H3 e H4. Como H2, H3 e H4 são blindados na alocação,
// o estado de viabilidade resume-se a verificar se H1 (alocação completa) foi atendido.
bool GradeHoraria::esta_viavel() const {
    return validar_alocacao_completa();
}

// Identifica qual das restrições suaves está gerando a pior penalidade isolada
std::string GradeHoraria::obter_pior_gargalo() const {
    // Para simplificar a análise inicial da IA, vamos segmentar as penalidades
    // (Em um cenário real, você pode quebrar o cálculo de calcular_total_penalidades() por blocos)
    int total = calcular_total_penalidades();
    if (total == 0) return "NENHUM";
    
    // Se houver penalidade, por enquanto apontaremos para a genérica ou para a pior conhecida
    return "S1_S4";
}

// Tamanho do domínio da disciplina: posições (dia, período, sala) permitidas pela H4
int GradeHoraria::tamanho_dominio(int disciplina_indice) const {
    int periodos_livres = 0;
    for (int d = 0; d < inst.qtd_dias; ++d) {
        for (int p = 0; p < inst.periodos_por_dia; ++p) {
            if (!esta_indisponivel(disciplina_indice, d, p)) periodos_livres++;
        }
    }
    return periodos_livres * inst.qtd_salas;
}

// Número de outras disciplinas com que esta conflita (mesmo professor ou currículo em comum)
int GradeHoraria::grau_conflitos(int disciplina_indice) const {
    int grau = 0;
    for (int o = 0; o < inst.qtd_disciplinas; ++o) {
        if (o != disciplina_indice && conflitam(disciplina_indice, o)) grau++;
    }
    return grau;
}

// Para cada posição permitida pela H4, as aulas (disciplina, sala) que precisariam sair para a disciplina entrar:
// o ocupante da sala (H2) e as aulas do mesmo período com o mesmo professor ou currículo em comum (H3)
std::vector<std::tuple<int, int, int, std::vector<std::pair<int, int>>>>
GradeHoraria::conflitos_por_posicao(int disciplina_indice) const {
    std::vector<std::tuple<int, int, int, std::vector<std::pair<int, int>>>> posicoes;
    for (int d = 0; d < inst.qtd_dias; ++d) {
        for (int p = 0; p < inst.periodos_por_dia; ++p) {
            if (esta_indisponivel(disciplina_indice, d, p)) continue;

            // Conflitos de H3 valem para qualquer sala do período
            std::vector<std::pair<int, int>> conflitos_periodo;
            for (int s = 0; s < inst.qtd_salas; ++s) {
                int ocupante = matriz[d][p][s];
                if (ocupante != -1 && conflitam(disciplina_indice, ocupante)) {
                    conflitos_periodo.push_back({ocupante, s});
                }
            }

            for (int r = 0; r < inst.qtd_salas; ++r) {
                std::vector<std::pair<int, int>> conflitos = conflitos_periodo;
                int ocupante = matriz[d][p][r];
                // O ocupante da sala sai pela H2, a menos que já esteja na lista pela H3
                if (ocupante != -1 && !conflitam(disciplina_indice, ocupante)) {
                    conflitos.push_back({ocupante, r});
                }
                posicoes.emplace_back(d, p, r, conflitos);
            }
        }
    }
    return posicoes;
}