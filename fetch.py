"""Récupère le dernier cours de clôture des 10 actions de l'appli chez EODHD
et l'écrit dans data/data.json. Lancé chaque soir par GitHub Actions.
Aucune bibliothèque à installer : uniquement Python standard."""
import json, os, sys, urllib.request, urllib.error
from datetime import datetime, timedelta, timezone

KEY = os.environ.get("EODHD_KEY", "").strip()
if not KEY:
    sys.exit("ERREUR : le secret EODHD_KEY est absent (Settings > Secrets and variables > Actions).")

# ticker de l'appli -> symbole EODHD (SYMBOLE.BOURSE)
SYMBOLS = {
    "NVDA": "NVDA.US", "MSFT": "MSFT.US", "LLY": "LLY.US", "JPM": "JPM.US",
    "CCJ": "CCJ.US", "FCX": "FCX.US",
    "ASML": "ASML.AS",   # Euronext Amsterdam
    "SU": "SU.PA",       # Euronext Paris
    "RHM": "RHM.XETRA",  # Xetra Francfort
    "IBE": "IBE.MC",     # Bourse de Madrid
}

OUT = "data/data.json"
try:
    data = json.load(open(OUT, encoding="utf-8"))
except Exception:
    data = {"quotes": {}}
data.setdefault("quotes", {})

since = (datetime.now(timezone.utc) - timedelta(days=10)).strftime("%Y-%m-%d")
ok, errors = 0, []
for ticker, sym in SYMBOLS.items():
    url = f"https://eodhd.com/api/eod/{sym}?api_token={KEY}&fmt=json&order=d&from={since}"
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            rows = json.load(r)
        last = rows[0]  # order=d : le plus récent en premier
        data["quotes"][ticker] = {"symbol": sym, "close": round(float(last["close"]), 4), "date": last["date"]}
        ok += 1
        print(f"OK   {ticker:5} {sym:10} {last['date']}  {last['close']}")
    except Exception as e:  # on garde l'ancien cours si un appel échoue
        errors.append(f"{ticker} ({sym}) : {e}")
        print(f"ECHEC {ticker:5} {sym:10} {e}")

data["updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
data["errors"] = errors
os.makedirs("data", exist_ok=True)
json.dump(data, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"{ok}/{len(SYMBOLS)} cours mis à jour.")
if ok == 0:
    sys.exit("ERREUR : aucun cours reçu. Vérifie la clé EODHD et le quota du jour (20 appels).")
