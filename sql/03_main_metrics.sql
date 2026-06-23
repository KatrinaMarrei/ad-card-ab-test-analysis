-- Ключевые метрики A/B-теста по экспериментальным группам.
WITH user_groups AS (
    SELECT DISTINCT
        user_id,
        experiment_group
    FROM events
),
event_metrics AS (
    SELECT
        experiment_group,
        COUNT(DISTINCT user_id) AS users_count,
        SUM(CASE WHEN event_type = 'view_ad' THEN 1 ELSE 0 END) AS views,
        SUM(CASE WHEN event_type = 'contact_seller' THEN 1 ELSE 0 END) AS contacts,
        SUM(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) AS purchases,
        COUNT(DISTINCT CASE WHEN event_type = 'contact_seller' THEN user_id END) AS users_with_contact,
        COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN user_id END) AS users_with_purchase
    FROM events
    GROUP BY experiment_group
),
payment_metrics AS (
    SELECT
        user_groups.experiment_group,
        COUNT(DISTINCT payments.user_id) AS paying_users,
        COALESCE(SUM(payments.amount), 0) AS revenue
    FROM user_groups
    LEFT JOIN payments
        ON user_groups.user_id = payments.user_id
        AND user_groups.experiment_group = payments.experiment_group
    GROUP BY user_groups.experiment_group
)
SELECT
    event_metrics.experiment_group,
    event_metrics.users_count,
    event_metrics.views,
    event_metrics.contacts,
    event_metrics.purchases,
    payment_metrics.paying_users,
    ROUND(payment_metrics.revenue, 2) AS revenue,
    ROUND(1.0 * event_metrics.users_with_contact / NULLIF(event_metrics.users_count, 0), 4) AS contact_conversion_per_user,
    ROUND(1.0 * event_metrics.users_with_purchase / NULLIF(event_metrics.users_count, 0), 4) AS purchase_conversion_per_user,
    ROUND(1.0 * event_metrics.contacts / NULLIF(event_metrics.views, 0), 4) AS contact_rate_from_view,
    ROUND(1.0 * event_metrics.purchases / NULLIF(event_metrics.views, 0), 4) AS purchase_rate_from_view,
    ROUND(1.0 * payment_metrics.revenue / NULLIF(event_metrics.users_count, 0), 2) AS arpu,
    ROUND(1.0 * payment_metrics.revenue / NULLIF(payment_metrics.paying_users, 0), 2) AS arppu
FROM event_metrics
LEFT JOIN payment_metrics
    ON event_metrics.experiment_group = payment_metrics.experiment_group
ORDER BY event_metrics.experiment_group;
