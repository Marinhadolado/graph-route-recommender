import os
import sys
from pathlib import Path

import yaml
from elliot.run import run_experiment

BASE_DIR = Path(__file__).resolve().parent


def main(experiment_name):
    experiment_dir = BASE_DIR / "data" / experiment_name

    if not experiment_dir.is_dir():
        raise FileNotFoundError(
            f"No existe el experimento: {experiment_dir}"
        )

    for filename in ("train.tsv", "test.tsv", "recommendations.tsv"):
        filepath = experiment_dir / filename

        if not filepath.is_file():
            raise FileNotFoundError(
                f"Falta el archivo: {filepath}"
            )

    config_path = BASE_DIR / "exp_configuration.yml"

    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    exp = config["experiment"]

    # se cambian las rutas de los archivos del experimento 
    # para que apunten al experimento en concreto
    exp["data_config"]["train_path"] = (
        f"data/{experiment_name}/train.tsv"
    )

    exp["data_config"]["test_path"] = (
        f"data/{experiment_name}/test.tsv"
    )

    exp["models"]["ProxyRecommender"]["path"] = (
        f"data/{experiment_name}/recommendations.tsv"
    )


    results_dir = f"results/{experiment_name}"

    exp["path_output_rec_result"] = f"{results_dir}/recommendations"
    exp["path_output_rec_weight"] = f"{results_dir}/weights"
    exp["path_output_rec_performance"] = f"{results_dir}/performance"
    exp["path_log_folder"] = f"{results_dir}/logs"

    # Generamos una configuración independiente para esta ejecución
    generated_config = experiment_dir / "elliot_config.yml"

    with open(generated_config, "w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, sort_keys=False)

    # Ejecutar Elliot desde su carpeta de trabajo
    os.chdir(BASE_DIR)

    print(f"[ELLIOT] Evaluando {experiment_name}")

    run_experiment(str(generated_config))


if __name__ == "__main__":
    #se realiza una implementacion completa para que se pueda ejecutar 
    # diferentes experimentos sin estar cambiando de forma manual el .yml
    try:
        if len(sys.argv) != 2:
            print("Usage: python run_elliot.py <experiment_name>")
            sys.exit(1)

        experiment_name = sys.argv[1]
        main(experiment_name)

    except Exception as e:
        print(f"[ELLIOT] ¡ERROR FATAL!: {e}")
        sys.exit(1)