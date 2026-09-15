from dataclasses import asdict, is_dataclass

import lightgbm
import pandas as pd


class Classifier:
    def __init__(self, cfg):
        self.classifier_model = cfg.exp.classifier_model
        if cfg.exp.classifier_model == "lgbm":
            self.lgbm_params = (
                asdict(cfg.exp.lgbm_params) if is_dataclass(cfg.exp.lgbm_params) else dict(cfg.exp.lgbm_params)
            )
            self.model = lightgbm.LGBMClassifier(**self.lgbm_params)

        else:
            raise ValueError(f"Unknown classifier model: {cfg.exp.classifier_model}")

    def train(self, X_train: pd.DataFrame, y_train: pd.Series, validation_data: tuple[pd.DataFrame, pd.Series]):
        if self.classifier_model == "lgbm":
            self.model.fit(
                X_train,
                y_train,
                eval_X=validation_data[0],
                eval_y=validation_data[1],
                callbacks=[
                    lightgbm.early_stopping(
                        stopping_rounds=self.lgbm_params.get("early_stopping_rounds", 100),
                        verbose=False,
                    )
                ],
            )

    def predict(self, X: pd.DataFrame) -> pd.Series:
        if self.classifier_model == "lgbm":
            return pd.Series(self.model.predict_proba(X)[:, 1])
