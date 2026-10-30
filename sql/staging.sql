-- Reload staging (idempotent). Python loads rows into stg_transactions via to_sql.
DELETE FROM fact_transaction_line;
DELETE FROM stg_transactions;
