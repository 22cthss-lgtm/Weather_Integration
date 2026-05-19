# Weather Integration Website

This project provides a simple weather-data integration site with:

- `backend/`: Flask API, SQLite, manual image ingestion services
- `frontend/`: React dashboard for testing image and FAQ APIs

## Backend Features

- Manual image ingestion with independent services for:
  - CWA satellite / radar / weather chart / rainfall
  - AQI
  - KMA 850hPa
  - SST / OHC
  - NCDR wind
  - SSEC wind shear
  - Meteologix rainfall
  - Reservoir map
- Image APIs:
  - `GET /api/images/latest?type=xxx`
  - `GET /api/images/history?type=xxx`
## Project Structure

```text
Weather_
|-- backend
|   |-- app.py
|   |-- requirements.txt
|   `-- src
|-- frontend
|   |-- package.json
|   `-- src
`-- README.md
```

## Start Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Backend default URL: `http://127.0.0.1:5000`

## Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend default URL: `http://127.0.0.1:5173`

If needed, configure API base URL:

```bash
set VITE_API_BASE_URL=http://127.0.0.1:5000
```

## Notes

- `satellite` now uses the official CWA latest satellite image URL:
  `https://www.cwa.gov.tw/Data/satellite/LCC_IR1_MB_2750/LCC_IR1_MB_2750.jpg`
- `/api/images/latest?type=satellite` refreshes satellite data immediately before returning.
- Other image types are still initialized with placeholder data on startup.
- The frontend is intentionally minimal and focused on API verification.
