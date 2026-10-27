from pathlib import Path

from ranx import compare

from evaluation.Evaluator import (
    Evaluator,
    CONFIGURATIONS,
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

ONE_HOP_CONFIGURATIONS = [
    "Baseline",
    "NoWeather",
    "NoTime",
    "NoTimeNoWeather",
]

TWO_HOP_CONFIGURATIONS = [
    "RelaxLoc",
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
    hops,
    experiment_name,
    output_dir,
    max_p
):

    print("\n" + "=" * 70)
    print(f"ALGORITHM: {algorithm.upper()}")
    print(f"EXPERIMENT: {experiment_name}")
    print(f"SIGNIFICANCE THRESHOLD: p < {max_p}")
    print("=" * 70)

    # Cargar Qrels
    qrels, qrels_dict = evaluator.load_qrels(
        hops=hops
    )

    print(f"\nQueries in Qrels: {len(qrels_dict)}")

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

    # p=0.01 -> p001
    # p=0.05 -> p005
    p_label = f"p{int(max_p * 1000):03d}"

    txt_path = (
        output_dir
        / f"{algorithm}_{experiment_name}_{p_label}.txt"
    )

    with open(
        txt_path,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(f"Algorithm: {algorithm}\n")
        f.write(f"Experiment: {experiment_name}\n")
        f.write(f"Qrels hops: {hops}\n")
        f.write(f"Queries: {len(qrels_dict)}\n")
        f.write(f"Statistical test: {STAT_TEST}\n")
        f.write(f"Significance threshold: {max_p}\n\n")

        if experiment_name == "general":

            f.write(
                "WARNING: EXPLORATORY COMPARISON.\n"
                "One-hop and two-hop configurations "
                "use different starting POIs.\n"
                "Results do not isolate the effect "
                "of contextual filtering.\n\n"
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

    evaluate_all_individually(evaluator)

    for max_p in P_VALUES:

        print("\n" + "#" * 70)
        print(f"STATISTICAL TESTS WITH p < {max_p}")
        print("#" * 70)

        for algorithm in ALGORITHMS:

            print(
                "\nWARNING: General comparison "
                "includes different starting POIs."
            )

            run_comparison(
                evaluator=evaluator,
                algorithm=algorithm,
                configurations=ALL_CONFIGURATIONS,
                hops=2,
                experiment_name="general",
                output_dir=output_dir,
                max_p=max_p
            )

            #comparación de un solo salto
            run_comparison(
                evaluator=evaluator,
                algorithm=algorithm,
                configurations=ONE_HOP_CONFIGURATIONS,
                hops=1,
                experiment_name="hops1",
                output_dir=output_dir,
                max_p=max_p
            )

            # comparación de dos saltos
            run_comparison(
                evaluator=evaluator,
                algorithm=algorithm,
                configurations=TWO_HOP_CONFIGURATIONS,
                hops=2,
                experiment_name="hops2",
                output_dir=output_dir,
                max_p=max_p
            )

    print("\n" + "=" * 70)
    print("ALL EVALUATIONS COMPLETED")
    print("=" * 70)

    print(f"\nResults saved in: {output_dir}")


if __name__ == "__main__":
    main()