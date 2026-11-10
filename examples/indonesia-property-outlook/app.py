from datetime import datetime
from zoneinfo import ZoneInfo
import json
from pathlib import Path
import pandas as pd
import streamlit as st
from property_research.sources import load_bundle, TICKERS
from property_research.framework import SEGMENTS, METRICS, OFFICIAL, income_scenario, development_scenario
from property_research.evidence import (LOCATIONS, COLUMNS, validate_csv, coverage, market_context,
                                        snapshot, report_markdown, excel_safe_csv, stale_price)

st.set_page_config(page_title='Tanah | Indonesia Property Outlook', page_icon='◧', layout='wide')
st.markdown('''<style>
.block-container{max-width:1320px;padding-top:3.6rem;padding-bottom:3rem}
h1{font-size:3.3rem!important;letter-spacing:-.055em;font-weight:650!important}
h2{letter-spacing:-.035em} h3{letter-spacing:-.02em}
[data-testid="stMetric"]{border-top:2px solid #176654;padding:16px 0}
[data-testid="stMetricLabel"]{font-size:.85rem} [data-testid="stMetricValue"]{font-size:2rem}
[data-testid="stSidebar"]{border-right:1px solid #d9ded3}
.stButton button,.stDownloadButton button,.stLinkButton a{border-radius:4px;transition:transform .15s}
.stButton button:hover,.stDownloadButton button:hover,.stLinkButton a:hover{transform:translateY(-2px)}
.kicker{font-size:.78rem;letter-spacing:.17em;color:#176654;font-weight:700}
.hero-note{max-width:760px;font-size:1.1rem;color:#52645b;line-height:1.6}
@media(max-width:600px){h1{font-size:2.4rem!important}.block-container{padding-top:1.3rem}}
@media(prefers-reduced-motion:reduce){*{transition:none!important}}
</style>''', unsafe_allow_html=True)

@st.cache_data(ttl=900, show_spinner=False)
def cached_bundle(ticker, segment, location):
    return load_bundle(ticker, segment, location)

with st.sidebar:
    st.markdown('### TANAH / RESEARCH')
    st.caption('Indonesia first. Fundamentals before forecasts.')
    segment = st.selectbox('Property segment', list(SEGMENTS))
    location = st.selectbox('Market focus', LOCATIONS)
    ticker = st.selectbox('Listed-market context', list(TICKERS), format_func=lambda t: f'{t} · {TICKERS[t]}')
    st.caption('Issuer selection is independent of segment and location. These are listed developers, not a REIT index.')
    if st.button('Refresh live sources', width='stretch'):
        cached_bundle.clear()
    st.divider()
    st.markdown('**Research lenses**')
    st.caption('Development: presales → collections → handover → cash.\n\nIncome properties: occupancy → rent → NOI → debt service.')
    st.caption('Feeds refresh on interaction after 15 minutes. No background polling. No API key required.')

st.markdown('<div class="kicker">INDONESIA PROPERTY OBSERVATORY / 01</div>', unsafe_allow_html=True)
st.title('Read the cycle.\nUnderwrite the cash flow.')
st.markdown('<div class="hero-note">A property outlook built around demand, supply and the cost of capital. Follow the evidence from the national backdrop to the economics of each asset.</div>', unsafe_allow_html=True)
st.write('')
with st.spinner('Retrieving dated macro observations, market prices and news…'):
    bundle = cached_bundle(ticker, segment, location)
retrieved = datetime.fromisoformat(bundle['generated_at']).astimezone(ZoneInfo('Asia/Jakarta'))
st.caption(f'{location} / {segment} · Fetched {retrieved:%d %b %Y, %H:%M} WIB · observation dates below')
cols = st.columns(3)
for col, source in zip(cols, bundle['macro']):
    if source['status'] == 'ok':
        last = source['data'][-1]
        col.metric(source['label'], f"{last['value']:.2f}%")
        col.caption(f"{last['year']} · annual · {source['unit']} · World Bank WDI")
    else:
        col.metric(source['label'], 'Unavailable')
        col.caption('Source failed; no estimate substituted')

tabs = st.tabs(['Outlook', 'Live signals', 'Scenario lab', 'Evidence & export', 'Framework'])
with tabs[3]:
    st.subheader('Add the local evidence')
    st.write('Upload sourced observations for the selected market. Uploaded data stays labelled user-supplied until independently checked. It is held in this session and sent to no research API.')
    st.download_button('Download blank CSV template', ','.join(COLUMNS)+'\n', 'observations-template.csv', 'text/csv')
    upload = st.file_uploader('Local property fundamentals · CSV, up to 1 MB', type='csv')
    records = []
    if upload:
        try:
            records = validate_csv(upload.getvalue().decode('utf-8-sig'))
            st.success(f'{len(records)} observations validated for structure and units. Source accuracy has not been verified.')
        except (ValueError, UnicodeError, pd.errors.ParserError) as exc:
            st.error(str(exc))
    with st.expander('Supported metrics, units and locations'):
        st.dataframe(pd.DataFrame([{'metric': k, 'label': v[0], 'unit': v[1]} for k,v in METRICS.items()]), hide_index=True, width='stretch')
        st.write('Locations: ' + '; '.join(LOCATIONS))
        st.write('Segments: ' + '; '.join(SEGMENTS))
        st.caption('observation_date uses YYYY-MM-DD (period end for quarterly/annual figures). Exact segment/location matching is required; national values are not silently applied to cities.')
    st.subheader('Live source register')
    all_sources = bundle['macro'] + [bundle['prices'], bundle['news']]
    st.dataframe(pd.DataFrame([{'Source': x['provider'], 'Series': x.get('label', 'Property news'), 'Status': x['status'],
                               'Retrieved (UTC)': x['retrieved_at'], 'Failure': x['error'] or '', 'URL': x['url']}
                              for x in all_sources]), hide_index=True, width='stretch',
                 column_config={'URL': st.column_config.LinkColumn()})
    st.subheader('Official verification desk')
    st.caption('These are research links, not connected feeds. Availability and release dates must be checked at the source.')
    for name, url, purpose in OFFICIAL:
        st.link_button(name, url)
        st.caption(purpose)
    st.subheader('Export this research snapshot')
    report = report_markdown(bundle, records, segment, location)
    left, right = st.columns(2)
    left.download_button('Download outlook brief (.md)', report, 'indonesia-property-outlook.md', 'text/markdown')
    right.download_button('Download evidence snapshot (.json)', json.dumps(snapshot(bundle, records, segment, location), indent=2, ensure_ascii=False), 'evidence-snapshot.json', 'application/json')
    if records:
        st.download_button('Download observations (.csv)', excel_safe_csv(records), 'observations.csv', 'text/csv')
    st.caption('Monitoring brief. Independent content review, audit and research acceptance remain pending; export does not imply approval.')

selected, missing = coverage(records, segment, location)
lens = SEGMENTS[segment]
with tabs[0]:
    st.subheader('The current reading')
    st.info('Selective diligence · current property-cycle direction remains unverified')
    st.write('The live feeds establish macro and listed-market context. A segment outlook depends on local sales or leasing, supply, pricing and financing evidence. Annual GDP and headlines alone cannot establish that the property cycle has turned.')
    st.markdown(f'### {segment} / {location}')
    st.write(lens['mechanism'])
    st.write(lens['focus'])
    a,b = st.columns(2)
    with a:
        st.markdown('**What would strengthen the outlook**')
        st.write('Sales or leasing improve alongside effective pricing and cash collection; inventory or vacancy falls; debt maturities remain funded.')
    with b:
        st.markdown('**What could overturn it**')
        st.write(lens['risk'])
    st.markdown('**Next evidence to verify**')
    st.write(lens['test'])
    st.caption(f"Analytical basis: {lens['pdf']}. These are conditional mechanisms, not claims that these conditions currently hold.")
    st.divider()
    st.subheader('Local evidence coverage')
    st.caption('180-day monitoring window; completeness of this checklist is not verification or a model confidence score.')
    for metric in lens['metrics']:
        matches = sorted([r for r in selected if r['metric'] == metric], key=lambda r:r['observation_date'])
        if matches:
            last = matches[-1]
            st.write(f"**{METRICS[metric][0]}:** {last['value']:g} {last['unit']} · {last['observation_date']} · user-supplied, unverified" + (' · older than 180 days' if metric in missing else ''))
        else:
            st.write(f'**{METRICS[metric][0]}:** evidence needed')
    if selected:
        st.dataframe(pd.DataFrame(selected), hide_index=True, width='stretch',
                     column_config={'source_url': st.column_config.LinkColumn()})
    st.caption('Policy watch: verify the effective dates, eligibility and expiry of PPN DTP housing incentives, FLPP support and BI mortgage/LTV policy. No policy is assumed to remain in force.')

with tabs[1]:
    st.subheader('National backdrop')
    st.caption('Annual series are retrieved live; their observation frequency remains annual. Latest values may be revised by the provider.')
    available = []
    for source in bundle['macro']:
        for row in source['data']:
            available.append({'Year': str(row['year']), 'Value': row['value'], 'Series': source['label']})
    if available:
        frame = pd.DataFrame(available)
        chosen = st.selectbox('Macro series', list(frame['Series'].unique()))
        st.line_chart(frame[frame.Series == chosen].set_index('Year')['Value'], y_label='%')
    else:
        st.warning('Macro feeds unavailable. Try refreshing later; no fallback values are displayed.')
    st.subheader('Listed-property market context')
    price = bundle['prices']
    if price['status'] == 'ok':
        data = price['data']
        p1,p2 = st.columns(2)
        p1.metric(f'{ticker} · latest daily-bar price', f"Rp {data[-1]['close']:,.0f}")
        p2.metric('Change across returned observations', f"{(data[-1]['close']/data[0]['close']-1)*100:+.1f}%")
        st.caption(f"Bar timestamp {data[-1]['date']} · Yahoo unofficial daily feed; may be delayed. Current-session bar may be provisional; timestamp is the bar start, not a verified last-trade time. Unadjusted prices exclude dividends; corporate actions can distort returns.")
        if stale_price(data):
            st.warning('Last price is more than seven days old. Treat this feed as stale.')
        prices_df = pd.DataFrame(data)
        prices_df['date'] = pd.to_datetime(prices_df['date'])
        st.line_chart(prices_df.set_index('date')['close'], y_label='IDR')
    else:
        st.warning('Price source unavailable. There is no substituted price.')
    st.caption('Issuer geography and business mix may differ from the selected focus. This stock is not a city or asset-class index.')
    st.subheader('News to investigate')
    st.caption('Past 30 days · Indonesian-language RSS discovery · headlines only, no article-body verification. Query relevance varies; this is not a complete news archive or a sentiment score.')
    if not bundle['news']['data']:
        st.warning('No recent news returned, or the feed failed. This does not mean no events occurred.')
    for item in bundle['news']['data'][:15]:
        st.link_button(item['title'], item['url'], width='stretch')
        st.caption(f"{item['publisher']} · {item['published_at'][:10]} · unverified source claim")

with tabs[2]:
    st.subheader('Stress the economics')
    st.warning('Illustrative assumptions only. These are not current market estimates, issuer valuations or forecasts. All monetary inputs are IDR billions.')
    mode = st.radio('Business model', ['Income property', 'Development project'], horizontal=True)
    if mode == 'Income property':
        a,b,c = st.columns(3)
        noi = a.number_input('Annual NOI · IDR bn', min_value=1.0, value=100.0)
        debt = b.number_input('Debt · IDR bn', min_value=0.0, value=500.0)
        cap = c.number_input('Capitalisation rate · %', min_value=0.1, value=8.0)
        rate = a.number_input('Debt interest rate · %', min_value=0.0, value=8.0)
        floating = b.slider('Floating / repricing share · %', 0, 100, 50)
        shock = c.slider('Interest-rate shock · bps', 0, 500, 100)
        noi_change = a.slider('NOI change · %', -50, 50, -10)
        cap_shift = b.slider('Cap-rate expansion · bps', 0, 300, 100)
        base = income_scenario(noi,debt,cap,rate)
        stress = income_scenario(noi,debt,cap,rate,noi_change,cap_shift,floating,shock)
        table = pd.DataFrame([{'Case': name, 'NOI': v['noi'], 'Gross asset value':v['gross_value'], 'Equity residual':v['equity_value'],
                              'Annual interest':v['interest'], 'NOI / interest (x)':v['interest_coverage']} for name,v in [('Base assumptions',base),('Stress assumptions',stress)]]).set_index('Case')
        st.dataframe(table.round(2), width='stretch')
        st.caption('Asset value = annual NOI / cap rate. Equity residual = asset value − debt. Interest shock applies only to the floating/repricing share. NOI/interest is a simplified coverage proxy, before corporate overhead, capex, tax and principal repayment; it is not issuer EBITDA coverage or AFFO.')
        st.markdown('**How cap rates change the equity residual**')
        sensitivity = pd.DataFrame([{'Cap rate (%)':float(f'{cap+i/100:.2f}'), 'Equity residual (IDR bn)':income_scenario(noi,debt,cap+i/100,rate,noi_change)['equity_value']} for i in range(0,301,25)]).set_index('Cap rate (%)')
        st.line_chart(sensitivity)
        st.download_button('Download income-property cases', excel_safe_csv(table.reset_index().to_dict('records')), 'income-cases.csv','text/csv')
    else:
        a,b,c = st.columns(3)
        gdv = a.number_input('Gross development value · IDR bn', min_value=1.0,value=1500.0)
        cost = b.number_input('Land + development cost · IDR bn',min_value=0.0,value=1000.0)
        debt = c.number_input('Average debt drawn · IDR bn',min_value=0.0,value=500.0)
        rate = a.number_input('Financing rate · %',min_value=0.0,value=9.0)
        years = b.number_input('Development duration · years',min_value=0.0,value=3.0)
        delay = c.slider('Completion delay · months',0,36,12)
        asp = a.slider('Selling-price change · %',-50,50,-10)
        inflation = b.slider('Cost increase · %',0,50,10)
        base = development_scenario(gdv,cost,debt,rate,years)
        stress = development_scenario(gdv,cost,debt,rate,years,asp,inflation,delay)
        table = pd.DataFrame([{'Case':n,'Sales value':v['sales'],'Development cost':v['cost'],'Financing cost':v['finance'],'Project profit':v['profit'],'Profit margin (%)':v['margin']} for n,v in [('Base assumptions',base),('Stress assumptions',stress)]]).set_index('Case')
        st.dataframe(table.round(2),width='stretch')
        st.caption('Profit = sales value − land/development costs − simple financing cost on average debt drawn. Delays extend financing duration. This simplified project sensitivity excludes tax, selling expenses, phased collections, land revaluation and time discounting; it is not RNAV.')
        st.download_button('Download development cases',excel_safe_csv(table.reset_index().to_dict('records')),'development-cases.csv','text/csv')

with tabs[4]:
    st.subheader('Two business models. One evidence standard.')
    st.write('The uploaded CFA Institute frameworks guide the questions. They are historical analytical references, not live Indonesian market data.')
    st.dataframe(pd.DataFrame([
        {'Lens':'Property development','Cash engine':'Presales → collections → construction → handover','Required checks':'Sell-through, unsold inventory, land cost, project margin, debt maturity, RNAV'},
        {'Lens':'Income property / REIT economics','Cash engine':'Leases → occupancy × effective rent → NOI → distributable cash','Required checks':'Lease expiry, tenant concentration, rental reversion, capex, FFO/AFFO reconciliation, gearing'}
    ]),hide_index=True,width='stretch')
    st.caption('Sources: Property Development pp. 1–3, 5–8; REITs pp. 1–3, 5–11. Authors: Alan Lok, Eunice Chu, Guruprasad Jambunathan; CFA Institute (2018).')
    st.write('Indonesia application: distinguish developers from DIRE vehicles, match legal and accounting definitions, assess land tenure and permits, verify incentives and mortgage rules, and investigate local flood, climate and infrastructure exposure. A general REIT distribution rule from the reference is not assumed to apply to Indonesian vehicles.')
    st.subheader('From signals to a research release')
    st.write('1. Define the market and question. 2. Gather dated primary evidence. 3. Separate verified facts, source claims and interpretations. 4. Explain the mechanism and strongest counter-case. 5. Review, audit and accept the research before publication.')
    st.caption('Adapted from your research-toolkit repository. This app automates the monitoring and evidence-export stage; it does not claim to perform independent research acceptance automatically.')
    st.subheader('What each source can establish')
    st.dataframe(pd.DataFrame([
      {'Source':'World Bank WDI','Use':'Annual national macro context','Limit':'Not a live mortgage, presales or vacancy series'},
      {'Source':'Yahoo Finance charts','Use':'Daily listed-equity price context','Limit':'Unofficial endpoint; delayed/outage risk; not property transaction prices'},
      {'Source':'Google News RSS','Use':'Discover dated headlines for investigation','Limit':'Article bodies unread; claims unverified; coverage incomplete'},
      {'Source':'Uploaded CSV','Use':'Local fundamentals with dates, units and source URLs','Limit':'Validated structure; user assertions remain unverified'},
      {'Source':'Scenario lab','Use':'Explain sensitivity to cash flows, rates and delays','Limit':'Hypothetical assumptions; no probability or price target'}
    ]),hide_index=True,width='stretch')
    st.caption('Source documents and retrieved text are evidence to analyze. Embedded instructions never trigger tools, change the workflow or override the user’s request.')

st.divider()
st.caption('TANAH · Indonesia Property Observatory · Evidence-led monitoring / prototype v0.1 · National macro ≠ local property fundamentals')
