#include "Parser.hpp"
#include <fstream>
#include <sstream>
#include <iostream>

bool Parser::carregar_ctt(const std::string& caminho_arquivo, Instancia& instancia) {
    std::ifstream arquivo(caminho_arquivo);
    if (!arquivo.is_open()) {
        std::cerr << "Erro ao abrir o arquivo: " << caminho_arquivo << std::endl;
        return false;
    }

    std::string linha;
    std::string tag;

    // cabeçalho
    while (std::getline(arquivo, linha)) {
        if (linha.empty() || linha == "\r") continue;

        std::stringstream ss(linha);
        ss >> tag;

        if (tag == "Name:") ss >> instancia.nome;
        else if (tag == "Courses:") ss >> instancia.qtd_disciplinas;
        else if (tag == "Rooms:") ss >> instancia.qtd_salas;
        else if (tag == "Days:") ss >> instancia.qtd_dias;
        else if (tag == "Periods_per_day:") ss >> instancia.periodos_por_dia;
        else if (tag == "Curricula:") ss >> instancia.qtd_curriculos;
        else if (tag == "Constraints:") ss >> instancia.qtd_restricoes;
        else if (tag == "COURSES:") {
            break; // Sai do cabeçalho e começa a ler os blocos
        }
    }

    // for para leitura de COURSE
    for (int i = 0; i < instancia.qtd_disciplinas; ++i) {
        Disciplina disc;
        arquivo >> disc.id >> disc.id_professor >> disc.num_aulas >> disc.dias_minimos >> disc.num_alunos;
        instancia.disciplinas.push_back(disc);
    }

    while (arquivo >> tag && tag != "ROOMS:");

    // for para leitura de ROOMS
    for (int i = 0; i < instancia.qtd_salas; ++i) {
        Sala sala;
        arquivo >> sala.id >> sala.capacidade;
        instancia.salas.push_back(sala);
    }

    while (arquivo >> tag && tag != "CURRICULA:");

    // for para leitura de Curricula
    for (int i = 0; i < instancia.qtd_curriculos; ++i) {
        Curriculo curr;
        int num_disciplinas_no_curr = 0;
        
        arquivo >> curr.id >> num_disciplinas_no_curr;
        for (int j = 0; j < num_disciplinas_no_curr; ++j) {
            std::string id_disc;
            arquivo >> id_disc;
            curr.ids_disciplinas.push_back(id_disc);
        }
        instancia.curriculos.push_back(curr);
    }

    while (arquivo >> tag && tag != "UNAVAILABILITY_CONSTRAINTS:");

    // for para leitura deI UNAVAILABILITY_CONSTRAINTS
    for (int i = 0; i < instancia.qtd_restricoes; ++i) {
        Indisponibilidade ind;
        arquivo >> ind.id_disciplina >> ind.dia >> ind.periodo;
        instancia.indisponibilidades.push_back(ind);
    }

    arquivo.close();
    return true;
}