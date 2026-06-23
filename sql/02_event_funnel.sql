-- Расчет событийной воронки по группам эксперимента.
SELECT
    experiment_group,
    SUM(CASE WHEN event_type = 'view_ad' THEN 1 ELSE 0 END) AS views,
    SUM(CASE WHEN event_type = 'add_to_favorite' THEN 1 ELSE 0 END) AS favorites,
    SUM(CASE WHEN event_type = 'contact_seller' THEN 1 ELSE 0 END) AS contacts,
    SUM(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) AS purchases,
    ROUND(
        1.0 * SUM(CASE WHEN event_type = 'add_to_favorite' THEN 1 ELSE 0 END)
        / NULLIF(SUM(CASE WHEN event_type = 'view_ad' THEN 1 ELSE 0 END), 0),
        4
    ) AS favorite_rate_from_view,
    ROUND(
        1.0 * SUM(CASE WHEN event_type = 'contact_seller' THEN 1 ELSE 0 END)
        / NULLIF(SUM(CASE WHEN event_type = 'view_ad' THEN 1 ELSE 0 END), 0),
        4
    ) AS contact_rate_from_view,
    ROUND(
        1.0 * SUM(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END)
        / NULLIF(SUM(CASE WHEN event_type = 'view_ad' THEN 1 ELSE 0 END), 0),
        4
    ) AS purchase_rate_from_view
FROM events
GROUP BY experiment_group
ORDER BY experiment_group;
