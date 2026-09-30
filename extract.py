"""Decode Prof.dat (vanilla layout, 170 x 716 bytes) + repo JSON into data.js for the explorer.
Field order mirrors ExtractMercProfile in src/game/Tactical/LoadSaveMercProfile.cc."""
import struct, json, re, sys, os
GAME = r"D:\SteamLibrary\steamapps\common\Jagged Alliance 2 Gold\Data\BinaryData\Prof.dat"
EXT = os.path.join(os.path.dirname(__file__), "..", "assets", "externalized")
ROT = [132,235,125,99,15,220,140,89,205,132,254,144,217,78,156,58,215,76,163,187,55,49,65,48,156,140,201,68,184,13,45,69,102,185,122,225,23,250,160,220,114,240,64,175,0o57,233]
def dec(b):
    out = bytearray(len(b)); last = 0
    for i, c in enumerate(b):
        out[i] = (c - (last + ROT[i % 46])) & 255; last = c
    return bytes(out)
raw = open(GAME, "rb").read()
assert len(raw) == 170 * 716

# (fmt-char/name, size) sequence
SEQ = []
def add(n, t): SEQ.append((n, t))
def skip(n): SEQ.append((None, n))
add("name", "w30"); add("nick", "w10"); skip(28); add("face", "B")
for k in ("pants","vest","skin","hair"): add(k, "s30")
for n,t in [("sex","b"),("armourAttr","b"),("misc2","B"),("evolution","b"),("misc","B"),("sexist","B"),("learnToHate","b")]: add(n,t)
skip(2); add("quoteRecord","B"); add("deathRate","b"); skip(2)
for n in ("expLevelGain","lifeGain","agilityGain","dexterityGain","wisdomGain","marksmanshipGain","medicalGain","mechanicGain","explosivesGain"): add(n,"h")
add("bodyType","B"); add("medical","b")
for n in ("eyesX","eyesY","mouthX","mouthY"): add(n,"H")
skip(10); add("blink","I"); add("expr","I"); add("secX","H"); add("secY","H"); add("dayAvail","I")
add("strength","b"); add("lifeMax","b")
for n in ("expLevelDelta","lifeDelta","agilityDelta","dexterityDelta","wisdomDelta","marksmanshipDelta","medicalDelta","mechanicDelta","explosivesDelta","strengthDelta","leadershipDelta"): add(n,"b")
skip(1)
for n in ("kills","assists","shotsFired","shotsHit","battles","wounded","daysServed"): add(n,"H")
add("leadershipGain","h"); add("strengthGain","h"); add("bodySub","I"); add("salary","h")
for n,t in [("life","b"),("dexterity","b"),("personality","b"),("skill1","b"),("repTolerance","b"),("explosive","b"),("skill2","b"),("leadership","b")]: add(n,t)
add("buddy","5b"); add("hated","5b")
add("expLevel","b"); add("marksmanship","b"); skip(1); add("wisdom","b"); skip(2)
add("invStatus","19B"); add("invNumber","19B"); add("approachFactor","4H")
add("mainGunAttr","b"); add("agility","b"); add("useInsertion","B"); skip(1); add("gridNo","h"); add("quoteAction","B")
add("mechanical","b"); add("invUndroppable","B"); add("roomStart","2B"); skip(1); add("inv","19H"); skip(20)
add("statChances","12H"); add("statSucc","12H"); add("insCode","B"); add("roomEnd","2B"); skip(4); add("lastQuote","B")
for n in ("race","nationality","appearance","appearanceCare","refinement","refinementCare","hatedNat","hatedNatCare","racist"): add(n,"b")
skip(1); add("weeklySalary","I"); add("biWeeklySalary","I"); add("medDeposit","b"); add("attitude","b"); skip(2)
add("medDepositAmt","H"); add("learnToLike","b"); add("approachVal","4B"); add("approachMod","12B")
add("town","b"); add("townAttach","b"); skip(1); add("gearCost","H"); add("opinion","75b"); add("approached","b"); add("mercStatus","b"); add("hatedTime","5b"); add("learnToLikeTime","b"); add("learnToHateTime","b"); add("hatedCount","5b"); add("learnToLikeCount","b"); add("learnToHateCount","b")
def parse(rec):
    p = 0; d = {}
    for n, t in SEQ:
        if n is None: p += t; continue
        if t.startswith("w"):
            L = int(t[1:]); d[n] = rec[p:p+2*L].decode("utf-16le").split("\0")[0]; p += 2*L
        elif t.startswith("s"):
            L = int(t[1:]); d[n] = rec[p:p+L].split(b"\0")[0].decode("latin1"); p += L
        else:
            m = re.match(r"(\d*)(.)", t); c = int(m.group(1) or 1); f = m.group(2)
            sz = struct.calcsize(f); v = list(struct.unpack_from("<%d%s" % (c, f), rec, p)); p += sz*c
            d[n] = v if c > 1 else v[0]
    return d
def strip_comments(s):
    return re.sub(r'/\*.*?\*/|(?<!:)//[^\n]*', '', s, flags=re.S)
info = json.loads(strip_comments(open(os.path.join(EXT,"mercs-profile-info.json"),encoding="utf8").read()))
info = {e["profileID"]: e for e in info}
aim = json.loads(strip_comments(open(os.path.join(EXT,"mercs-AIM-listings.json"),encoding="utf8").read()))
merc = json.loads(strip_comments(open(os.path.join(EXT,"mercs-MERC-listings.json"),encoding="utf8").read()))
profs = []
for i in range(170):
    d = parse(dec(raw[i*716:(i+1)*716])); d["id"] = i; profs.append(d)
byname = {e["internalName"]: i for i, e in info.items()}
SK = "NONE LOCKPICKING HANDTOHAND ELECTRONICS NIGHTOPS THROWING TEACHING HEAVY_WEAPS AUTO_WEAPS STEALTHY AMBIDEXT THIEF MARTIALARTS KNIFING ONROOF CAMOUFLAGED".split()
PT = "NONE HEAT_INTOLERANT NERVOUS CLAUSTROPHOBIC NONSWIMMER FEAR_OF_INSECTS FORGETFUL PSYCHO".split()
AT = "NORMAL FRIENDLY LONER OPTIMIST PESSIMIST AGGRESSIVE ARROGANT BIG_SHOT ASSHOLE COWARD".split()
def med_deposit(p):  # CalcMedicalDeposit / CalcCompetence in Soldier_Profile.cc
    import math
    stats = (2*p["lifeMax"] + p["strength"] + p["agility"] + p["dexterity"] + (p["leadership"] + p["wisdom"])//2)//3
    skills = int(2*(p["marksmanship"]**3/10000) + 1.5*(p["medical"]**3/10000) + p["mechanical"]**3/10000 + p["explosive"]**3/10000)
    ap = 5 + (10*p["expLevel"] + 3*p["agility"] + 2*p["lifeMax"] + 2*p["dexterity"] + 20)//40
    sp = (p["skill1"] != 0) + (p["skill2"] != 0)
    comp = int(p["expLevel"]**0.2 * stats * skills * (ap - 6) * (1 + 0.05*sp) / 1000) & 0xffff
    return (5*comp + 50)//100*100
out = []
for i, d in enumerate(profs):
    e = info[i]
    if e["type"] not in ("AIM", "MERC", "RPC"): continue
    if not d["name"] or "Removed" in d["name"]: continue
    o = {"id": i, "type": e["type"], "internal": e["internalName"]}
    o["name"] = d["name"]; o["nick"] = d["nick"]; o["sex"] = "F" if d["sex"] else "M"
    st = dict(life=d["lifeMax"], agility=d["agility"], dexterity=d["dexterity"], strength=d["strength"],
      leadership=d["leadership"], wisdom=d["wisdom"], exp=d["expLevel"], marksmanship=d["marksmanship"],
      explosive=d["explosive"], mechanical=d["mechanical"], medical=d["medical"])
    st.update({k:v for k,v in {"life":e.get("stats",{}).get("health")}.items() if v is not None})
    o["stats"] = st
    o["skill1"] = SK[d["skill1"]]; o["skill2"] = SK[d["skill2"]]
    o["personality"] = PT[d["personality"]]; o["attitude"] = AT[d["attitude"]]
    o["salary"] = d["salary"]; o["weekly"] = d["weeklySalary"]; o["biweekly"] = d["biWeeklySalary"]
    o["medDeposit"] = med_deposit(d) if d["medDeposit"] else 0
    o["gearCost"] = d["gearCost"]; o["repTolerance"] = d["repTolerance"]
    o["buddy"] = [x for x in d["buddy"][:3] if x >= 0]; o["hated"] = [x for x in d["hated"][:3] if x >= 0]
    o["learnToLike"] = d["learnToLike"]; o["learnToHate"] = d["learnToHate"]
    o["hatedTime"] = d["hatedTime"][:2]; o["learnToLikeTime"] = d["learnToLikeTime"]; o["learnToHateTime"] = d["learnToHateTime"]
    o["opinion"] = d["opinion"]
    o["sexist"] = d["sexist"]; o["face"] = i
    o["town"] = d["town"]; o["sleep"] = None
    out.append(o)
import base64, sti
E = sti.slf_entries()
for o in out:
    k = "BIGFACES/%02d.STI" % o["face"]
    if k in E:
        w, h, px, _ = sti.decode(E[k]); o["portrait"] = "data:image/png;base64," + base64.b64encode(sti.png(w, h, px)).decode()
for o in out:
    o["opinion"] = o["opinion"][:75]
    if o["nick"].startswith("RPC"): o["nick"] = (o["name"].split() or [o["internal"].title()])[0]
data = {"mercs": out}
open(os.path.join(os.path.dirname(__file__),"data.js"),"w",encoding="utf8").write("window.DATA=" + json.dumps(data, separators=(",",":")) + ";")
print(len(out))
for o in out[:6]: print(o["id"], o["name"], o["nick"], o["stats"], o["skill1"], o["skill2"], o["buddy"], o["hated"], o["learnToLike"], o["learnToHate"], o["salary"])
