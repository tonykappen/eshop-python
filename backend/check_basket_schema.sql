-- Check if basket schema exists and has tables
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables 
WHERE schemaname = 'basket'
ORDER BY tablename;

-- Check row counts in basket schema tables
SELECT 
    'shopping_carts' as table_name,
    COUNT(*) as row_count
FROM basket.shopping_carts
UNION ALL
SELECT 
    'shopping_cart_items' as table_name,
    COUNT(*) as row_count
FROM basket.shopping_cart_items;
