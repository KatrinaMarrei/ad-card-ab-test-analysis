"""Генерация синтетических данных для учебного A/B-теста."""

from pathlib import Path

import numpy as np
import pandas as pd


RANDOM_SEED = 42
N_USERS = 12_000
N_ADS = 4_500

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"


def weighted_choice(rng, values, probabilities, size):
    """Возвращает случайную выборку с заданными вероятностями."""
    return rng.choice(values, size=size, p=probabilities)


def generate_users(rng):
    """Создает пользователей и назначение в группы эксперимента."""
    user_ids = np.arange(1, N_USERS + 1)

    # Сгенерировать базовые признаки пользователей.
    users = pd.DataFrame(
        {
            "user_id": user_ids,
            "registration_date": pd.to_datetime("2025-01-01")
            + pd.to_timedelta(rng.integers(0, 420, size=N_USERS), unit="D"),
            "region": weighted_choice(
                rng,
                ["Moscow", "Saint Petersburg", "Ural", "Siberia", "South", "Volga"],
                [0.24, 0.16, 0.15, 0.15, 0.13, 0.17],
                N_USERS,
            ),
            "device": weighted_choice(
                rng,
                ["android", "ios", "desktop", "mobile_web"],
                [0.42, 0.25, 0.22, 0.11],
                N_USERS,
            ),
            "user_segment": weighted_choice(
                rng,
                ["new", "regular", "power_seller", "bargain_hunter"],
                [0.28, 0.45, 0.09, 0.18],
                N_USERS,
            ),
        }
    )

    # Разделить пользователей на группы эксперимента.
    experiment_groups = np.array(["control"] * (N_USERS // 2) + ["test"] * (N_USERS - N_USERS // 2))
    rng.shuffle(experiment_groups)
    assignment = pd.DataFrame({"user_id": user_ids, "experiment_group": experiment_groups})

    return users, assignment


def generate_ads(rng, users):
    """Создает объявления с разными категориями, ценами и качеством карточки."""
    categories = ["electronics", "real_estate", "auto", "jobs", "services", "home_goods", "fashion"]
    category_probabilities = [0.24, 0.10, 0.12, 0.08, 0.14, 0.19, 0.13]
    category_price_params = {
        "electronics": (8.4, 0.65),
        "real_estate": (13.3, 0.75),
        "auto": (12.6, 0.70),
        "jobs": (7.5, 0.55),
        "services": (7.9, 0.60),
        "home_goods": (8.0, 0.70),
        "fashion": (7.1, 0.55),
    }

    ad_categories = weighted_choice(rng, categories, category_probabilities, N_ADS)
    prices = [
        rng.lognormal(mean=category_price_params[category][0], sigma=category_price_params[category][1])
        for category in ad_categories
    ]

    sellers = users.loc[users["user_segment"].isin(["regular", "power_seller"]), "user_id"].to_numpy()
    seller_probabilities = np.where(
        users.loc[users["user_segment"].isin(["regular", "power_seller"]), "user_segment"].to_numpy()
        == "power_seller",
        4.0,
        1.0,
    )
    seller_probabilities = seller_probabilities / seller_probabilities.sum()

    ads = pd.DataFrame(
        {
            "ad_id": np.arange(1, N_ADS + 1),
            "seller_id": rng.choice(sellers, size=N_ADS, p=seller_probabilities),
            "category": ad_categories,
            "price": np.round(np.clip(prices, 100, 35_000_000), 2),
            "created_at": pd.to_datetime("2026-02-01")
            + pd.to_timedelta(rng.integers(0, 58, size=N_ADS), unit="D"),
            "has_photo": rng.choice([0, 1], size=N_ADS, p=[0.12, 0.88]),
            "description_length": np.clip(rng.normal(420, 210, size=N_ADS).astype(int), 30, 1_800),
        }
    )

    return ads


def get_probability_multiplier(row):
    """Считает поправку к вероятностям событий по признакам пользователя."""
    device_multiplier = {
        "android": 1.00,
        "ios": 1.08,
        "desktop": 0.92,
        "mobile_web": 0.84,
    }[row["device"]]
    segment_multiplier = {
        "new": 0.82,
        "regular": 1.00,
        "power_seller": 1.18,
        "bargain_hunter": 1.10,
    }[row["user_segment"]]
    region_multiplier = {
        "Moscow": 1.08,
        "Saint Petersburg": 1.04,
        "Ural": 0.98,
        "Siberia": 0.95,
        "South": 0.96,
        "Volga": 0.99,
    }[row["region"]]

    return device_multiplier * segment_multiplier * region_multiplier


def generate_events(rng, users, ads, assignment):
    """Создает события просмотра, добавления в избранное, контакта и покупки."""
    group_by_user = assignment.set_index("user_id")["experiment_group"].to_dict()
    ads_by_id = ads.set_index("ad_id")

    category_interest = {
        "electronics": 1.15,
        "real_estate": 0.72,
        "auto": 0.82,
        "jobs": 0.68,
        "services": 0.90,
        "home_goods": 1.05,
        "fashion": 1.10,
    }
    viewed_ad_weights = ads["category"].map(category_interest).to_numpy()
    viewed_ad_weights = viewed_ad_weights / viewed_ad_weights.sum()

    event_rows = []
    event_id = 1
    experiment_start = pd.Timestamp("2026-03-01")

    # Сгенерировать пользовательские просмотры и дальнейшие действия в воронке.
    for user in users.itertuples(index=False):
        user_group = group_by_user[user.user_id]
        user_factor = get_probability_multiplier(user._asdict())
        base_views = {
            "new": 4.5,
            "regular": 7.0,
            "power_seller": 9.0,
            "bargain_hunter": 8.5,
        }[user.user_segment]
        n_views = max(1, rng.poisson(base_views * user_factor))

        viewed_ads = rng.choice(ads["ad_id"].to_numpy(), size=n_views, p=viewed_ad_weights)

        for ad_id in viewed_ads:
            ad = ads_by_id.loc[ad_id]
            event_time = experiment_start + pd.to_timedelta(rng.integers(0, 28 * 24 * 60), unit="m")

            event_rows.append(
                {
                    "event_id": event_id,
                    "user_id": user.user_id,
                    "ad_id": int(ad_id),
                    "event_type": "view_ad",
                    "event_time": event_time,
                    "experiment_group": user_group,
                }
            )
            event_id += 1

            price_factor = 1 / (1 + np.log1p(ad["price"]) / 18)
            photo_factor = 1.10 if ad["has_photo"] == 1 else 0.78
            category_factor = category_interest[ad["category"]]

            favorite_probability = np.clip(0.045 * user_factor * category_factor * photo_factor, 0.01, 0.22)
            # Заложить небольшой положительный эффект тестовой версии на контакт.
            contact_uplift = 1.08 if user_group == "test" else 1.00
            contact_probability = np.clip(
                0.070 * user_factor * category_factor * photo_factor * price_factor * contact_uplift,
                0.008,
                0.24,
            )

            if rng.random() < favorite_probability:
                event_rows.append(
                    {
                        "event_id": event_id,
                        "user_id": user.user_id,
                        "ad_id": int(ad_id),
                        "event_type": "add_to_favorite",
                        "event_time": event_time + pd.to_timedelta(rng.integers(1, 90), unit="m"),
                        "experiment_group": user_group,
                    }
                )
                event_id += 1

            if rng.random() < contact_probability:
                contact_time = event_time + pd.to_timedelta(rng.integers(2, 180), unit="m")
                event_rows.append(
                    {
                        "event_id": event_id,
                        "user_id": user.user_id,
                        "ad_id": int(ad_id),
                        "event_type": "contact_seller",
                        "event_time": contact_time,
                        "experiment_group": user_group,
                    }
                )
                event_id += 1

                purchase_probability = np.clip(0.075 * user_factor * price_factor, 0.004, 0.18)
                if rng.random() < purchase_probability:
                    event_rows.append(
                        {
                            "event_id": event_id,
                            "user_id": user.user_id,
                            "ad_id": int(ad_id),
                            "event_type": "purchase",
                            "event_time": contact_time + pd.to_timedelta(rng.integers(20, 1_440), unit="m"),
                            "experiment_group": user_group,
                        }
                    )
                    event_id += 1

    return pd.DataFrame(event_rows)


def generate_payments(rng, users, assignment):
    """Создает редкие платежи за платные услуги платформы."""
    user_groups = assignment.set_index("user_id")["experiment_group"]
    payment_rows = []
    payment_id = 1
    payment_start = pd.Timestamp("2026-03-01")

    # Сгенерировать платежи только для небольшой части пользователей.
    for user in users.itertuples(index=False):
        user_group = user_groups.loc[user.user_id]
        user_factor = get_probability_multiplier(user._asdict())
        group_factor = 1.03 if user_group == "test" else 1.00
        payment_probability = np.clip(0.035 * user_factor * group_factor, 0.005, 0.12)

        if rng.random() < payment_probability:
            n_payments = 1 + int(rng.random() < 0.18)
            for _ in range(n_payments):
                amount = rng.choice([99, 149, 199, 299, 499, 799, 999], p=[0.12, 0.17, 0.24, 0.18, 0.14, 0.09, 0.06])
                payment_rows.append(
                    {
                        "payment_id": payment_id,
                        "user_id": user.user_id,
                        "amount": float(amount),
                        "payment_time": payment_start + pd.to_timedelta(rng.integers(0, 28 * 24 * 60), unit="m"),
                        "experiment_group": user_group,
                    }
                )
                payment_id += 1

    return pd.DataFrame(payment_rows)


def save_tables(tables):
    """Сохраняет таблицы в CSV-файлы в data/raw."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    for table_name, table in tables.items():
        table.to_csv(RAW_DATA_DIR / f"{table_name}.csv", index=False)


def main():
    """Запускает генерацию всех таблиц и сохраняет CSV-файлы."""
    rng = np.random.default_rng(RANDOM_SEED)

    # Сгенерировать основные сущности проекта.
    users, assignment = generate_users(rng)
    ads = generate_ads(rng, users)
    events = generate_events(rng, users, ads, assignment)
    payments = generate_payments(rng, users, assignment)

    tables = {
        "users": users,
        "ads": ads,
        "events": events,
        "payments": payments,
    }
    save_tables(tables)

    print("Синтетические данные успешно сгенерированы:")
    for table_name, table in tables.items():
        print(f"- {table_name}: {len(table):,} строк")
    print(f"Файлы сохранены в: {RAW_DATA_DIR}")


if __name__ == "__main__":
    main()
