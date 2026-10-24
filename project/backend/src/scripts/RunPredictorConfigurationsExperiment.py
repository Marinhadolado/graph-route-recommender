import subprocess
import sys

USER_ID = "155648"
CITY = "Tokyo"

# Configuraciones del paper
CONFIGURATIONS = {
    "BASELINE_Tokyo": {
        "prefilter": "true",
        "hops": 1,
        "context": "time_segment,conditions"
    },

    "WCTX_T": {
        "prefilter": "true",
        "hops": 1,
        "context": "conditions"
    },

    "WCTX_C": {
        "prefilter": "true",
        "hops": 1,
        "context": "time_segment"
    },

    "WCTX_L2": {
        "prefilter": "true",
        "hops": 2,
        "context": "time_segment,conditions"
    },

    "WCTX_TC": {
        "prefilter": "true",
        "hops": 1,
        "context": ""
    },

    "WCTX_TCL2": {
        "prefilter": "true",
        "hops": 2,
        "context": ""
    }
}

ALGORITHMS = ["markov", "random"]


def main():

    total = len(CONFIGURATIONS) * len(ALGORITHMS)
    completed = 0

    for algorithm in ALGORITHMS:

        for name, config in CONFIGURATIONS.items():

            print(f"\n{'=' * 60}")
            print(f"Experiment: {name}")
            print(f"Algorithm: {algorithm}")
            print(f"{'=' * 60}\n", flush=True)

            command = [
                sys.executable,
                "-m",
                "services.Predictor",
                USER_ID,
                config["prefilter"],
                algorithm,
                CITY,
                str(config["hops"]),
                config["context"]
            ]

            subprocess.run(command, check=True)

            completed += 1

            print(
                f"\nCompleted: {completed}/{total}",
                flush=True
            )

    print("\nAll experiments completed!")


if __name__ == "__main__":
    main()