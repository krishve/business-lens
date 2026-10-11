# Business Lens input data

All files are UTF-8 CSVs with a header row. IDs are text and must match exactly across files. Amounts are USD and nonnegative. Date fields accept ISO dates or timestamps; timestamps are read as UTC. Blank values are allowed only where marked optional. Boolean fields accept `true` or `false`.

Each file can hold all reporting years. You may split records into `table_name__2025.csv` files, provided keys do not repeat. All 15 tables are required; transaction tables may contain headers only.

## periods.csv

Key: `year`.

| Column | Type | Meaning |
| --- | --- | --- |
| year | Integer | Complete calendar year covered by the input set, such as 2025 |
| complete | Boolean | Must be true; partial years are not supported |

Transaction dates must fall in a declared year. The latest declared December 31 is the dataset cutoff. Defects and cases may start before the first declared year so backlog can carry forward. Do not provide events after the cutoff.

## customers.csv

Key: `customer_id`.

| Column | Type | Meaning |
| --- | --- | --- |
| customer_id | Text | Stable customer identifier |
| customer_name | Text | Display name; keep names unique for customer pickers |
| industry | Text | Business sector |
| joined_date | Date | Date the customer relationship began |

## customer_years.csv

Key: `customer_id` + `year`. A snapshot is required for each customer/year with license or support revenue. Other missing snapshots appear blank rather than zero in comparisons.

| Column | Type | Meaning |
| --- | --- | --- |
| customer_id | Text | Link to customers |
| year | Integer | Reporting year |
| licensed_users | Integer | Seats licensed at year-end |
| active_users | Integer | Distinct licensed users active in the final 90 days of the year; cannot exceed licensed_users |
| customizations | Integer | Customer-specific extensions in use at year-end |
| training_hours | Number | Total instructor-led customer training hours delivered during the year, not attendee-hours |

Training hours are descriptive. Their costs belong in the appropriate services worklogs and must not be added again from this table. Year-end users are a rough denominator for annual case rates, not a time-weighted usage measure.

## staff.csv

Key: `staff_id`.

| Column | Type | Meaning |
| --- | --- | --- |
| staff_id | Text | Stable staff identifier |
| staff_name | Text | Display name |
| role | Text | Support, Engineering or Services |

The support team page lists staff with role Support and anyone with selected-year support ownership or time entries. Hourly rates are stored on worklogs so historical costs are preserved.

## releases.csv

Key: `release_id`.

| Column | Type | Meaning |
| --- | --- | --- |
| release_id | Text | Version identifier, such as 6.2; never a decimal number |
| release_date | Date | Date the release became available |

## topics.csv

Key: `topic_id`.

| Column | Type | Meaning |
| --- | --- | --- |
| topic_id | Text | Stable functionality or recurring-topic identifier |
| product_area | Text | Broad area, such as Reporting or Workflow |
| functionality | Text | Specific task or topic, such as Export reports |
| approved_answer | Boolean | Whether a reviewed answer is currently available |
| answer_only | Boolean | Whether this topic can be resolved by providing information without changing customer data or access |
| knowledge_article | Text | Article reference; use Not available when absent |

The two Boolean values are reviewed input judgments, not conclusions inferred by the program. They describe current readiness, not historical readiness. The eligibility rules also check each case's type and resolution.

## license_revenue.csv

Key: `entry_id`.

| Column | Type | Meaning |
| --- | --- | --- |
| entry_id | Text | Unique license revenue entry |
| customer_id | Text | Link to customers |
| revenue_date | Date | Recognition date, not necessarily invoice or payment date |
| amount_usd | Number | License revenue recognized on this date |
| delivery_cost_usd | Number | Direct license delivery expense recorded with this entry |

The sample uses one-time license and expansion sales. It does not label license revenue as recurring revenue or ARR.

## support_revenue.csv

Key: `entry_id`.

| Column | Type | Meaning |
| --- | --- | --- |
| entry_id | Text | Unique support revenue entry |
| customer_id | Text | Link to customers |
| revenue_date | Date | Recognition date |
| amount_usd | Number | Support revenue recognized; sample annual fees are spread across 12 monthly rows |

Do not repeat the full annual fee on every monthly row or on every case.

## projects.csv

Key: `project_id`.

| Column | Type | Meaning |
| --- | --- | --- |
| project_id | Text | Stable consulting project identifier |
| customer_id | Text | Link to customers |
| project_name | Text | Project name or service, such as Migration |
| billing_model | Text | Fixed price or Time and materials |
| budget_hours | Number | Total project hours budget, including all years |

The hours comparison uses lifetime hours observed through the selected year-end. The budget is the current supplied budget, not a versioned historical budget.

## services_revenue.csv

Key: `entry_id`.

| Column | Type | Meaning |
| --- | --- | --- |
| entry_id | Text | Unique services revenue entry |
| project_id | Text | Link to projects; the customer is obtained from the project |
| revenue_date | Date | Recognition date |
| amount_usd | Number | Revenue recognized on that date |

Use an agreed recognition schedule for fixed-price work. Do not calculate its revenue by multiplying hours by a billing rate.

## defects.csv

Key: `defect_id`.

| Column | Type | Meaning |
| --- | --- | --- |
| defect_id | Text | One unique software defect |
| topic_id | Text | Link to topics |
| severity | Text | Critical, High, Medium or Low |
| origin | Text | Customer or Internal; who first discovered the defect |
| detected_release | Text | Link to releases; version where the defect was first logged |
| created_at | Timestamp | Defect creation time |
| resolved_at | Timestamp, optional | Engineering resolution time; blank means unresolved at dataset cutoff |
| prevention_gap | Text | Example: Missing regression test, Missing integration test or Missing validation |

Resolved does not imply that the fix was deployed to every customer. The sample does not include deployment history, affected-version lists or reopened defects.

## defect_customers.csv

Key: `defect_id` + `customer_id`.

| Column | Type | Meaning |
| --- | --- | --- |
| defect_id | Text | Link to defects |
| customer_id | Text | Link to customers |
| associated_at | Timestamp | When this customer became known to be affected |

Associations stay effective after this date. Removal or changing allocation weights are not supported. Engineering logs use only associations known on their work date. Internal-origin defects can have customer associations without changing their origin.

## support_cases.csv

Key: `case_id`. A case belongs to one customer and one topic. Several cases may link to the same defect.

| Column | Type | Meaning |
| --- | --- | --- |
| case_id | Text | Unique support case |
| customer_id | Text | Link to customers |
| topic_id | Text | Link to topics |
| defect_id | Text, optional | Link to a confirmed product defect; required for Code defect cases |
| analyst_id | Text | Case owner's staff ID |
| case_type | Text | Q&A, Configuration help, Code defect, Data issue or Enhancement request |
| confirmed_cause | Text | What investigation found: for example Expected behavior, Code defect, Incorrect configuration, Data quality, Product limitation |
| prevention_gap | Text | What could prevent recurrence: for example Documentation gap, Confusing UI, Missing validation, Missing regression test |
| resolution | Text | Knowledge article, Code fix, Data correction, Configuration change, Product review or Unresolved in the sample |
| severity | Text | Critical, High, Medium or Low |
| created_at | Timestamp | When the case was received |
| first_response_at | Timestamp, optional | First response; blank means unanswered at dataset cutoff |
| resolved_at | Timestamp, optional | Case resolution; blank means unresolved at dataset cutoff |
| response_sla_hours | Number | Positive elapsed-hour target for first response |
| csat_score | Integer 1–5, optional | Customer survey response; missing is not zero |
| survey_at | Timestamp, optional | Survey response date; required exactly when a score is supplied |

Cause, prevention gap and resolution are separate dimensions. Keep spelling consistent because tables group exact strings. The FAQ calculation specifically requires case_type Q&A and resolution Knowledge article. A linked defect must also have a matching customer association.

All case dates are event timestamps, not durations. Resolution must follow response and creation; a survey follows resolution. Staff reassignment and reopening history are not modeled.

## worklogs.csv

Key: `worklog_id`.

| Column | Type | Meaning |
| --- | --- | --- |
| worklog_id | Text | Unique time entry |
| work_date | Timestamp | When the work occurred; used to select the cost year |
| staff_id | Text | Link to staff |
| activity | Text | Support, Engineering or Services |
| case_id | Text, optional | Required for Support; blank for other activities |
| defect_id | Text, optional | Required for Engineering; blank for other activities |
| project_id | Text, optional | Required for Services; blank for other activities |
| minutes | Number | Positive actual effort |
| hourly_cost_usd | Number | Internal hourly cost at the time of work; may be zero for genuinely zero-cost work |

Exactly one target ID is required according to activity. Do not put a defect ID on a Support entry just because its case links to a defect. This keeps each cost in one category.

Support cost is charged to the case customer. Services cost is charged to the project customer. Engineering cost is split across effective defect/customer associations. No billable rate or extra time-and-materials revenue is inferred from these records.

## operating_expenses.csv

Key: `expense_id`.

| Column | Type | Meaning |
| --- | --- | --- |
| expense_id | Text | Unique expense entry |
| expense_date | Date | Period expense date |
| category | Text | Example: Sales and marketing, Product development, Administration, Hosting and tools |
| amount_usd | Number | Expense amount that is not already recorded as a delivery cost |

The sample categories are management assumptions. Ensure your own accounting treatment is consistent. The app cannot detect the same economic cost entered under two different record IDs in different files.

## Relationship summary

```text
customers -> customer_years, license_revenue, support_revenue
customers -> projects -> services_revenue and Services worklogs
customers -> support_cases -> Support worklogs
topics -> support_cases and defects
defects -> defect_customers -> customers
defects -> Engineering worklogs
staff -> worklogs and case ownership
releases -> defects
periods -> allowed financial and worklog years
```

Revenue is aggregated separately from cases and time before customer results are joined. This prevents a customer's annual fee from being repeated once per support case.
