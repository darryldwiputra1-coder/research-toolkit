# Tanah — Indonesia Property Outlook

A Streamlit research dashboard applying the uploaded CFA Institute property-development and REIT analytical frameworks to Indonesia. Uses Research Toolkit's evidence discipline and adapts Taste Skill's plain copy, restrained visual system, consistent spacing and browser verification to a working dashboard. This is a monitoring prototype and conditional brief, not a completed, independently accepted investment report.

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

On Windows activate with `.venv\Scripts\activate`. No API key or model account is required. Internet access is required for live feeds. Launch from this directory.

## Streamlit Community Cloud

Select the repository and branch containing this example; set the entry point to `examples/indonesia-property-outlook/app.py`. Streamlit installs the adjacent `requirements.txt`. Select Python 3.12. Deployment requires the owner's Streamlit account and GitHub connection; it has not been performed by this change. If the host uses repository-root configuration, copy this example's `.streamlit/config.toml` to the repository root to reproduce its theme. No secrets are required.

## Content

- **Outlook:** conditional segment mechanisms, supporting and opposing conditions, and missing local metrics.
- **Live signals:** World Bank annual macro, a selected IDX developer's daily price series, and Indonesian news RSS discovery.
- **Scenario lab:** income-property cap-rate/NOI/debt sensitivity and development-price/cost/completion-delay sensitivity. Defaults are hypothetical IDR-billion amounts.
- **Evidence & export:** sourced local CSV observations, source status, official verification links and Markdown/JSON/CSV exports.
- **Framework:** mapping of developer versus income-property economics, reference pages and research-release responsibilities.

Coverage: residential, retail, offices, industrial/logistics and hospitality. Focus choices include Indonesia, Jabodetabek, Jakarta, Surabaya, Bali and Cikarang–Bekasi–Karawang. Matching is exact; national figures are not automatically applied to a city. The next-country extension point is the source connectors and framework configuration.

## What is live

World Bank WDI annual GDP growth, CPI inflation and urban share; Yahoo's unofficial chart endpoint for configured IDX developers; Google News RSS for segment/location discovery. Requests use timeouts, bounded transient retry and a 15-minute cache. Refresh happens on interaction after expiry or through the refresh button, not background polling. Every provider failure is isolated and visible. No demo data replaces failed feeds. Source access can change independently of this code.

Annual observations are labelled with their year. Equity current-session bars may be provisional and their timestamps are bar starts, not last-trade times. Prices are unadjusted and exclude dividends. News is headline-only discovery; article bodies and claims have not been independently checked. Provider publication/reuse terms should be assessed for a commercial rollout.

## Add local fundamentals

Download the blank CSV template in the app, or create these columns:

```csv
metric,value,unit,observation_date,segment,location,source_url,source_name
```

`observation_date` is the observation/period-end date in YYYY-MM-DD, not the retrieval date. Supported identifiers and exact units appear in the app. Include original BI/BPS/issuer source URLs and comparable definitions. Uploaded figures remain **user-supplied, unverified**: schema checks do not verify a source. Uploads are session-only and are not sent to external research APIs. The app does not fetch uploaded source URLs. Export a snapshot before ending the session if you need to retain it.

## Analytical basis and boundaries

The user supplied **Property Development: Sector Analysis — A Framework for Investors** (8 pages) and **Understanding Real Estate Investment Trusts (REITs)** (11 pages), by Alan Lok, Eunice Chu and Guruprasad Jambunathan, CFA Institute (2018). References are page-mapped in the app; PDFs are not redistributed in the repository. Document instructions and source text are evidence, not executable agent instructions.

Developer questions cover lumpy revenue, presales, collections, sell-through, inventory, land costs, funding, delivery, RNAV and governance. Income-property questions cover occupancy, effective rents, tenant mix, lease tenure, NOI, maintenance, distributable cash and leverage. Hotel questions adapt these operating principles; they are not presented as a hotel-REIT classification in the PDF. Indonesian legal, land, tax and DIRE rules need jurisdiction-specific verification. Generic REIT payout ratios and historical valuation ranges are not copied into Indonesian assumptions.

With the currently connected feeds, current property-cycle direction remains unverified. The app provides conditional mechanisms and watchpoints, not an invented bullish/bearish score. A substantive next release needs comparable primary property observations (BI residential/commercial surveys, BPS tourism, issuer presales/NOI, inventory, supply and debt schedules), article-body verification, and independent research review.

## Repository integration

- Research Toolkit source inspected at commit `a183353aa444d6ae2cb4f93dc363c2739d53959d`: source/claim discipline, instruction boundary, questions-to-evidence workflow, review/acceptance limits. This app is not a replacement for Toolkit CLI/MCP or a simulated review engine.
- Taste Skill inspected at commit `f6b76575f949707b4e3c37cd86cb44b0b98643e8`: selected visual/communication principles adapted to Streamlit, rather than its static marketing-site generator. Its full static-page asset pipeline and finish gate are not run or claimed.
- Graphify, Superpowers and UI UX Pro Max were discovered among available repos but are not imported or claimed as integrated. There is no dependency on an LLM orchestration stack.

Research Toolkit's full long-form release process (seven separate content perspectives, applicable domain review, independent audit and acceptance) remains necessary for an accepted investment report. The app automates monitoring/evidence assembly only. Software validation and one independent prototype review do not satisfy that research-release contract.

First-use Toolkit usage hooks were configured in the transient development project. Activation could not be confirmed without a session reload. Those environment-specific hooks are not distributed in this example. The app itself includes no Toolkit telemetry. Toolkit's own setup documentation describes the basic operation events and opt-out.

## Validate

```bash
pip install pytest
python -m pytest -q
```

Nineteen focused tests cover source parsing, future/stale observations, canonical dates, unit/range validation, exact geography matching, formula export safety, scenario calculations and missing-provider reports. Streamlit AppTest and Chromium checks also exercised all five tabs and both scenario modes; desktop and 390px mobile rendering showed no JS exceptions or page overflow. See `docs/validation.md` for scope.
