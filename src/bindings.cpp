#include <pybind11/pybind11.h>
#include <pybind11/stl.h> 
#include "dados/Instancia.hpp"
#include "dados/Parser.hpp"
#include "solucao/GradeHoraria.hpp"

namespace py = pybind11;

PYBIND11_MODULE(core_otimizador, m) {
    // struct Disciplina
    py::class_<Disciplina>(m, "Disciplina")
        .def_readonly("id", &Disciplina::id)
        .def_readonly("id_professor", &Disciplina::id_professor)
        .def_readonly("num_aulas", &Disciplina::num_aulas)
        .def_readonly("dias_minimos", &Disciplina::dias_minimos)
        .def_readonly("num_alunos", &Disciplina::num_alunos);

    // struct Sala
    py::class_<Sala>(m, "Sala")
        .def_readonly("id", &Sala::id)
        .def_readonly("capacidade", &Sala::capacidade);

    // classe principal Instancia
    py::class_<Instancia>(m, "Instancia")
        .def(py::init<>())
        .def_readonly("nome", &Instancia::nome)
        .def_readonly("qtd_dias", &Instancia::qtd_dias)
        .def_readonly("periodos_por_dia", &Instancia::periodos_por_dia)
        .def_readonly("disciplinas", &Instancia::disciplinas)
        .def_readonly("salas", &Instancia::salas)
        .def_readonly("qtd_salas", &Instancia::qtd_salas)
        .def_readonly("qtd_disciplinas", &Instancia::qtd_disciplinas);

    // Parser
    py::class_<Parser>(m, "Parser")
        .def_static("carregar_ctt", &Parser::carregar_ctt);

    py::class_<GradeHoraria>(m, "GradeHoraria")
        .def(py::init<const Instancia&>()) // Construtor recebendo a instância
        // Cópia feita no C++ (construtor de cópia): habilita copy.copy e copy.deepcopy no Python
        .def("__copy__", [](const GradeHoraria& self) { return GradeHoraria(self); })
        .def("__deepcopy__", [](const GradeHoraria& self, py::dict) { return GradeHoraria(self); }, py::arg("memo"))
        .def("alocar_aula", &GradeHoraria::alocar_aula)
        .def("remover_aula", &GradeHoraria::remover_aula)
        .def("obter_disciplina_na_gaveta", &GradeHoraria::obter_disciplina_na_gaveta)
        .def("espaco_esta_livre", &GradeHoraria::espaco_esta_livre)
        .def("calcular_total_penalidades", &GradeHoraria::calcular_total_penalidades)
        .def("validar_movimento_viavel", &GradeHoraria::validar_movimento_viavel)
        .def("validar_alocacao_completa", &GradeHoraria::validar_alocacao_completa)
        .def("esta_viavel", &GradeHoraria::esta_viavel)
        .def("obter_pior_gargalo", &GradeHoraria::obter_pior_gargalo)
        .def("conflitos_por_posicao", &GradeHoraria::conflitos_por_posicao)
        .def("tamanho_dominio", &GradeHoraria::tamanho_dominio)
        .def("grau_conflitos", &GradeHoraria::grau_conflitos);
}