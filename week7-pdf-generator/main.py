import os
import sqlite3
from datetime import datetime
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from playwright.sync_api import sync_playwright

DB_NAME = "report.db"
REPORTS_DIR = "reports"

os.makedirs(REPORTS_DIR, exist_ok=True)

def init_reports_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()

init_reports_db()

app = FastAPI(title="PDF Report Generator")

def get_report_data():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as total_orders, SUM(amount) as total_revenue FROM orders;")
    totals = cursor.fetchone()
    
    cursor.execute("""
        SELECT product, SUM(amount) as revenue, COUNT(*) as count 
        FROM orders 
        GROUP BY product 
        ORDER BY revenue DESC 
        LIMIT 5;
    """)
    top_products = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("SELECT id, customer, product, amount, created_at FROM orders ORDER BY created_at DESC;")
    all_orders = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "total_orders": totals["total_orders"],
        "total_revenue": round(totals["total_revenue"] or 0, 2),
        "top_products": top_products,
        "all_orders": all_orders
    }

def generate_pdf_file(data: dict, output_path: str):
    top_rows = "".join([f"<tr><td>{p['product']}</td><td>{p['count']}</td><td>${p['revenue']:,.2f}</td></tr>" for p in data['top_products']])
    all_rows = "".join([f"<tr><td>{o['id']}</td><td>{o['customer']}</td><td>{o['product']}</td><td>${o['amount']:,.2f}</td><td>{o['created_at']}</td></tr>" for o in data['all_orders']])

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 30px; color: #1e293b; }}
            h1 {{ color: #0f172a; border-bottom: 2px solid #2563eb; padding-bottom: 8px; }}
            .stats {{ display: flex; gap: 20px; margin: 20px 0; }}
            .card {{ background: #f8fafc; border: 1px solid #e2e8f0; padding: 15px; border-radius: 6px; width: 45%; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
            th, td {{ border: 1px solid #cbd5e1; padding: 8px; text-align: left; font-size: 12px; }}
            th {{ background: #1e293b; color: white; }}
            tr {{ break-inside: avoid; }}
            thead {{ display: table-header-group; }}
        </style>
    </head>
    <body>
        <h1>Sales Executive Report ({data['date']})</h1>
        <div class="stats">
            <div class="card"><h3>Total Orders</h3><p>{data['total_orders']}</p></div>
            <div class="card"><h3>Total Revenue</h3><p>${data['total_revenue']:,.2f}</p></div>
        </div>

        <h2>Top 5 Products</h2>
        <table>
            <thead><tr><th>Product</th><th>Orders</th><th>Revenue</th></tr></thead>
            <tbody>{top_rows}</tbody>
        </table>

        <h2>Full Order Log</h2>
        <table>
            <thead><tr><th>ID</th><th>Customer</th><th>Product</th><th>Amount</th><th>Date</th></tr></thead>
            <tbody>{all_rows}</tbody>
        </table>
    </body>
    </html>
    """

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_content(html_content)
        page.pdf(path=output_path, format="A4", print_background=True)
        browser.close()

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/reports", status_code=status.HTTP_201_CREATED)
def create_report(force: bool = False):
    today_str = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    if not force:
        cursor.execute("SELECT id, path FROM reports WHERE created_at LIKE ? ORDER BY id DESC LIMIT 1;", (f"{today_str}%",))
        existing = cursor.fetchone()
        if existing:
            conn.close()
            return {"id": existing[0], "file": f"/reports/{existing[0]}/file", "message": "Reused existing report"}
            
    data = get_report_data()
    cursor.execute("INSERT INTO reports (path, created_at) VALUES ('', ?);", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),))
    report_id = cursor.lastrowid
    
    file_path = os.path.join(REPORTS_DIR, f"report_{report_id}.pdf")
    generate_pdf_file(data, file_path)
    
    cursor.execute("UPDATE reports SET path = ? WHERE id = ?;", (file_path, report_id))
    conn.commit()
    conn.close()
    
    return {"id": report_id, "file": f"/reports/{report_id}/file"}

@app.get("/reports/{report_id}")
def get_report_details(report_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, path, created_at FROM reports WHERE id = ?;", (report_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Report not found")
        
    return {"id": row[0], "created_at": row[2], "file": f"/reports/{row[0]}/file"}

@app.get("/reports/{report_id}/file")
def download_report_file(report_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT path FROM reports WHERE id = ?;", (report_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row or not os.path.exists(row[0]):
        raise HTTPException(status_code=404, detail="PDF artifact file not found")
        
    return FileResponse(row[0], media_type="application/pdf", filename=f"report_{report_id}.pdf")