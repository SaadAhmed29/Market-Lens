from ml_module.data_formation import build_dataset
from utils.ml_utils import load_ml_config


def main():
    config_path = "ml_module/config.yaml"
    config = load_ml_config(config_path)
    df = build_dataset(config)

    print(df.head())

    # save df to csv with date as index
    df.to_csv("dataset.csv", index=True)
    print("Dataset saved to dataset.csv")

if __name__ == "__main__":
    main()
