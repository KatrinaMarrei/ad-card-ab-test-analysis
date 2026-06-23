"""Вспомогательные функции для статистической проверки A/B-теста."""

import numpy as np
from scipy import stats


def proportion_z_test(control_successes, control_total, test_successes, test_total):
    """Считает двусторонний z-тест для двух долей вручную."""
    if control_total <= 0 or test_total <= 0:
        raise ValueError("Размеры групп должны быть положительными.")

    control_rate = control_successes / control_total
    test_rate = test_successes / test_total
    absolute_difference = test_rate - control_rate
    relative_difference = absolute_difference / control_rate if control_rate != 0 else np.nan

    # Посчитать статистику z-критерия через объединенную долю.
    pooled_rate = (control_successes + test_successes) / (control_total + test_total)
    standard_error = np.sqrt(
        pooled_rate
        * (1 - pooled_rate)
        * (1 / control_total + 1 / test_total)
    )

    if standard_error == 0:
        z_stat = np.nan
        p_value = np.nan
    else:
        z_stat = absolute_difference / standard_error
        p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))

    return {
        "control_rate": control_rate,
        "test_rate": test_rate,
        "absolute_difference": absolute_difference,
        "relative_difference": relative_difference,
        "z_stat": z_stat,
        "p_value": p_value,
    }


def bootstrap_mean_diff(control_values, test_values, n_bootstrap=10000, random_state=42):
    """Считает bootstrap-разницу средних: среднее test минус среднее control."""
    control_values = np.asarray(control_values, dtype=float)
    test_values = np.asarray(test_values, dtype=float)

    if len(control_values) == 0 or len(test_values) == 0:
        raise ValueError("Обе выборки должны быть непустыми.")

    rng = np.random.default_rng(random_state)
    control_mean = control_values.mean()
    test_mean = test_values.mean()
    observed_difference = test_mean - control_mean

    # Выполнить bootstrap батчами, чтобы не держать большую матрицу в памяти.
    batch_size = 500
    bootstrap_differences = np.empty(n_bootstrap)
    null_differences = np.empty(n_bootstrap)

    # Построить bootstrap-распределение при нулевой гипотезе.
    pooled_mean = np.concatenate([control_values, test_values]).mean()
    control_null_values = control_values - control_mean + pooled_mean
    test_null_values = test_values - test_mean + pooled_mean

    for start in range(0, n_bootstrap, batch_size):
        stop = min(start + batch_size, n_bootstrap)
        current_batch_size = stop - start

        control_samples = rng.choice(
            control_values,
            size=(current_batch_size, len(control_values)),
            replace=True,
        )
        test_samples = rng.choice(
            test_values,
            size=(current_batch_size, len(test_values)),
            replace=True,
        )
        bootstrap_differences[start:stop] = test_samples.mean(axis=1) - control_samples.mean(axis=1)

        control_null_samples = rng.choice(
            control_null_values,
            size=(current_batch_size, len(control_null_values)),
            replace=True,
        )
        test_null_samples = rng.choice(
            test_null_values,
            size=(current_batch_size, len(test_null_values)),
            replace=True,
        )
        null_differences[start:stop] = test_null_samples.mean(axis=1) - control_null_samples.mean(axis=1)

    ci_lower, ci_upper = np.percentile(bootstrap_differences, [2.5, 97.5])
    bootstrap_p_value = np.mean(np.abs(null_differences) >= abs(observed_difference))

    return {
        "control_mean": control_mean,
        "test_mean": test_mean,
        "observed_difference": observed_difference,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "bootstrap_p_value": bootstrap_p_value,
    }


def mann_whitney_test(control_values, test_values):
    """Считает двусторонний непараметрический тест Манна-Уитни."""
    statistic, p_value = stats.mannwhitneyu(
        control_values,
        test_values,
        alternative="two-sided",
    )

    return {
        "statistic": statistic,
        "p_value": p_value,
    }


def format_percent(value):
    """Форматирует число как процент с двумя знаками после запятой."""
    if value is None or np.isnan(value):
        return "nan"
    return f"{value:.2%}"


def format_money(value):
    """Форматирует денежное значение с двумя знаками после запятой."""
    if value is None or np.isnan(value):
        return "nan"
    return f"{value:.2f}"


def format_p_value(value):
    """Форматирует p-value без лишних десятичных хвостов."""
    if value is None or np.isnan(value):
        return "nan"
    return f"{value:.6f}" if value < 0.01 else f"{value:.4f}"
