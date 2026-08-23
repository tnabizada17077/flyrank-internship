# BE-08: PDF Report Generator API

## Overview
This backend application queries data stored in SQLite (`report.db`), aggregates key performance metrics, renders the results into an HTML document, and converts it into a multi-page PDF using Playwright (headless Chromium).

## Dataset
Option A: 200 random order transactions stored in `report.db`.

## Setup & Running
1. Activate virtual environment and install dependencies:
   ```bash
   pip install fastapi uvicorn pydantic playwright jinja2 python-dotenv
   playwright install chromium

   ## Aggregation Queries Used

### Total Orders & Revenue
```sql
SELECT COUNT(*) as total_orders, SUM(amount) as total_revenue 
FROM orders;

Top 5 Products by Revenue
SQL
SELECT product, SUM(amount) as revenue, COUNT(*) as count 
FROM orders 
GROUP BY product 
ORDER BY revenue DESC 
LIMIT 5;