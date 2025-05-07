
# Excel to SQLite API

This Flask-based API lets you upload Excel files and append them to SQLite databases smartly — with optional conditions.

## Features
- Upload Excel `.xlsx`
- Upload or auto-create SQLite `.db`
- Append rows based on column (like ID)
- Supports multiple sheets

## Example Usage

### Upload Excel only
```bash
curl -X POST http://localhost:5000/upload -F "excel=@myfile.xlsx"
```

### Upload with SQLite + Condition
```bash
curl -X POST http://localhost:5000/upload \
  -F "excel=@myfile.xlsx" \
  -F "db=@mydatabase.db" \
  -F "append_conditions={\"Sheet1\":\"ID\"}"
```

## Deploy on Render
1. Push this repo to GitHub
2. Go to https://render.com
3. Create New Web Service → Link your GitHub
4. Set:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python app.py`
