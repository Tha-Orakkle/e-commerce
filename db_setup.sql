-- DROP DATABASE
DROP DATABASE IF EXISTS test_ecommerce;
CREATE DATABASE test_ecommerce;
GRANT ALL PRIVILEGES ON test_ecommerce.* TO orakkle@localhost;
FLUSH PRIVILEGES
