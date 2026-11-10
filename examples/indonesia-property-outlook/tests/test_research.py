import json
from datetime import datetime, timezone, timedelta
import pytest
from property_research.sources import parse_worldbank, parse_yahoo, parse_news, safe_url, envelope
from property_research.evidence import validate_csv, COLUMNS, coverage, excel_safe_csv, report_markdown
from property_research.framework import income_scenario, development_scenario


def csvrow(**overrides):
    row = dict(metric='occupancy', value='88', unit='%', observation_date=datetime.now(timezone.utc).date().isoformat(),segment='Office',location='Jakarta',source_url='https://example.com/report',source_name='Issuer')
    row.update(overrides)
    return ','.join(COLUMNS)+'\n'+','.join(row[c] for c in COLUMNS)+'\n'


def test_worldbank_filters_null_and_sorts():
    assert parse_worldbank(json.dumps([{},[{'date':'2024','value':5.0},{'date':'2025','value':None},{'date':'2023','value':4.9}]])) == [{'year':2023,'value':4.9},{'year':2024,'value':5.0}]


def test_prices_reject_wrong_currency_and_null():
    payload = {'chart':{'result':[{'meta':{'currency':'IDR'},'timestamp':[100,200], 'indicators':{'quote':[{'close':[None,100]}]}}]}}
    assert len(parse_yahoo(json.dumps(payload))) == 1
    payload['chart']['result'][0]['meta']['currency'] = 'USD'
    with pytest.raises(ValueError):
        parse_yahoo(json.dumps(payload))


def test_news_excludes_future_old_duplicate_and_unsafe():
    from email.utils import format_datetime
    now = datetime.now(timezone.utc)
    def item(title, link, date):
        return f'<item><title>{title}</title><link>{link}</link><pubDate>{format_datetime(date)}</pubDate><source>News</source></item>'
    raw='<rss><channel>'+item('Current','https://news.example/a',now)+item('Current','https://news.example/b',now)+item('Future','https://news.example/c',now+timedelta(days=5))+item('Old','https://news.example/d',now-timedelta(days=40))+item('Bad','javascript:alert(1)',now)+'</channel></rss>'
    assert [r['title'] for r in parse_news(raw)] == ['Current']


@pytest.mark.parametrize('overrides',[{'value':'nan'},{'value':'inf'},{'value':'101'},{'unit':'fraction'},{'observation_date':'2099-01-01'},{'source_url':'javascript:alert(1)'},{'source_url':'https://user:pass@example.com'},{'metric':'no-such-metric'}])
def test_upload_rejects_invalid_observations(overrides):
    with pytest.raises(ValueError):
        validate_csv(csvrow(**overrides))


def test_coverage_is_local_and_unverified():
    records=validate_csv(csvrow())
    assert records[0]['evidence_type'].startswith('User-supplied')
    assert 'occupancy' not in coverage(records,'Office','Jakarta')[1]
    assert 'occupancy' in coverage(records,'Office','Indonesia')[1]
    assert 'occupancy' in coverage(records,'Office','Surabaya')[1]
    assert 'occupancy' in coverage(validate_csv(csvrow(observation_date='2020-01-01')),'Office','Jakarta')[1]


def test_income_scenario_matches_cash_economics():
    base=income_scenario(100,500,8,8)
    stress=income_scenario(100,500,8,8,-10,100,50,100)
    assert base['gross_value'] == pytest.approx(1250)
    assert stress['gross_value'] == pytest.approx(1000)
    assert stress['interest'] == pytest.approx(42.5)
    assert stress['equity_value'] == pytest.approx(500)
    assert income_scenario(100,0,8,8)['interest_coverage'] is None


def test_development_finance_delay():
    assert development_scenario(1500,1000,500,9,3)['profit'] == pytest.approx(365)
    stress=development_scenario(1500,1000,500,9,3,-10,10,12)
    assert stress['finance'] == pytest.approx(180)
    assert stress['profit'] == pytest.approx(70)


def test_csv_export_neutralizes_formula_cells():
    assert "'=IMPORTXML" in excel_safe_csv([{'name':'=IMPORTXML(a)','number':-10}])
    assert not safe_url('javascript:alert(1)')


def test_failed_sources_report_is_complete():
    fail={'status':'unavailable','data':[],'provider':'test','url':'https://example.com','retrieved_at':'2026-01-01','error':'TimeoutError'}
    bundle={'generated_at':'2026-01-01','macro':[],'news':fail,'prices':fail}
    text=report_markdown(bundle,[],'Residential','Indonesia')
    assert 'unverified' in text
    assert 'Live macro observations unavailable' in text
    assert 'No local observations supplied' in text


def test_non_padded_dates_normalize_before_recency_check():
    records=validate_csv(csvrow(observation_date='2020-2-1'))
    assert records[0]['observation_date'] == '2020-02-01'
    assert 'occupancy' in coverage(records,'Office','Jakarta')[1]


@pytest.mark.parametrize('value',[float('nan'),float('inf')])
def test_nonfinite_scenario_inputs_rejected(value):
    with pytest.raises(ValueError):
        income_scenario(value,500,8,8)
    with pytest.raises(ValueError):
        development_scenario(1500,value,500,9,3)
