# Streamlit Cloud deploy guide

## 1) Files to add to your GitHub repo
- `hiring_process_dashboard_full_lifecycle.py`  (your Streamlit app)
- `requirements.txt`
- `runtime.txt`  (optional; pins Python to 3.11 on Streamlit Cloud)

## 2) Minimal `requirements.txt`
```
streamlit>=1.37,<2
plotly>=5.18
numpy>=1.23
```

## 3) Pin Python (optional but recommended)
```
python-3.11
```

## 4) On Streamlit Cloud
- Create app → point to your repo/branch.
- **Main file path** must match your app filename, e.g. `hiring_process_dashboard_full_lifecycle.py`.
- Click Deploy.

## 5) Common fix for `ModuleNotFoundError`
If you see errors like `ModuleNotFoundError: plotly`:
- Make sure `plotly` is included in `requirements.txt`
- Reboot the app from the Streamlit Cloud "Manage app" panel after pushing the file.

## 6) Logs
- Open the app → lower-right "Manage app" → "Logs" for full tracebacks.
