# tools.py
# Purpose: Salary lookup using Adzuna API , with robust stats.
# - Collect salaries from Adzuna
# - Filter extreme outliers
# - Use median 
# - Return a structured payload; handle "no data" gracefully.

import os
import statistics
from typing import Dict, Optional, List

import requests
from dotenv import load_dotenv

load_dotenv()

ADZUNA_APP_ID: Optional[str] = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY: Optional[str] = os.getenv("ADZUNA_APP_KEY")


def _adzuna_salary(
    role: str,
    location: str,
    *,
    country: str = "au",
    results_per_page: int = 50,
    pages: int = 2,                 # fetch a bit more data to stabilize stats
    category: str = "it-jobs",      # keep results in IT
    max_days_old: int = 90,         # fresher ads
    server_salary_min: Optional[int] = None,  # e.g., 50000 if you want a server-side floor
    full_time: Optional[int] = None           # 1 for full-time only (if plan supports)
) -> Optional[Dict]:
    """
    Query Adzuna Jobs API and compute a robust salary statistic.
    - Gather salaries from multiple pages
    - Filter extreme outliers (e.g., <30k or >300k AUD)
    - Use median for robustness
    Returns None if no usable salaries or on HTTP/JSON errors.
    """
    if not (ADZUNA_APP_ID and ADZUNA_APP_KEY):
        return None

    base = f"https://api.adzuna.com/v1/api/jobs/{country}/search"
    raw_salaries: List[float] = []

    for page in range(1, pages + 1):
        params = {
            "app_id": ADZUNA_APP_ID,
            "app_key": ADZUNA_APP_KEY,
            "results_per_page": results_per_page,
            "what": role,
            "where": location,
            "category": category,
            "max_days_old": max_days_old,
            "content-type": "application/json",
        }
        if server_salary_min is not None:
            params["salary_min"] = server_salary_min
        if full_time is not None:
            params["full_time"] = full_time  # 1 or 0 (check Adzuna docs/plan)

        url = f"{base}/{page}"
        try:
            r = requests.get(url, params=params, timeout=15)
            r.raise_for_status()
            data = r.json()
        except Exception:
            return None

        for item in data.get("results", []):
            smin = item.get("salary_min")
            smax = item.get("salary_max")
            sval = item.get("salary")  # sometimes present as a single value
            try:
                if smin and smax:
                    raw_salaries.append((float(smin) + float(smax)) / 2.0)
                elif sval:
                    raw_salaries.append(float(sval))
            except Exception:
                # skip unparsable values
                pass

    # ---- client-side cleaning & robust statistic ----
    clean = [s for s in raw_salaries if 30000 <= s <= 300000]  # tune thresholds as needed
    if not clean:
        return None

    median_salary = statistics.median(clean)

    return {
        "role": role,
        "location": location,
        "average_salary_AUD": round(median_salary, 2),
        "n_samples": len(clean),  # number of samples after filtering
        "source": "Adzuna API (median, filtered)",
        "notes": {
            "pages_queried": pages,
            "results_per_page": results_per_page,
            "category": category,
            "max_days_old": max_days_old,
            "client_filters": "30k<=s<=300k, median",
        },
    }


def get_salary(
    role: str,
    location: str = "Australia",
    *,
    use_adzuna: bool = True,
    country: str = "au",
) -> Dict:
    """
    Public entrypoint used by the app/UI:
    - If enabled, call Adzuna and return a structured result
    - If no data available, return a clear 'no data' payload (no mock fallback)
    """
    if not use_adzuna:
        return {
            "role": role,
            "location": location,
            "average_salary_AUD": None,
            "source": "Disabled (use_adzuna=false)",
        }

    res = _adzuna_salary(
        role,
        location,
        country=country,
        results_per_page=50,
        pages=2,
        category="it-jobs",
        max_days_old=90,
        # server_salary_min=50000,  # uncomment if you want server-side floor
        # full_time=1,              # uncomment if your plan supports full-time filter
    )
    if res is not None:
        return res

    return {
        "role": role,
        "location": location,
        "average_salary_AUD": None,
        "n_samples": 0,
        "source": "Adzuna API (no data)",
        "message": "No salary data returned by the API for this query.",
    }


if __name__ == "__main__":
    # Simple CLI for quick terminal testing:
    #   python tools.py "software engineer" "Australia" au
    import sys
    role = sys.argv[1] if len(sys.argv) > 1 else "software engineer"
    where = sys.argv[2] if len(sys.argv) > 2 else "Australia"
    ctry = sys.argv[3] if len(sys.argv) > 3 else "au"
    print(get_salary(role, location=where, use_adzuna=True, country=ctry))
