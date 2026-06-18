# App Atlas — operator notes

Developer/operator guide for the scripts in this directory. For the
*output* (the atlas itself) see
[`docs/research/app-atlas/README.md`](../../docs/research/app-atlas/README.md).

## APK sources (Phase A.2)

`apk_extractor.py` acquires each brand's APK from a priority chain. The
first source that yields a valid APK wins; any failure falls through:

1. **Google Play via [`apkeep`](https://github.com/EFForg/apkeep)** —
   the authoritative source (the real Play Store APK) and the only one
   that covers brands no mirror serves (notably **Škoda**).
2. **APKCombo** — XAPK from a fast CDN.
3. **Uptodown** — broadest mirror coverage.

apkeep is *strictly additive*: if it's not installed, not configured, or
the download fails (region-lock, rate-limit), extraction falls back to
the mirror chain exactly as before. Set `APKEEP_DISABLE=1` to skip it.

### Installing apkeep

- **CI (Linux):** handled by `app-atlas-builder.yml` (downloads the
  pinned `x86_64-unknown-linux-gnu` release binary to `/usr/local/bin`).
- **Local:** download the release binary for your platform from
  [apkeep releases](https://github.com/EFForg/apkeep/releases) and put it
  on `PATH` (or point `APKEEP_BIN` at it).

#### ⚠️ Windows: PE main-thread stack patch required

apkeep 1.0.0's `x86_64-pc-windows-msvc.exe` **crashes on the download
step** with `thread 'main' has overflowed its stack` — Windows reserves
only a 1 MB main-thread stack (Linux gives 8 MB) and the Play delivery
protobuf decode overflows it. `--list-versions` works; downloads don't.
`RUST_MIN_STACK` does *not* help (it only affects spawned threads).

Fix — bump the reserved stack in the PE header in-place (no rebuild):

```bash
py scripts/app_atlas/patch_pe_stack.py /path/to/apkeep.exe 67108864   # 1 MB -> 64 MB
```

Keep a `.orig` backup of the binary first. After patching, the Windows
download path works. The Linux/CI binary is unaffected.

### Google Play credentials

apkeep needs a Play account. Credential precedence (env vars, first set
wins):

| Vars | apkeep flag | Notes |
|---|---|---|
| `APKEEP_EMAIL` + `APKEEP_AAS_TOKEN` | `-t` | Long-lived. **Best for CI** (store as repo secrets). |
| `APKEEP_EMAIL` + `APKEEP_AUTH_TOKEN` | `--auth-token` | `ya29.*` token, short-lived. |
| *(none set)* | `--auth-token` | Anonymous token auto-fetched from the **Aurora Store dispenser** (`APKEEP_DISPENSER_URL`, default `https://auroraoss.com/api/auth`). Turnkey but rate-limited and may be IP-blocked — fine locally, unreliable from CI runner IPs. |

The anonymous dispenser is the default (zero-config) path. The fetched
token is memoized per run, so a 7-brand run hits the dispenser once.

To mint a long-lived `aas_token` for CI, see apkeep's
[Google Play usage doc](https://github.com/EFForg/apkeep/blob/master/USAGE-google-play.md)
(`apkeep -e you@gmail.com --oauth-token oauth2_4/...`).

## Manual runs

```bash
# Version-polling only (Phase A.1):
python build_atlas.py

# Single brand, full APK extraction (downloads + apktool decode + grep):
python build_atlas.py --brand skoda --with-apk-extraction

# Rebuild the whole apk-cache from scratch (all brands):
python build_atlas.py --force-extract
```

Local extraction also needs `apktool` (+ Java) on `PATH`; `ripgrep`
(`rg`) is used when present, else it falls back to `grep`.
