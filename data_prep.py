import pandas as pd
import numpy as np
import gc
import os

pd.set_option("future.infer_string", False)

DATA_DIR = "data"


def run():
    print("Loading transactions (only needed columns)...")
    transactions = pd.read_csv(
        os.path.join(DATA_DIR, "transaction_data.csv"),
        usecols=["PRODUCT_ID", "STORE_ID", "WEEK_NO", "QUANTITY", "SALES_VALUE"],
        dtype={
            "PRODUCT_ID": "int32",
            "STORE_ID": "int32",
            "WEEK_NO": "int16",
            "QUANTITY": "int32",
            "SALES_VALUE": "float32",
        },
    )

    print("Cleaning transactions...")
    transactions = transactions[
        (transactions["QUANTITY"] > 0) & (transactions["SALES_VALUE"] > 0)
    ]
    transactions["unit_price"] = (
        transactions["SALES_VALUE"] / transactions["QUANTITY"]
    ).astype("float32")

    print("Loading product categories (only needed columns)...")
    products = pd.read_csv(
        os.path.join(DATA_DIR, "product.csv"),
        usecols=["PRODUCT_ID", "COMMODITY_DESC"],
        dtype={"PRODUCT_ID": "int32"},
    )

    print("Attaching category info...")
    transactions = transactions.merge(products, on="PRODUCT_ID", how="left")
    del products
    gc.collect()
    transactions = transactions.dropna(subset=["COMMODITY_DESC"])

    print("Loading promo flags (filtered, only needed columns)...")
    relevant_products = transactions["PRODUCT_ID"].unique()
    relevant_stores = transactions["STORE_ID"].unique()

    causal_chunks = []
    for chunk in pd.read_csv(
        os.path.join(DATA_DIR, "causal_data.csv"),
        usecols=["PRODUCT_ID", "STORE_ID", "WEEK_NO", "display", "mailer"],
        dtype={"PRODUCT_ID": "int32", "STORE_ID": "int32", "WEEK_NO": "int16"},
        chunksize=2_000_000,
    ):
        chunk = chunk[
            chunk["PRODUCT_ID"].isin(relevant_products)
            & chunk["STORE_ID"].isin(relevant_stores)
        ]
        chunk["promo_flag"] = (
            (chunk["display"].astype(str) != "0")
            | (chunk["mailer"].astype(str) != "0")
        ).astype("int8")
        causal_chunks.append(chunk[["PRODUCT_ID", "STORE_ID", "WEEK_NO", "promo_flag"]])

    causal = pd.concat(causal_chunks, ignore_index=True)
    del causal_chunks
    gc.collect()

    print("Attaching promo flags...")
    transactions = transactions.merge(
        causal, on=["PRODUCT_ID", "STORE_ID", "WEEK_NO"], how="left"
    )
    del causal
    gc.collect()
    transactions["promo_flag"] = transactions["promo_flag"].fillna(0).astype("int8")

    print("Aggregating to weekly category level...")
    weekly = (
        transactions.groupby(["WEEK_NO", "COMMODITY_DESC"])
        .agg(
            units_sold=("QUANTITY", "sum"),
            avg_price=("unit_price", "mean"),
            promo_flag=("promo_flag", "max"),
        )
        .reset_index()
        .rename(columns={"COMMODITY_DESC": "category"})
    )
    weekly = weekly[(weekly["units_sold"] > 0) & (weekly["avg_price"] > 0)]

    out_path = os.path.join(DATA_DIR, "weekly_category_data.csv")
    weekly.to_csv(out_path, index=False)
    print(f"Saved cleaned dataset to {out_path} ({len(weekly)} rows)")


if __name__ == "__main__":
    run()