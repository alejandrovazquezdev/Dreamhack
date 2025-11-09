-- Crear tabla usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    lastanme VARCHAR(255) NOT NULL,
    lastname2 VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    wallet_link VARCHAR(500)
);

-- Insertar datos de ejemplo
-- NOTA: Todos los usuarios tienen la contraseña 'temporal123'
INSERT INTO usuarios (id, name, lastanme, lastname2, email, password, wallet_link) VALUES
(1, 'Regina Valeria', 'Diaz', 'Vazquez', 'rege@gmail.com', 'scrypt:32768:8:1$hOarnFyAmTCqUhe6$41d20b6fd621eee55edc5970b67a621152130e2f6f3d1db1ca3b5aff7dccb51fdf0c634f458ce339c098076dfbb89ea262b89bc2bb33be6e34868d57e0fe75b7', NULL),
(2, 'Aro', 'Labastida', 'Perez', 'arro@gmail.com', 'scrypt:32768:8:1$hOarnFyAmTCqUhe6$41d20b6fd621eee55edc5970b67a621152130e2f6f3d1db1ca3b5aff7dccb51fdf0c634f458ce339c098076dfbb89ea262b89bc2bb33be6e34868d57e0fe75b7', NULL),
(3, 'Joss', 'Perez', 'Martinez', 'jos@gmail.com', 'scrypt:32768:8:1$hOarnFyAmTCqUhe6$41d20b6fd621eee55edc5970b67a621152130e2f6f3d1db1ca3b5aff7dccb51fdf0c634f458ce339c098076dfbb89ea262b89bc2bb33be6e34868d57e0fe75b7', NULL),
(7, 'JossASD', 'PerezCDAS', 'MartinezAS', 'josASC@gmail.com', 'scrypt:32768:8:1$hOarnFyAmTCqUhe6$41d20b6fd621eee55edc5970b67a621152130e2f6f3d1db1ca3b5aff7dccb51fdf0c634f458ce339c098076dfbb89ea262b89bc2bb33be6e34868d57e0fe75b7', NULL),
(9, 'fer', 'sacnbbbca', 'asklcal', 'ldkaock', 'scrypt:32768:8:1$hOarnFyAmTCqUhe6$41d20b6fd621eee55edc5970b67a621152130e2f6f3d1db1ca3b5aff7dccb51fdf0c634f458ce339c098076dfbb89ea262b89bc2bb33be6e34868d57e0fe75b7', NULL),
(10, 'Dagan Jael', 'Vega', 'Vega', 'daganjy.pro@gmail.com', 'scrypt:32768:8:1$hOarnFyAmTCqUhe6$41d20b6fd621eee55edc5970b67a621152130e2f6f3d1db1ca3b5aff7dccb51fdf0c634f458ce339c098076dfbb89ea262b89bc2bb33be6e34868d57e0fe75b7', NULL),
(11, 'ALEJANDRO ISAAC', 'LOPEZ', 'VAZQUEZ', 'alejandroisaacvazquez@gmail.com', 'scrypt:32768:8:1$hOarnFyAmTCqUhe6$41d20b6fd621eee55edc5970b67a621152130e2f6f3d1db1ca3b5aff7dccb51fdf0c634f458ce339c098076dfbb89ea262b89bc2bb33be6e34868d57e0fe75b7', NULL)
ON CONFLICT (id) DO NOTHING;

-- Actualizar la secuencia para que el próximo ID sea 12
SELECT setval('usuarios_id_seq', (SELECT MAX(id) FROM usuarios));


