-- Финальный датасет для EDA и статистического тестирования.
-- Все пропуски заменены на нули, бинарные признаки представлены как 0/1.
WITH user_groups AS (
    SELECT DISTINCT
        user_id,
        experiment_group
    FROM events
),
event_metrics AS (
    SELECT
        user_id,
        experiment_group,
        SUM(CASE WHEN event_type = 'view_ad' THEN 1 ELSE 0 END) AS views,
        SUM(CASE WHEN event_type = 'add_to_favorite' THEN 1 ELSE 0 END) AS favorites,
        SUM(CASE WHEN event_type = 'contact_seller' THEN 1 ELSE 0 END) AS contacts,
        SUM(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) AS purchases
    FROM events
    GROUP BY user_id, experiment_group
),
payment_metrics AS (
    SELECT
        user_id,
        experiment_group,
        SUM(amount) AS revenue
    FROM payments
    GROUP BY user_id, experiment_group
)
SELECT
    users.user_id,
    user_groups.experiment_group,
    users.region,
    users.device,
    users.user_segment,
    CAST(COALESCE(event_metrics.views, 0) AS INTEGER) AS views,
    CAST(COALESCE(event_metrics.favorites, 0) AS INTEGER) AS favorites,
    CAST(COALESCE(event_metrics.contacts, 0) AS INTEGER) AS contacts,
    CAST(COALESCE(event_metrics.purchases, 0) AS INTEGER) AS purchases,
    ROUND(COALESCE(payment_metrics.revenue, 0), 2) AS revenue,
    CAST(CASE WHEN COALESCE(event_metrics.contacts, 0) > 0 THEN 1 ELSE 0 END AS INTEGER) AS has_contact,
    CAST(CASE WHEN COALESCE(event_metrics.purchases, 0) > 0 THEN 1 ELSE 0 END AS INTEGER) AS has_purchase,
    CAST(CASE WHEN COALESCE(payment_metrics.revenue, 0) > 0 THEN 1 ELSE 0 END AS INTEGER) AS is_payer
FROM user_groups
INNER JOIN users
    ON user_groups.user_id = users.user_id
LEFT JOIN event_metrics
    ON user_groups.user_id = event_metrics.user_id
    AND user_groups.experiment_group = event_metrics.experiment_group
LEFT JOIN payment_metrics
    ON user_groups.user_id = payment_metrics.user_id
    AND user_groups.experiment_group = payment_metrics.experiment_group
ORDER BY users.user_id;
