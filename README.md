# ML-Precision-Agriculture-Web-App

This web application uses Machine Learning to recommend crop, fertilizer, pesticide and storage process based on various variables.

This Flask application uses soil measurements and a machine-learning model to recommend crops. The repository root is the application root.

## Project structure

```text
app.py                 Flask application
db.py                  SQLite initialization and connections
run.py                 Application runner
templates/             HTML templates
static/                Images and frontend assets
ml/                    Model training code
data/                  Training dataset, schema, and data documentation
models/                Model artifacts and training reports
instance/              Local runtime databases (not committed)
```

## Configuration

Use `.env.example` as the configuration reference. Set secrets such as `FLASK_SECRET_KEY`, `ADMIN_USERNAME`, and `ADMIN_PASSWORD` in the deployment environment rather than committing them to the repository.

The local SQLite databases are kept under `instance/` for development and are ignored by Git. User accounts and analysis history must move to a managed production database before launch.

## Deployment

This is an open-source, platform-agnostic Flask application. Anyone is free to deploy it on the hosting platform that best fits their needs, or adapt it for another runtime.

For deployment, configure the required environment variables and choose suitable persistent storage for user accounts and analysis history. The included SQLite database is intended for development and small deployments.

## Model training

After changing the training data or model code, rebuild the compatible model artifact:

```text
python ml/model.py
```

The training script compares RBF SVC, linear SVC, logistic regression, random
forest, and extra trees with stratified cross-validation. It selects the model by
macro-F1, then balanced accuracy, so the minority crop labels are considered.
The trained pipeline is saved under `models/` and includes the same preprocessing
used during prediction. The comparison is written to
`models/model_comparison.csv`.

Before adding or replacing training data, audit it first:

```text
python ml/audit_data.py
```

The current `data/final_data.csv` is legacy data with unknown provenance. See
`data/README.md` for the audit findings and the rules for adding external data.

The selected model's dataset hash, validation metrics, and warnings are recorded in
`models/model_metadata.json`. This baseline must be revalidated when a traceable
agricultural dataset is added.

## Verification

Run the application checks with:

```text
pytest
```
