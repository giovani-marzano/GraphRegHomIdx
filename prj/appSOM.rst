Aplicativo SOM
##############

:Autor: Giovani Melo Marzano

Objetivo: Permitir ao usuário gerar um Self Organizing Map (SOM) a partir de uma
base de dados.

Glossário
=========

Atributo
    Um atributo associa um valor a uma característica de um objeto. Por exemplo,
    em uma flor vermelha, *vermelho* é o valor do atributo *cor* da flor.

CSV
    Comma-Separeted Values. Formato de arquivo texto para dados tabulares. Cada
    linha do arquivo é uma linha da tabela. As colunas são separadas por um
    caractere ecolhido para este fim, originalmente usa-se a vírgula (,).

Elemento
    Usado aqui para referenciar cada amostra a ser usada no treinamento do SOM.
    Um elemento é um ponto no espaço n-dimensional associado ao conjunto de
    dados em estudo. É caracterizado por uma lista de atributos. Vendo o
    conjunto de dados como uma tabela, cada linha é um elemento.

Graphml
    Formato de arquivo utilizado para a representação de grafos.

SOM
    Self Organizing Map. Um tipo de rede neuronal artificial.

Entradas
========

Dados que o usuário deve fornecer ao aplicativo para seu funcionamento.

1. Arquivo csv com os elementos a serem utilizados no treinamento do SOM.

    Cada linha do arquivo é um elemento. A primeira linha deve ser um cabeçalho
    com o nome de cada columa do csv. As colunas são interpretadas como os
    atributos dos elementos. Os nomes das colunas (atributos) devem ser únicos.

2. Lista dos atributos que servem como identificação dos elementos.

    O usuário lista os nomes dos atributos que em conjunto identificam os
    elementos. Estes atributos não serão utilizados no treinamento do SOM, mas
    serão replicados nos arquivos de saída relevantes.

3. Lista dos atributos de valor dos elementos.

    O usuário lista os nomes dos atributos que constituem o vetor de valores dos
    elementos. Estes atributos são utilizados no treinamento do SOM. Os valores
    desses atributos devem ser numéricos.

4. Parâmetros de configuração para treinamanto do SOM.

    Parâmetros que controlam o algoritmo SOM. Os parâmatros existentes e suas
    definições podem ser vistas na string de documentação da classe *Config* do
    pacote *SOM*.

5. Nome do arquivo graphml onde o SOM gerado será salvo.

6. Nome do arquivo csv onde a atibuição dos elementos aos nodos do SOM será
   salva.

Saídas
======

1. Arquivo graphml com o SOM gerado.

    O SOM é salvo como um grafo em que cada vértice representa um nodo do SOM e
    as arestas representam as relações de vizinhança entre os nodos do SOM.

2. Arquivo CSV que traz a associação de cada elemento da base de dados ao nodo
   do SOM a que este elemento foi atribuído.
