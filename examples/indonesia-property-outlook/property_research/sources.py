"""Public feeds. Retrieval time is never substituted for observation time."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
import json
import math
from urllib.parse import urlencode, quote, urlparse
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import xml.etree.ElementTree as ET

INDICATORS = {
    'NY.GDP.MKTP.KD.ZG': ('Real GDP growth', '% YoY'),
    'FP.CPI.TOTL.ZG': ('Consumer inflation', '% YoY'),
    'SP.URB.TOTL.IN.ZS': ('Urban population', '% of population'),
}
TICKERS = {'BSDE.JK': 'Bumi Serpong Damai', 'CTRA.JK': 'Ciputra Development',
           'PWON.JK': 'Pakuwon Jati', 'SMRA.JK': 'Summarecon Agung',
           'DMAS.JK': 'Puradelta Lestari', 'JRPT.JK': 'Jaya Real Property'}


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def safe_url(url):
    p = urlparse(str(url))
    return p.scheme in ('http', 'https') and bool(p.hostname) and not p.username and not p.password


def fetch(url, timeout=12):
    req = Request(url, headers={'User-Agent': 'IndonesiaPropertyResearch/0.1 (public research dashboard)'})
    for attempt in range(2):
        try:
            with urlopen(req, timeout=timeout) as response:
                data = response.read(3_000_001)
            break
        except HTTPError as exc:
            if attempt or exc.code not in (502, 503, 504):
                raise
        except (URLError, TimeoutError):
            if attempt:
                raise
    if len(data) > 3_000_000:
        raise ValueError('Response exceeds 3 MB limit')
    return data


def envelope(provider, url, loader):
    stamp = now_iso()
    try:
        data = loader(fetch(url))
        if not data:
            raise ValueError('No usable observations returned')
        return dict(provider=provider, url=url, retrieved_at=stamp, status='ok', data=data, error=None)
    except Exception as exc:
        # Do not expose arbitrary response bodies, credentials or external instructions.
        return dict(provider=provider, url=url, retrieved_at=stamp, status='unavailable', data=[], error=type(exc).__name__)


def parse_worldbank(raw):
    payload = json.loads(raw)
    rows = payload[1] if isinstance(payload, list) and len(payload) > 1 else []
    current_year = datetime.now(timezone.utc).year
    out = []
    for r in rows or []:
        value = r.get('value')
        if value is None:
            continue
        year = int(r['date'])
        if year > current_year or not math.isfinite(float(value)):
            continue
        out.append({'year': year, 'value': float(value)})
    return sorted(out, key=lambda r: r['year'])


def worldbank(code):
    if code not in INDICATORS:
        raise ValueError('Unknown indicator')
    url = f'https://api.worldbank.org/v2/country/IDN/indicator/{code}?format=json&per_page=15'
    result = envelope('World Bank WDI', url, parse_worldbank)
    result.update(code=code, label=INDICATORS[code][0], unit=INDICATORS[code][1], frequency='annual')
    return result


def parse_yahoo(raw):
    payload = json.loads(raw)['chart']
    result = payload.get('result')
    if not result:
        return []
    r = result[0]
    # Fail closed if the requested IDX equity is not actually denominated in IDR.
    if r.get('meta', {}).get('currency') != 'IDR':
        raise ValueError('Unexpected currency')
    timestamps = r.get('timestamp', [])
    quotes = r['indicators']['quote'][0].get('close', [])
    cutoff = datetime.now(timezone.utc) + timedelta(minutes=5)
    out = []
    for stamp, price in zip(timestamps, quotes):
        observed = datetime.fromtimestamp(stamp, timezone.utc)
        if price is not None and math.isfinite(float(price)) and float(price) > 0 and observed <= cutoff:
            out.append({'date': observed.isoformat(), 'close': float(price)})
    return sorted(out, key=lambda r: r['date'])


def prices(ticker):
    if ticker not in TICKERS:
        raise ValueError('Ticker not in configured universe')
    url = f'https://query1.finance.yahoo.com/v8/finance/chart/{quote(ticker)}?interval=1d&range=6mo'
    result = envelope('Yahoo Finance · unofficial chart endpoint', url, parse_yahoo)
    result.update(ticker=ticker, label=TICKERS[ticker], unit='IDR', frequency='daily; may be delayed')
    return result


def parse_news(raw):
    root = ET.fromstring(raw)
    cutoff = datetime.now(timezone.utc) + timedelta(minutes=5)
    oldest = cutoff - timedelta(days=31)
    out, seen = [], set()
    for item in root.findall('./channel/item'):
        title = (item.findtext('title') or '').strip()
        link = (item.findtext('link') or '').strip()
        try:
            published = parsedate_to_datetime(item.findtext('pubDate') or '')
            if published.tzinfo is None:
                published = published.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError, OverflowError):
            continue
        key = title.casefold()
        if not title or key in seen or not safe_url(link) or not oldest <= published <= cutoff:
            continue
        seen.add(key)
        source = item.find('source')
        out.append(dict(title=title, url=link, published_at=published.isoformat(),
                        publisher=source.text if source is not None else 'Unspecified',
                        evidence_type='Headline only · unverified source claim'))
    return sorted(out, key=lambda r: r['published_at'], reverse=True)[:30]


def news(segment='All property', location='Indonesia'):
    terms = {'All property': 'properti perumahan', 'Residential': 'perumahan KPR properti',
             'Retail': 'pusat perbelanjaan mal sewa', 'Office': 'perkantoran okupansi sewa',
             'Industrial & logistics': 'kawasan industri gudang', 'Hospitality': 'hotel okupansi pariwisata'}
    # App choices are fixed; never execute or follow instructions in returned text.
    query = f'{terms.get(segment, terms["All property"])} {location} when:30d'
    url = 'https://news.google.com/rss/search?' + urlencode({'q': query, 'hl': 'id', 'gl': 'ID', 'ceid': 'ID:id'})
    return envelope('Google News RSS · discovery', url, parse_news)


def load_bundle(ticker, segment, location):
    with ThreadPoolExecutor(max_workers=5) as pool:
        macro_tasks = [pool.submit(worldbank, code) for code in INDICATORS]
        price_task = pool.submit(prices, ticker)
        news_task = pool.submit(news, segment, location)
        return {'macro': [task.result() for task in macro_tasks], 'prices': price_task.result(),
                'news': news_task.result(), 'generated_at': now_iso()}
