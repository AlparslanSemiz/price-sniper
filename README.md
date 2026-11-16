<h1 align="center">PriceSniper</h1>
<p align="center">Tracks electronics prices on Geizhals.de and Kleinanzeigen.de and warns you when a price leaves the range you set.</p>

<p align="center">
<img src="https://img.shields.io/badge/Python-3-555?style=flat" alt="Python 3">
<img src="https://img.shields.io/badge/Playwright-scraping-555?style=flat" alt="Playwright">
<img src="https://img.shields.io/badge/SQLite-history-555?style=flat" alt="SQLite">
<img src="https://img.shields.io/badge/status-early-555?style=flat" alt="early stage">
</p>

<p align="center"><b><a href="#install">Install</a></b> · <a href="#run">Run</a> · <a href="#configuration">Configure</a></p>

## Why

Good prices on graphics cards and CPUs come and go within hours, on the new-goods price comparison and on the second-hand market alike. PriceSniper checks both for the products in a JSON file, stores every price in SQLite and tells you when one falls below or rises above your limits.

## Features

- Two providers: Geizhals.de (new) and Kleinanzeigen.de (new and used).
- Many products at once, configured in `config.json` (8 sample products included).
- Alert thresholds per product (`price_alert_min`, `price_alert_max`).
- Single run or scheduled runs with APScheduler (default every 60 minutes).
- Notifications to the console and to `alerts.log`. Notifiers are small classes, so new channels are easy to add.
- Price history in SQLite.

## Install

```bash
pip install -r requirements_new.txt
playwright install chromium
```

Run both commands from the repository root.

## Run

```bash
python main_orchestrator.py            # check every product once and exit
python main_scheduler.py --scheduled   # check on an interval
```

Alerts are logged as warnings (to the console) by both `main_orchestrator.py` and `main_scheduler.py`. The browser window opens visibly while scraping (`headless=False` in the providers).

## Configuration

`config.json`:

```json
{
  "products": [
    {
      "id": 1,
      "name": "NVIDIA RTX 4070",
      "search_query": "RTX 4070",
      "price_alert_min": 450,
      "price_alert_max": 650,
      "active": true
    }
  ],
  "settings": {
    "check_interval_minutes": 60,
    "enable_notifications": true,
    "notification_channels": ["console", "file"]
  }
}
```

Prices are in euros. The alert fires below `price_alert_min` or above `price_alert_max`.

<details>
<summary>Project layout and database</summary>

```
main_orchestrator.py        single run
main_scheduler.py           scheduled run and alerts
config.json                 products and settings
data/pricesniper.db         SQLite database
priceSniper/src/
  database/models.py        SQLAlchemy models
  providers/                geizhals.py, kleinanzeigen.py
  notifiers/                base.py, console_notifier.py, file_notifier.py
  brain/                    placeholder for an LLM step (empty)
```

Tables: `products` (id, name, search_query) and `price_history` (id, product_id, source, price in EUR, url, timestamp).

Adding a provider: put a new class with `async get_price(product_name)` in `priceSniper/src/providers/`. Adding a notifier: subclass `BaseNotifier` in `priceSniper/src/notifiers/` and implement `notify(message)`.

</details>

## Troubleshooting

- Playwright errors: run `playwright install chromium` again.
- No price found: check the product's `search_query` in `config.json` and open the site by hand to see whether its page layout changed.
- Both scripts log to the console; only `main_scheduler.py` also writes `pricesniper.log`.

## Status

An early prototype from May 2026. The scrapers depend on the sites' current page layout and can break when it changes. Alert messages are in Turkish. Respect the terms of the sites you scrape and keep the interval modest.

## Tech

Python, Playwright, BeautifulSoup, SQLAlchemy, APScheduler.

## License

MIT
