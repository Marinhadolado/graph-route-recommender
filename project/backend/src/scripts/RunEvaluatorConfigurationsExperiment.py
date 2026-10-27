from pathlib import Path

from ranx import compare

from evaluation.Evaluator import (
    Evaluator,
    METRICS,
)

CITY = "Tokyo"

ALGORITHMS = [
    "random",
    "markov",
]

ALL_CONFIGURATIONS = [
    "Baseline",
    "NoWeather",
    "NoTime",
    "RelaxLoc",
    "NoTimeNoWeather",
    "FullRelaxation",
]

STAT_TEST = "student"

P_VALUES = [0.01, 0.05]

RANDOM_SEED = 42

ROUNDING_DIGITS = 4

def run_comparison(
    evaluator,
    algorithm,
    configurations,
    output_dir,
    max_p
):

    print("\n" + "=" * 70)
    print(f"ALGORITHM: {algorithm.upper()}")
    print(f"SIGNIFICANCE THRESHOLD: p < {max_p}")
    print("=" * 70)
    qrels, qrels_dict = evaluator.load_qrels(hops=1)

    print(
        f"\nQueries in Qrels: {len(qrels_dict)}"
    )

    runs = []

    for configuration in configurations:

        run = evaluator.load_run(
            configuration,
            algorithm
        )

        runs.append(run)

    report = compare(
        qrels=qrels,
        runs=runs,
        metrics=METRICS,
        stat_test=STAT_TEST,
        max_p=max_p,
        random_seed=RANDOM_SEED,
        rounding_digits=ROUNDING_DIGITS,
        make_comparable=True,
        threads=1
    )

    print("\nSTATISTICAL COMPARISON\n")
    print(report)

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    # 0.01 -> p010
    # 0.05 -> p050
    p_label = f"p{int(max_p * 1000):03d}"

    txt_path = (
        output_dir
        / f"{algorithm}_general_{p_label}.txt"
    )

    with open(
        txt_path,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(
            f"Algorithm: {algorithm}\n"
        )

        f.write(
            "Experiment: all configurations\n"
        )

        f.write(
            "Prediction target: next observed POI\n"
        )

        f.write(
            f"Queries: {len(qrels_dict)}\n"
        )

        f.write(
            f"Statistical test: {STAT_TEST}\n"
        )

        f.write(
            f"Significance threshold: {max_p}\n\n"
        )

        f.write(str(report))

    print(f"\nSaved TXT: {txt_path}")

    return report

def evaluate_all_individually(evaluator):

    print("\n" + "=" * 70)
    print("INDIVIDUAL NDCG RESULTS")
    print("=" * 70)

    for algorithm in ALGORITHMS:

        print(f"\n{'-' * 50}")
        print(f"ALGORITHM: {algorithm.upper()}")
        print(f"{'-' * 50}")

        for configuration in ALL_CONFIGURATIONS:

            evaluator.evaluate_configuration(
                configuration,
                algorithm
            )

def main():

    evaluator = Evaluator(
        city_name=CITY
    )

    scripts_dir = Path(__file__).resolve().parent

    output_dir = (
        scripts_dir / "evaluation_reports"
    )

    # Primero mostramos el nDCG individual
    evaluate_all_individually(evaluator)

    # Comparamos las seis configuraciones
    # por separado para cada algoritmo.

    for max_p in P_VALUES:

        print("\n" + "#" * 70)
        print(f"STATISTICAL TESTS WITH p < {max_p}")
        print("#" * 70)

        for algorithm in ALGORITHMS:

            run_comparison(
                evaluator=evaluator,
                algorithm=algorithm,
                configurations=ALL_CONFIGURATIONS,
                output_dir=output_dir,
                max_p=max_p
            )

    print("\n" + "=" * 70)
    print("ALL EVALUATIONS COMPLETED")
    print("=" * 70)

    print(f"\nResults saved in: {output_dir}")


if __name__ == "__main__":
    main()