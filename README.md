# pplkz_streamlit

Employer Analytics Dashboard (Streamlit).

## Local Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy (Public Link) via Streamlit Community Cloud

1. Push this repo to GitHub (including `data/Copy_2026.xlsx`).
2. Open: `https://share.streamlit.io/`
3. Click `New app`.
4. Select repository: `latethwe/pplkz_streamlit`.
5. Branch: `main` (or your production branch).
6. Main file path: `app.py`.
7. Click `Deploy`.

After deploy, you will get a public URL like:
`https://<app-name>.streamlit.app`

Share this link with users; they can open it from any browser.

## Important

- The app needs `data/Copy_2026.xlsx` in the repository.
- If you update data/code, push to GitHub and the app will redeploy automatically.
