from typing import Any

import pandas as pd


def load_sql(path: str) -> str:
    with open(path, "r") as f:
        query = f.read()
    return query



def convert_df_types(df: pd.DataFrame, schema: dict[str, Any]) -> pd.DataFrame:
    for col, dtype in schema.items():
        if dtype is int:
            # NaN を 0 で置換してから整数型に変換
            df[col] = df[col].fillna(0).astype(dtype)
        elif dtype == "datetime64[ns]":
            # 範囲外の日時値を NaT に置換
            df[col] = pd.to_datetime(df[col], errors="coerce")
        else:
            # それ以外の型変換
            df[col] = df[col].astype(dtype)
    return df


def save_csv(df: pd.DataFrame, path: str) -> None:
    df.to_csv(path, index=False)


def load_csv(path: str, schema: dict[str, Any]) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = convert_df_types(df, schema)
    return df
