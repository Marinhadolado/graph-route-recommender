import subprocess
import sys
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR.parents[1]
PREDICTIONS_DIR = SRC_DIR.parent / "predictions"

CONFIGURATIONS = {
    "BASELINE_Tokyo": 1,
    "WCTX_T": 1,
    "WCTX_C": 1,
    "WCTX_L2": 2,
    "WCTX_TC": 1,
    "WCTX_TCL2": 2
}

ALGORITHMS = ["markov", "random"]


def get_latest_prediction(experiment_name):
    """Busca el CSV de predicciones más reciente para el experimento."""

    pattern = re.compile(
        rf"^{re.escape(experiment_name)}_\d{{8}}_\d{{6}}(?:_\d+)?\.csv$"
    )

    files = [
        file for file in PREDICTIONS_DIR.glob("*.csv")
        if pattern.fullmatch(file.name)
    ]

    if not files:
        return None

    return max(files, key=lambda file: file.stat().st_mtime)


def run_command(command):
    """Ejecuta un módulo Python desde backend/src."""

    subprocess.run(
        [sys.executable, "-m", *command],
        cwd=SRC_DIR,
        check=True
    )


def main():

    completed = []
    failed = []
    skipped = []

    total = len(CONFIGURATIONS) * len(ALGORITHMS)

    for algorithm in ALGORITHMS:

        for config, hops in CONFIGURATIONS.items():

            if config == "BASELINE_Tokyo":
                experiment_name = f"{config}_{algorithm}"
            else:
                experiment_name = f"{config}_Tokyo_{algorithm}"

            print(f"\n{'=' * 60}")
            print(f"[ELLIOT] Experiment: {experiment_name}")
            print(f"{'=' * 60}", flush=True)

            # 1. Buscar el CSV correspondiente del Predictor
            predictions_file = get_latest_prediction(experiment_name)

            if predictions_file is None:
                print(
                    f"[SKIPPED] No se encontraron predicciones para "
                    f"{experiment_name}"
                )
                skipped.append(experiment_name)
                continue

            print(f"[ELLIOT] Predictions: {predictions_file.name}")
            print(f"[ELLIOT] Hops: {hops}", flush=True)

            try:
                # 2. Preparar los TSV
                print("\n[ELLIOT] Preparing TSV files...", flush=True)

                run_command([
                    "evaluation.elliot_diversity.PrepareElliot",
                    str(predictions_file),
                    "Tokyo",
                    str(hops)
                ])

                # 3. Comprobar que existen los TSV
                experiment_dir = BASE_DIR / "data" / experiment_name

                for filename in (
                    "train.tsv",
                    "test.tsv",
                    "recommendations.tsv"
                ):
                    if not (experiment_dir / filename).is_file():
                        raise FileNotFoundError(
                            f"Falta {filename} en {experiment_dir}"
                        )

                # 4. Ejecutar Elliot
                print("\n[ELLIOT] Running evaluation...", flush=True)

                run_command([
                    "evaluation.elliot_diversity.ElliotExperiment",
                    experiment_name
                ])

                completed.append(experiment_name)

                print(f"\n[OK] {experiment_name}", flush=True)

            except (subprocess.CalledProcessError, FileNotFoundError) as e:

                failed.append(experiment_name)

                print(f"\n[ERROR] {experiment_name}: {e}", flush=True)

    print(f"\n{'=' * 60}")
    print("ELLIOT EXPERIMENT SUMMARY")
    print(f"{'=' * 60}")

    print(f"Total: {total}")
    print(f"Completed: {len(completed)}")
    print(f"Failed: {len(failed)}")
    print(f"Skipped: {len(skipped)}")

    if failed:
        print("\nFailed experiments:")
        for exp in failed:
            print(f"  - {exp}")

    if skipped:
        print("\nSkipped experiments:")
        for exp in skipped:
            print(f"  - {exp}")

    if failed or skipped:
        sys.exit(1)


if __name__ == "__main__":
    main()