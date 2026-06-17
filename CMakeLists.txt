cmake_minimum_required(VERSION 3.12)
project(core_otimizador CXX)

# Força o uso do C++ moderno (C++17 ou superior)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Baixa e configura o pybind11 automaticamente no projeto
include(FetchContent)
FetchContent_Declare(
  pybind11
  GIT_REPOSITORY https://github.com/pybind/pybind11.git
  GIT_TAG        v2.11.1 # Versão estável do pybind11
)
FetchContent_MakeAvailable(pybind11)

# Define quais arquivos C++ serão compilados
#file(GLOB SOURCES "src/*.cpp")
set(SOURCES
    src/bindings.cpp
    src/dados/Parser.cpp
    src/solucao/GradeHoraria.cpp
)

# Cria o módulo nativo para o Python usando o pybind11
pybind11_add_module(core_otimizador ${SOURCES})

# Informa onde estão os arquivos de cabeçalho (.hpp)
target_include_directories(core_otimizador PRIVATE 
  src
  src/dados
  src/solucao
)
# Força o compilador a salvar o arquivo .pyd diretamente na raiz do projeto
set_target_properties(core_otimizador PROPERTIES LIBRARY_OUTPUT_DIRECTORY "${CMAKE_SOURCE_DIR}")