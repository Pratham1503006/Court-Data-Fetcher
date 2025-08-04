# Court Data Fetcher & Mini-Dashboard

A web application that enables users to search Delhi High Court case metadata and download the latest orders/judgments via a simple UI.

## Table of Contents

- [Features](#features)  
- [Demo](#demo)  
- [Prerequisites](#prerequisites)  
- [Setup & Installation](#setup--installation)  
- [Usage](#usage)  
- [Project Structure](#project-structure)  
- [Database Schema](#database-schema)  
- [CAPTCHA Strategy](#captcha-strategy)  
- [Error Handling](#error-handling)  
- [Security & Compliance](#security--compliance)  
- [Optional Enhancements](#optional-enhancements)  
- [License](#license)  

---

## Features

- **Search by Case**: Select case type, enter case number, and filing year.  
- **CAPTCHA Handling**: Manual solve with audio fallback.  
- **Metadata Extraction**: Petitioner & respondent names, filing and next hearing dates, case status.  
- **Document Links**: List and download latest PDF orders/judgments.  
- **Query History**: View recent searches and outcomes.  
- **Audit Logging**: All queries and results logged in SQLite.  
- **Error Handling**: Friendly messages for invalid cases or downtime.

---

## Demo

Watch a 5-minute screen capture demonstrating:

1. Application launch  
2. Case search form interaction  
3. CAPTCHA solving  
4. Results display and PDF downloads  
5. Query history view  

---

## Prerequisites

- Python 3.8+  
- Chrome or Chromium browser  
- ChromeDriver compatible with your browser version  
- Git  

---

## Setup & Installation

1. **Clone the repository**  

   ```bash
   git clone https://github.com/yourusername/court-data-fetcher.git
   cd court-data-fetcher
   ```

2. **Install dependencies**  

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**  

   ```bash
   python app.py
   ```

4. **Access the app** at `http://localhost:5000` in your browser.  

---

## Usage

1. Select case type from dropdown.  
2. Enter case number.  
3. Choose filing year.  
4. Click "Search Case".  
5. Solve CAPTCHA if prompted.  
6. View results or error message.  
7. Download PDFs if available.  
8. Check history for past searches.  

---

## Project Structure

```
court-data-fetcher/
├── app.py
├── court_scraper.py
├── requirements.txt
├── templates/
│   ├── index.html
│   ├── results.html
│   └── history.html
├── static/
│   ├── styles.css
│   ├── script.js
│   └── favicon.ico
└── LICENSE
```

---

## Database Schema


---

## Database Schema

- **queries**  
  - id, case_type, case_number, filing_year, query_timestamp, status  
- **cases**  
  - id, query_id, petitioner, respondent, filing_date, next_hearing_date, case_status, raw_response  
- **documents**  
  - id, case_id, document_type, document_url, document_date  

---

## CAPTCHA Strategy

- **Manual Solve**: Users manually enter the CAPTCHA code displayed in the browser.  
- **Audio Option**: Supports audio CAPTCHA for accessibility.  
- **Ethical & Legal**: No automated breaking; fully compliant.

---

## Error Handling

- Invalid inputs → flash error & redirect to form.  
- No results → friendly “No case found” message.  
- Site errors or timeouts → catch exceptions & inform user.

---

## Security & Compliance

- **Environment Variables**: No hard-coded secrets.  
- **SQL Injection Protection**: Parameterized queries.  
- **Secure Sessions**: Flask secret key.  
- **Public Data Only**: No personal data stored beyond public records.  
- **Audit Trail**: Full logging in SQLite.

---

## Optional Enhancements

- Dockerfile for container deployment.  
- Unit tests with pytest.  
- CI/CD workflow (GitHub Actions).  
- Pagination for multiple orders.  
- Bulk search capabilities.  

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.  

