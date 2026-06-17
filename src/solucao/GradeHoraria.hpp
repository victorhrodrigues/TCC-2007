#ifndef GRADE_HORARIA_HPP
#define GRADE_HORARIA_HPP

#include "../dados/Instancia.hpp"
#include <vector>
#include <string>

class GradeHoraria{
private:
    const Instancia& inst;

    // Matriz principal: [DIA] [PERIODO] [SALA] -
    std::vector<std::vector<std::vector<int>>> matriz;

    // Condição H3 (conflitos) - verificação professor já tem aula no horário
    std::vector<std::vector<std::vector<bool>>> matriz_professor_ocupado;

    // condição H3 - verificação se a turma já tiver aula no horário
    std::vector<std::vector<std::vector<bool>>> matriz_curriculo_ocupado;

    int obter_index_curriculo_da_disciplina(int disciplina_idx) const;

public: 
    GradeHoraria(const Instancia& instancia);

    // Função para verificação do movimento para atender restrições H3 e H4
    bool validar_movimento_viavel(int dia, int periodo, int sala_indice, int disciplina_indice) const;

    bool alocar_aula(int dia, int periodo, int sala_indice, int disciplina_indice);
    void remover_aula(int dia, int periodo, int sala_indice);
    
    int obter_disciplina_na_gaveta(int dia, int periodo, int sala_indice) const;
    bool espaco_esta_livre(int dia, int periodo, int sala_indice) const;


    int calcular_total_penalidades() const;

};

#endif