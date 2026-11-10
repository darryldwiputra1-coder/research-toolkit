"""CFA sector framework translated into Indonesia-specific diligence questions."""
import math

SEGMENTS = {
 'Residential': {
  'mechanism': 'Household income and mortgage affordability drive take-up. Presales must convert into cash collections and completed handovers; recognised revenue can lag the cycle.',
  'test': 'Compare BI primary-market sales and prices with issuer presales, cancellations, mortgage rates and inventory for the same location and period.',
  'risk': 'Subsidy expiry, weak affordability, stalled collections and simultaneous new launches can leave inventory financed by short-term debt.',
  'metrics': ['property_sales_yoy', 'property_price_yoy', 'mortgage_rate', 'inventory_months'],
  'pdf': 'Property Development pp. 1–3, 5–7; REITs pp. 9–10',
  'focus': 'Jabodetabek township and affordable-housing demand must be assessed separately from city-centre apartments.'},
 'Retail': {
  'mechanism': 'Tenant sales and catchment spending support occupancy and rental reversions. Recurring rent matters only after property costs, maintenance and financing.',
  'test': 'Verify same-property occupancy, rent reversions, tenant sales, concentration and lease expiry rather than assuming a busy mall generates distributable cash.',
  'risk': 'Anchor-tenant weakness, incentives disguised as headline rent growth, e-commerce competition and refinancing costs.',
  'metrics': ['occupancy', 'rent_growth', 'noi_growth', 'interest_coverage'],
  'pdf': 'REITs pp. 1–3, 5–7',
  'focus': 'Compare each mall catchment and tenant mix; a national consumption series cannot establish Jakarta or Surabaya mall performance.'},
 'Office': {
  'mechanism': 'White-collar employment and absorption relative to completions determine vacancy and effective rent. Incentives can delay the translation from leases to cash flow.',
  'test': 'Separate Jakarta CBD from non-CBD and building grades; examine net absorption, pipeline, effective rents, lease expiries and tenant credit.',
  'risk': 'Excess supply, short leases, fit-out costs and tenant downsizing can overwhelm broad GDP growth.',
  'metrics': ['occupancy', 'rent_growth', 'noi_growth', 'interest_coverage'],
  'pdf': 'REITs pp. 2, 5–6, 8',
  'focus': 'Jakarta CBD observations do not establish national office conditions.'},
 'Industrial & logistics': {
  'mechanism': 'Manufacturing investment, trade and distribution demand support industrial land sales and warehouse leasing. Land-sale bookings and recurring warehouse income have different economics.',
  'test': 'Reconcile realised investment with signed land sales, cash collections, power and transport access, warehouse occupancy and tenant concentration.',
  'risk': 'Large one-off land deals, infrastructure delays, concentrated tenants and export-cycle weakness.',
  'metrics': ['property_sales_yoy', 'occupancy', 'rent_growth', 'interest_coverage'],
  'pdf': 'Property Development pp. 2, 5–7; REITs pp. 3, 8',
  'focus': 'Assess Cikarang–Bekasi–Karawang corridors by estate and infrastructure; do not extrapolate them to all of Indonesia.'},
 'Hospitality': {
  'mechanism': 'Visitor demand, room supply and room rates jointly determine RevPAR. Occupancy growth can coexist with weak profit if room rates or margins fall.',
  'test': 'Use BPS arrivals, local occupancy and room supply with issuer ADR, RevPAR and operating cash flow. Distinguish Bali leisure from Jakarta business travel.',
  'risk': 'New room supply, travel shocks, seasonality, operating leverage and foreign-currency debt.',
  'metrics': ['occupancy', 'revpar_growth', 'noi_growth', 'interest_coverage'],
  'pdf': 'Property Development pp. 2, 5; REITs pp. 1–2 (income-property framework adapted to hotels)',
  'focus': 'Bali tourism and Jakarta business hotel cycles require separate evidence.'},
}
METRICS = {
 'property_sales_yoy': ('Property sales growth', '% YoY', -100, None),
 'property_price_yoy': ('Property price growth', '% YoY', -100, None),
 'mortgage_rate': ('Mortgage rate', '% p.a.', 0, 100),
 'inventory_months': ('Unsold inventory', 'months', 0, None),
 'occupancy': ('Occupancy', '%', 0, 100),
 'rent_growth': ('Effective rent growth', '% YoY', -100, None),
 'noi_growth': ('NOI growth', '% YoY', -100, None),
 'interest_coverage': ('Interest coverage', 'x', 0, None),
 'revpar_growth': ('RevPAR growth', '% YoY', -100, None),
}
OFFICIAL = [
 ('Bank Indonesia · residential survey / SHPR', 'https://www.bi.go.id/en/publikasi/laporan/Pages/SHPR.aspx', 'Quarterly primary residential prices and sales; survey coverage differs from the total housing market.'),
 ('Bank Indonesia · monetary policy', 'https://www.bi.go.id/en/moneter/bi-7day-RR/Default.aspx', 'Policy rate; verify the latest decision and distinguish policy rates from mortgage rates.'),
 ('BPS Statistics Indonesia', 'https://www.bps.go.id/en', 'GDP, inflation, household spending, construction and tourism; observation frequency varies.'),
 ('OJK · financial-sector statistics', 'https://ojk.go.id/en/kanal/perbankan/data-dan-statistik/Pages/Statistik-Perbankan-Indonesia.aspx', 'Credit and banking conditions; verify definitions and reporting period.'),
 ('IDX · company financial reports', 'https://www.idx.co.id/en/listed-companies/financial-statements-and-annual-report', 'Issuer filings for presales, debt, recurring income and project delivery.'),
 ('Ministry of Investment / BKPM', 'https://www.bkpm.go.id/', 'Realised investment; announcements are not signed land sales or rental contracts.'),
]


def income_scenario(noi, debt, cap_rate, debt_rate, noi_change=0, cap_shift_bps=0, floating_share=100, rate_shock_bps=0):
    if not all(math.isfinite(v) for v in [noi, debt, cap_rate, debt_rate, noi_change, cap_shift_bps, floating_share, rate_shock_bps]):
        raise ValueError("Assumptions must be finite numbers")
    cap = (cap_rate + cap_shift_bps / 100) / 100
    if noi <= 0 or debt < 0 or cap <= 0 or debt_rate < 0 or not 0 <= floating_share <= 100 or noi_change < -100:
        raise ValueError('Invalid income-property assumptions')
    stressed_noi = noi * (1 + noi_change / 100)
    interest = debt * (debt_rate / 100 + floating_share / 100 * rate_shock_bps / 10000)
    if interest < 0:
        raise ValueError('Interest cannot be negative')
    gross = stressed_noi / cap
    return {'noi': stressed_noi, 'gross_value': gross, 'equity_value': gross - debt,
            'interest': interest, 'interest_coverage': stressed_noi / interest if interest > 0 else None}


def development_scenario(gdv, cost, debt, rate, years, price_change=0, cost_change=0, delay_months=0):
    if not all(math.isfinite(v) for v in [gdv, cost, debt, rate, years, price_change, cost_change, delay_months]):
        raise ValueError("Assumptions must be finite numbers")
    if min(gdv, cost, debt, rate, years, delay_months) < 0 or price_change < -100 or cost_change < -100:
        raise ValueError('Invalid development assumptions')
    sales = gdv * (1 + price_change / 100)
    build_cost = cost * (1 + cost_change / 100)
    finance = debt * rate / 100 * (years + delay_months / 12)
    profit = sales - build_cost - finance
    return {'sales': sales, 'cost': build_cost, 'finance': finance, 'profit': profit,
            'margin': profit / sales * 100 if sales else None}
