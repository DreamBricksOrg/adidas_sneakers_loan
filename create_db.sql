CREATE DATABASE IF NOT EXISTS adidas;

USE adidas;

CREATE TABLE IF NOT EXISTS Usuario (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(255),
    nome_iniciais VARCHAR(255),
    sobrenome VARCHAR(255),
    idade INT,
    email VARCHAR(255),
    documento VARCHAR(255),
    telefone VARCHAR(255),
    local_de_locacao VARCHAR(255),
    genero VARCHAR(255),
    confirmacao_sms BOOLEAN,
    dados_criptografados VARCHAR(14000)
);

CREATE TABLE IF NOT EXISTS Promotor (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(255),
    usuario VARCHAR(255),
    senha VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS Tenis (
    id INT PRIMARY KEY AUTO_INCREMENT,
    tamanho DOUBLE,
    quantidade INT,
    Estande INT,
    FOREIGN KEY (Estande) REFERENCES Estande(id)
);

CREATE TABLE IF NOT EXISTS Locacao (
    id INT PRIMARY KEY AUTO_INCREMENT,
    Tenis INT,
    Usuario INT,
    Promotor INT,
    Local INT,
    Estande INT,
    data_inicio DATE,
    data_fim DATE,
    status VARCHAR(255),
    FOREIGN KEY (Tenis) REFERENCES Tenis(id),
    FOREIGN KEY (Usuario) REFERENCES Usuario(id),
    FOREIGN KEY (Promotor) REFERENCES Promotor(id),
    FOREIGN KEY (Local) REFERENCES Local(id),
    FOREIGN KEY (Estande) REFERENCES Estande(id)
);

CREATE TABLE IF NOT EXISTS Local (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS CodigoVerificacao (
    id INT PRIMARY KEY AUTO_INCREMENT,
    codigo INT,
    status VARCHAR(255),
    Usuario INT,
    FOREIGN KEY (Usuario) REFERENCES Usuario(id)
);

CREATE TABLE IF NOT EXISTS Avaliacao (
    id INT PRIMARY KEY AUTO_INCREMENT,
    Usuario INT,
    conforto INT,
    estabilidade INT,
    estilo INT,
    compraria BOOLEAN,
    FOREIGN KEY (Usuario) REFERENCES Usuario(id)
);

CREATE TABLE IF NOT EXISTS Fotos (
    id INT PRIMARY KEY AUTO_INCREMENT,
    Usuario INT,
    documento MEDIUMBLOB,
    retrato MEDIUMBLOB,
    FOREIGN KEY (Usuario) REFERENCES Usuario(id)
);

CREATE TABLE IF NOT EXISTS LogTenis (
    id INT PRIMARY KEY AUTO_INCREMENT,
    Promotor INT,
    Local INT,
    tamanho INT,
    quantidadeOriginal INT,
    quantidadeNova INT,
    FOREIGN KEY (Promotor) REFERENCES Promotor(id),
    FOREIGN KEY (Local) REFERENCES Local(id)
);

CREATE TABLE IF NOT EXISTS Estande (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(255)
);