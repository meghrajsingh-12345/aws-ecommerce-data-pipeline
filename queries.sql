-- queries.sql
-- Run these in the Athena console (or via the AWS CLI) once the Glue Crawler
-- has cataloged the "processed" Parquet data. All queries hit
-- ecommerce_catalog.orders_processed directly — there is no database server,
-- Athena reads straight from S3 using the schema in the Glue Data Catalog.

-- 1. Monthly revenue trend
SELECT
    order_year,
    order_month,
    ROUND(SUM(total_amount), 2) AS monthly_revenue,
    COUNT(DISTINCT order_id)    AS total_orders
FROM ecommerce_catalog.orders_processed
GROUP BY order_year, order_month
ORDER BY order_year, order_month;

-- 2. Top 5 product categories by revenue
SELECT
    category,
    ROUND(SUM(total_amount), 2) AS revenue,
    COUNT(*)                    AS units_sold
FROM ecommerce_catalog.orders_processed
GROUP BY category
ORDER BY revenue DESC
LIMIT 5;

-- 3. Top 10 customers by lifetime spend
SELECT
    customer_id,
    ROUND(SUM(total_amount), 2) AS lifetime_spend,
    COUNT(DISTINCT order_id)    AS num_orders
FROM ecommerce_catalog.orders_processed
GROUP BY customer_id
ORDER BY lifetime_spend DESC
LIMIT 10;

-- 4. Regional performance — average order value by region
SELECT
    region,
    ROUND(AVG(total_amount), 2) AS avg_order_value,
    COUNT(*)                    AS total_orders
FROM ecommerce_catalog.orders_processed
GROUP BY region
ORDER BY avg_order_value DESC;

-- 5. Partition pruning example — this query only scans the June 2026
--    partition's files, not the whole table, because we partitioned by
--    order_year/order_month. This is where partitioning saves real money.
SELECT category, ROUND(SUM(total_amount), 2) AS revenue
FROM ecommerce_catalog.orders_processed
WHERE order_year = 2026 AND order_month = 6
GROUP BY category
ORDER BY revenue DESC;
