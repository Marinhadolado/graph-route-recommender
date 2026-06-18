# Context-Aware POI Route Recommender

Graph-based, context-aware system for next-POI prediction and tourist route
recommendation, evaluated on cities data from the Context Trails dataset.

It implements and compares five recommendation algorithms (Random, Popularity,
Markov, NMF Preferences and a Markov+NMF hybrid) using Next-POI ranking metrics
(HR@K, MRR@K, nDCG@K).

The backend uses **Neo4j** for persistence and **graph-tool** for in-memory
graph operations, with **Ranx** for evaluation.

---

## Requirements

- Docker + Docker Compose (for Neo4j)
- Python 3.x with the dependencies in `backend/requirements.txt`
- A separate environment for NMF training that includes `scikit-surprise`

```bash
pip install -r backend/requirements.txt
```

---

## Project layout

```
project/
├── docker-compose.yml
├── import/
└── backend/
    ├── dataset/
    ├── predictions/
    └── src/
        ├── persistence/
        ├── graph/
        ├── services/
            └── algorithms/
        └── evaluation/
```
---

## Setup

1. Start Neo4j:

   ```bash
   docker-compose up -d
   ```

2. Run everything below from `backend/src/` using `python3 -m`.

---

## Pipeline

Run the steps in order. Steps 1–4 are the one-time data preparation; steps 5–6
are the experiment loop you repeat per algorithm.

### 1. Load data into Neo4j
Interactive — pick the city. Purges and reloads the database.

```bash
python3 -m persistence.LoadDB
```

### 2. Generate the dataset (train/test split)
Arguments: `<min_steps> <num_trails> <city>`

```bash
python3 -m persistence.DatasetGenerator 3 2 Tokyo
```

### 3. Build the in-memory graph (.gt)
Interactive — pick the city. Produces `import/<City>/<City>.gt`.

```bash
python3 -m graph.BuildGraph
```

### 4. Train the NMF model (only for `preferences` and `markov_preferences`)
Requires the environment with `scikit-surprise`. Produces
`dataset/fm_<City>.pkl`.

```bash
python3 -m scripts.FMTraining
```

### 5. Generate predictions
Arguments: `<user_id> <context> <algorithm> <city>`
`context` is `None` or a JSON string. Algorithms: `random`, `popularity`,
`markov`, `preferences`, `markov_preferences`.

```bash
# No context
python3 -m services.Predictor 155648 None popularity Tokyo

# With context
python3 -m services.Predictor 155648 '{"conditions": "Partially cloudy", "time_segment": "Weekend_EarlyMorning"}' popularity Tokyo
```

### 6. Evaluate
Interactive — pick the city and algorithm. For `markov_preferences` it also
asks for a weight suffix (e.g. `50_50`). Reads the most recent prediction file.

```bash
python3 -m evaluation.Evaluator
```

---

## Hybrid weight sweep

To generate predictions for every Markov/NMF weight combination at once:

```bash
python3 -m scripts.MarkovPreferencesExperiment
```

Then evaluate each combination via `Evaluator`, choosing `markov_preferences`
and the suffix you want (e.g. `20_80`, `50_50`, `70_30`).

---

## Quick smoke test

Verifies the full pipeline runs without errors after a code change:

```bash
python3 -m services.Predictor 155648 None random Tokyo      && python3 -m evaluation.Evaluator
python3 -m services.Predictor 155648 None popularity Tokyo  && python3 -m evaluation.Evaluator
python3 -m services.Predictor 155648 None markov Tokyo      && python3 -m evaluation.Evaluator
python3 -m services.Predictor 155648 None preferences Tokyo && python3 -m evaluation.Evaluator
```

---

## Notes

- Always run modules with `python3 -m` from `backend/src/` so package imports
  resolve correctly.
- If you regenerate the dataset (step 2), rebuild the graph (step 3) and
  retrain NMF (step 4) so all artifacts stay consistent.
- `preferences` and `markov_preferences` need `fm_<City>.pkl`; if it is missing
  the model is skipped and predictions fall back to the available signal.
- Neo4j connection defaults can be overridden with the `NEO4J_URI`,
  `NEO4J_USER` and `NEO4J_PASSWORD` environment variables.
