Aplicativo de manipulação de grafos
###################################

Funcionalidades
===============

Carregamento de grafos
----------------------

_`RF001`: Carregamento de grafo a partir de arquivo graphml.

    O programa lê o arquivo graphml importando os nodos, as arestas, e os
    atributos de grafo, nodos e arestas.

_`RF002`: Carregamento de grafo a partir de arquivo csv.

    _`RF002.01`: O programa lê um arquivo csv que contém uma aresta por linha e
    cada linha possui 3 a 4 colunas: nodo de origem, nodo de destino, relação
    (tipo) da aresta e, opcionalmente, peso da aresta. O peso da aresta deve ser um valor numérico.

    _`RF002.02`: O usuário deve poder escolher se quer que se crie um atributo
    de aresta numérico para representar o peso da aresta. O valor default para o
    peso, caso a coluna de peso não exista no csv, é 1 para cada ocorrência de
    uma aresta no arquivo.

    _`RF002.03`: Caso uma aresta pareça mais de uma vez no arquivo csv, o peso
    das linhas serão acumulados na aresta, caso o atributo de peso tenha sido
    criado. Se não há atributo de peso, a aresta será criada apenas uma vez como
    se ocorresse apenas uma vez no arquivo.
        
    _`RF002.04`: O usuário deve poder fornecer o nome que quer para o atributo
    de peso. Se a coluna de peso estiver presente no arquivo, o nome desta
    coluna deve ser o default para o nome do atributo de peso.

Salvamento de grafos
--------------------

_`RF003`: Salvamento de grafo em um arquivo graphml. São salvos os nodos,
arestas e atributos de grafo, nodos e arestas.

Importação de atributos
-----------------------

_`RF004`: Importa atributos de nodos ou arestas a partir de arquivos csv.

    Para nodos o arquivo deve ter uma coluna com os identificadores dos nodos e
    uma com os valores do atributo. Para as arestas, devem haver de 2 a 3 colunas que
    permitam identificar as arestas (nodo origem, nodo destino, tipo da aresta)
    e uma com os valores dos atributos. O usuário deve poder indicar que colunas
    presentes no arquivo cumprem cada papel. No caso de arestas, se não houver
    coluna com o tipo da aresta, o usuário deve fornecer um valor para tipo que
    será assumido para todas as arestas do arquivo.

    Em todos os casos o usuário deverá especificar o tipo do atributo que está
    sendo importado: inteiro, ponto flutuante ou string.

Exportação de atributos
-----------------------

Idéias
======

Questões
========
