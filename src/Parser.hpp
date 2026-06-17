#ifndef PARSER_HPP
#define PARSER_HPP

#include "Instancia.hpp"
#include <string>

class Parser {
public:
    // Recebe o caminho do arquivo e preenche a Instancia por referência
    static bool carregar_ctt(const std::string& caminho_arquivo, Instancia& instancia);
};

#endif