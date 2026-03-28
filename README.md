# GitHub Cloud Connector

A backend API built with Python and FastAPI to seamlessly connect and interact with GitHub's API. 

## Features
* **Authentication:** Secured via Personal Access Token (PAT), with a Bonus OAuth 2.0 flow implementation.
* **API Integration:** Fetches repositories, lists issues, and creates issues.
* **Bonus Integration:** Creates Pull Requests.
* **Code Quality:** Fully typed with Pydantic models and includes robust HTTP error handling.

## Setup Instructions

1. **Clone the repository:**
   `git clone [your-repo-link]`
2. **Create a virtual environment:**
   `python -m venv venv`
   `source venv/bin/activate` (Mac/Linux) OR `venv\Scripts\activate` (Windows)
3. **Install dependencies:**
   `pip install -r requirements.txt` (Run `pip freeze > requirements.txt` before uploading to GitHub to generate this file!)
4. **Environment Variables:**
   Create a `.env` file in the root directory and add:
   ```text
   GITHUB_PAT=your_personal_access_token
   GITHUB_CLIENT_ID=your_oauth_app_client_id
   GITHUB_CLIENT_SECRET=your_oauth_app_client_secret