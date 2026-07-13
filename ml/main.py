from ml.data_formation import build_dataset
from ml.data_utils import load_ml_config


def main():
    config_path = "ml/config.yaml"
    config = load_ml_config(config_path)
    df = build_dataset(config)

    print(df.head())

    # save df to csv with date as index
    model = config.get("model_type")
    df.to_csv(f"{model}_dataset.csv", index=True)
    print(f"{model} dataset saved to {model}_dataset.csv")

if __name__ == "__main__":
    main()
