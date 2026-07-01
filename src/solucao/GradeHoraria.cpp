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
}

/*
    Função para verificação a qual currículo uma disciplina pertence
*/
int GradeHoraria::obter_index_curriculo_da_disciplina(int disciplina_indice) const {
    std::string id_busca = inst.disciplinas[disciplina_indice].id;
    for (int i = 0; i < inst.qtd_curriculos; ++i) {
        for (const auto& id_disc : inst.curriculos[i].ids_disciplinas) {
            if (id_disc == id_busca) return i;
        }
    }
    return -1; // Não achou currículo 
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

    // H3 (Currículo): Alunos dessa turma/curriculo já estão em outra aula nesse horário
    int curr_indice = obter_index_curriculo_da_disciplina(disciplina_indice);
    if (curr_indice != -1 && matriz_curriculo_ocupado[dia][periodo][curr_indice]) {
        return false; // Conflito de Currículo detectado
    }

    return true; // Movimento viável
}

bool GradeHoraria::alocar_aula(int dia, int periodo, int sala_indice, int disciplina_indice) {
    // Validar o movimento antes (Centraliza checagem de limites, H2, H3 e H4)
    if (!validar_movimento_viavel(dia, periodo, sala_indice, disciplina_indice)) {
        return false; 
    }

    matriz[dia][periodo][sala_indice] = disciplina_indice;

    int curr_indice = obter_index_curriculo_da_disciplina(disciplina_indice);
    if (curr_indice != -1) {
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
        int curr_indice = obter_index_curriculo_da_disciplina(disciplina_indice);
        if (curr_indice != -1) {
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
                    // Varre todos os currículos para ver quais incluem o ID desta disciplina
                    std::string id_busca = inst.disciplinas[disc_idx].id;
                    for (int c = 0; c < inst.qtd_curriculos; ++c) {
                        for (const auto& id_disc : inst.curriculos[c].ids_disciplinas) {
                            if (id_disc == id_busca) {
                                grade_curriculo_ocupada[d][p][c] = true;
                                break; // Já achou neste currículo, pula para o próximo c
                            }
                        }
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
            penalty += (inst.disciplinas[i].dias_minimos - qtd_dias_distintos);
        }
    }

    // CÁLCULO DE PENALIDADES DE S4 (COMPACTAÇÃO DO CURRÍCULO)
    for (int c = 0; c < inst.qtd_curriculos; ++c) {
        for (int d = 0; d < inst.qtd_dias; ++d) {
            int primeira_aula = -1;
            int ultima_aula = -1;
            int total_aulas_no_dia = 0;

            for (int p = 0; p < inst.periodos_por_dia; ++p) {
                if (grade_curriculo_ocupada[d][p][c]) {
                    if (primeira_aula == -1) primeira_aula = p;
                    ultima_aula = p;
                    total_aulas_no_dia++;
                }
            }

            if (total_aulas_no_dia > 0) {
                if (total_aulas_no_dia == 1) {
                    penalty += 1;
                } else {
                    for (int p = primeira_aula; p <= ultima_aula; ++p) {
                        if (!grade_curriculo_ocupada[d][p][c]) {
                            penalty += 1; 
                        }
                    }
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