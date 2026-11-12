"""In-game verification of the Salvage content mod.

Launches a throwaway offscreen creative world whose game home holds a copy of
the installed .hmod files, then smelts one item per recipe in a real furnace
and reads the output slot back. The two crafting recipes are checked at a real
crafting table. Player data is never touched.
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

# Smelting recipes: (input, expected output, cooking ticks, expected count).
# Vanilla already recycles iron and golden horse armour in a furnace (one
# nugget), and a content mod cannot override a vanilla cooking recipe, so the
# metal horse armours break down at the crafting table instead.
RECIPES = [
    ("leather_helmet", "leather", 200, 1),
    ("leather_chestplate", "leather", 200, 1),
    ("leather_leggings", "leather", 200, 1),
    ("leather_boots", "leather", 200, 1),
    ("leather_horse_armor", "leather", 200, 1),
    ("saddle", "leather", 200, 1),
    ("wooden_sword", "charcoal", 200, 1),
    ("wooden_shovel", "charcoal", 200, 1),
    ("wooden_pickaxe", "charcoal", 200, 1),
    ("wooden_axe", "charcoal", 200, 1),
    ("wooden_hoe", "charcoal", 200, 1),
    ("diamond_sword", "diamond", 400, 1),
    ("diamond_pickaxe", "diamond", 400, 1),
    ("diamond_axe", "diamond", 400, 1),
    ("diamond_shovel", "diamond", 400, 1),
    ("diamond_hoe", "diamond", 400, 1),
    ("stone_sword", "cobblestone", 100, 2),
    ("stone_shovel", "cobblestone", 100, 2),
    ("stone_pickaxe", "cobblestone", 100, 2),
    ("stone_axe", "cobblestone", 100, 2),
    ("stone_hoe", "cobblestone", 100, 2),
    ("turtle_helmet", "turtle_scute", 200, 1),
    ("nautilus_shell", "turtle_scute", 200, 1),
    ("elytra", "phantom_membrane", 400, 1),
]

# Crafting-table recipes: (input, expected output, expected count).
CRAFTING = [
    ("bow", "string", 2),
    ("fishing_rod", "string", 2),
    ("iron_horse_armor", "iron_nugget", 3),
    ("golden_horse_armor", "gold_nugget", 3),
    ("diamond_horse_armor", "diamond", 3),
]

# No smelting recipe exists for this in vanilla or in the mod: it must NOT cook.
# A stick: diamond_sword would not do, the mod has its own 400-tick recipe for it.
CONTROL = "stick"
COOK_TICKS = 260  # recipe cookingtime is 200; 400-tick recipes get their own

# Crafting table grid slot ids are 100 + row*3 + col; the result is slot 200.
GRID = [100, 101, 102, 103, 104, 105, 106, 107, 108]
RESULT = 200

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


def slot_stack(n):
    """(item id, stack size) of a slot."""
    slots, _ = slots_now()
    for s in slots:
        if s.get("slot") == n:
            return norm(s.get("item")), s.get("count", 0)
    return None, 0


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
    if src is None:
        raise RuntimeError(f"move: source slot is None (dst={dst})")
    j("click-slot", str(src))
    j("click-slot", str(dst))


def counts():
    inv = j("inventory")
    c = inv.get("counts") or {}
    if isinstance(c, dict):
        return {norm(k): v for k, v in c.items()}
    return {norm(e.get("item")): e.get("count") for e in c}


def clear_inventory():
    """Each test leaves its output item in the player's inventory, so after a
    few dozen the inventory is full and there is nowhere to put the next
    output. /clear wipes it between tests."""
    try:
        j("command", "clear @s")
        return True
    except Exception as exc:
        log(f"  ! clear failed: {exc}")
        return False


def wait_for_item(item, tries=30, ticks=2):
    """The give command returns before the stack lands in the inventory.
    Poll the slots until the item shows up (or give up)."""
    for _ in range(tries):
        slot = find_slot(item)
        if slot is not None:
            return slot
        j("wait", str(ticks))
    return None


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


# --------------------------------------------------------------------------
# Furnace
# --------------------------------------------------------------------------

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


def test_recipe(src_item, want, pos, index, cook_ticks=None, want_count=1):
    ticks = cook_ticks or COOK_TICKS
    wait_ticks = ticks + 60
    log(f"\n[{index}] {src_item} -> {want} x{want_count} (cookingtime {ticks})")
    # Start from an empty inventory: earlier tests' outputs would fill it.
    clear_inventory()
    ok, _ = furnace_open()
    if not ok:
        back_to_game()
        j("interact", str(pos[0]), str(pos[1]), str(pos[2]))
    # Empty the output slot: a leftover from an earlier test would be read as
    # this test's result.
    if slot_item(302):
        landing = empty_player_slot()
        if landing is None:
            clear_inventory()
            landing = empty_player_slot()
        if landing is not None:
            move(302, landing)
    try:
        j("give", src_item, "1")
    except Exception as exc:
        return {"input": src_item, "expected": want, "pass": False, "why": f"give failed: {exc}"}
    src = wait_for_item(src_item)
    if src is None:
        return {"input": src_item, "expected": want, "pass": False, "why": "give did not land in inventory"}
    # Snapshot after the give landed: the input must be present to measure it being consumed.
    before = counts()
    log(f"  {src_item} in slot {src}; before counts: {want}={before.get(norm(want), 0)}")
    move(src, 300)
    loaded = slot_item(300)
    log(f"  furnace input slot 300 = {loaded}")
    if loaded != norm(src_item):
        return {"input": src_item, "expected": want, "pass": False, "why": f"input slot holds {loaded}"}

    if slot_item(301) is None:
        try:
            j("give", "coal", "64")
        except Exception as exc:
            return {"input": src_item, "expected": want, "pass": False,
                    "why": f"fuel give failed: {exc}"}
        fuel = wait_for_item("coal")
        if fuel is None:
            return {"input": src_item, "expected": want, "pass": False,
                    "why": "fuel (coal) did not land in inventory"}
        move(fuel, 301)
        log(f"  fuel slot 301 = {slot_item(301)}")

    shot = OUT / f"shot-{index}-{src_item}-cooking.png"
    soft("screenshot", lambda: j("screenshot", str(shot), timeout=20))
    # Wait for the result rather than a fixed tick count: the furnace may still
    # have to ignite, and a fixed wait flakes on the first test. The result
    # lands a tick after the input is consumed, so never stop early.
    max_wait = ticks + 240
    waited = 0
    got, got_count = slot_stack(302)
    while got is None and waited < max_wait:
        j("wait", "20")
        waited += 20
        got, got_count = slot_stack(302)
    log(f"  after {waited} ticks (needed {ticks}): output slot 302 = {got} x{got_count}, input slot 300 = {slot_item(300)}")
    shot2 = OUT / f"shot-{index}-{src_item}-result.png"
    soft("screenshot", lambda: j("screenshot", str(shot2), timeout=20))

    result = {"input": src_item, "expected": want, "expected_count": want_count,
              "output": got, "output_count": got_count,
              "pass": got == norm(want) and got_count == want_count}

    # Take the output (or the uncooked input) back out so the next test starts clean.
    take = 302 if got else 300
    landing = empty_player_slot()
    if landing is None:
        # The inventory filled up: wipe it and try again.
        clear_inventory()
        landing = empty_player_slot()
    if landing is not None:
        move(take, landing)
    else:
        log(f"  ! no free player slot; left {take} in the furnace")
    after = counts()
    if want:
        gained = after.get(norm(want), 0) - before.get(norm(want), 0)
        spent = before.get(norm(src_item), 0) - after.get(norm(src_item), 0)
        result["gained"] = gained
        result["spent"] = spent
        result["pass"] = result["pass"] and gained == want_count and spent == 1
        log(f"  inventory delta: +{gained} {want}, -{spent} {src_item}")
    else:
        result["pass"] = got is None
        log(f"  control: output stayed {got} (expected None)")
    log(f"  {'PASS' if result['pass'] else 'FAIL'}")
    return result


# --------------------------------------------------------------------------
# Crafting table
# --------------------------------------------------------------------------

def table_open():
    slots, screen = slots_now()
    return any(s.get("slot") == RESULT for s in slots), screen.get("screen")


def open_table(pos):
    x, y, z = pos
    back_to_game()
    j("fill", str(x), str(y), str(z), str(x), str(y + 1), str(z), "air")
    j("setblock", str(x), str(y), str(z), "crafting_table")
    j("interact", str(x), str(y), str(z))
    ok, label = table_open()
    if not ok:
        j("interact", str(x), str(y), str(z), "up")
        ok, label = table_open()
    log(f"crafting table at {pos}: open={ok} screen={label}")
    return ok


def clear_grid():
    for cell in GRID:
        if slot_item(cell):
            landing = empty_player_slot()
            if landing is None:
                return
            j("click-slot", str(cell))
            j("click-slot", str(landing))


def test_craft(src_item, want, want_count, index):
    log(f"\n[{index}] craft {src_item} -> {want} x{want_count}")
    clear_inventory()
    ok, label = table_open()
    if not ok:
        return {"input": src_item, "expected": want, "pass": False,
                "why": f"no crafting menu ({label})"}
    clear_grid()
    try:
        j("give", src_item, "1")
    except Exception as exc:
        return {"input": src_item, "expected": want, "pass": False, "why": f"give failed: {exc}"}
    src = wait_for_item(src_item)
    if src is None:
        return {"input": src_item, "expected": want, "pass": False,
                "why": "give did not land in inventory"}
    before = counts()
    j("click-slot", str(src))          # pick the item up
    j("click-slot", "100", "right")    # right-click places one into the grid
    j("wait", "5")
    log(f"  grid slot 100 = {slot_item(100)}; before counts: {want}={before.get(norm(want), 0)}")
    got, got_count = slot_stack(RESULT)
    log(f"  result slot {RESULT} = {got} x{got_count}")
    soft("screenshot", lambda: j("screenshot", str(OUT / f"shot-{index}-craft-{src_item}.png")))

    result = {"input": src_item, "expected": want, "expected_count": want_count,
              "output": got, "output_count": got_count,
              "pass": got == norm(want) and got_count == want_count}
    if not result["pass"]:
        clear_grid()
        log("  FAIL")
        return result

    # Take the result out, then measure the inventory delta.
    j("click-slot", str(RESULT))
    landing = empty_player_slot()
    if landing is None:
        clear_inventory()
        landing = empty_player_slot()
    if landing is not None:
        j("click-slot", str(landing))
    j("wait", "5")
    after = counts()
    gained = after.get(norm(want), 0) - before.get(norm(want), 0)
    spent = before.get(norm(src_item), 0) - after.get(norm(src_item), 0)
    result.update(gained=gained, spent=spent)
    result["pass"] = result["pass"] and gained == want_count and spent == 1
    clear_grid()
    log(f"  delta: +{gained} {want}, -{spent} {src_item}")
    log(f"  {'PASS' if result['pass'] else 'FAIL'}")
    return result


def test_craft_control(src_item, index):
    """An item no Salvage recipe takes: the result slot must stay empty."""
    log(f"\n[{index}] craft control: {src_item} -> nothing")
    clear_inventory()
    ok, label = table_open()
    if not ok:
        return {"input": src_item, "expected": None, "pass": False,
                "why": f"no crafting menu ({label})"}
    clear_grid()
    try:
        j("give", src_item, "1")
    except Exception as exc:
        return {"input": src_item, "expected": None, "pass": False, "why": f"give failed: {exc}"}
    src = wait_for_item(src_item)
    if src is None:
        return {"input": src_item, "expected": None, "pass": False,
                "why": "give did not land in inventory"}
    j("click-slot", str(src))
    j("click-slot", "100", "right")
    j("wait", "5")
    got, got_count = slot_stack(RESULT)
    log(f"  result slot {RESULT} = {got} x{got_count} (expected None)")
    clear_grid()
    log(f"  {'PASS' if got is None else 'FAIL'}")
    return {"input": src_item, "expected": None, "output": got, "pass": got is None}


def main():
    report = {"mod": "salvage", "version": "1.2.0", "recipes": [], "mods_screen": None}
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
        log(f"player block {state['player']['block_pos']}; target {pos}")

        # --- crafting table recipes first ---
        if open_table(pos):
            report["recipes"].append(test_craft_control("stick", 0))
            for i, (src, want, count) in enumerate(CRAFTING, start=1):
                report["recipes"].append(test_craft(src, want, count, i))
            soft("close", lambda: j("close"))
        else:
            report["fatal"] = "could not open a crafting table menu"
            return report

        # --- then the furnace recipes ---
        if not open_furnace(pos):
            report["fatal"] = "could not open a furnace menu"
            return report
        for i, (src, want, ticks, count) in enumerate(RECIPES, start=len(CRAFTING) + 1):
            report["recipes"].append(test_recipe(src, want, pos, i, ticks, count))
        report["recipes"].append(test_recipe(CONTROL, None, pos, len(RECIPES) + len(CRAFTING) + 1))

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