import zipfile
from pathlib import Path

# Back-end (Flask) code for enhanced Excel-to-SQLite API
import os 
import sqlite3
import pandas as pd
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
from tempfile import NamedTemporaryFile

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/analyze', methods=['POST'])
def analyze_excel():
    file = request.files.get('excel')
    if not file:
        return jsonify({'error': 'No Excel file provided'}), 400

    path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
    file.save(path)

    sheets_info = {}
    try:
        xl = pd.read_excel(path, sheet_name=None)
        for sheet, df in xl.items():
            sheets_info[sheet] = list(df.columns)
        return jsonify(sheets_info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload_excel_to_sqlite():
    excel_file = request.files.get('excel')
    db_file = request.files.get('db')
    append_conditions = request.form.get('append_conditions', '{}')

    if not excel_file:
        return 'Excel file is required.', 400

    excel_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(excel_file.filename))
    excel_file.save(excel_path)

    if db_file:
        db_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(db_file.filename))
        db_file.save(db_path)
    else:
        temp_db = NamedTemporaryFile(delete=False, suffix='.db', dir=app.config['UPLOAD_FOLDER'])
        db_path = temp_db.name
        temp_db.close()

    append_conditions = eval(append_conditions)
    conn = sqlite3.connect(db_path)
    excel_data = pd.read_excel(excel_path, sheet_name=None)

    for sheet_name, df in excel_data.items():
        df.columns = [str(c).strip().replace(" ", "_") for c in df.columns]
        condition_col = append_conditions.get(sheet_name)

        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (sheet_name,))
        exists = cursor.fetchone()

        if not exists:
            df.to_sql(sheet_name, conn, if_exists="replace", index=False)
            continue

        existing_cols = [row[1] for row in cursor.execute(f"PRAGMA table_info({sheet_name})")]
        df = df[[col for col in df.columns if col in existing_cols]]

        if condition_col and condition_col in df.columns:
            existing_vals = pd.read_sql_query(f"SELECT {condition_col} FROM {sheet_name}", conn)[condition_col].tolist()
            df = df[~df[condition_col].isin(existing_vals)]

        if not df.empty:
            df.to_sql(sheet_name, conn, if_exists="append", index=False)

    conn.close()
    return send_file(db_path, as_attachment=True, download_name="updated_data.db")


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)



