# Importa o módulo que você acabou de compilar em C++
import core_otimizador 

# Cria o objeto C++ dentro do Python
minha_instancia = core_otimizador.Instancia()

# Altera atributos diretamente do Python para a memória do C++
minha_instancia.nome = "ITC-2007 Track 3"
minha_instancia.qtd_dias = 5

# Chama um método do C++
resultado = minha_instancia.saudar()

print(resultado)
print(f"Dias configurados no C++: {minha_instancia.qtd_dias}")