
from flask import Flask, request, jsonify
import pandas as pd
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = './uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'excel' not in request.files:
        return jsonify({"error": "Excel file missing"}), 400

    excel_file = request.files['excel']
    db_file = request.files.get('db', None)
    append_conditions = request.form.get('append_conditions', '{}')

    excel_path = os.path.join(UPLOAD_FOLDER, secure_filename(excel_file.filename))
    excel_file.save(excel_path)

    if db_file:
        db_path = os.path.join(UPLOAD_FOLDER, secure_filename(db_file.filename))
        db_file.save(db_path)
    else:
        db_path = os.path.join(UPLOAD_FOLDER, "generated.db")

    try:
        append_dict = eval(append_conditions) if append_conditions else {}
        process_excel_to_sqlite(excel_path, db_path, append_dict)
        return jsonify({"status": "success", "db_file": db_path})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def process_excel_to_sqlite(excel_path, db_path, append_conditions: dict):
    conn = sqlite3.connect(db_path)
    excel_data = pd.read_excel(excel_path, sheet_name=None)

    for sheet_name, df in excel_data.items():
        df.columns = [str(c).strip().replace(" ", "_") for c in df.columns]
        append_col = append_conditions.get(sheet_name, None)

        if not table_exists(conn, sheet_name):
            df.to_sql(sheet_name, conn, if_exists="replace", index=False)
            continue

        existing_cols = get_table_columns(conn, sheet_name)
        df = df[[col for col in df.columns if col in existing_cols]]

        if append_col and append_col in df.columns:
            existing_ids = pd.read_sql_query(f"SELECT {append_col} FROM {sheet_name}", conn)[append_col].tolist()
            df = df[~df[append_col].isin(existing_ids)]

        if not df.empty:
            df.to_sql(sheet_name, conn, if_exists="append", index=False)

    conn.close()

def table_exists(conn, table):
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    return cursor.fetchone() is not None

def get_table_columns(conn, table):
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table})")
    return [row[1] for row in cursor.fetchall()]

if __name__ == '__main__':
    app.run(debug=True)
        app.run(host='0.0.0.0', port=10000)
