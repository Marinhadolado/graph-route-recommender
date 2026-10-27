import csv
from pathlib import Path

from ranx import Qrels, Run, evaluate

CONFIGURATIONS = {
    "Baseline": {
        "label": "BASELINE",
        "hops": 1,
    },
    "NoWeather": {
        "label": "WCTX_C",
        "hops": 1,
    },
    "NoTime": {
        "label": "WCTX_T",
        "hops": 1,
    },
    "RelaxLoc": {
        "label": "WCTX_L2",
        "hops": 2,
    },
    "NoTimeNoWeather": {
        "label": "WCTX_TC",
        "hops": 1,
    },
    "FullRelaxation": {
        "label": "WCTX_TCL2",
        "hops": 2,
    },
}

METRICS = ["ndcg@5", "ndcg@10"]


class Evaluator:

    def __init__(self, city_name="Tokyo"):

        self.city_name = city_name
        self.base_dir = Path(__file__).resolve().parent
        self.backend_dir = self.base_dir.parent.parent
        self.dataset_dir = self.backend_dir / "dataset"
        self.predictions_dir = (
            self.backend_dir / "predictions"
        )
        self.test_file = self.dataset_dir / "test.csv"

    def find_prediction_file(self, configuration, algorithm):
        #buscamos los csv por los nombres de las configuraciones del experimento(BASELINE...)
        # y el nombre del algoritmo

        if configuration not in CONFIGURATIONS:
            raise ValueError(
                f"Unknown configuration: {configuration}"
            )

        label = CONFIGURATIONS[configuration]["label"]

        if label == "BASELINE":
            prefix = f"BASELINE_{self.city_name}"
        else:
            prefix = f"{label}_{self.city_name}"

        pattern = (
            f"{prefix}_{algorithm}_"
            f"????????_??????.csv"
        )

        files = list(self.predictions_dir.glob(pattern))

        if not files:
            raise FileNotFoundError(
                f"No prediction files found: {pattern}"
            )

        # Los timestamps YYYYMMDD_HHMMSS se ordenan
        # cronológicamente como cadenas.
        latest_file = max(
            files,
            key=lambda p: p.name
        )

        return latest_file

    def load_test_routes(self):
        #cargamos las rutas del test y se devuelven como diccionarios

        if not self.test_file.exists():
            raise FileNotFoundError(
                f"Test file not found: {self.test_file}"
            )

        routes = {}

        with open(
            self.test_file,
            "r",
            encoding="utf-8-sig",
            newline=""
        ) as f:

            reader = csv.DictReader(f)

            for row in reader:

                trail_id = row["trail_id"]
                poi_id = row["poi_id"]

                routes.setdefault(
                    trail_id, []
                ).append(poi_id)

        return routes

    def load_qrels(self, hops=1):

        routes = self.load_test_routes()

        qrels_dict = {}

        for trail_id, pois in routes.items():

            # Siempre predecimos el siguiente POI
            for i in range(len(pois) - 1):

                target_index = i + 1

                step_number = i + 2

                target_poi = pois[target_index]

                query_id = f"{trail_id}_{step_number}"

                qrels_dict[query_id] = {
                    target_poi: 1
                }

        return Qrels(qrels_dict), qrels_dict

    def load_run(self, configuration, algorithm):

        file_path = self.find_prediction_file(
            configuration,
            algorithm
        )

        print(
            f"[Evaluator] {configuration} / {algorithm}: "
            f"{file_path.name}"
        )

        run_dict = {}

        with open(
            file_path,
            "r",
            encoding="utf-8-sig",
            newline=""
        ) as f:

            reader = csv.DictReader(f)

            for row in reader:

                query_id = (
                    f"{row['trail_id']}_{row['step']}"
                )

                poi_id = row["poi_id"]

                score = float(row["prediction"])

                run_dict.setdefault(
                    query_id, {}
                )[poi_id] = score

        if not run_dict:
            raise ValueError(
                f"Empty prediction file: {file_path}"
            )

        return Run(
            run_dict,
            name=configuration
        )

    def evaluate_configuration(self, configuration, algorithm):

        hops = CONFIGURATIONS[configuration]["hops"]

        qrels, qrels_dict = self.load_qrels(hops)

        run = self.load_run(configuration, algorithm)

        results = evaluate(qrels=qrels,run=run, metrics=METRICS,make_comparable=True)

        print(f"\n{algorithm.upper()} - {configuration}")

        print(f"Queries in qrels: {len(qrels_dict)}")

        for metric, value in results.items():
            print(f"{metric}: {value:.6f}")

        return results

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--city",
        default="Tokyo"
    )

    parser.add_argument(
        "--algorithm",
        choices=["random", "markov"],
        required=True
    )

    parser.add_argument(
        "--config",
        choices=list(CONFIGURATIONS.keys()),
        required=True
    )

    args = parser.parse_args()

    evaluator = Evaluator(args.city)

    evaluator.evaluate_configuration(
        args.config,
        args.algorithm
    )