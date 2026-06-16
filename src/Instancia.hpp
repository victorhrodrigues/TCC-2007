#ifndef INSTANCIA_HPP
#define INSTANCIA_HPP

#include <string>

class Instancia {
public:
    std::string nome;
    int qtd_dias;

    Instancia() : nome("Não carregada"), qtd_dias(0) {}

    std::string saudar() {
        return "C++ está pronto! Instância: " + nome;
    }
};

#endif