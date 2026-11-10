"""Launch a throwaway offscreen Horizon and probe mod state + game commands.

Phase 1 of the Salvage in-game smoke test. Nothing touches real player data:
HORIZON_HOME / launcher / XDG dirs are fresh temp folders. Mods still load from
the install's horizon-mods/ folder next to the exe.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

INSTALL = Path(r"D:\CGRLabs\Horizon-Ecosystem\horizon-windows-x64")
CTL = INSTALL / "horizon-ctl.exe"
GAME = INSTALL / "horizon-client.exe"
RESOURCES = INSTALL / ".local" / "horizon-client" / "26.3"
OUT = Path(__file__).resolve().parent.parent / "target" / "smoke"
OUT.mkdir(parents=True, exist_ok=True)


def env_scratch():
    env = dict(os.environ)
    for var, name in (("HORIZON_HOME", "home"), ("HORIZON_LAUNCHER_HOME", "launcher"),
                      ("XDG_DATA_HOME", "data"), ("XDG_CONFIG_HOME", "config")):
        d = tempfile.mkdtemp(prefix=f"salvage-smoke-{name}-")
        env[var] = d
    return env


ENV = env_scratch()


def ctl(*args, timeout=180):
    # The game inherits our handles: never pipe, write to files (proof.py gotcha).
    out_path, err_path = OUT / "ctl.out", OUT / "ctl.err"
    with open(out_path, "wb") as out, open(err_path, "wb") as err:
        done = subprocess.run([str(CTL), *args], stdout=out, stderr=err,
                              env=ENV, timeout=timeout, cwd=str(INSTALL))
    text = out_path.read_text(encoding="utf-8", errors="replace")
    error = err_path.read_text(encoding="utf-8", errors="replace")
    if done.returncode != 0:
        raise SystemExit(f"horizon-ctl {' '.join(args)} failed ({done.returncode}): {(text or error).strip()}")
    return text


def main():
    print("launching offscreen creative world...", flush=True)
    launch = ctl("launch", "--game", str(GAME), "--world", "SalvageSmoke", "--creative",
                 "--offscreen", "--wait", "--render-distance", "6",
                 "--resources", str(RESOURCES), timeout=300)
    (OUT / "launch.txt").write_text(launch, encoding="utf-8")
    print("launch ok", flush=True)

    for name, args in (("status", ("status",)), ("state", ("state",)),
                       ("help-game", ("help", "--game")), ("options-mods", ("options", "mods"))):
        try:
            text = ctl(*args, timeout=60)
        except SystemExit as e:
            text = str(e)
        (OUT / f"{name}.txt").write_text(text, encoding="utf-8")
        print(f"--- {name} ---", flush=True)
        print(text[:1500], flush=True)

    try:
        ui = ctl("ui", timeout=60)
        (OUT / "ui-mods.txt").write_text(ui, encoding="utf-8")
        print("--- ui (mods screen) ---", flush=True)
        print(ui[:2000], flush=True)
    except SystemExit as e:
        print("ui failed:", e, flush=True)


if __name__ == "__main__":
    main()