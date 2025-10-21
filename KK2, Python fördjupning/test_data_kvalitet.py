
import csv
from pathlib import Path
from datetime import datetime


# ----------  kontrollera batcher.csv ----------


DATA_FILE = Path("data_raw/batcher.csv")

def _read_batches():
    assert DATA_FILE.exists(), f"Saknar fil: {DATA_FILE.resolve()}"
    with DATA_FILE.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))

def _to_dt(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d %H:%M")

# ----------
#Kontrollera att starttid är före sluttid och att summor stämmer
#----------

def test_times_are_ordered():
    """starttid < sluttid för alla batcher"""
    rows = _read_batches()
    for i, r in enumerate(rows, start=1):
        start = _to_dt(r["starttid"])
        slut = _to_dt(r["sluttid"])
        assert start < slut, f"Rad {i}: starttid {start} är EJ före sluttid {slut} (batch_id={r['batch_id']})"

def test_counts_add_up():
    """antal_godkända + antal_kasserade == antal_påsar"""
    rows = _read_batches()
    for i, r in enumerate(rows, start=1):
        tot = int(r["antal_påsar"])
        godk = int(r["antal_godkända"])
        kass = int(r["antal_kasserade"])
        assert godk + kass == tot, (
            f"Rad {i}: godkända({godk}) + kasserade({kass}) != påsar({tot}) (batch_id={r['batch_id']})"
        )


# --------- 
# Test-skript (Pytest) som kontrollera summor och tider mot batcher.csv
# ---------


# ----------  kontrollera stopp per packlina ----------

STOPP_FILE = Path("data_raw/stopp.csv")

def _read_stopp():
    assert STOPP_FILE.exists(), f"Saknar fil: {STOPP_FILE.resolve()}"
    with STOPP_FILE.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))

def test_stopp_per_packlina():
    """
    Säkerställer att varje stopp:
      - har start/sluttid
      - har positiv längd (start < slut)
      - inte överlappar ett annat stopp på samma packlina (per batch)
        (dvs nästa stopp får börja tidigast när föregående har slutat)
    """
    rows = _read_stopp()

    # tider finns och är i rätt ordning
    for i, r in enumerate(rows, 1):
        ss = r.get("starttid", "")
        se = r.get("sluttid", "")
        assert ss and se, f"Tom start/stopptid i stopp rad {i}"
        start = datetime.strptime(ss, "%Y-%m-%d %H:%M")
        slut  = datetime.strptime(se, "%Y-%m-%d %H:%M")
        assert start < slut, f"Stopp rad {i}: start >= slut ({start} vs {slut})"

    # Inga överlapp inom samma packlina och samma batch
    
    from collections import defaultdict
    grupper = defaultdict(list)
    for r in rows:
        key = (r["packlina_id"], r["batch_id"])
        grupper[key].append(r)

    for key, lst in grupper.items():
        # sortera på starttid inom gruppen
        lst.sort(key=lambda x: datetime.strptime(x["starttid"], "%Y-%m-%d %H:%M"))
        prev_end = None
        for r in lst:
            s = datetime.strptime(r["starttid"], "%Y-%m-%d %H:%M")
            e = datetime.strptime(r["sluttid"], "%Y-%m-%d %H:%M")
            if prev_end is not None:
                assert s >= prev_end, (
                    f"Överlapp på packlina/batch {key}: "
                    f"stopp start {s} < föregående slut {prev_end}"
                )
            prev_end = e


# ---------- stopp måste ligga inom batchens tidsfönster ----------

BATCH_FILE = Path("data_raw/batcher.csv")

def test_stopp_ligger_inom_batchens_tidsfonster():
    """
    Säkerställ att varje stopp:
      - tillhör en känd batch
      - ligger helt inom batchens starttid–sluttid
      - har samma packlina som batchen
    """
    stopp_rows   = _read_stopp()
    batch_rows   = _read_batches()
    batch_by_id  = {b["batch_id"]: b for b in batch_rows}

    for i, r in enumerate(stopp_rows, 1):
        bid = r["batch_id"]
        assert bid in batch_by_id, f"Stopp rad {i}: okänd batch_id={bid}"

        b   = batch_by_id[bid]
        bs  = datetime.strptime(b["starttid"], "%Y-%m-%d %H:%M")
        be  = datetime.strptime(b["sluttid"], "%Y-%m-%d %H:%M")
        ss  = datetime.strptime(r["starttid"], "%Y-%m-%d %H:%M")
        se  = datetime.strptime(r["sluttid"],  "%Y-%m-%d %H:%M")

        # tillåt att stopp börjar exakt på batchstart/slutar exakt på batchslut
        assert bs <= ss <= be, (
            f"Stopp rad {i}: start {ss} ligger utanför batchfönster [{bs}–{be}] (batch_id={bid})"
        )
        assert bs <= se <= be, (
            f"Stopp rad {i}: slut  {se} ligger utanför batchfönster [{bs}–{be}] (batch_id={bid})"
        )


