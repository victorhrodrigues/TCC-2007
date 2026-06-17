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
    
    if (dia >= inst.qtd_dias || periodo >= inst.periodos_por_dia || sala_indice >= inst.qtd_salas) {
        return false;
    }
    
    //H2 - A sala já está ocupada nesse horário?
    if (matriz[dia][periodo][sala_indice] != -1) return false;

    /* 
        H3(Professor): O professor dessa disciplina já está dando aula em outro lugar nesse horário
    */ 
    for (int s = 0; s < inst.qtd_salas; ++s) {
        int o_outro_idx = matriz[dia][periodo][s];
        if (o_outro_idx != -1) {
            if (inst.disciplinas[o_outro_idx].id_professor == inst.disciplinas[disciplina_indice].id_professor) {
                return false; // Conflito de Professor detectado
            }
        }
    }

    // H3(Currículo): Alunos dessa turma/curriculo já estão em outra aula nesse horário
    int curr_indice = obter_index_curriculo_da_disciplina(disciplina_indice);
    if (curr_indice != -1 && matriz_curriculo_ocupado[dia][periodo][curr_indice]) {
        return false; // Conflito de Currículo detectado
    }

    return true; // moviment viável
}


bool GradeHoraria::alocar_aula(int dia, int periodo, int sala_indice, int disciplina_indice) {
    // verifica espaço do vetor antes de leitura - passar essa verificação para validar_movimento_viavel depois
    // if (dia >= inst.qtd_dias || periodo >= inst.periodos_por_dia || sala_indice >= inst.qtd_salas) {
    //     return false;
    // }
    
    // validar o movimento antes (restrições H2 e h3)
    if (!validar_movimento_viavel(dia, periodo, sala_indice, disciplina_indice)) {
        return false; 
    }
    
    // verificação movida para validar_movimento_viável
    // if (matriz[dia][periodo][sala_indice] != -1) {
    //     return false; 
    // }

    matriz[dia][periodo][sala_indice] = disciplina_indice;

    int curr_indice = obter_index_curriculo_da_disciplina(disciplina_indice);
    if (curr_indice != -1) {
        matriz_curriculo_ocupado[dia][periodo][curr_indice] = true;
    }

    return true;
}

void GradeHoraria::remover_aula(int dia, int periodo, int sala_indice) {
    // verifica indice inválido 
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


    for (int d = 0; d < inst.qtd_dias; ++d) {
        for (int p = 0; p < inst.periodos_por_dia; ++p) {
            for (int s = 0; s < inst.qtd_salas; ++s) {
                int disc_indice = matriz[d][p][s];
                if (disc_indice != -1) {
                    // Busca quantos alunos a matéria tem e qual a capacidade física da sala alocada
                    int alunos = inst.disciplinas[disc_indice].num_alunos; 
                    int capacidade = inst.salas[s].capacidade; 
                    
                    if (alunos > capacidade) {
                        // Conforme a restrição suave S1, cada aluno excedente penaliza 1 ponto 
                        penalty += (alunos - capacidade); 
                    }
                }
            }
        }
    }

    // necessário fazer as restrições suaves (S2, S3, S4) 
    return penalty;
}