import pandas as pd

_month_ends = [31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365]


def preprocess(cfg, train_df: pd.DataFrame) -> pd.DataFrame:
    """train csvを読み込み、test/validに分割する.
    Args:
        cfg: Config
        train_df: train csv
    Returns:
        train_df: 前処理済みのtrain csv
    """
    train_df["group"] = train_df["day"].eq(1).cumsum()
    train_df["month"] = pd.cut(train_df["day"], bins=[0] + _month_ends, labels=range(1, 13), include_lowest=True)
    return train_df
