-- Crear tabla usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    lastanme VARCHAR(255) NOT NULL,
    lastname2 VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL
);

-- Insertar datos de la imagen de DBeaver
INSERT INTO usuarios (id, name, lastanme, lastname2, email) VALUES
(1, 'Regina Valeria', 'Diaz', 'Vazquez', 'rege@gmail.com'),
(2, 'Aro', 'Labastida', 'Perez', 'arro@gmail.com'),
(3, 'Joss', 'Perez', 'Martinez', 'jos@gmail.com'),
(7, 'JossASD', 'PerezCDAS', 'MartinezAS', 'josASC@gmail.com'),
(9, 'fer', 'sacnbbbca', 'asklcal', 'ldkaock'),
(10, 'Dagan Jael', 'Vega', 'Vega', 'daganjy.pro@gmail.com'),
(11, 'ALEJANDRO ISAAC', 'LOPEZ', 'VAZQUEZ', 'alejandroisaacvazquez@gmail.com')
ON CONFLICT (id) DO NOTHING;

-- Actualizar la secuencia para que el próximo ID sea 12
SELECT setval('usuarios_id_seq', (SELECT MAX(id) FROM usuarios));
