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
data/                  Training dataset
models/                Model artifacts
instance/              Local runtime databases (not committed)
```

## Configuration

Use `.env.example` as the configuration reference. Set secrets such as `FLASK_SECRET_KEY`, `ADMIN_USERNAME`, and `ADMIN_PASSWORD` in the deployment environment rather than committing them to the repository.

The local SQLite databases are kept under `instance/` for development and are ignored by Git. User accounts and analysis history must move to a managed production database before launch.

## Deployment

This is an open-source, platform-agnostic Flask application. Anyone is free to deploy it on the hosting platform that best fits their needs, or adapt it for another runtime.

For deployment, configure the required environment variables and choose suitable persistent storage for user accounts and analysis history. The included SQLite database is intended for development and small deployments.
