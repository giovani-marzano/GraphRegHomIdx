-- Clusrter de vertice
CREATE TABLE clst_node(
     id     INTEGER PRIMARY KEY
    ,name   TEXT
    ,color  TEXT
);

-- Clusrter de aresta
CREATE TABLE clst_edge(
     id     INTEGER PRIMARY KEY
    ,name   TEXT
    ,color  TEXT
);

-- Instancia de cluster de aresta. Estas sao as arestas do grafo de cluster
CREATE TABLE inst_clst_edge(
     id     INTEGER PRIMARY KEY
    ,clst   INTEGER -- Cluster de arestas a que esta intancia pertence
    ,src    INTEGER -- Cluster de vertice origem desta aresta
    ,tgt    INTEGER -- Cluster de vertice destino desta aresta

    ,FOREIGN KEY (clst) REFERENCES clst_edge (id)
    ,FOREIGN KEY (src) REFERENCES clst_node (id)
    ,FOREIGN KEY (tgt) REFERENCES clst_node (id)
);

-- Vertices do grafo original
CREATE TABLE node(
     id     INTEGER PRIMARY KEY
    ,label  TEXT
    ,clst   INTEGER -- Cluster a que este vertice pertence

    ,FOREIGN KEY (clst) REFERENCES clst_node (id)
);

-- Arestas do grafo original
CREATE TABLE edge(
     id     INTEGER PRIMARY KEY
    ,label  TEXT
    ,src    INTEGER -- Vertice de origem da aresta
    ,tgt    INTEGER -- Vertice de destino da aresta
    ,clst   INTEGER -- Cluster a que esta aresta pertence
    ,inst_clst INTEGER -- Instancia de cluster a que esta aresta pertence

    ,FOREIGN KEY (clst) REFERENCES clst_edge (id)
    ,FOREIGN KEY (inst_clst) REFERENCES inst_clst_edge (id)
    ,FOREIGN KEY (src) REFERENCES node (id)
    ,FOREIGN KEY (tgt) REFERENCES node (id)
);

-- Atributos de vertices e arestas
CREATE TABLE attribute(
     id     INTEGER PRIMARY KEY
    ,name   TEXT
    ,type   TEXT
);

-- Valores de atributos de vertices
CREATE TABLE node_attr_value(
     node    INTEGER
    ,id_attr INTEGER
    ,value   NONE

    ,PRIMARY KEY (node, id_attr)
    ,FOREIGN KEY (node) REFERENCES node (id)
    ,FOREIGN KEY (id_attr) REFERENCES attribute (id)
);

-- Valores de atributos de arestas
CREATE TABLE edge_attr_value(
     edge    INTEGER
    ,id_attr INTEGER
    ,value   NONE

    ,PRIMARY KEY (edge, id_attr)
    ,FOREIGN KEY (edge) REFERENCES edge (id)
    ,FOREIGN KEY (id_attr) REFERENCES attribute (id)
);
