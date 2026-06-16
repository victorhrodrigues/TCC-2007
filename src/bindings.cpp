#include <pybind11/pybind11.h>
#include "Instancia.hpp"

namespace py = pybind11;

PYBIND11_MODULE(core_otimizador, m) {
    py::class_<Instancia>(m, "Instancia")
        .def(py::init<>()) // Excede o construtor padrão
        .def_readwrite("nome", &Instancia::nome)
        .def_readwrite("qtd_dias", &Instancia::qtd_dias)
        .def("saudar", &Instancia::saudar);
}