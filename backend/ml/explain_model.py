from pathlib import Path

import pandas as pd
import shap
import joblib
import matplotlib.pyplot as plt


# ==================================================
# PATHS
# ==================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "agu_ml_dataset.csv"
)

MODEL_FILE = (
    PROJECT_ROOT
    / "backend"
    / "ml"
    / "models"
    / "xgboost_event_carbon_model.pkl"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "backend"
    / "ml"
    / "shap_outputs"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ==================================================
# LOAD DATA AND MODEL
# ==================================================

df = pd.read_csv(DATA_FILE)

model = joblib.load(MODEL_FILE)

features = [
    "participants",
    "distance_km"
]

X = df[features]


print("\nSHAP ANALYSIS")
print("=" * 60)

print("Rows:", len(X))
print("Features:", features)


# ==================================================
# CREATE SHAP EXPLAINER
# ==================================================

explainer = shap.TreeExplainer(model)

shap_values = explainer.shap_values(X)


# ==================================================
# SHAP SUMMARY PLOT
# ==================================================

plt.figure()

shap.summary_plot(
    shap_values,
    X,
    show=False
)

plt.tight_layout()

summary_file = (
    OUTPUT_DIR
    / "shap_summary.png"
)

plt.savefig(
    summary_file,
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# ==================================================
# SHAP BAR PLOT
# ==================================================

plt.figure()

shap.summary_plot(
    shap_values,
    X,
    plot_type="bar",
    show=False
)

plt.tight_layout()

bar_file = (
    OUTPUT_DIR
    / "shap_feature_importance.png"
)

plt.savefig(
    bar_file,
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# ==================================================
# FEATURE IMPORTANCE VALUES
# ==================================================

importance = pd.DataFrame(
    {
        "feature": features,
        "mean_abs_shap": abs(shap_values).mean(axis=0)
    }
)

importance = importance.sort_values(
    "mean_abs_shap",
    ascending=False
)

print("\nSHAP FEATURE IMPORTANCE")
print("=" * 60)

print(
    importance.to_string(
        index=False
    )
)


# ==================================================
# SAVE IMPORTANCE
# ==================================================

importance_file = (
    OUTPUT_DIR
    / "shap_feature_importance.csv"
)

importance.to_csv(
    importance_file,
    index=False
)


print("\nFILES SAVED")
print("=" * 60)

print(summary_file)
print(bar_file)
print(importance_file)