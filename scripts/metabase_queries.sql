-- 📊 METABASE UCHUN TAYYOR SQL SO'ROVLAR

-- 1. DAU (Kunlik Aktivlik)
-- Vizualizatsiya: Line Chart yoki Bar Chart
SELECT 
    day, 
    dau 
FROM view_analytics_daily 
ORDER BY day DESC;

-- 2. Funnel (Konversiya)
-- Vizualizatsiya: Bar Chart (Stacked)
SELECT 
    day,
    menu_generated,
    shopping_opened
FROM view_analytics_funnel
ORDER BY day DESC;

-- 3. Retention (Qaytib kelish)
-- Vizualizatsiya: Table
WITH cohort AS (
  SELECT user_id, MIN(date_trunc('day', created_at)) AS day0
  FROM event_logs
  WHERE event_type = 'onboarding_completed'
  GROUP BY 1
),
activity AS (
  SELECT DISTINCT user_id, date_trunc('day', created_at) AS day
  FROM event_logs
)
SELECT
  c.day0 as cohort_date,
  COUNT(*) as cohort_size,
  ROUND(100.0 * SUM(CASE WHEN a.day = c.day0 + interval '1 day' THEN 1 ELSE 0 END) / COUNT(*), 1) as d1_percent,
  ROUND(100.0 * SUM(CASE WHEN a.day = c.day0 + interval '3 day' THEN 1 ELSE 0 END) / COUNT(*), 1) as d3_percent
FROM cohort c
LEFT JOIN activity a ON a.user_id = c.user_id AND a.day > c.day0
GROUP BY 1
ORDER BY 1 DESC;
