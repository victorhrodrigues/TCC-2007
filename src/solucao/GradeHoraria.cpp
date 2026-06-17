#include "GradeHoraria.hpp"
#include <iostream>

GradeHoraria::GradeHoraria(const Instancia& instancia) : inst(instancia) {
    // -1 = espaço livre
    matriz.resize(inst.qtd_dias, 
        std::vector<std::vector<int>>(inst.periodos_por_dia, 
            std::vector<int>(inst.qtd_salas, -1)
        )
    );
}

bool GradeHoraria::alocar_aula(int dia, int periodo, int sala_indice, int disciplina_indice) {

    if (dia >= inst.qtd_dias || periodo >= inst.periodos_por_dia || sala_indice >= inst.qtd_salas) {
        return false;
    }
    
  
    if (matriz[dia][periodo][sala_indice] != -1) {
        return false; 
    }

    matriz[dia][periodo][sala_indice] = disciplina_indice;
    return true;
}

void GradeHoraria::remover_aula(int dia, int periodo, int sala_indice) {
    if (dia < inst.qtd_dias && periodo < inst.periodos_por_dia && sala_indice < inst.qtd_salas) {
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
                        // Conforme regulamento da ITC-2007, cada aluno excedente penaliza 1 ponto 
                        penalty += (alunos - capacidade); 
                    }
                }
            }
        }
    }

    // necessário fazer as restrições complexas (S2, S3, S4) 
    return penalty;
}