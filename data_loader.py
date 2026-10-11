"""Read CSV inputs without silently substituting sample data or dropping bad rows."""
import csv
import io
import re
from pathlib import Path
import numpy as np
import pandas as pd
from schema import SCHEMAS, KEYS, CASE_TYPES, SEVERITIES, fields


class DataError(ValueError):
    """An input problem that can be shown directly in the dashboard."""


def read_files(files):
    """Accept (filename, bytes) pairs; __YEAR suffixes allow annual exports."""
    grouped = {name: [] for name in SCHEMAS}
    errors = []
    seen = set()
    for filename, content in files:
        filename = Path(filename).name
        name = re.sub(r'__\d{4}$', '', Path(filename).stem)
        if name not in SCHEMAS or not filename.lower().endswith('.csv'):
            errors.append(f'{filename}: unrecognized filename. Use the names in Data & definitions.')
            continue
        if filename in seen:
            errors.append(f'{filename}: file was supplied twice.')
            continue
        seen.add(filename)
        try:
            header = next(csv.reader(io.StringIO(content.decode('utf-8-sig'))))
            if len(header) != len(set(header)):
                raise ValueError('duplicate column names')
            df = pd.read_csv(io.BytesIO(content), dtype=str, keep_default_na=False)
            required = {col for col, _ in fields(name)}
            missing = required - set(df.columns)
            if missing:
                raise ValueError('missing columns: ' + ', '.join(sorted(missing)))
            for col, kind in fields(name):
                raw = df[col].str.strip()
                optional = kind.endswith('?')
                base = kind.rstrip('?')
                if not optional and raw.eq('').any():
                    raise ValueError(f'{col} has blank values')
                if base in ['float', 'int']:
                    values = pd.to_numeric(raw.replace('', np.nan), errors='coerce')
                    invalid = (raw.ne('') & values.isna()) | (values.notna() & ~np.isfinite(values))
                    if invalid.any() or (values.dropna() < 0).any():
                        raise ValueError(f'{col} requires finite, nonnegative numbers')
                    if base == 'int' and (values.dropna() % 1 != 0).any():
                        raise ValueError(f'{col} requires whole numbers')
                    df[col] = values.astype(int) if base == 'int' else values.astype(float)
                elif base == 'date':
                    values = pd.to_datetime(raw.replace('', None), format='mixed', errors='coerce', utc=True).dt.tz_localize(None)
                    if (raw.ne('') & values.isna()).any():
                        raise ValueError(f'{col} contains invalid dates')
                    df[col] = values
                elif base == 'bool':
                    values = raw.str.lower().map({'true': True, 'false': False})
                    if values.isna().any():
                        raise ValueError(f'{col} requires true or false')
                    df[col] = values.astype(bool)
                else:
                    df[col] = raw
            grouped[name].append(df)
        except (ValueError, UnicodeError, StopIteration, pd.errors.ParserError) as exc:
            errors.append(f'{filename}: {exc}')
    missing_files = [name + '.csv' for name, frames in grouped.items() if not frames]
    if missing_files:
        errors.append('Missing input files: ' + ', '.join(missing_files))
    if errors:
        raise DataError('\n'.join(errors))
    data = {name: pd.concat(frames, ignore_index=True) for name, frames in grouped.items()}
    validate(data)
    return data


def load_folder(folder):
    return read_files([(p.name, p.read_bytes()) for p in sorted(Path(folder).glob('*.csv'))])


def validate(d):
    errors = []

    def check(condition, message):
        if bool(condition):
            errors.append(message)

    def ref(table, col, target, key=None, blank=False):
        s = d[table][col]
        bad = ~s.isin(d[target][key or col])
        if blank:
            bad &= s.ne('')
        check(bad.any(), f'{table}.{col}: unknown {target} reference.')

    for name, df in d.items():
        check(df.duplicated(KEYS[name]).any(), f'{name}: duplicate key ({", ".join(KEYS[name])}).')
    for name in ['periods', 'customers', 'staff', 'topics', 'releases']:
        check(d[name].empty, f'{name}: at least one row is required.')
    check(d['customers'].customer_name.duplicated().any(), 'customers: display names must be unique for customer selection.')
    check((~d['staff'].role.isin(['Support', 'Engineering', 'Services'])).any(), 'staff: role must be Support, Engineering or Services.')
    check((d['topics'].approved_answer & d['topics'].knowledge_article.str.lower().isin(['not available', 'none', 'n/a'])).any(), 'topics: approved answers require an article reference.')
    check((~d['periods'].complete).any(), 'periods: only complete calendar years are supported. Do not compare partial years with full years.')
    check((~d['periods'].year.between(2000, 2100)).any(), 'periods: year must be between 2000 and 2100.')
    for name in ['customer_years', 'license_revenue', 'support_revenue', 'projects', 'support_cases', 'defect_customers']:
        ref(name, 'customer_id', 'customers')
    for name in ['defects', 'support_cases']:
        ref(name, 'topic_id', 'topics')
        check((~d[name].severity.isin(SEVERITIES)).any(), f'{name}: invalid severity.')
        check((d[name].resolved_at < d[name].created_at).any(), f'{name}: resolution precedes creation.')
    ref('defects', 'detected_release', 'releases', 'release_id')
    ref('defect_customers', 'defect_id', 'defects')
    ref('support_cases', 'defect_id', 'defects', blank=True)
    ref('support_cases', 'analyst_id', 'staff', 'staff_id')
    ref('services_revenue', 'project_id', 'projects')
    ref('worklogs', 'staff_id', 'staff')
    for col, table in [('case_id', 'support_cases'), ('defect_id', 'defects'), ('project_id', 'projects')]:
        ref('worklogs', col, table, blank=True)
    check((~d['worklogs'].activity.isin(['Support', 'Engineering', 'Services'])).any(), 'worklogs: activity must be Support, Engineering or Services.')
    check((~d['defects'].origin.isin(['Internal', 'Customer'])).any(), 'defects: origin must be Internal or Customer.')
    check((~d['support_cases'].case_type.isin(CASE_TYPES)).any(), 'support_cases: invalid case_type.')
    check((~d['projects'].billing_model.isin(['Fixed price', 'Time and materials'])).any(), 'projects: invalid billing_model.')
    check((d['worklogs'].minutes <= 0).any(), 'worklogs: minutes must be positive.')
    check((d['support_cases'].response_sla_hours <= 0).any(), 'support_cases: SLA hours must be positive.')
    check((d['customer_years'].active_users > d['customer_years'].licensed_users).any(), 'customer_years: active_users exceeds licensed_users.')
    cases = d['support_cases']
    check((cases.first_response_at < cases.created_at).any(), 'support_cases: response precedes creation.')
    check((cases.first_response_at > cases.resolved_at).any(), 'support_cases: response follows resolution.')
    check((cases.resolved_at.notna() & cases.first_response_at.isna()).any(), 'support_cases: resolved cases require first_response_at.')
    check((cases.csat_score.notna() & (~cases.csat_score.between(1, 5) | (cases.csat_score % 1 != 0))).any(), 'support_cases: CSAT must be a whole number from 1 to 5, or blank.')
    check((cases.csat_score.notna() != cases.survey_at.notna()).any(), 'support_cases: CSAT and survey date must both be present or both blank.')
    check((cases.survey_at.notna() & (cases.resolved_at.isna() | (cases.survey_at < cases.resolved_at))).any(), 'support_cases: survey requires a preceding resolution.')
    check(((cases.case_type == 'Code defect') & cases.defect_id.eq('')).any(), 'support_cases: Code defect cases require defect_id.')
    years = set(d['periods'].year)
    check((~d['customer_years'].year.isin(years)).any(), 'customer_years: year is not declared in periods.')
    for name, col in [('license_revenue', 'revenue_date'), ('support_revenue', 'revenue_date'), ('services_revenue', 'revenue_date'), ('worklogs', 'work_date'), ('operating_expenses', 'expense_date')]:
        check((~d[name][col].dt.year.isin(years)).any(), f'{name}: transaction year is not declared in periods.')
    if years:
        cutoff = pd.Timestamp(max(years), 12, 31, 23, 59, 59)
        for name, df in d.items():
            for col, kind in fields(name):
                if kind.startswith('date'):
                    check((df[col] > cutoff).any(), f'{name}.{col}: date is after the reporting cutoff.')
    if errors:
        raise DataError('\n'.join(errors))
    # Dependent checks run only after keys and references are known to be valid.
    for activity, target, table in [('Support', 'case_id', 'support_cases'), ('Engineering', 'defect_id', 'defects'), ('Services', 'project_id', 'projects')]:
        logs = d['worklogs'].loc[d['worklogs'].activity.eq(activity)]
        check(logs[target].eq('').any(), f'worklogs: {activity} requires {target}.')
        for other in {'case_id', 'defect_id', 'project_id'} - {target}:
            check(logs[other].ne('').any(), f'worklogs: {activity} must leave {other} blank to avoid ambiguous cost allocation.')
        if table != 'projects':
            merged = logs.merge(d[table][[target, 'created_at', 'resolved_at']], on=target)
            check(((merged.work_date < merged.created_at) | (merged.work_date > merged.resolved_at)).any(), f'worklogs: {activity} time is outside the case/defect lifetime.')
    links = d['defect_customers'].merge(d['defects'][['defect_id', 'created_at']], on='defect_id')
    check((links.associated_at < links.created_at).any(), 'defect_customers: association precedes defect creation.')
    linked = cases[cases.defect_id.ne('')].merge(d['defect_customers'], on=['defect_id', 'customer_id'], how='left')
    check(linked.associated_at.isna().any(), 'support_cases: linked defect must have a matching customer association.')
    release_dates = d['defects'].merge(d['releases'], left_on='detected_release', right_on='release_id')
    check((release_dates.created_at < release_dates.release_date).any(), 'defects: created before detected release was available.')
    snapshots = set(zip(d['customer_years'].customer_id, d['customer_years'].year))
    for name in ['license_revenue', 'support_revenue']:
        missing = set(zip(d[name].customer_id, d[name].revenue_date.dt.year)) - snapshots
        check(bool(missing), f'{name}: customer/year snapshots missing for {len(missing)} account-years.')
    if errors:
        raise DataError('\n'.join(errors))
