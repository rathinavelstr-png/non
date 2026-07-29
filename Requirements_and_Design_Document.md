# Business Income & Spending Dashboard
### Requirements and Technical Design Document

---

## 1. Project Overview

A web-based business dashboard built with **Python** and **Streamlit** that lets a business owner or manager:

1. View **yearly** income vs spending trends.
2. View **month-wise** income vs spending charts within a selected year.
3. **Click / select a month** to drill down into **department-wise** income and spending details for that month.

The app is data-driven (reads from a CSV/Excel file or a database) and renders interactive charts using **Plotly**.

---

## 2. Goals & Objectives

- Give management a quick visual summary of financial health (income vs spending) over time.
- Allow drill-down analysis from Year → Month → Department.
- Keep the app simple to deploy (single command: `streamlit run app.py`), with no heavy backend needed.
- Make the data source swappable (CSV now, database later) without changing the UI code.

---

## 3. Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-1 | The system shall load transaction data containing at least: Date, Department, Type (Income/Spending), Amount. |
| FR-2 | The system shall display a **Year selector** (dropdown). |
| FR-3 | For the selected year, the system shall display a **month-wise bar/line chart** comparing Income vs Spending for each of the 12 months. |
| FR-4 | The system shall display a **yearly summary** (year-over-year Income vs Spending) chart, independent of the month selected. |
| FR-5 | The system shall display **KPI cards** — Total Income, Total Spending, Net Profit/Loss — for the selected year. |
| FR-6 | The system shall provide a **Month selector** (dropdown or clicking a bar in the chart) within the selected year. |
| FR-7 | When a month is selected, the system shall display a **department-wise breakdown** of Income and Spending for that month (bar chart + table). |
| FR-8 | The system shall display department-wise **Net (Income − Spending)** for the selected month. |
| FR-9 | The system shall allow the user to filter by department (optional, multi-select) to narrow charts. |
| FR-10 | The system shall handle missing/absent data for a month or department gracefully (show zero / "No data"). |
| FR-11 | The system shall allow exporting the filtered/aggregated data as CSV. |

## 4. Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| NFR-1 | The app should load and respond within 2–3 seconds for datasets up to ~100,000 rows. |
| NFR-2 | Code should be modular (data loading, aggregation, and UI kept in separate functions/files). |
| NFR-3 | The app should be responsive (usable on laptop and tablet browser widths). |
| NFR-4 | Data source should be configurable (CSV path, or DB connection string) via a config file/environment variable. |
| NFR-5 | The app should cache expensive operations (`st.cache_data`) to avoid recomputation on every interaction. |

---

## 5. Data Model

The simplest approach is a single **transactions table** (CSV, Excel, or SQL table) with one row per transaction:

| Column        | Type    | Description                                  |
|---------------|---------|-----------------------------------------------|
| `date`        | Date    | Transaction date (YYYY-MM-DD)                 |
| `year`        | Int     | Derived from date (or stored directly)        |
| `month`       | Int     | Derived from date (1–12)                       |
| `department`  | String  | e.g., Sales, Marketing, HR, Operations, IT     |
| `type`        | String  | `Income` or `Spending`                         |
| `category`    | String  | Optional sub-category (e.g., "Salaries", "Product Sales") |
| `amount`      | Float   | Transaction amount (always positive; sign is implied by `type`) |
| `description` | String  | Optional free-text note                        |

**Sample row:**
```
date, department, type, category, amount, description
2026-03-15, Sales, Income, Product Sales, 125000, "Q1 bulk order"
2026-03-18, Marketing, Spending, Ad Campaign, 40000, "Social media ads"
```

> This flat structure keeps aggregation simple: yearly = groupby(year), monthly = groupby(year, month), department-wise = groupby(year, month, department).

---

## 6. System Architecture

```
business_dashboard/
├── app.py                  # Main Streamlit entry point (UI + page flow)
├── data/
│   └── transactions.csv    # Sample / real data source
├── modules/
│   ├── data_loader.py      # Load & clean data, cache it
│   ├── aggregations.py     # Groupby logic (yearly, monthly, department)
│   └── charts.py           # Plotly chart-building functions
├── requirements.txt        # Python dependencies
└── README.md
```

**Flow:**
1. `data_loader.py` reads the CSV/DB into a pandas DataFrame, parses dates, validates columns.
2. `aggregations.py` provides pure functions that take the DataFrame + filters (year, month) and return summarized DataFrames.
3. `charts.py` takes summarized DataFrames and returns Plotly figure objects.
4. `app.py` wires it together: sidebar filters → call aggregation → call chart function → `st.plotly_chart()`.

This separation means you can later swap the CSV for a real database by only changing `data_loader.py`.

---

## 7. Tech Stack

| Layer          | Choice |
|----------------|--------|
| Language       | Python 3.10+ |
| UI Framework   | Streamlit |
| Data handling  | pandas |
| Charts         | Plotly Express / Plotly Graph Objects |
| Data source    | CSV (default) — swappable to SQLite/PostgreSQL/Excel |
| Deployment     | Streamlit Community Cloud, or any server running `streamlit run app.py` |

**requirements.txt**
```
streamlit>=1.35
pandas>=2.0
plotly>=5.20
openpyxl>=3.1
```

---

## 8. UI / Page Design

**Sidebar:**
- Year selector (dropdown, defaults to latest year in data)
- Department multi-select filter (optional, defaults to "All")
- File uploader (optional — lets user upload their own CSV/Excel)

**Main area, top to bottom:**
1. **KPI row** — 3 metric cards: Total Income, Total Spending, Net Profit (for selected year)
2. **Yearly Trend chart** — Income vs Spending across all years (grouped bar or line chart), always visible regardless of month selection
3. **Month-wise chart** for the selected year — grouped/stacked bar chart, 12 months, Income vs Spending
4. **Month selector** below/above that chart (dropdown: Jan–Dec) — OR clicking directly on a bar (Streamlit supports `on_select` for Plotly charts in recent versions)
5. **Department-wise breakdown** (appears once a month is selected):
   - Bar chart: Department vs Income/Spending for the chosen month
   - Table: Department, Income, Spending, Net
   - Small pie/donut chart: share of spending by department (optional nice-to-have)
6. **Export button** — download the currently filtered data as CSV

---

## 9. Interaction Flow

```
User opens app
   ↓
Selects Year (sidebar)
   ↓
Sees: KPIs + Yearly trend chart + Month-wise chart (for that year)
   ↓
Selects a Month (dropdown or clicks a bar)
   ↓
Sees: Department-wise Income/Spending chart + table for that month
```

---

## 10. Edge Cases & Validation

- If uploaded file is missing required columns → show `st.error()` with a clear message listing the expected columns.
- If a selected year/month has no transactions → show `st.info("No data available for this period")` instead of an empty/broken chart.
- Duplicate rows are not deduplicated automatically — flagged as a data quality note in the README.
- Currency formatting: use a config constant (e.g., `₹`, `$`) so it's easy to change.

---

## 11. Future Enhancements (Out of Scope for v1)

- User authentication / role-based access (owner vs department manager)
- Database backend (PostgreSQL) with a data-entry form to add transactions from the UI
- Budget vs Actual comparison
- Forecasting (e.g., simple linear trend or Prophet) for next month's income/spending
- Multi-year comparison view (side-by-side)
- Automated email/PDF report generation

---

## 12. Deliverables

1. `app.py` — runnable Streamlit application (provided alongside this document)
2. Sample `transactions.csv` — dummy data to test the app immediately
3. This requirements/design document

---

## 13. How to Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open the local URL Streamlit prints (usually `http://localhost:8501`).
