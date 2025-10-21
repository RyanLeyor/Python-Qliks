import csv
import logging
from pathlib import Path
from collections import Counter


#--------- Läser in data och skapar en logging på nivån INFO ---------------


DATA_DIR = Path("data_raw")
IN_FILE = DATA_DIR / "batcher.csv"
OUT_DUMP = DATA_DIR / "dumpade_batcher.csv"
OUT_KPI  = DATA_DIR / "kpi_dump_rate.csv"

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    filename=LOG_DIR / "app.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


# läsa in och filtrera data efter status: dump
#----------

def läs_batcher(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)

def filtrera_dumpade(rows):
    return [r for r in rows if r.get("status") == "Dumpad"]


# Skriva ut data i CSV-format och räkna dump-rate per produkt och packlina
#----------

def skriv_csv(path: Path, rows, fieldnames):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)

def summera_dump_rate(rows, dumpade):
    tot = len(rows)
    n_dump = len(dumpade)
    dump_rate = (n_dump / tot) * 100 if tot else 0.0 #beräkna dump i procent
   
    per_produkt = Counter(r["produkt"] for r in dumpade) 
    per_packlina = Counter(r["packlina_id"] for r in dumpade)
    return {
        "totala_batcher": tot,
        "dumpade_batcher": n_dump,
        "dump_rate_procent": round(dump_rate, 2),
        "dumpade_per_produkt": dict(per_produkt),
        "dumpade_per_packlina": dict(per_packlina),
    }

# Huvudflöde
#-----------------------------

def main():
    if not IN_FILE.exists(): #kontrollera att batcher.csv finns
        raise FileNotFoundError(f"Hittar inte filen: {IN_FILE}")

    rows = läs_batcher(IN_FILE)
    dumpade = filtrera_dumpade(rows)

    # Logga varje dumpad batch
    for r in dumpade:
        logging.info(
            "Dumpad batch: id=%s, produkt=%s, packlina=%s, start=%s, slut=%s, kasserade=%s",
            r["batch_id"], r["produkt"], r["packlina_id"], r["starttid"], r["sluttid"], r["antal_kasserade"]
        )

    # Skriv dumpade batcher till egen CSV
    if dumpade:
        flds = list(dumpade[0].keys())
        skriv_csv(OUT_DUMP, dumpade, flds)

    # KPI-sammanställning
    kpi = summera_dump_rate(rows, dumpade)
    # spara som enkel CSV för BI-import
    skriv_csv(OUT_KPI, [kpi], ["totala_batcher","dumpade_batcher","dump_rate_procent","dumpade_per_produkt","dumpade_per_packlina"])

    # Konsol-summering
    print(f"Totala batcher: {kpi['totala_batcher']}")
    print(f"Dumpade batcher: {kpi['dumpade_batcher']} ({kpi['dump_rate_procent']}%)")
    print("Detaljer loggade i logs/app.log")
    if dumpade:
        print(f"Sparade dumpade batcher i: {OUT_DUMP}")
    print(f"Sparade KPI i: {OUT_KPI}")

if __name__ == "__main__":
    main()
