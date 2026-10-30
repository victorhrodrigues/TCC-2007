#ifndef GRADE_HORARIA_HPP
#define GRADE_HORARIA_HPP

#include "../dados/Instancia.hpp"
#include <vector>
#include <string>
#include <tuple>
#include <utility>

class GradeHoraria{
private:
    const Instancia& inst;

    // Matriz principal: [DIA] [PERIODO] [SALA] -
    std::vector<std::vector<std::vector<int>>> matriz;

    // Condição H3 (conflitos) - verificação professor já tem aula no horário
    std::vector<std::vector<std::vector<bool>>> matriz_professor_ocupado;

    // condição H3 - verificação se a turma já tiver aula no horário
    std::vector<std::vector<std::vector<bool>>> matriz_curriculo_ocupado;

    // Índices de TODOS os currículos de cada disciplina (relação N:N), calculados uma vez no construtor
    std::vector<std::vector<int>> curriculos_da_disciplina;

    // Pares de disciplinas que não podem ocupar o mesmo período (mesmo professor ou currículo em comum),
    // em vetor plano [c * qtd_disciplinas + o]; inclui c == o (duas aulas da mesma disciplina)
    std::vector<bool> disciplinas_em_conflito;

    // Períodos proibidos para cada disciplina (H4), em vetor plano [(c * qtd_dias + d) * periodos_por_dia + p]
    std::vector<bool> indisponivel;

    bool conflitam(int c, int o) const { return disciplinas_em_conflito[c * inst.qtd_disciplinas + o]; }

public:
    // H4: a disciplina c não pode ter aula no período (d, p); também usada pela ação de período no Python
    bool esta_indisponivel(int c, int d, int p) const { return indisponivel[(c * inst.qtd_dias + d) * inst.periodos_por_dia + p]; }

    GradeHoraria(const Instancia& instancia);

    // Função para verificação do movimento para atender restrições H3 e H4
    bool validar_movimento_viavel(int dia, int periodo, int sala_indice, int disciplina_indice) const;

    bool alocar_aula(int dia, int periodo, int sala_indice, int disciplina_indice);
    void remover_aula(int dia, int periodo, int sala_indice);
    
    int obter_disciplina_na_gaveta(int dia, int periodo, int sala_indice) const;
    bool espaco_esta_livre(int dia, int periodo, int sala_indice) const;


    int calcular_total_penalidades() const;

    bool validar_alocacao_completa() const;

    bool esta_viavel() const;

    std::string obter_pior_gargalo() const;

    // Usadas pela ação de reparo inspirada na IFS de Müller
    std::vector<std::tuple<int, int, int, std::vector<std::pair<int, int>>>> conflitos_por_posicao(int disciplina_indice) const;
    int tamanho_dominio(int disciplina_indice) const;
    int grau_conflitos(int disciplina_indice) const;

    // Currículos de uma disciplina (relação N:N), usados pela ação de período no Python
    const std::vector<int>& curriculos_de(int disciplina_indice) const { return curriculos_da_disciplina[disciplina_indice]; }

    // Todas as aulas alocadas, na ordem dia -> período -> sala: (dia, período, sala, disciplina)
    std::vector<std::tuple<int, int, int, int>> listar_aulas() const;

    // Reconstrução reativa de Geiger (§3.3); devolve (trocou a grade?, aulas que ficaram de fora)
    std::pair<bool, std::vector<int>> reconstruir(const std::vector<int>& prioritarias, unsigned int semente, int max_nao_alocadas);

};

#endif