#ifndef GRADE_HORARIA_HPP
#define GRADE_HORARIA_HPP

#include "../dados/Instancia.hpp"
#include <vector>
#include <string>

class GradeHoraria{
private:
    const Instancia& inst;

    std::vector<std::vector<std::vector<int>>> matriz;

public: 
    GradeHoraria(const Instancia& instancia);

    bool alocar_aula(int dia, int periodo, int sala_indice, int disciplina_indice);
    void remover_aula(int dia, int periodo, int sala_indice);
    
    int obter_disciplina_na_gaveta(int dia, int periodo, int sala_indice) const;
    bool espaco_esta_livre(int dia, int periodo, int sala_indice) const;


    int calcular_total_penalidades() const;

};

#endif