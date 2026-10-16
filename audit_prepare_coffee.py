"""Audit dan siapkan data Coffee Shop Sales untuk dashboard."""

import argparse
import json
from pathlib import Path

import pandas as pd


DEFAULT_FOLDER = Path(__file__).resolve().parent

COLUMNS = [
    "transaction_id", "transaction_date", "transaction_time", "transaction_qty",
    "store_id", "store_location", "product_id", "unit_price",
    "product_category", "product_type", "product_detail",
]
TEXT_COLUMNS = ["store_location", "product_category", "product_type", "product_detail"]
NUMERIC_COLUMNS = ["transaction_id", "transaction_qty", "store_id", "product_id", "unit_price"]
DAY_NAMES_ID = {0: "Senin", 1: "Selasa", 2: "Rabu", 3: "Kamis", 4: "Jumat", 5: "Sabtu", 6: "Minggu"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_FOLDER / "Coffee Shop Sales.xlsx")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    source = args.input.resolve()
    if not source.is_file():
        raise FileNotFoundError(f"File sumber tidak ditemukan: {source}")

    output = args.output or source.parent / "data_prepared"
    output.mkdir(parents=True, exist_ok=True)
    df = pd.read_excel(source, sheet_name="Transactions")
    raw = df.copy()

    missing_columns = sorted(set(COLUMNS) - set(df.columns))
    if missing_columns:
        raise ValueError(f"Kolom wajib tidak tersedia: {missing_columns}")
    if df.empty:
        raise ValueError("Dataset tidak memiliki baris.")

    issues = []
    report = {
        "source_file": source.name,
        "sheet": "Transactions",
        "original_rows": len(df),
        "original_columns": list(df.columns),
        "missing_before": {column: int(count) for column, count in df.isna().sum().items()},
        "duplicate_rows_before": int(df.duplicated().sum()),
        "trimmed_values": {},
    }

    for column in TEXT_COLUMNS:
        text = df[column].astype("string")
        cleaned = text.str.strip()
        report["trimmed_values"][column] = int(text.ne(cleaned).fillna(False).sum())
        df[column] = cleaned
        if df[column].isna().any() or df[column].eq("").any():
            issues.append(f"{column}: teks kosong atau hilang")

    for column in NUMERIC_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="coerce")
        if df[column].isna().any():
            issues.append(f"{column}: angka tidak valid atau hilang")
        if (df[column] <= 0).any():
            issues.append(f"{column}: angka nol atau negatif")
        if not df[column].dropna().map(lambda value: float("-inf") < value < float("inf")).all():
            issues.append(f"{column}: angka tak hingga")
        if column != "unit_price" and (df[column].dropna() % 1 != 0).any():
            issues.append(f"{column}: seharusnya bilangan bulat")

    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
    if df["transaction_date"].isna().any():
        issues.append("transaction_date: tanggal tidak valid atau hilang")
    elif df["transaction_date"].ne(df["transaction_date"].dt.normalize()).any():
        issues.append("transaction_date mengandung jam. Periksa sebelum menggabungkan waktu.")

    parsed_time = pd.to_datetime(
        df["transaction_time"].astype("string"), format="%H:%M:%S", errors="coerce"
    )
    if parsed_time.isna().any():
        issues.append("transaction_time: waktu tidak valid, harus HH:MM:SS")

    report["duplicate_transaction_ids"] = int(df["transaction_id"].duplicated().sum())
    report["duplicate_rows_after_trim"] = int(df.duplicated().sum())
    if report["duplicate_transaction_ids"]:
        issues.append("transaction_id berulang: pastikan grain sebelum lanjut")
    if report["duplicate_rows_after_trim"]:
        issues.append("Ada baris duplikat, perlu diperiksa sebelum lanjut")

    attribute_mappings = {
        "store_id": ["store_location"],
        "product_id": ["product_category", "product_type", "product_detail"],
    }
    for key, columns in attribute_mappings.items():
        if (df.groupby(key)[columns].nunique() > 1).any().any():
            issues.append(f"Pemetaan {key} ke atribut tidak konsisten")

    report["products_with_multiple_prices"] = int(
        df.groupby("product_id")["unit_price"].nunique().gt(1).sum()
    )
    report["price_note"] = "Harga yang berbeda dipertahankan, bukan otomatis kesalahan."
    report["issues"] = issues
    report["status"] = "PERLU PEMERIKSAAN" if issues else "LULUS AUDIT DASAR"

    if issues:
        (output / "audit_report.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(json.dumps(report, indent=2, ensure_ascii=False))
        raise ValueError(
            "Audit belum lulus. Output siap dashboard tidak dibuat. Periksa audit_report.json."
        )

    for column in NUMERIC_COLUMNS:
        if column != "unit_price":
            df[column] = df[column].astype("int64")

    df["transaction_time"] = parsed_time.dt.strftime("%H:%M:%S")
    df["transaction_datetime"] = df["transaction_date"] + pd.to_timedelta(df["transaction_time"])
    df["sales"] = (df["transaction_qty"] * df["unit_price"]).round(2)
    df["month"] = df["transaction_date"].dt.strftime("%Y-%m")
    df["hour"] = df["transaction_datetime"].dt.hour
    df["day_of_week"] = df["transaction_date"].dt.dayofweek
    df["day_name_id"] = df["day_of_week"].map(DAY_NAMES_ID)

    assert len(df) == len(raw), "Jumlah baris berubah tanpa izin"
    original_sales = (raw["transaction_qty"] * raw["unit_price"]).sum().round(2)
    assert df["sales"].sum().round(2) == original_sales

    dates = pd.DatetimeIndex(df["transaction_date"].unique()).sort_values()
    report.update({
        "prepared_rows": len(df),
        "date_min": str(dates.min().date()),
        "date_max": str(dates.max().date()),
        "observed_days": len(dates),
        "dates_without_records": [str(date.date()) for date in pd.date_range(dates.min(), dates.max()).difference(dates)],
        "total_sales": round(float(df["sales"].sum()), 2),
        "total_transactions": int(df["transaction_id"].nunique()),
        "total_units": int(df["transaction_qty"].sum()),
        "average_recorded_transaction_value": float(df["sales"].sum() / df["transaction_id"].nunique()),
        "currency": "Tidak dinyatakan pada file sumber",
        "grain": "Satu baris per transaction_id, satu produk. Belum dipastikan sebagai seluruh isi struk.",
    })

    monthly = df.groupby("month", as_index=False).agg(
        total_sales=("sales", "sum"),
        total_transactions=("transaction_id", "nunique"),
        total_units=("transaction_qty", "sum"),
    )
    previous_sales = monthly["total_sales"].shift(1)
    period = pd.PeriodIndex(monthly["month"], freq="M")
    consecutive_months = pd.Series(period.asi8).diff().eq(1)
    monthly["growth_pct"] = (
        (monthly["total_sales"] - previous_sales) / previous_sales * 100
    ).where(previous_sales.ne(0) & consecutive_months)
    monthly["average_transaction_value"] = monthly["total_sales"] / monthly["total_transactions"]

    df.to_csv(
        output / "coffee_sales_prepared.csv",
        index=False,
        encoding="utf-8-sig",
        date_format="%Y-%m-%d %H:%M:%S",
    )
    monthly.to_csv(output / "monthly_summary.csv", index=False, encoding="utf-8-sig")
    (output / "audit_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print("\nLULUS AUDIT DASAR")
    print("Perbaikan spasi:", report["trimmed_values"])
    print(f"Baris tetap: {len(df):,}")
    print(f"Total penjualan: {report['total_sales']:,.2f}")
    print(f"Total unit: {report['total_units']:,}")
    print("\nRingkasan bulanan:\n", monthly.round(2).to_string(index=False))
    print("\nOutput:", output.resolve())


if __name__ == "__main__":
    main()
