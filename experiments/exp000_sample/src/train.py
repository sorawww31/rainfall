from pathlib import Path

import pandas as pd
from sklearn.model_selection import GroupKFold
from src.model import Classifier
from src.psocess_data import preprocess


def train(cfg, logger) -> None:

    train_df = pd.read_csv(Path(cfg.env.input_dir) / cfg.exp.train_csv_path)
    train_base_df = pd.read_csv(
        Path(cfg.env.input_dir) / "datasets/subho117/rainfall-prediction-using-machine-learning/Rainfall.csv"
    )
    train_base_df.columns = train_base_df.columns.str.strip()

    X = train_df.drop(columns=["rainfall"])
    y = train_df["rainfall"]

    X_base = train_base_df.drop(columns=["rainfall"])
    y_base = train_base_df["rainfall"].map({"yes": 1, "no": 0}).astype(int)

    del train_df
    cv = GroupKFold(n_splits=cfg.exp.n_splits, shuffle=True, random_state=cfg.exp.seed)

    X = preprocess(cfg, X)
    results = []
    for fold, (train_idx, valid_idx) in enumerate(cv.split(X, y, groups=X["group"])):
        if fold not in cfg.exp.folds:
            continue

        X_train, y_train = X.iloc[train_idx], y.iloc[train_idx]
        X_valid, y_valid = X.iloc[valid_idx], y.iloc[valid_idx]

        X_train = pd.concat([X_train, X_base])
        y_train = pd.concat([y_train, y_base])
        # preprocessor = build_preprocessor()
        # X_train = preprocessor.fit_transform(X_train)
        # X_valid = preprocessor.transform(X_valid)

        model = Classifier(cfg)

        model.train(X_train, y_train, validation_data=(X_valid, y_valid))
        y_pred = model.predict(X_valid)
        accuracy = roc_auc_score(y_valid, y_pred)
        results.append(accuracy)

    for fold, score in zip(cfg.exp.folds, results):
        logger.info(f"Fold {fold} ROC AUC score: {score:.4f}")
    logger.info(f"Mean ROC AUC score: {sum(results) / len(results):.4f}")

    logger.info(f"Saving submission file to {cfg.env.exp_output_dir}")
    create_submision(model, cfg)


def roc_auc_score(y_true, y_pred):
    # ROC AUCスコアを計算する関数
    from sklearn.metrics import roc_auc_score

    return roc_auc_score(y_true, y_pred)


def create_submision(model, cfg):
    test_df = pd.read_csv(Path(cfg.env.input_dir) / cfg.exp.test_csv_path)
    X_test = preprocess(cfg, test_df)
    # X_test = preprocessor.transform(X_test)
    y_pred = model.predict(X_test)
    submission_df = pd.DataFrame({"id": test_df["id"], "rainfall": y_pred})
    submission_df.to_csv(Path(cfg.env.exp_output_dir) / "submission.csv", index=False)
