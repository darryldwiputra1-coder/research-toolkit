from datetime import datetime, timezone, timedelta
from io import StringIO
from zoneinfo import ZoneInfo
import csv
import math
import pandas as pd
from .framework import SEGMENTS, METRICS
from .sources import safe_url

COLUMNS = ['metric', 'value', 'unit', 'observation_date', 'segment', 'location', 'source_url', 'source_name']
LOCATIONS = ['Indonesia', 'Jabodetabek', 'Jakarta', 'Surabaya', 'Bali', 'Cikarang–Bekasi–Karawang']


def validate_csv(text):
    if len(text.encode('utf-8')) > 1_000_000:
        raise ValueError('CSV must be smaller than 1 MB')
    df = pd.read_csv(StringIO(text), dtype=str, keep_default_na=False)
    missing = set(COLUMNS) - set(df.columns)
    if missing:
        raise ValueError('Missing columns: ' + ', '.join(sorted(missing)))
    if len(df) > 5000:
        raise ValueError('Limit uploads to 5,000 observations')
    records = []
    for n, r in enumerate(df[COLUMNS].to_dict('records'), 2):
        r = {k: v.strip() for k, v in r.items()}
        if r['metric'] not in METRICS:
            raise ValueError(f'Row {n}: unknown metric')
        _, unit, minimum, maximum = METRICS[r['metric']]
        try:
            value = float(r['value'])
        except ValueError:
            raise ValueError(f'Row {n}: value must be numeric') from None
        if not math.isfinite(value) or value < minimum or (maximum is not None and value > maximum):
            raise ValueError(f'Row {n}: value outside permitted range')
        if r['unit'] != unit:
            raise ValueError(f'Row {n}: expected unit {unit}')
        try:
            observed = datetime.strptime(r['observation_date'], '%Y-%m-%d').replace(tzinfo=timezone.utc)
        except ValueError:
            raise ValueError(f'Row {n}: use YYYY-MM-DD dates') from None
        if observed.date() > datetime.now(ZoneInfo('Asia/Jakarta')).date():
            raise ValueError(f'Row {n}: future observations are not accepted')
        if r['segment'] not in SEGMENTS or r['location'] not in LOCATIONS:
            raise ValueError(f'Row {n}: choose a supported segment and location')
        if not safe_url(r['source_url']) or not r['source_name'] or len(r['source_name']) > 150:
            raise ValueError(f'Row {n}: provide an HTTP(S) source URL and source name (max 150 characters)')
        records.append({**r, 'observation_date': observed.date().isoformat(), 'value': value, 'evidence_type': 'User-supplied · not independently verified'})
    keys = [(r['metric'], r['observation_date'], r['segment'], r['location']) for r in records]
    if len(set(keys)) != len(keys):
        raise ValueError('Duplicate metric/date/segment/location rows: reconcile conflicting observations first')
    return records


def coverage(records, segment, location):
    selected = [r for r in records if r['segment'] == segment and r['location'] == location]
    recent_cutoff = (datetime.now(ZoneInfo('Asia/Jakarta')) - timedelta(days=180)).date().isoformat()
    required = SEGMENTS[segment]['metrics']
    recent = {r['metric'] for r in selected if r['observation_date'] >= recent_cutoff}
    return selected, [m for m in required if m not in recent]


def stale_price(rows):
    if not rows:
        return True
    date = datetime.fromisoformat(rows[-1]['date'])
    return datetime.now(timezone.utc) - date > timedelta(days=7)


def excel_safe_csv(rows):
    if not rows:
        return ''
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=list(rows[0]))
    writer.writeheader()
    for row in rows:
        writer.writerow({k: "'" + v if isinstance(v, str) and v.lstrip().startswith(('=', '+', '-', '@')) else v for k, v in row.items()})
    return output.getvalue()


def snapshot(bundle, records, segment, location):
    selected, missing = coverage(records, segment, location)
    return {'schema_version': 1, 'segment': segment, 'location': location,
            'bundle': bundle, 'user_observations': selected, 'missing_recent_metrics': missing,
            'research_status': 'Monitoring brief; independent research review pending',
            'news_policy': 'Headlines are discovery only; no article-body verification',
            'framework': SEGMENTS[segment]}


def market_context(bundle):
    observations = []
    for source in bundle['macro']:
        if source['status'] == 'ok':
            latest = source['data'][-1]
            observations.append(f"{source['label']}: {latest['value']:.2f} {source['unit']} ({latest['year']}; annual, World Bank WDI).")
    return observations


def report_markdown(bundle, records, segment, location):
    selected, missing = coverage(records, segment, location)
    lens = SEGMENTS[segment]
    lines = [f'# Indonesia property outlook — {segment}', f'Focus: {location}',
             f"Generated: {bundle['generated_at']} (UTC; retrieval time, not the observation period)",
             '', '## View and evidence limits',
             'Selective diligence is appropriate; the connected feeds do not establish a verified current property-cycle direction. '
             'Current property-cycle direction is unverified. Annual macro observations describe the background. Equity prices reflect listed-company expectations and news headlines identify questions for verification. '
             'A stronger segment view requires local sales/leasing, supply and financing evidence for comparable periods.',
             'This is a reproducible monitoring brief, not an independently accepted Research Toolkit investment report.',
             '', '## Observed macro context']
    lines.extend(market_context(bundle) or ['Live macro observations unavailable.'])
    lines += ['', '## Conditional segment outlook', lens['mechanism'], lens['focus'],
              '', '**What would strengthen the outlook:** improving sales or leasing with stable effective pricing, cash conversion and manageable debt, supported by comparable local observations.',
              '**What would weaken it:** rising unsold inventory or vacancy, falling effective rents/collections and refinancing pressure.',
              f"**Segment risk:** {lens['risk']}", f"**Next verification:** {lens['test']}",
              '', '## Local fundamentals']
    if selected:
        for r in sorted(selected, key=lambda r: (r['metric'], r['observation_date'])):
            lines.append(f"- {METRICS[r['metric']][0]}: {r['value']:g} {r['unit']} on {r['observation_date']}; user-supplied, unverified; {r['source_name']}: {r['source_url']}")
    else:
        lines.append('No local observations supplied for this exact location and segment.')
    lines.append('Missing observations within 180 days: ' + (', '.join(METRICS[m][0] for m in missing) or 'None of the checklist metrics; comparability and source verification still required.'))
    price = bundle['prices']
    lines += ['', '## Listed-market context']
    if price['status'] == 'ok':
        rows = price['data']
        change = (rows[-1]['close'] / rows[0]['close'] - 1) * 100
        lines += [f"{price['ticker']}: latest daily-bar price {rows[-1]['close']:,.0f} IDR; bar timestamp {rows[-1]['date']} (bar start; current-session price may be provisional). "
                  f"Price change across returned observations: {change:+.1f}%; unadjusted, excludes dividends. "
                  f"{'Stale feed (>7 days).' if stale_price(rows) else 'Daily feed; may be delayed.'}",
                  'The selected issuer may have a different geography or business mix from this segment. It is context, not a segment benchmark.']
    else:
        lines.append('Selected equity feed unavailable.')
    lines += ['', '## News discovery — headlines only']
    for r in bundle['news']['data'][:10]:
        lines.append(f"- {r['published_at']} — {r['title']} ({r['publisher']}). Unverified headline; {r['url']}")
    if not bundle['news']['data']:
        lines.append('No recent headlines returned; this does not establish the absence of market events.')
    lines += ['', '## Source register']
    for source in bundle['macro'] + [bundle['prices'], bundle['news']]:
        lines.append(f"- {source['provider']}; {source['status']}; retrieved {source['retrieved_at']}; {source['url']}")
    lines += ['', '## Analytical basis', lens['pdf'],
              'Alan Lok, Eunice Chu and Guruprasad Jambunathan, CFA Institute Sector Analysis frameworks (2018). '
              'The PDFs supply questions and mechanisms, not current Indonesian data. REIT operating concepts are applied to income properties; '
              'this does not assume Indonesian DIRE has identical legal or distribution rules.',
              '', '## Research workflow', 'Question → dated evidence → claim classification → mechanism and counter-case → verification → review → publish. '
              'Automatic refresh updates the monitoring data only. Source verification, seven independent content perspectives, domain review, audit and final acceptance '
              'remain required for a complete Research Toolkit long-form research release.']
    return '\n\n'.join(lines)
