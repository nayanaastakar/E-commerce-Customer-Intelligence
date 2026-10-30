-- MySQL 8.0. NOT EXECUTED (no MySQL server in authoring environment).
-- Non-destructive: only creates objects that do not exist.
CREATE DATABASE IF NOT EXISTS ecommerce_ci CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE ecommerce_ci;

CREATE TABLE IF NOT EXISTS stg_transactions (
  source_row_id INT PRIMARY KEY,
  invoice_no    VARCHAR(20)  NOT NULL,
  stock_code    VARCHAR(30)  NOT NULL,
  description   VARCHAR(255) NULL,
  quantity      INT          NOT NULL,
  invoice_date  DATETIME     NOT NULL,
  unit_price    DECIMAL(12,4) NOT NULL,
  customer_id   VARCHAR(20)  NULL,
  country       VARCHAR(80)  NULL,
  line_type     VARCHAR(15)  NOT NULL,   -- sale | cancellation | adjustment
  has_customer  TINYINT(1)   NOT NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS dim_date (
  date_key INT PRIMARY KEY,              -- yyyymmdd
  full_date DATE NOT NULL UNIQUE,
  `year` SMALLINT NOT NULL, `quarter` TINYINT NOT NULL, `month` TINYINT NOT NULL,
  `year_month` CHAR(7) NOT NULL, month_name VARCHAR(10) NOT NULL, day_of_week TINYINT NOT NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS dim_customer (
  customer_key INT AUTO_INCREMENT PRIMARY KEY,
  customer_id  VARCHAR(20) NOT NULL UNIQUE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS dim_product (
  product_key INT AUTO_INCREMENT PRIMARY KEY,
  stock_code  VARCHAR(30) NOT NULL UNIQUE,
  description VARCHAR(255) NULL           -- most recent description seen for the code
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS dim_country (
  country_key INT AUTO_INCREMENT PRIMARY KEY,
  country_name VARCHAR(80) NOT NULL UNIQUE
) ENGINE=InnoDB;

-- Grain: one source invoice line (no invoice-level measures stored -> no join fan-out).
CREATE TABLE IF NOT EXISTS fact_transaction_line (
  line_key      BIGINT AUTO_INCREMENT PRIMARY KEY,
  source_row_id INT NOT NULL UNIQUE,
  invoice_no    VARCHAR(20) NOT NULL,
  date_key      INT NOT NULL,
  customer_key  INT NULL,                 -- NULL = no customer id in source
  product_key   INT NOT NULL,
  country_key   INT NOT NULL,
  invoice_ts    DATETIME NOT NULL,
  quantity      INT NOT NULL,
  unit_price    DECIMAL(12,4) NOT NULL,
  line_value    DECIMAL(16,4) NOT NULL,   -- signed quantity * unit_price
  line_type     ENUM('sale','cancellation','adjustment') NOT NULL,
  CONSTRAINT fk_f_date FOREIGN KEY (date_key) REFERENCES dim_date(date_key),
  CONSTRAINT fk_f_cust FOREIGN KEY (customer_key) REFERENCES dim_customer(customer_key),
  CONSTRAINT fk_f_prod FOREIGN KEY (product_key) REFERENCES dim_product(product_key),
  CONSTRAINT fk_f_ctry FOREIGN KEY (country_key) REFERENCES dim_country(country_key),
  INDEX ix_f_invoice (invoice_no),
  INDEX ix_f_cust_date (customer_key, invoice_ts),
  INDEX ix_f_type_date (line_type, date_key)
) ENGINE=InnoDB;
