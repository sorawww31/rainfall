import pandas as pd

_month_ends = [31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365]


def preprocess(cfg, df: pd.DataFrame) -> pd.DataFrame:
    """train csvを読み込み、test/validに分割する.
    Args:
        cfg: Config
        df: train csv
    Returns:
        df: 前処理済みのtrain csv
    """
    df["group"] = df["day"].eq(1).cumsum()
    df["month"] = pd.cut(df["day"], bins=[0] + _month_ends, labels=range(1, 13), include_lowest=True)
    df["month"] = df["month"].astype("category")
    # df["saturation_vapor_pressure"] = 0.6108 * np.exp(17.27 * df["temparature"] / (df["temparature"] + 237.3))

    # df["temp_range"] = df["maxtemp"] - df["mintemp"]

    # temperature = df["temparature"]
    # humidity = df["humidity"]
    # pressure = df["pressure"]
    # wind_speed = df["windspeed"]
    # wind_direction = np.deg2rad(df["winddirection"])
    # saturation_vapor_pressure = df["saturation_vapor_pressure"]

    # df["dewpoint_depression"] = temperature - df["dewpoint"]
    # df["vapor_pressure"] = saturation_vapor_pressure * (humidity / 100)
    # df["vpd"] = saturation_vapor_pressure - df["vapor_pressure"]

    # # 絶対湿度の式は水蒸気圧をhPaで扱うため、kPaから変換する。
    # vapor_pressure_hpa = df["vapor_pressure"] * 10
    # df["absolute_humidity"] = 216.7 * vapor_pressure_hpa / (temperature + 273.15)

    # df["mixing_ratio"] = 0.622 * vapor_pressure_hpa / (pressure - vapor_pressure_hpa)
    # df["specific_humidity"] = 0.622 * vapor_pressure_hpa / (pressure - 0.378 * vapor_pressure_hpa)

    # # Stull (2011) の近似式による湿球温度。
    # # df["wetbulb"] = (
    # #     temperature * np.arctan(0.151977 * np.sqrt(humidity + 8.313659))
    # #     + np.arctan(temperature + humidity)
    # #     - np.arctan(humidity - 1.676331)
    # #     + 0.00391838 * humidity**1.5 * np.arctan(0.023101 * humidity)
    # #     - 4.686035
    # # )

    # # NOAA式による暑さ指数。華氏で計算して摂氏へ戻す。
    # temperature_f = temperature * 9 / 5 + 32
    # df["heatindex"] = (
    #     -42.379
    #     + 2.04901523 * temperature_f
    #     + 10.14333127 * humidity
    #     - 0.22475541 * temperature_f * humidity
    #     - 0.00683783 * temperature_f**2
    #     - 0.05481717 * humidity**2
    #     + 0.00122874 * temperature_f**2 * humidity
    #     + 0.00085282 * temperature_f * humidity**2
    #     - 0.00000199 * temperature_f**2 * humidity**2
    # )
    # df["heatindex"] = (df["heatindex"] - 32) * 5 / 9

    # # NOAA式による風冷指数。華氏で計算して摂氏へ戻す。
    # wind_speed_mph = wind_speed * 0.621371
    # df["windchill"] = (
    #     35.74 + 0.6215 * temperature_f - 35.75 * wind_speed_mph**0.16 + 0.4275 * temperature_f * wind_speed_mph**0.16
    # )
    # df["windchill"] = (df["windchill"] - 32) * 5 / 9

    # # 風向は北を0度、時計回りを正とする気象学上の風向として変換する。
    # df["wind_u"] = -wind_speed * np.sin(wind_direction)
    # df["wind_v"] = -wind_speed * np.cos(wind_direction)

    return df
