import csv
from datetime import date, datetime, timedelta
from pathlib import Path
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("pharmacy-stock")
DATA = Path(__file__).parent / "data" / "pharmacy_stock.csv"
MAX_ROWS = 10   # keeps replies small (saves tokens)

# A stdio MCP server talks to the
# client over stdout, so printing would corrupt the protocol.


def load():
    with open(DATA, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save(rows):
    with open(DATA, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _match(rows, item, strength=""):
    return [r for r in rows
            if item.lower() in r["item"].lower()
            and strength.lower() in r["strength"].lower()]


# ---------- READ tools (percepts) ----------

@mcp.tool()
def check_stock(item: str, strength: str = "") -> list[dict]:
    """Return stock rows whose item name contains `item` (and whose strength
    contains `strength`, if given). Use this for 'do we have X?' questions."""
    return _match(load(), item, strength)[:MAX_ROWS]


@mcp.tool()
def search_items(query: str) -> list[dict]:
    """Search stock by a word in the item name or the form (tablet, syrup,
    capsule...). Use this when the user does not name an exact medicine,
    e.g. 'what syrups do we have?'."""
    q = query.lower()
    rows = [r for r in load() if q in r["item"].lower()
            or q in r["form"].lower()]
    return rows[:MAX_ROWS]


@mcp.tool()
def list_expiring(days: int) -> list[dict]:
    """List items that expire within `days` days from today, soonest first.
    Includes items already expired (negative days_left)."""
    today = date.today()
    cutoff = today + timedelta(days=days)
    out = []
    for r in load():
        try:
            exp = datetime.strptime(r["expiry_date"], "%Y-%m-%d").date()
        except ValueError:
            continue
        if exp <= cutoff:
            out.append({**r, "days_left": (exp - today).days})
    out.sort(key=lambda r: r["days_left"])
    return out[:MAX_ROWS]


@mcp.tool()
def price_quote(item: str, strength: str, qty: int) -> dict:
    """Work out the price of `qty` packs of one medicine (unit price x qty).
    Does NOT change stock. Use this for 'what do N packs of X cost?'."""
    rows = _match(load(), item, strength)
    if len(rows) != 1:
        return {"ok": False, "message": f"Found {len(rows)} matches. Give an exact item and strength."}
    price = float(rows[0]["unit_price_ghs"])
    return {"ok": True, "item": rows[0]["item"], "strength": rows[0]["strength"],
            "qty": qty, "unit_price_ghs": price, "total_ghs": round(price * qty, 2)}


# ---------- WRITE tool (actuator) ----------

@mcp.tool()
def record_sale(item: str, strength: str, qty: int) -> dict:
    """RECORD A SALE: permanently reduces stock by `qty` packs. Only call this
    when the user explicitly asks to sell or record a sale. Needs the item name,
    its strength and a positive whole number `qty`. Refuses if stock is too low."""
    if qty <= 0:
        return {"ok": False, "message": "Refused: qty must be a positive whole number."}
    rows = load()
    matches = _match(rows, item, strength)
    if not matches:
        return {"ok": False, "message": f"Refused: no item matching '{item} {strength}'."}
    if len(matches) > 1:
        names = [f"{r['item']} {r['strength']}" for r in matches]
        return {"ok": False, "message": f"Refused: ambiguous, matches {names}. Be specific."}
    row = matches[0]
    available = int(row["quantity"])
    if qty > available:
        return {"ok": False, "message": f"Refused: only {available} packs of "
                                        f"{row['item']} {row['strength']} in stock, cannot sell {qty}."}
    row["quantity"] = str(available - qty)
    save(rows)
    return {"ok": True, "message": f"Sold {qty} packs of {row['item']} {row['strength']}.",
            "remaining": available - qty}


if __name__ == "__main__":
    mcp.run()
