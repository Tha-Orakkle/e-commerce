-- DROP DATABASE
DROP DATABASE test_ecommerce;
CREATE DATABASE test_ecommerce;
GRANT ALL PRIVILEGES ON test_ecommerce.* TO admin@localhost;
FLUSH PRIVILEGES
