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
    """Busca el CSV más reciente de una configuración."""

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


def main():

    completed = []
    failed = []
    skipped = []

    for algorithm in ALGORITHMS:
        for config, hops in CONFIGURATIONS.items():

            if config == "BASELINE_Tokyo":
                experiment_name = f"{config}_{algorithm}"
            else:
                experiment_name = f"{config}_Tokyo_{algorithm}"

            print(f"\n{'=' * 60}")
            print(f"[PREPARE] {experiment_name}")
            print(f"{'=' * 60}", flush=True)

            predictions_file = get_latest_prediction(experiment_name)

            if predictions_file is None:
                print(f"[SKIPPED] No existe CSV para {experiment_name}")
                skipped.append(experiment_name)
                continue

            print(f"Predictions: {predictions_file.name}")
            print(f"Hops: {hops}", flush=True)

            command = [
                sys.executable,
                "-m",
                "evaluation.elliot_diversity.PrepareElliot",
                str(predictions_file),
                "Tokyo",
                str(hops)
            ]

            try:
                subprocess.run(
                    command,
                    cwd=SRC_DIR,
                    check=True
                )

                completed.append(experiment_name)
                print(f"[OK] {experiment_name}", flush=True)

            except subprocess.CalledProcessError:
                failed.append(experiment_name)
                print(f"[ERROR] {experiment_name}", flush=True)

    print("\n========== PREPARE SUMMARY ==========")
    print(f"Completed: {len(completed)}")
    print(f"Failed: {len(failed)}")
    print(f"Skipped: {len(skipped)}")

    if failed or skipped:
        sys.exit(1)


if __name__ == "__main__":
    main()