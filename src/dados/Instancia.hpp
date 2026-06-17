#ifndef INSTANCIA_HPP
#define INSTANCIA_HPP

#include <string>
#include <vector>

struct Disciplina 
{
    std::string id;
    std::string id_professor;
    int num_aulas;
    int dias_minimos;
    int num_alunos;
};

struct Sala
{
    std::string id;
    int capacidade;
};

struct Curriculo
{
    std::string id;
    std::vector<std::string> ids_disciplinas;
};

struct Indisponibilidade 
{
    std::string id_disciplina;
    int dia;
    int periodo;
};

class Instancia {
public:
    std::string nome;
    int qtd_disciplinas;
    int qtd_salas;
    int qtd_dias;
    int periodos_por_dia;
    int qtd_curriculos;
    int qtd_restricoes;

    std::vector<Disciplina> disciplinas;
    std::vector<Sala> salas;
    std::vector<Curriculo> curriculos;
    std::vector<Indisponibilidade> indisponibilidades;

    // declara valores iniciais nulos ou zero - depende do tipo do dado, evitar iniciar dentro do {} pois é menos eficiente e pode capturar um lixo na memória
    Instancia() : nome(""), qtd_disciplinas(0), qtd_salas(0), qtd_dias(0), 
                  periodos_por_dia(0), qtd_curriculos(0), qtd_restricoes(0) {}
};

#endif