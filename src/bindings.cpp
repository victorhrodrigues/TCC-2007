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
        .def_readonly("salas", &Instancia::salas);

    // Parser
    py::class_<Parser>(m, "Parser")
        .def_static("carregar_ctt", &Parser::carregar_ctt);

    py::class_<GradeHoraria>(m, "GradeHoraria")
        .def(py::init<const Instancia&>()) // Construtor recebendo a instância
        .def("alocar_aula", &GradeHoraria::alocar_aula)
        .def("remover_aula", &GradeHoraria::remover_aula)
        .def("obter_disciplina_na_gaveta", &GradeHoraria::obter_disciplina_na_gaveta)
        .def("espaco_esta_livre", &GradeHoraria::espaco_esta_livre)
        .def("calcular_total_penalidades", &GradeHoraria::calcular_total_penalidades);
}