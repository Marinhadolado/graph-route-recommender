import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

CONFIGURATIONS = [
    "BASELINE_Tokyo",
    "WCTX_T",
    "WCTX_C",
    "WCTX_L2",
    "WCTX_TC",
    "WCTX_TCL2"
]

ALGORITHMS = ["markov", "random"]


def main():

    completed = []
    failed = []
    skipped = []

    for algorithm in ALGORITHMS:
        for config in CONFIGURATIONS:

            if config == "BASELINE_Tokyo":
                experiment_name = f"{config}_{algorithm}"
            else:
                experiment_name = f"{config}_Tokyo_{algorithm}"

            experiment_dir = BASE_DIR / "data" / experiment_name

            print(f"\n{'=' * 60}")
            print(f"[ELLIOT] {experiment_name}")
            print(f"{'=' * 60}", flush=True)

            required_files = [
                "train.tsv",
                "test.tsv",
                "recommendations.tsv"
            ]

            if not all(
                (experiment_dir / filename).is_file()
                for filename in required_files
            ):
                print(f"[SKIPPED] Faltan TSV para {experiment_name}")
                skipped.append(experiment_name)
                continue

            command = [
                sys.executable,
                "-m",
                "evaluation.elliot_diversity.ElliotExperiment",
                experiment_name
            ]

            try:
                subprocess.run(
                    command,
                    cwd=BASE_DIR.parents[1],
                    check=True
                )

                completed.append(experiment_name)
                print(f"[OK] {experiment_name}", flush=True)

            except subprocess.CalledProcessError:
                failed.append(experiment_name)
                print(f"[ERROR] {experiment_name}", flush=True)

    print("\n========== ELLIOT SUMMARY ==========")
    print(f"Completed: {len(completed)}")
    print(f"Failed: {len(failed)}")
    print(f"Skipped: {len(skipped)}")

    if failed or skipped:
        sys.exit(1)


if __name__ == "__main__":
    main()