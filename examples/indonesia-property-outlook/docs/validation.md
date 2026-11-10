# Validation — 10 November 2026

- 19 pytest cases passed with Python 3.12, Streamlit 1.67.0 and pandas 3.1.1.
- Streamlit AppTest rendered five tabs and both scenario modes without exceptions.
- Headless Chromium at 1440px and 390px: five tabs exercised, both scenario modes exercised, no JavaScript exceptions, no page-level mobile horizontal overflow.
- Independently tested World Bank GDP/inflation/urban-share endpoints, Yahoo BSDE/CTRA chart and Google News Indonesian RSS; all worked in source probes. Later World Bank requests intermittently failed; app kept prices/news and exports working and labelled missing feeds explicitly. Successful access is run-specific.
- BI SHPR landing page returned HTTP 503. Official property figures are not presented as an automatically connected feed.
- Independent reviewer checked source suitability, PDF business-model mapping, local scope, CSV handling, formulas, exports, price timing and app rendering.
- Review corrections: canonicalize dates before recency/duplicate checks; label provisional Yahoo bars and bar timestamps accurately; reject nonfinite scenario inputs; use WIB dates for date-only user observations; replace deprecated Streamlit width arguments.
- Income-property stress case independently reconciled: NOI 90; gross value 1,000; debt 500; equity residual 500; interest 42.5; coverage 2.117647x, IDR billions except ratio.
- Development stress case independently reconciled: sales 1,350; cost 1,100; financing 180; profit 70; margin 5.185185%, IDR billions except margin.

Limits: this is software/prototype validation, not independent acceptance of a completed long-form investment report. No claim of fully automated primary-document verification, current property forecast, continuous streaming data or public hosting deployment.
