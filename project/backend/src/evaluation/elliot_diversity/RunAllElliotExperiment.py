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

    total = len(CONFIGURATIONS) * len(ALGORITHMS)

    for algorithm in ALGORITHMS:

        for config in CONFIGURATIONS:

            if config == "BASELINE_Tokyo":
                experiment_name = f"{config}_{algorithm}"
            else:
                experiment_name = f"{config}_Tokyo_{algorithm}"

            experiment_dir = BASE_DIR / "data" / experiment_name

            print(f"\n{'=' * 60}")
            print(f"[ELLIOT] Experiment: {experiment_name}")
            print(f"{'=' * 60}", flush=True)

            # Comprobar que los TSV existen
            required_files = [
                "train.tsv",
                "test.tsv",
                "recommendations.tsv"
            ]

            if not experiment_dir.is_dir() or any(
                not (experiment_dir / file).is_file()
                for file in required_files
            ):
                print(
                    f"[SKIPPED] Faltan archivos TSV para {experiment_name}",
                    flush=True
                )
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
                    check=True
                )

                completed.append(experiment_name)

                print(
                    f"[OK] {experiment_name}",
                    flush=True
                )

            except subprocess.CalledProcessError:
                failed.append(experiment_name)

                print(
                    f"[ERROR] {experiment_name}",
                    flush=True
                )

    print(f"\n{'=' * 60}")
    print("ELLIOT EXPERIMENT SUMMARY")
    print(f"{'=' * 60}")

    print(f"Total configurations: {total}")
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