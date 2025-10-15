ApaPlan/
├── src/
│   ├── main.py                     # Main Flask + Dash app entry
│   ├── pages/
│   │   ├── login.py                # Login, signup, reset password
│   │   └── home.py                 # Home page with password change & logout
│   ├── components/
│   │   └── auth.py
│   │   └── header.py
│   │   └── sidebar.py
│   ├── assets/        
│   │   └── style.css 
│   └── shared/
│   │   └── config.py   
├── Dockerfile                      # For Cloud Run deployment (optional)
├── cloudbuild.yaml                 # For Cloud Build automation (optional)
├── README.md
├── firebase_config.py
└── requirements.txt
