import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

# ----------------------------- Skapa mock-data för batcher, kontroller och lager -----------------------------

ANTAL_BATCHER = 150
STARTDATUM = datetime(2025, 1, 1, 6, 0)
DAGAR_SPANN = 45
PACKLINOR = ["Packlina 1", "Packlina 2", "Packlina 3"]
PRODUKTER = ["Smofkabiven", "Kabiven", "Smoflipid", "Aminoven"]
STATUS_BATCH = ["Avslutad", "Dumpad"]  
KONTROLL_TYPER = ["Syning", "Hanteringsetiketter"]
UTFALL = ["Godkänd", "Underkänd"]

OUT_DIR = Path("data_raw")
random.seed(42)

# -----------------------------
# Hjälpfunktioner
# -----------------------------
def slump_tid(start: datetime, max_dagar: int) -> datetime:
    """Skapar en slumpad tidpunkt mellan startdatum och start + max_dagar."""
    d = random.randint(0, max_dagar)
    m = random.randint(0, 12*60)
    return start + timedelta(days=d, minutes=m)

def fmt(ts: datetime) -> str:
    """Formaterar datetime till sträng YYYY-MM-DD HH:MM."""
    return ts.strftime("%Y-%m-%d %H:%M")

# -----------------------------
# Generera batcher
# -----------------------------
def generera_batcher(n=ANTAL_BATCHER):
    rader = []
    for i in range(1, n+1):
        batch_id = f"B{i:04d}"
        packlina = random.choice(PACKLINOR)
        produkt = random.choice(PRODUKTER)
        start = slump_tid(STARTDATUM, DAGAR_SPANN)
        bas_tid_h = random.randint(6, 12)
        slack_h = random.randint(0, 4)
        slut = start + timedelta(hours=bas_tid_h + slack_h)

        antal = random.randint(684, 12000)
        kasserade = max(0, int(round(antal * random.uniform(0.002, 0.03))))
        godkända = antal - kasserade

        status = random.choices(STATUS_BATCH, weights=[0.92, 0.08], k=1)[0]

        rader.append({
            "batch_id": batch_id,
            "packlina_id": packlina,
            "produkt": produkt,
            "antal_påsar": antal,
            "antal_godkända": godkända,
            "antal_kasserade": kasserade,
            "starttid": fmt(start),
            "sluttid": fmt(slut),
            "status": status
        })
    return rader

# -----------------------------
# Generera kontroller
# -----------------------------
def generera_kontroller(batcher):
    rader = []
    kid = 1
    for b in batcher:
        n = random.randint(1, 3)  # varje batch får 1–3 kontroller
        start = datetime.strptime(b["starttid"], "%Y-%m-%d %H:%M")
        slut = datetime.strptime(b["sluttid"], "%Y-%m-%d %H:%M")
        for _ in range(n):
            total_min = int((slut - start).total_seconds() // 60)
            ts = start + timedelta(minutes=random.randint(30, max(31, total_min - 10)))
            ktyp = random.choice(KONTROLL_TYPER)
            utfall = random.choices(UTFALL, weights=[0.85, 0.15], k=1)[0]  # 85% chans Godkänd

            kommentar = ""
            if utfall == "Underkänd":
                if ktyp == "Syning":
                    kommentar = random.choice(["Hål ytterpåse", "Läckage", "Partikel i lösning"])
                elif ktyp == "Hanteringsetiketter":
                    kommentar = random.choice(["Saknad batch-etikett", "Felaktig etikettplacering"])

            rader.append({
                "kontroll_id": f"K{kid:05d}",
                "batch_id": b["batch_id"],
                "kontroll_typ": ktyp,
                "utfall": utfall,
                "kommentar": kommentar,
                "tidsstämpel": fmt(ts)
            })
            kid += 1
    return rader

# -----------------------------
# Generera lager
# -----------------------------
def generera_lager(batcher):
    rader = []
    lid = 1
    for b in batcher:
        if b["status"] != "Avslutad":
            continue
        slut = datetime.strptime(b["sluttid"], "%Y-%m-%d %H:%M")
        inlagd = slut + timedelta(hours=random.randint(1, 8))
        per_låda = random.randint(10, 12)
        lådor = b["antal_godkända"] // per_låda
        plats = random.choice(["HYLLA-A1", "HYLLA-B3", "HYLLA-C2", "PALLET-D4"])
        rader.append({
            "lager_id": f"L{lid:05d}",
            "batch_id": b["batch_id"],
            "antal_lådor": lådor,
            "inlagd_tid": fmt(inlagd),
            "lagringsplats": plats
        })
        lid += 1
    return rader

# -----------------------------
# Skriv CSV
# -----------------------------
def skriv_csv(path: Path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)

def main():
    batcher = generera_batcher()
    kontroller = generera_kontroller(batcher)
    lager = generera_lager(batcher)

    skriv_csv(OUT_DIR / "batcher.csv", batcher,
              ["batch_id","packlina_id","produkt","antal_påsar","antal_godkända","antal_kasserade","starttid","sluttid","status"])
    skriv_csv(OUT_DIR / "kontroller.csv", kontroller,
              ["kontroll_id","batch_id","kontroll_typ","utfall","kommentar","tidsstämpel"])
    skriv_csv(OUT_DIR / "lager.csv", lager,
              ["lager_id","batch_id","antal_lådor","inlagd_tid","lagringsplats"])

    print(f"✓ Klart! Skrev {len(batcher)} batcher, {len(kontroller)} kontroller, {len(lager)} lager-rader till {OUT_DIR}/")

if __name__ == "__main__":
    main()
