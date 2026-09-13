"""Low-level PicCall brain: safety index, nearby, one-trip planner, FAQ."""

from __future__ import annotations

import math
import re

EARTH_MI = 3958.8

FAQ = [
    {"id": "hashtag", "q": "How do I call a business without a phone number?",
     "tags": "call hashtag number dial tap tag phone",
     "a": "Search the place in PicCall and tap its #Hashtag. That tag is tied to the verified business line, so you never hunt a number. Example: #NightOwlRx dials NightOwl Pharmacy."},
    {"id": "safety-index", "q": "What is the safety index?",
     "tags": "safety index score rating grade cameras lighting night lot pickle",
     "a": "The safety index is a 0–100 score, not just stars. It blends neighbor ratings with hard facts: cameras inside and out, a lit lot, a night photo, staff on site after dark, and an SMS-verified phone. 85+ is A (go), 70–84 is B, under 55 is caution — take someone or go in daylight."},
    {"id": "photos", "q": "What photos should I look at before I drive?",
     "tags": "photo interior parking lot night storefront destination pickle",
     "a": "Open the profile and check four shots: storefront, interior, parking lot, and the approach after dark. A sunny Google photo is not the lot you meet at 11pm. If the night shot is missing, treat the index as incomplete."},
    {"id": "nearby", "q": "How do I find stores nearby?",
     "tags": "nearby near me stores close distance miles around",
     "a": "Use Nearby. PicCall sorts listed places by miles from you and by safety index. You can stay inside a few miles and still pick the safer door."},
    {"id": "trip", "q": "Can I hit three businesses in one trip?",
     "tags": "trip three 3 stops one stop shop errand route chain recommend",
     "a": "Yes. One-trip shop builds a 3-stop loop: it picks a high-index place for each errand (pharmacy, food, auto, and so on), then orders them so you do not criss-cross town. See the photos and index for each stop before you roll."},
    {"id": "lookup", "q": "Someone gave me a phone number. Is that place safe?",
     "tags": "lookup phone number paste check rating unknown",
     "a": "Paste the number into Lookup. If the business is on PicCall you get the safety index, night photo, and whether the line is SMS-verified — then you can tap the hashtag to call."},
    {"id": "verify", "q": "How do businesses prove their phone number?",
     "tags": "sms verify verification code twilio business line own",
     "a": "The owner texts a code to the listing number. PicCall will not publish the profile until that code comes back. Verified listings show an SMS-verified badge."},
    {"id": "specials", "q": "Where are today’s specials?",
     "tags": "special today deal coupon specials post",
     "a": "Specials live on the same profile as the photos and the hashtag. If you build a 3-stop trip, each stop’s special rides along so you can shop the deal without a second drive."},
    {"id": "night", "q": "Is it safe to go after dark?",
     "tags": "night dark after hours late evening staffed cameras lot",
     "a": "Read the index first, then the night shot. Prefer places marked night-safe and staffed nights. If the lot is dim or the alley is the only door, go with someone or wait for daylight — that is the pickle PicCall is built to avoid."},
    {"id": "list", "q": "How does a business get listed?",
     "tags": "list profile fee price lite standard verified upload",
     "a": "Open a paid profile: Lite $29, Standard $79, Verified $149 a month. Verify the phone by SMS, upload interior / lot / night photos, mark cameras and lighting, and claim a hashtag."},
    {"id": "recommend", "q": "How do recommendations work?",
     "tags": "recommend recommendation suggest best pick for me",
     "a": "Recommendations rank nearby listings by safety index, distance, a live special, and whether the phone is verified. They are a short list of places worth the drive — not ads."},
]


def haversine_mi(a, b):
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_MI * math.asin(min(1.0, math.sqrt(h)))


def safety_index(b):
    ratings = float(b.get("safetyScore") or 0)
    n = int(b.get("ratingsCount") or 0)
    crowd = 18.0 if n <= 0 and ratings <= 0 else (ratings / 5.0) * 40.0
    if n and n < 5:
        crowd *= 0.85
    features = 0.0
    features += 15 if b.get("cameras") else 0
    features += 15 if b.get("wellLit") else 0
    features += 15 if b.get("nightSafe") else 0
    features += 10 if b.get("staffedNight") else 0
    features += 5 if b.get("phoneVerified") else 0
    photos = b.get("photos") or {}
    filled = sum(1 for k in ("storefront", "interior", "parking", "night") if photos.get(k))
    photo_pts = 5 if filled >= 4 else (2 if filled >= 2 else 0)
    raw = max(0.0, min(100.0, crowd + features + photo_pts))
    if raw >= 88:
        grade, band = "A", "Go"
    elif raw >= 76:
        grade, band = "B", "Mostly safe"
    elif raw >= 62:
        grade, band = "C", "Use care"
    elif raw >= 48:
        grade, band = "D", "Daylight only"
    else:
        grade, band = "F", "Skip after dark"
    why = []
    if b.get("cameras"):
        why.append("cameras in/out")
    if b.get("wellLit"):
        why.append("lit lot")
    if b.get("nightSafe"):
        why.append("night-safe")
    if b.get("staffedNight"):
        why.append("staffed nights")
    if b.get("phoneVerified"):
        why.append("SMS-verified line")
    if not why:
        why.append("thin evidence — photos and ratings still filling in")
    return {"safetyIndex": round(raw), "safetyGrade": grade, "safetyBand": band, "safetyWhy": why}


def attach_index(pub, raw):
    pub.update(safety_index(raw))
    if raw.get("lat") is not None:
        pub["lat"] = raw["lat"]
        pub["lng"] = raw["lng"]
    return pub


def nearby(businesses, origin, radius, publicize):
    out = []
    for b in businesses:
        if b.get("lat") is None:
            continue
        miles = haversine_mi(origin, (b["lat"], b["lng"]))
        if miles <= radius:
            item = publicize(b)
            item["miles"] = round(miles, 1)
            out.append(item)
    out.sort(key=lambda x: (x.get("miles", 99), -x.get("safetyIndex", 0)))
    return out


def recommend(businesses, origin, publicize, limit=4):
    ranked = []
    for b in businesses:
        item = publicize(b)
        if origin and b.get("lat") is not None:
            item["miles"] = round(haversine_mi(origin, (b["lat"], b["lng"])), 1)
        else:
            item["miles"] = None
        miles = item["miles"] if item["miles"] is not None else 8
        special = 8 if b.get("special") else 0
        score = item.get("safetyIndex", 0) * 1.2 - miles * 4 + special
        if b.get("phoneVerified"):
            score += 4
        item["recommendScore"] = round(score, 1)
        ranked.append(item)
    ranked.sort(key=lambda x: -x["recommendScore"])
    return ranked[:limit]


def _cat_key(s):
    s = (s or "").lower()
    if "pharm" in s or "rx" in s:
        return "pharmacy"
    if "lock" in s:
        return "locksmith"
    if "auto" in s or "tire" in s or "brake" in s:
        return "auto"
    if "rest" in s or "kitchen" in s or "food" in s:
        return "restaurant"
    if "urgent" in s or ("care" in s and "vet" not in s):
        return "urgent care"
    if "dent" in s:
        return "dental"
    if "vet" in s:
        return "veterinary"
    if "stor" in s:
        return "storage"
    return s


def plan_trip(businesses, origin, needs, publicize, max_stops=3, radius=12):
    needs = [n for n in needs if n][:max_stops] or ["pharmacy", "restaurant", "auto"]
    pool = []
    for b in businesses:
        if b.get("lat") is None:
            continue
        miles = haversine_mi(origin, (b["lat"], b["lng"]))
        if miles > radius:
            continue
        item = publicize(b)
        item["miles"] = round(miles, 1)
        item["_cat"] = _cat_key(b.get("category"))
        pool.append((b, item))
    picked, used_ids = [], set()
    for need in needs:
        key = _cat_key(need)
        candidates = [item for raw, item in pool if item["id"] not in used_ids and (item["_cat"] == key or key in (item.get("name") or "").lower() or key in (item.get("category") or "").lower())]
        if not candidates:
            candidates = [item for raw, item in pool if item["id"] not in used_ids]
        candidates.sort(key=lambda x: (-x.get("safetyIndex", 0), x.get("miles", 99)))
        if candidates:
            choice = candidates[0]
            picked.append(choice)
            used_ids.add(choice["id"])
    ordered, cursor, total, remaining = [], origin, 0.0, picked[:]
    while remaining:
        remaining.sort(key=lambda x: haversine_mi(cursor, (x["lat"], x["lng"])))
        nxt = remaining.pop(0)
        leg = haversine_mi(cursor, (nxt["lat"], nxt["lng"]))
        nxt = {k: v for k, v in nxt.items() if not k.startswith("_")}
        nxt["legMiles"] = round(leg, 1)
        total += leg
        ordered.append(nxt)
        cursor = (nxt["lat"], nxt["lng"])
    return {"stops": ordered, "stopCount": len(ordered), "totalMiles": round(total, 1), "needs": needs,
            "pitch": f"{len(ordered)} stops · ~{round(total, 1)} miles · one loop instead of three drives"}


def _tokens(text):
    return set(re.findall(r"[a-z0-9#]+", (text or "").lower()))


def answer_faq(question, businesses, publicize, origin=None):
    q = (question or "").strip()
    if not q:
        return {"error": "need_question"}
    qtok = _tokens(q)
    mentioned = None
    blob = q.lower().replace("#", "")
    for b in businesses:
        if b["hashtag"].lower() in blob or b["name"].lower() in blob:
            mentioned = publicize(b)
            if origin and b.get("lat") is not None:
                mentioned["miles"] = round(haversine_mi(origin, (b["lat"], b["lng"])), 1)
            break
    scored = []
    for card in FAQ:
        hay = _tokens(card["q"] + " " + card["tags"] + " " + card["a"])
        scored.append((len(qtok & hay), card))
    scored.sort(key=lambda x: -x[0])
    top = [c for s, c in scored if s > 0][:3] or [FAQ[1], FAQ[4], FAQ[0]]
    extra = ""
    if mentioned:
        extra = (
            f" {mentioned['name']} (#{mentioned['hashtag']}) is safety index "
            f"{mentioned.get('safetyIndex')} grade {mentioned.get('safetyGrade')} — {mentioned.get('safetyBand')}. "
            f"{mentioned.get('safetyNotes') or ''} Hours: {mentioned.get('hours')}."
        )
        if mentioned.get("special"):
            extra += f" Today: {mentioned['special']['title']}."
    wants_trip = bool(qtok & {"trip", "three", "3", "stops", "errand", "loop"})
    wants_near = bool(qtok & {"nearby", "near", "close", "around"})
    wants_rec = bool(qtok & {"recommend", "recommendation", "suggest", "best"})
    return {
        "question": q,
        "answer": top[0]["a"] + extra,
        "matched": [{"id": c["id"], "q": c["q"]} for c in top],
        "business": mentioned,
        "intent": "trip" if wants_trip else "nearby" if wants_near else "recommend" if wants_rec else "faq",
        "engine": "piccall-grok-lite",
        "suggestions": [c["q"] for c in FAQ[:5]],
    }
