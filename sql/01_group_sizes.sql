-- Проверка размеров экспериментальных групп и их долей.
WITH group_sizes AS (
    SELECT
        experiment_group,
        COUNT(DISTINCT user_id) AS users_count
    FROM events
    GROUP BY experiment_group
),
total_users AS (
    SELECT
        COUNT(DISTINCT user_id) AS total_users_count
    FROM events
)
SELECT
    group_sizes.experiment_group,
    group_sizes.users_count,
    ROUND(1.0 * group_sizes.users_count / total_users.total_users_count, 4) AS users_share
FROM group_sizes
CROSS JOIN total_users
ORDER BY group_sizes.experiment_group;
