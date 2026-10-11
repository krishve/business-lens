# Business Lens

Business Lens is a small Python and Streamlit dashboard for a software business. It connects revenue, delivery costs, customer support and product defects so an owner can see where the business earns money and where effort is being spent.

It runs locally and accepts CSV files. No database, API key or external AI service is required.

## Project objective

The goal is to give a software business owner one place to compare income with the effort required to serve customers. A large customer is not always the most profitable: support cases, custom changes and consulting work can consume much of its revenue.

This project demonstrates how to load related CSV files, validate records, calculate financial and service metrics, and present the results in an interactive dashboard. It includes five years of fictional data so anyone can try it without connecting a business system.

## What it helps answer

- How did revenue and operating profit change from year to year?
- Which customers contribute the most and the least after delivery costs?
- Does a customer's support and consulting effort outweigh the fees it pays?
- How do usage, training and customization differ between more and less profitable customers?
- Which product areas cause repeated questions or defects?
- Which repeated questions are worth testing with an FAQ agent?

The dashboard explains its calculations. Its suggestions are fixed rules applied to the data. They are prompts for investigation, not proof of why something happened.

## Start the dashboard

Install **Python 3.13** and **Git**, then clone the repository:

```bash
git clone https://github.com/krishve/business-lens.git
cd business-lens
```

### Windows

Double-click `setup.bat`, wait for setup to finish, then double-click `run.bat`.

Or run these commands from the project folder:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m streamlit run app.py
```

### macOS or Linux

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m streamlit run app.py
```

Open <http://localhost:8501>. The dashboard opens on the Intro page, which explains the business questions, views and basic terms. Select Business overview in the sidebar, then choose a year; no upload is needed to try the bundled sample data.

For local-only access, add `--server.address=127.0.0.1` to the Streamlit command. Stop it with Ctrl+C in its terminal. If port 8501 is busy, add `--server.port 8502` to the Streamlit command and open that port instead.

## Sample data

The `data/sample` folder contains 15 CSV files covering the five complete years **2021–2025**. All names and records are fictional. The data contains:

- 12 customers, including two that join in 2023.
- 56 customer-year snapshots and 56 consulting projects.
- 2,000 support cases and 540 product defects.
- 4,336 time entries, 20 releases and 10 support topics.
- Separate license, support and services revenue records.
- Operating expenses for each year.

The sample includes low-fee customers with heavy support needs, customized accounts, a higher defect load in 2023, growing how-to questions and consulting projects that use more hours than planned. These patterns were deliberately created to make the dashboard useful to demonstrate. They are not industry benchmarks.

One file holds all years for a table. Year selectors use dates in the records, not separate copies of the dashboard.

## Dashboard views

| View | What it shows |
| --- | --- |
| Ask Lenny | Guided questions with calculated answers, supporting figures and a friendly character; no LLM or API key |
| Intro | A plain-language introduction, getting-started steps, a guide to each view and key terms |
| Business overview | Five-year revenue mix, year-over-year growth, delivery costs, operating profit and areas to review |
| Customers | Most-to-least customer contribution, cost and revenue breakdown, customer history, and comparisons of usage, training and customization |
| Services | Project revenue, labor cost, contribution and hours compared with budget |
| Support insights | Cases by product area and type, average and median handling time, recurring topics and prevention gaps |
| Product quality | Distinct defects by detected release and severity, internal/customer origin and year-end backlog |
| Support team | Workload, response SLA, severity mix and customer survey results |
| FAQ opportunities | Three-year topic volumes, eligibility rules and an adjustable estimate of time that could be freed |
| Data & definitions | Input counts, a download of the current CSV set, definitions and cost reconciliation |

The year selector applies to the data views; the Intro page is a general guide. Customer and product-area filters are local to the views that show them. They do not silently change the business-wide financial totals.

## Input files

| File | One row represents |
| --- | --- |
| `periods.csv` | A complete reporting year |
| `customers.csv` | A customer |
| `customer_years.csv` | A customer's usage, training and customization snapshot for a year |
| `staff.csv` | A staff member and role |
| `releases.csv` | A product release |
| `topics.csv` | A product functionality and its current FAQ documentation status |
| `license_revenue.csv` | A license revenue entry and its direct delivery cost |
| `support_revenue.csv` | A support revenue entry |
| `projects.csv` | A consulting project and its total hours budget |
| `services_revenue.csv` | A project's recognized revenue entry |
| `defects.csv` | A unique product defect |
| `defect_customers.csv` | A customer associated with a defect, with the date the association became known |
| `support_cases.csv` | A customer question, issue or request; it can link to a defect |
| `worklogs.csv` | A support, engineering or consulting time entry |
| `operating_expenses.csv` | An expense that is not already included in delivery cost |

See [DATA_DICTIONARY.md](DATA_DICTIONARY.md) for every column, the allowed values and the relationships between files.

## Upload your own CSV files

1. Keep the sample column names and use stable IDs across files.
2. Select **Upload CSV files** in the sidebar.
3. Select all required tables together. A table without records still needs a CSV with its header row.
4. Correct any validation errors shown, then choose a year.

You can split a table into annual exports, for example `support_cases__2024.csv` and `support_cases__2025.csv`. The part before `__YEAR` identifies the table. The records' dates determine their reporting year. Each record must appear only once across the uploads. Do not upload both a combined file and annual files containing the same records.

Uploads replace the complete sample set. They are not mixed with sample records or written into `data/sample`. They remain in the running app's memory/cache; restarting the app clears that cache. This is a local single-user demo, not a shared hosting service.

Only complete calendar years are supported. Declare them in `periods.csv` with `complete=true`. Include an empty transaction table if that category really has no activity. The program cannot determine whether a missing transaction is an omission or a real zero.

All money is USD. Dates use ISO format, such as `2025-03-15` or `2025-03-15T10:30:00`. Timestamps are interpreted as UTC. Blank optional fields mean unknown or not applicable. Do not use zero for a missing survey score or missing time record.

## How profitability is calculated

```text
Customer revenue = license + support + services revenue
Customer delivery cost = license delivery + support labor + consulting labor + allocated fixes
Customer contribution = customer revenue - customer delivery cost

Business contribution = sum of customer contribution - internal product-quality cost
Operating profit = business contribution - operating expenses
```

Labor cost is `minutes / 60 * hourly_cost_usd`. The hourly rate is an internal cost, not the price billed to the customer.

A fix can help several customers. Its engineering cost is divided equally among the customers associated with that defect on the work date. A $600 fix shared by three customers allocates $200 to each. Selecting one customer does not change that split. A later association does not rewrite an earlier allocation. Work with no customer association remains in an internal product-quality pool.

Customer contribution is useful for ranking accounts. It is not customer-level net profit because general operating expenses are not allocated to customers. Business operating profit excludes interest and tax. It is only as complete as the supplied costs.

Revenue follows the date it is recognized. It does not measure bookings, invoices or cash collections. Fixed-price project revenue comes from its revenue schedule, not hours multiplied by a billing rate. The sample spreads annual support fees across twelve months.

Do not include the same labor in worklogs and operating expenses. In the sample, Product development expenses represent other development work; defect-fix labor is already in worklogs. No taxes, currencies, credits/refunds or mid-year contract proration are modeled in this version. Revenue and costs must be nonnegative entries.

## Understand customer differences

The customer page shows revenue mix, support hours, number of cases, customization count, training hours and the share of licensed users who are active. It also compares the top and bottom three customers by contribution.

These comparisons help form questions. For example, a low-fee account with many customizations and high support effort may need a scope or pricing review. A customer with little training and repeated how-to questions may need better onboarding. The dashboard cannot prove that customization or training caused the financial result.

Usage and customization are year-end snapshots. They are not historical measurements for every support case. The sample does not include customer satisfaction history outside case surveys, acquisition cost, churn, collections or contract renewal dates.

## Support cases and defects are different

A support case belongs to one customer. A product defect is a unique software problem and can affect several customers. Count cases for support demand and distinct defect IDs for product quality.

Case type describes the request: Q&A, configuration help, code defect, data issue or enhancement request. Confirmed cause records what was found. Prevention gap records an improvement such as a missing regression test or documentation gap. A code defect and a missing test can therefore appear on the same case without being treated as competing categories.

Handling time is logged analyst effort. Resolution time is elapsed calendar time. Support insights use cases created in the selected year and effort observed through that year-end. Still-open cases can have incomplete effort; missing logs are excluded from averages and reported separately.

Response SLA uses elapsed hours, not business hours. Overdue unanswered cases are breaches. Unanswered cases not yet due at the year-end cutoff are shown separately. Survey results use the same created-year case group and include surveys received by year-end. The response rate divides those survey responses by cases in that group resolved by year-end.

There is one analyst owner and one resolution per case in this version. Reassignments, reopenings, holidays and separate customer resolutions for a shared bug are not modeled.

## FAQ opportunity estimates

The app does not contain an FAQ agent. It identifies topics for a possible pilot.

A candidate needs three consecutive reporting years, at least 12 eligible cases in the selected year, an approved answer, and an answer-only topic. An eligible case is a resolved Q&A case answered with a knowledge article and known handling effort. Topics requiring changes or investigation remain human-led.

```text
Estimated net hours freed = eligible handling hours * assumed self-service success rate
                           - annual review and maintenance hours
```

The sliders change assumptions, not historical case counts. The estimate uses the selected year's workload as a baseline. It is not a forecast, proven cost saving or staffing recommendation. Current documentation readiness is applied retrospectively; a historic readiness snapshot is not available.

Before expanding a pilot, measure answer correctness, repeat contacts, escalation rate, customer satisfaction, maintenance effort and running cost. The estimate does not include model/API charges or software development costs.

## Technology

| Tool | Purpose |
| --- | --- |
| Python 3.13 | Data loading, calculations and tests |
| Streamlit | Local browser interface, filters, uploads and downloads |
| pandas | Joins, validation and grouped calculations |
| Plotly | Interactive charts |
| CSV | Portable input files that can be inspected in a text editor or spreadsheet |
| pytest and Streamlit AppTest | Calculation and interface checks |

There is no database and no external AI call. Package versions are pinned in `requirements.txt` and `requirements-dev.txt`.

## Project files

```text
app.py                    Dashboard layout and interactions
schema.py                 Expected columns and key definitions
data_loader.py            CSV parsing and validation
metrics.py                Financial, support and FAQ calculations
generate_sample_data.py   Repeatable sample data generator
data/sample/              Fifteen fictional input CSVs
tests/                    Calculation and app tests
README.md                 Project overview and run instructions
DATA_DICTIONARY.md        Input definitions
requirements.txt          Application packages
requirements-dev.txt      Testing packages
setup.bat / run.bat        Windows setup and launch shortcuts
.streamlit/config.toml    Local server and display settings
.github/workflows/        Automated tests on pushes and pull requests
```

## Tests and sample regeneration

```powershell
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe generate_sample_data.py
```

The second command replaces only the bundled sample CSVs. It uses a fixed random seed so the results are repeatable.

Tests cover yearly cost and revenue reconciliation, shared-fix timing, unallocated engineering costs, zero revenue, year-end backlog, missing effort, unanswered SLA cases, FAQ assumptions, CSV errors, and dashboard pages. Validation detects malformed records; it does not certify the completeness or accounting accuracy of real uploads.

## A short demonstration

1. Start on Business overview. Compare 2021–2025 and the change in license revenue.
2. Open Customers. Compare Elm Logistics with Aster Labs, including support effort and fee levels.
3. Open Support insights. Inspect recurring reporting questions and missing-test categories.
4. Open Services. Check hours used against project budgets.
5. Open FAQ opportunities for 2025. Change the success assumption and explain why the estimated hours change while case volumes do not.
6. Show Data & definitions and explain why each engineering cost is counted once.

## Repository and data privacy

Source code: [krishve/business-lens](https://github.com/krishve/business-lens).

The repository contains the application, documentation, tests and fictional sample data. GitHub Actions is configured to run the tests on pushes and pull requests.

The `.gitignore` excludes the Python environment, caches, secrets, temporary files and `data/private/`. Keep real customer exports outside the tracked sample folder, and review staged files before committing changes.

No license has been selected yet. Hosting for multiple users would need authentication, access controls and a review of how uploaded data is kept.

## Ask Lenny

Lenny is a rule-based guide to the loaded data. Choose one of 11 questions and a year, and select a customer for the customer breakdown. Answers update with the selected data and show the calculation, supporting figures and a CSV download. Lenny covers customer contribution, annual profit changes, revenue sources, support effort, unresolved defects, project hours, FAQ trial candidates and suggested areas to review.

The assistant reuses the dashboard calculations. It does not run an LLM, make predictions or send data to an AI service. The floating panel accepts typed questions and matches them to supported topics using explicit phrases. Comparisons explain recorded amounts; they do not prove why a customer behaves a certain way. FAQ estimates use a 60% success assumption and four maintenance hours per topic; the FAQ opportunities page lets you change those assumptions.

`lenny.py` holds the question catalog and answer calculations. `lenny_ui.py` displays the guide. The character is a static asset in `assets/lenny.png`, created with an image generation tool during development; no image generation runs in the app. Asset creation details are in `assets/LENNY.md`.

### Floating Lenny

The Ask Lenny button stays at the bottom-right while you scroll. Open it for help with the current page and relevant guided questions. The panel stays open as you navigate; its previous reply clears when the page, year or filters change. Answers refresh with the selected year and data source.

On Customers, a customer breakdown uses the account selected in the page history filter; rankings still use all customers. On Support insights, answers use both the customer and product-area filters. FAQ answers use the page's success and maintenance assumptions. On Intro, Lenny uses the latest loaded year and offers quick questions. Before valid uploads, it provides page guidance without calculating figures.

Lenny receives page and filter values directly from the app; it does not capture the screen. `floating_lenny.py` implements the panel with Streamlit controls and scoped CSS. Type a question or use a suggestion button. The phrase matcher supports explicit loaded years, known customer names and product areas. Unsupported requests and ambiguous questions receive clarification. A new question replaces the previous exchange; this is not unrestricted chat.

### Appearance

The app uses the fictional company name Avenlo Software and an original geometric logo (`assets/avenlo-logo.svg`). The company is a demonstration brand, not a real organization represented by the sample records.

Use the sidebar's Dark mode switch to change the appearance for your session. The choice stays while moving between pages and does not affect other users. App styles, Plotly charts, data cells and Lenny's panel follow the switch. A fresh session starts in light mode. `ui_theme.py` keeps these presentation choices in one place. Native table toolbars may retain Streamlit's own appearance.

The floating assistant uses `lenny_intents.py` to match phrases. Examples: “Which customers are losing money?”, “How profitable is Aster in 2024?”, “Show support hours”, and “Explain this page”. Named customers and explicit years override the corresponding page defaults for that answer; the displayed scope makes this visible. Future predictions, unavailable years, multiple-topic requests and percentage changes in text are not guessed. Change FAQ assumptions on the FAQ page.
