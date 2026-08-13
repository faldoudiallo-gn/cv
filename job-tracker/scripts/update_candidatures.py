#!/usr/bin/env python3
"""
Job Tracker Stratégique - Gestion de la base de candidatures (anti-doublon).

Rôle:
  - LIRE la base JSON job-tracker/data/candidatures.json
  - FILTRER une liste d'offres candidates (input JSON sur stdin) pour ne garder
    que celles dont l'URL n'est PAS déjà dans la base (anti-doublon)
  - RETOURNER sur stdout les nouvelles offres sous forme JSON (celles à presenter)

Usage:
  echo '[{"url":"...","entreprise":"...","poste":"...",...}]' | python3 update_candidatures.py check
  -> imprime sur stdout la liste des offres NOUVELLES (non deja vues)

Pour ENREGISTRER des offres (ou marquer un statut), utiliser le mode "add":
  echo '[{"statut":"postule","url":"..."}]' | python3 update_candidatures.py add

Le champ de dedup est 'url' (cle unique).
"""
import sys, json, os, datetime

BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
DB_PATH = os.path.join(BASE_DIR, "candidatures.json")

VALID_STATUTS = ["vu", "postule", "entretien", "refus", "accepte", "a_relancer"]

def load_db():
    if not os.path.exists(DB_PATH):
        return {"meta": {}, "candidatures": []}
    with open(DB_PATH, encoding="utf-8") as f:
        return json.load(f)

def save_db(db):
    os.makedirs(BASE_DIR, exist_ok=True)
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "check"
    raw = sys.stdin.read().strip()
    if not raw:
        print(json.dumps([]))
        return
    try:
        offers = json.loads(raw)
    except Exception as e:
        print(json.dumps({"error": f"JSON invalide: {e}"}))
        return

    db = load_db()
    cands = db.setdefault("candidatures", [])
    seen_urls = {c.get("url","").strip() for c in cands if c.get("url")}
    today = datetime.date.today().isoformat()

    if mode == "check":
        # ne garder que les nouvelles (url pas deja vue)
        new = [o for o in offers if o.get("url","").strip() not in seen_urls]
        print(json.dumps(new, ensure_ascii=False))
        return

    if mode == "add":
        added = 0
        updated = 0
        for o in offers:
            url = (o.get("url") or "").strip()
            if not url:
                continue
            # cherche si deja present
            idx = next((i for i,c in enumerate(cands) if c.get("url","").strip()==url), None)
            entry = {
                "url": url,
                "entreprise": o.get("entreprise",""),
                "poste": o.get("poste",""),
                "titre": o.get("titre",""),
                "ville": o.get("ville",""),
                "seniorite": o.get("seniorite",""),
                "match": o.get("match",""),
                "statut": o.get("statut","vu") if o.get("statut") in VALID_STATUTS else "vu",
                "date_ajout": o.get("date_ajout", today),
                "date_statut": today,
            }
            if idx is not None:
                # update statut si fourni, sinon garde l'ancien
                if o.get("statut"):
                    cands[idx]["statut"] = entry["statut"]
                    cands[idx]["date_statut"] = today
                updated += 1
            else:
                cands.append(entry)
                added += 1
        db["meta"]["derniere_maj"] = today
        save_db(db)
        print(json.dumps({"added": added, "updated": updated, "total": len(cands)}, ensure_ascii=False))
        return

    print(json.dumps({"error": f"mode inconnu: {mode}"}))
    return 1

if __name__ == "__main__":
    sys.exit(main())
