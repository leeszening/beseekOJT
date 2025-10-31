## 📁 Project Structure

```bash
ApaPlan_OJT/
├── .dockerignore
├── .gitignore
├── cloudbuild.yaml
├── deploy.sh
├── docker-compose.yml
├── Dockerfile
├── firebase_config.py
├── README.md
├── requirement.txt
└── src/
    ├── main.py
    ├── assets/
    │   ├── map_script.js
    │   └── styles.css
    ├── components/
    │   ├── auth.py
    │   └── pyrebase_auth.py
    ├── pages/
    │   ├── home_page.py
    │   ├── journal_detail_page.py
    │   ├── journal_edit_page.py
    │   ├── login_page.py
    │   ├── profile_page.py
    │   └── journal_edit/
    │       ├── __init__.py
    │       ├── callbacks.py
    │       └── layout.py
    └── shared/
        ├── auth_utils.py
        └── journal_utils.py
```

## 🚀 Running the App

### Using Docker Compose (Recommended)
```bash
docker-compose up -d --build
```

### Using Local Python Environment
1.  **Set up a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run the app:**
    ```bash
    python src/main.py
    ```

## ☁️ Deployment to Cloud Run

This project includes a script to automate manual deployments to Google Cloud Run.

**Prerequisites:**
*   Google Cloud SDK (`gcloud`) is installed and configured.
*   Docker is installed and running.
*   You have authenticated with Google Cloud (`gcloud auth login`).
*   You have configured Docker to use `gcloud` as a credential helper (`gcloud auth configure-docker europe-west1-docker.pkg.dev`).

**Steps:**

1.  Make sure the script is executable:
    ```bash
    chmod +x deploy.sh
    ```
2.  Run the deployment script:
    ```bash
    ./deploy.sh
    ```
The script will build the Docker image, push it to Google Artifact Registry, and deploy the new version to Cloud Run.
