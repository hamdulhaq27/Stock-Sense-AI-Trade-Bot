"""
Data loader: reads pre-processed CSVs and exposes merged DataFrames.
All heavy I/O happens once at startup; results are cached in module-level
variables so every request pays nothing for disk access.
"""

import os
import pandas as pd
from functools import lru_cache

DATA_DIR = os.path.join(os.path.dirname(__file__))

# ---------------------------------------------------------------------------
# Raw loaders (called once at startup via get_*_data())
# ---------------------------------------------------------------------------

def _load_stock() -> pd.DataFrame:
    df = pd.read_csv(os.path.join(DATA_DIR, "stock_data_clean.csv"), low_memory=False)
    df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["date"])
    df = df.rename(columns={"ticker": "symbol"})
    return df.sort_values(["symbol", "date"])


def _load_news() -> pd.DataFrame:
    df = pd.read_csv(os.path.join(DATA_DIR, "news_clean.csv"), low_memory=False)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    df = df.rename(columns={"ticker": "symbol"})
    return df.sort_values(["symbol", "date"])


def _load_reddit() -> pd.DataFrame:
    df = pd.read_csv(os.path.join(DATA_DIR, "agg_reddit.csv"), low_memory=False)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    return df.sort_values(["symbol", "date"])


def _load_stocktwits() -> pd.DataFrame:
    df = pd.read_csv(os.path.join(DATA_DIR, "agg_stocktwits.csv"), low_memory=False)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    return df.sort_values(["symbol", "date"])


# ---------------------------------------------------------------------------
# Cached accessors (module-level singletons)
# ---------------------------------------------------------------------------

_STOCK: pd.DataFrame | None = None
_NEWS: pd.DataFrame | None = None
_REDDIT: pd.DataFrame | None = None
_STOCKTWITS: pd.DataFrame | None = None


def get_stock_data() -> pd.DataFrame:
    global _STOCK
    if _STOCK is None:
        _STOCK = _load_stock()
    return _STOCK


def get_news_data() -> pd.DataFrame:
    global _NEWS
    if _NEWS is None:
        _NEWS = _load_news()
    return _NEWS


def get_reddit_data() -> pd.DataFrame:
    global _REDDIT
    if _REDDIT is None:
        _REDDIT = _load_reddit()
    return _REDDIT


def get_stocktwits_data() -> pd.DataFrame:
    global _STOCKTWITS
    if _STOCKTWITS is None:
        _STOCKTWITS = _load_stocktwits()
    return _STOCKTWITS


# ---------------------------------------------------------------------------
# Available symbols
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def get_all_symbols() -> list[str]:
    stock_syms = set(get_stock_data()["symbol"].unique())
    news_syms = set(get_news_data()["symbol"].unique())
    return sorted(stock_syms | news_syms)


def symbol_exists(symbol: str) -> bool:
    return symbol.upper() in get_all_symbols()
