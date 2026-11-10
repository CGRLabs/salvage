"""In-game verification of the Salvage content mod.

Launches a throwaway offscreen creative world whose game home holds a copy of
the installed .hmod files, then smelts one item per recipe family in a real
furnace and reads the output slot back. Player data is never touched.
"""

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INSTALL = Path(r"D:\CGRLabs\Horizon-Ecosystem\horizon-windows-x64")
CTL = INSTALL / "horizon-ctl.exe"
GAME = INSTALL / "horizon-client.exe"
RESOURCES = INSTALL / ".local" / "horizon-client" / "26.3"
OUT = ROOT / "target" / "smoke"
OUT.mkdir(parents=True, exist_ok=True)

# One representative per output family; the other nine share the same shape.
RECIPES = [
    ("leather_helmet", "leather"),
    ("saddle", "leather"),
    ("wooden_pickaxe", "charcoal"),
    ("bow", "string"),
]
# No smelting recipe exists for this in vanilla or in the mod: it must NOT cook.
CONTROL = "diamond_sword"
COOK_TICKS = 260  # recipe cookingtime is 200

LOG = (OUT / "run.log").open("w", encoding="utf-8")


def log(msg):
    print(msg, flush=True)
    LOG.write(msg + "\n")
    LOG.flush()


def scratch_env():
    env = dict(os.environ)
    home = Path(tempfile.mkdtemp(prefix="salvage-smoke-home-"))
    env["HORIZON_HOME"] = str(home)
    env["HORIZON_LAUNCHER_HOME"] = tempfile.mkdtemp(prefix="salvage-smoke-launcher-")
    env["XDG_DATA_HOME"] = tempfile.mkdtemp(prefix="salvage-smoke-data-")
    env["XDG_CONFIG_HOME"] = tempfile.mkdtemp(prefix="salvage-smoke-config-")
    # ctl launch points --game-dir at HORIZON_HOME, so the mods must live there.
    shutil.copytree(INSTALL / "horizon-mods", home / "horizon-mods")
    shutil.copy2(INSTALL / "horizon-mods.txt", home / "horizon-mods.txt")
    log(f"scratch game home: {home}")
    log("mods copied: " + ", ".join(p.name for p in (home / "horizon-mods").glob("*.hmod")))
    log("enabled: " + (home / "horizon-mods.txt").read_text(encoding="utf-8").replace("\n", " "))
    return env, home


ENV, HOME = scratch_env()
SEQ = 0


def ctl(*args, timeout=120):
    """Never pipe: the game inherits the handles and a pipe blocks forever."""
    out_path, err_path = OUT / "ctl.out", OUT / "ctl.err"
    with out_path.open("wb") as out, err_path.open("wb") as err:
        done = subprocess.run(
            [str(CTL), *args], stdout=out, stderr=err, env=ENV, timeout=timeout, cwd=str(INSTALL)
        )
    text = out_path.read_text(encoding="utf-8", errors="replace").strip()
    error = err_path.read_text(encoding="utf-8", errors="replace").strip()
    if done.returncode != 0:
        raise RuntimeError(f"ctl {' '.join(map(str, args))} -> {done.returncode}: {text or error}")
    return text


def j(*args, timeout=120):
    text = ctl(*args, timeout=timeout)
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return {"_raw": text}
    if isinstance(value, dict) and "error" in value:
        raise RuntimeError(f"ctl {' '.join(map(str, args))} -> {value['error']}")
    return value


def soft(label, fn):
    try:
        return fn()
    except Exception as exc:  # keep going: one failure must not hide the rest
        log(f"  ! {label}: {exc}")
        return None


def norm(item):
    if not item:
        return None
    return item.split(":")[-1]


def slots_now():
    screen = j("screen")
    if screen.get("slots"):
        return screen["slots"], screen
    inv = j("inventory")
    return inv.get("hotbar", []) + inv.get("main", []), screen


def slot_item(n):
    slots, _ = slots_now()
    for s in slots:
        if s.get("slot") == n:
            return norm(s.get("item"))
    return None


def find_slot(item):
    slots, _ = slots_now()
    for s in slots:
        if norm(s.get("item")) == norm(item) and s.get("slot", 999) < 300:
            return s["slot"]
    return None


def empty_player_slot():
    slots, _ = slots_now()
    for s in slots:
        n = s.get("slot", 999)
        if 9 <= n <= 35 and not s.get("item"):
            return n
    return None


def move(src, dst):
    j("click-slot", str(src))
    j("click-slot", str(dst))


def counts():
    inv = j("inventory")
    c = inv.get("counts") or {}
    if isinstance(c, dict):
        return {norm(k): v for k, v in c.items()}
    return {norm(e.get("item")): e.get("count") for e in c}


def back_to_game():
    """Mods -> Done lands on Options, not the game; unwind every open screen."""
    for _ in range(5):
        state = j("state")
        if state.get("screen") == "playing" and not state.get("paused"):
            return True
        soft("close", lambda: j("close"))
        soft("resume", lambda: j("resume"))
    state = j("state")
    log(f"back_to_game: screen={state.get('screen')} paused={state.get('paused')}")
    return state.get("screen") == "playing"


def furnace_open():
    slots, screen = slots_now()
    return any(s.get("slot") == 300 for s in slots), screen.get("screen")


def open_furnace(pos):
    x, y, z = pos
    back_to_game()
    j("fill", str(x), str(y), str(z), str(x), str(y + 1), str(z), "air")
    j("setblock", str(x), str(y), str(z), "furnace")
    j("interact", str(x), str(y), str(z))
    ok, label = furnace_open()
    if not ok:
        j("interact", str(x), str(y), str(z), "up")
        ok, label = furnace_open()
    log(f"furnace at {pos}: open={ok} screen={label}")
    return ok


def test_recipe(src_item, want, pos, index):
    log(f"\n[{index}] {src_item} -> {want or '(nothing)'}")
    ok, _ = furnace_open()
    if not ok:
        back_to_game()
        j("interact", str(pos[0]), str(pos[1]), str(pos[2]))
    j("give", src_item, "1")
    # Snapshot after the give: the input must be present to measure it being consumed.
    before = counts()
    src = find_slot(src_item)
    if src is None:
        return {"input": src_item, "expected": want, "pass": False, "why": "give did not land in inventory"}
    log(f"  {src_item} in slot {src}; before counts: {want}={before.get(norm(want), 0)}")
    move(src, 300)
    loaded = slot_item(300)
    log(f"  furnace input slot 300 = {loaded}")
    if loaded != norm(src_item):
        return {"input": src_item, "expected": want, "pass": False, "why": f"input slot holds {loaded}"}

    if slot_item(301) is None:
        j("give", "coal", "64")
        fuel = find_slot("coal")
        move(fuel, 301)
        log(f"  fuel slot 301 = {slot_item(301)}")

    shot = OUT / f"shot-{index}-{src_item}-cooking.png"
    soft("screenshot", lambda: j("screenshot", str(shot)))
    j("wait", str(COOK_TICKS), timeout=120)
    got = slot_item(302)
    log(f"  after {COOK_TICKS} ticks: output slot 302 = {got}, input slot 300 = {slot_item(300)}")
    shot2 = OUT / f"shot-{index}-{src_item}-result.png"
    soft("screenshot", lambda: j("screenshot", str(shot2)))

    result = {"input": src_item, "expected": want, "output": got, "pass": got == norm(want) if want else got is None}

    # Take the output (or the uncooked input) back out so the next test starts clean.
    take = 302 if got else 300
    landing = empty_player_slot()
    if landing is not None:
        move(take, landing)
    after = counts()
    if want:
        gained = after.get(norm(want), 0) - before.get(norm(want), 0)
        spent = before.get(norm(src_item), 0) - after.get(norm(src_item), 0)
        result["gained"] = gained
        result["spent"] = spent
        result["pass"] = result["pass"] and gained == 1 and spent == 1
        log(f"  inventory delta: +{gained} {want}, -{spent} {src_item}")
    else:
        result["pass"] = got is None
        log(f"  control: output stayed {got} (expected None)")
    log(f"  {'PASS' if result['pass'] else 'FAIL'}")
    return result


def main():
    report = {"mod": "salvage", "version": "1.0.0", "recipes": [], "mods_screen": None}
    log("launching offscreen creative world...")
    launch = ctl(
        "launch", "--game", str(GAME), "--world", "SalvageSmoke", "--creative", "--offscreen",
        "--wait", "--render-distance", "6", "--resources", str(RESOURCES), timeout=420,
    )
    (OUT / "launch.txt").write_text(launch, encoding="utf-8")
    log("launch ok")
    try:
        soft("wait-ready", lambda: j("wait-ready", "120", timeout=150))
        soft("resume", lambda: j("resume"))

        j("options", "mods")
        ui = j("ui")
        (OUT / "ui-mods.json").write_text(json.dumps(ui, indent=2), encoding="utf-8")
        labels = [w.get("label", "") for w in ui.get("widgets", [])]
        report["mods_screen"] = labels
        log("mods screen: " + " | ".join(labels))
        salvage = [l for l in labels if l.lower().startswith("salvage")]
        report["salvage_listed"] = bool(salvage)
        report["salvage_on"] = any(": ON" in l for l in salvage)
        j("click-button", "Done")
        back_to_game()

        state = j("state")
        px, py, pz = state["player"]["block_pos"]
        pos = (px + 2, py, pz)
        log(f"player block {state['player']['block_pos']}; furnace target {pos}")
        if not open_furnace(pos):
            report["fatal"] = "could not open a furnace menu"
            return report

        for i, (src, want) in enumerate(RECIPES, start=1):
            report["recipes"].append(test_recipe(src, want, pos, i))
        report["recipes"].append(test_recipe(CONTROL, None, pos, len(RECIPES) + 1))

        soft("close", lambda: j("close"))
        report["events"] = soft("events", lambda: j("events"))
    finally:
        soft("quit", lambda: j("quit", timeout=90))
        passed = sum(1 for r in report["recipes"] if r.get("pass"))
        report["summary"] = f"{passed}/{len(report['recipes'])} checks passed"
        (OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        log("\n=== " + report["summary"] + " ===")
        LOG.close()


if __name__ == "__main__":
    main()