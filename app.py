import os
import sqlite3
from flask import Flask, render_template, request, flash, redirect, url_for
from court_scraper import CourtScraper

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
DATABASE = os.environ.get('DATABASE_PATH', 'court_data.db')

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_type TEXT NOT NULL,
            case_number TEXT NOT NULL,
            filing_year INTEGER NOT NULL,
            query_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending'
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_id INTEGER,
            petitioner TEXT,
            respondent TEXT,
            filing_date DATE,
            next_hearing_date DATE,
            case_status TEXT,
            raw_response TEXT,
            FOREIGN KEY (query_id) REFERENCES queries(id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER,
            document_type TEXT,
            document_url TEXT,
            document_date DATE,
            FOREIGN KEY (case_id) REFERENCES cases(id)
        )
    """)
    conn.commit()
    conn.close()

@app.route('/')
def index():
    case_types = [
        'W.P.(C)', 'CRL.A.', 'CRL.REV.P.', 'RFA', 'LPA', 'FAO', 'O.M.P.',
        'MAT.APP.', 'CS(OS)', 'I.A.', 'BAIL APPLN.', 'CRL.M.C.', 'ARB.P.',
        'CO.PET.', 'EX.P.', 'ITA', 'VAT APPEAL', 'CONT.CAS(C)', 'TR.P.(C)'
    ]
    years = list(range(2025, 1950, -1))
    return render_template('index.html', case_types=case_types, years=years)

@app.route('/search', methods=['POST'])
def search_case():
    case_type = request.form.get('case_type')
    case_number = request.form.get('case_number')
    filing_year = request.form.get('filing_year')
    if not all([case_type, case_number, filing_year]):
        flash('All fields are required', 'error')
        return redirect(url_for('index'))

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("INSERT INTO queries (case_type, case_number, filing_year) VALUES (?, ?, ?)",
              (case_type, case_number, int(filing_year)))
    qid = c.lastrowid
    conn.commit()
    conn.close()

    scraper = CourtScraper()
    result = scraper.search_case(case_type, case_number, filing_year)

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    if result['success']:
        c.execute("""
            INSERT INTO cases (query_id, petitioner, respondent, filing_date,
                               next_hearing_date, case_status, raw_response)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (qid, result['petitioner'], result['respondent'],
              result['filing_date'], result['next_hearing_date'],
              result['status'], result['raw_html']))
        cid = c.lastrowid
        for doc in result.get('documents', []):
            c.execute("""
                INSERT INTO documents (case_id, document_type, document_url, document_date)
                VALUES (?, ?, ?, ?)
            """, (cid, doc['type'], doc['url'], doc.get('date')))
        c.execute("UPDATE queries SET status = 'completed' WHERE id = ?", (qid,))
        conn.commit()
        conn.close()
        return render_template('results.html', data=result)
    else:
        c.execute("UPDATE queries SET status = 'failed' WHERE id = ?", (qid,))
        conn.commit()
        conn.close()
        flash(f"Search failed: {result.get('error','Unknown')}", 'error')
        return redirect(url_for('index'))

@app.route('/history')
def history():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("""
        SELECT q.id, q.case_type, q.case_number, q.filing_year, 
               q.query_timestamp, q.status, c.petitioner, c.respondent
        FROM queries q
        LEFT JOIN cases c ON q.id = c.query_id
        ORDER BY q.query_timestamp DESC
        LIMIT 50
    """)
    rows = c.fetchall()
    conn.close()
    return render_template('history.html', history=rows)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
