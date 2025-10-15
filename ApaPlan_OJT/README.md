## 📁 Project Structure

```bash
ApaPlan/
├── src/
│   ├── main.py                     # Main Flask + Dash app entry
│   ├── pages/
│   │   ├── login.py                # Login, signup, reset password
│   │   └── home.py                 # Home page with password change & logout
│   ├── components/
│   │   ├── auth.py                 # Authentication utilities
│   │   ├── header.py               # App header layout
│   │   └── sidebar.py              # Sidebar navigation
│   ├── assets/        
│   │   └── style.css               # Custom styling
│   └── shared/
│       └── config.py               # Shared configuration settings
├── Dockerfile                      # For Cloud Run deployment (optional)
├── cloudbuild.yaml                 # For Cloud Build automation (optional)
├── firebase_config.py              # Firebase configuration
├── requirements.txt                # Python dependencies
└── README.md
