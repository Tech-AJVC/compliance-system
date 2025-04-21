# Add these to your configuration section
GOOGLE_CLIENT_ID = ""
GOOGLE_CLIENT_SECRET = ""
GOOGLE_REDIRECT_URI = "http://localhost:3000/auth/google/callback"
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/gmail.send"
]

# Environment detection (set this to False in production)
DEBUG = False


# CORS Configuration
if DEBUG:
    # Development environment
    CORS_ORIGINS = [
        "http://localhost:3000",     # React development server
        "http://localhost:8080",     # Vue development server
        "http://localhost:4200",     # Angular development server
    ]
else:
    # Production environment
    CORS_ORIGINS = [
        "https://compliance.ajuniorvc.com", 
        "https://compliance-system.netlify.app", 
        "https://compliance-system.vercel.app",  
        "https://ajvc-compliance-system.com",
        # Make sure to add any domains you missed here
        "http://compliance-system.netlify.app",
        "http://ajvc-compliance-system.com",
    ]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
CORS_ALLOW_HEADERS = ["*"]
CORS_EXPOSE_HEADERS = [
    "Content-Length", 
    "Content-Range"
]
CORS_MAX_AGE = 600  # How long the results of a preflight request can be cached (in seconds)
