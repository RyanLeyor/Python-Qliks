import csv
import random
from datetime import datetime, timedelta
from pathlib import Path



# ------------ Här skapar vi påhittade/slumpade stopp som vi använder som data och sedan använda för Visualisering -----------



IN_FILE  = Path("data_raw/batcher.csv")
OUT_FILE = Path("data_raw/stopp.csv")

STOPP_TYPER = ["Väntar på påsar", "Urlastare", "Lådresare", "Sammanräkning"]

#-------
# Skapar funktioner för att räkna stoppens start och sluttider
#-------

def to_dt(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d %H:%M")

def fmt(ts: datetime) -> str:
    return ts.strftime("%Y-%m-%d %H:%M")

#--------
# Huvudprogramet, kontrollera att batcher.csv verkligen finns innan man kör vidare
#--------

def main():
    assert IN_FILE.exists(), f"Hittar inte {IN_FILE}"
    with IN_FILE.open(encoding="utf-8") as f:
        batcher = list(csv.DictReader(f))

    rows = []
    sid = 1
    random.seed(42)
# Generera stopp för varje batch
    for b in batcher:
        start = to_dt(b["starttid"])
        slut  = to_dt(b["sluttid"])
        total_min = int((slut - start).total_seconds() // 60)
        if total_min < 20:
            continue

        # 0–4 stopp per batch
        n_stopp = random.randint(0, 4)
        for _ in range(n_stopp):
            # starttid för stopp: tidigast +10 min, senast 10 min före batch-slut
            stopp_start_min = random.randint(10, max(11, total_min - 10))
            stopp_dur = random.randint(5, 45)  # stopp-längd (minuter)
            s_start = start + timedelta(minutes=stopp_start_min)
            s_slut  = min(slut, s_start + timedelta(minutes=stopp_dur))

            rows.append({
                "stopp_id": f"S{sid:05d}",
                "batch_id": b["batch_id"],
                "packlina_id": b["packlina_id"],
                "stopp_typ": random.choice(STOPP_TYPER),
                "starttid": fmt(s_start),
                "sluttid": fmt(s_slut),
                "stopp_minuter": int((s_slut - s_start).total_seconds() // 60)
            })
            sid += 1

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUT_FILE.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "stopp_id","batch_id","packlina_id","stopp_typ",
            "starttid","sluttid","stopp_minuter"
        ])
        w.writeheader()
        w.writerows(rows)

    print(f" Skrev {len(rows)} stopp till {OUT_FILE}")

if __name__ == "__main__":
    main()
