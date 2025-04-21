#!/usr/bin/env python3
import sys
import pandas as pd

# ─── CONFIG ───────────────────────────────────────────────────────────────────
STARTER_SLOTS  = {'G': 2, 'F': 3}   # your starter position slots
UTIL_SLOTS     = 1                          # number of utility slots
STARTER_BUDGET = 90                      # dollars reserved for starters
SEASON_GAMES   = 40                        # expected games in season
# ────────────────────────────────────────────────────────────────────────────────

# ─── STEP 1: Compute fantasy scores ──────────────────────────────────────────────
def compute_fantasy_scores(df: pd.DataFrame, season_games: int = SEASON_GAMES) -> pd.DataFrame:
    """
    Adds FPG and FPS columns using league weights:
      1*3P + 1*TRB + 1*AST + 2*STL + 2*BLK –1*TOV + 1*PTS
    """
    df['FPG'] = (
          df['3P']
        + df['TRB']
        + df['AST']
        + 2 * df['STL']
        + 2 * df['BLK']
        - 1 * df['TOV']
        + df['PTS']
    )
    df['FPS'] = df['FPG'] * season_games
    return df

# ─── STEP 2: Simplify positions ─────────────────────────────────────────────────
def simplify_position(pos_str: str) -> str:
    pos = str(pos_str).upper()
    if 'G' in pos: return 'G'
    if 'F' in pos: return 'F'
    if 'C' in pos: return 'C'
    return None

# ─── STEP 3: Dynamic replacement levels ─────────────────────────────────────────
def compute_replacement_levels_dynamic(df: pd.DataFrame, slots_rem: dict, util_rem: int) -> dict:
    R = {}
    # positional slots
    for p, n in slots_rem.items():
        pool = df[df['POS_SIMPLE'] == p]
        if n > 0 and len(pool) >= n:
            R[p] = pool.nlargest(n, 'FPS')['FPS'].iloc[-1]
        else:
            R[p] = 0.0
    # utility cutoff as total slots
    cutoff = sum(slots_rem.values()) + util_rem
    if cutoff > 0 and len(df) >= cutoff:
        R['Util'] = df.nlargest(cutoff, 'FPS')['FPS'].iloc[-1]
    else:
        R['Util'] = 0.0
    return R

# ─── STEP 4: Compute VORP ──────────────────────────────────────────────────────
def compute_vorp(df: pd.DataFrame, R: dict) -> pd.DataFrame:
    df['VORP_POS']  = df.apply(lambda r: max(0.0, r.FPS - R.get(r.POS_SIMPLE, 0.0)), axis=1)
    df['VORP_UTIL'] = df['FPS'].apply(lambda f: max(0.0, f - R['Util']))
    df['VORP']      = df[['VORP_POS','VORP_UTIL']].max(axis=1)
    return df

# ─── STEP 5: Update bid ceilings dynamically ─────────────────────────────────────
def update_ceilings(df: pd.DataFrame, slots_rem: dict, util_rem: int, budget_rem: float) -> pd.DataFrame:
    # 1) Recompute replacement levels & VORP
    R = compute_replacement_levels_dynamic(df, slots_rem, util_rem)
    df = compute_vorp(df, R)

    # 2) Determine which players fill slots
    picks = []
    for p, n in slots_rem.items():
        if n > 0:
            picks += df[df['POS_SIMPLE']==p].nlargest(n, 'VORP')['Player'].tolist()
    if util_rem > 0:
        rem = df[~df['Player'].isin(picks)]
        picks += rem.nlargest(util_rem, 'VORP_UTIL')['Player'].tolist()

    # 3) Sum VORP of picks
    S = df.set_index('Player').loc[picks, 'VORP'].sum()

    # 4) Compute new ceilings
    df['Ceiling'] = df['VORP'].apply(
        lambda v: round(budget_rem * v / S, 2) if S > 0 else 0.0
    )
    return df

# ─── MAIN & INTERACTIVE LOOP ──────────────────────────────────────────────────
def main(csv_path):
    df = pd.read_csv(csv_path)
    raw_cols = ['3P','TRB','AST','STL','BLK','TOV','PTS','G']
    # Compute fantasy if needed
    if 'FPS' not in df.columns:
        missing = [c for c in raw_cols if c not in df.columns]
        if missing:
            print(f"Error: CSV must include per-game columns: {', '.join(raw_cols)}", file=sys.stderr)
            sys.exit(1)
        df = compute_fantasy_scores(df)
    # Check position column
    if 'Pos' not in df.columns:
        print("Error: CSV must include 'Pos' column.", file=sys.stderr)
        sys.exit(1)
    df['POS_SIMPLE'] = df['Pos'].apply(simplify_position)

    # initialize state
    budget_rem = STARTER_BUDGET
    slots_rem = dict(STARTER_SLOTS)
    util_rem = UTIL_SLOTS
    df = update_ceilings(df, slots_rem, util_rem, budget_rem)

    print("""Enter commands:
  win <Name>,<price>   → you won a bid
  lost <Name>,<price>  → opponent won a bid
  lookup <Name>        → show current ceiling
  suggest              → show top candidates for each remaining starter slot
Blank to quit.""")

    while True:
        line = input("> ").strip()
        if not line:
            break
        parts = line.split(maxsplit=1)
        cmd = parts[0].lower()

        if cmd in ['win','lost'] and len(parts) == 2:
            detail = parts[1]
            if ',' not in detail:
                print("Format: win Name,price or lost Name,price")
                continue
            name_part, price_part = map(str.strip, detail.split(',',1))
            try:
                price = float(price_part)
            except ValueError:
                print("Invalid price.")
                continue
            matches = df[df['Player'].str.contains(name_part, case=False, regex=False)]
            if len(matches) == 0:
                print("No such player.")
                continue
            if len(matches) > 1:
                print("Multiple matches:")
                for p in matches['Player']:
                    print("  " + p)
                continue
            player = matches.iloc[0]
            if cmd == 'win':
                budget_rem -= price
                pos = player.POS_SIMPLE
                if slots_rem.get(pos,0) > 0:
                    slots_rem[pos] -= 1
                elif util_rem > 0:
                    util_rem -= 1
            # remove player and recalc
            df = df[df['Player'] != player['Player']]
            df = update_ceilings(df, slots_rem, util_rem, budget_rem)
            print(f"Budget: ${budget_rem:.2f}")

        elif cmd == 'lookup' and len(parts) == 2:
            q = parts[1]
            hits = df[df['Player'].str.contains(q, case=False, regex=False)]
            if hits.empty:
                print("No matches.")
            else:
                for _, r in hits.iterrows():
                    print(f"{r.Player:25s} → ${r.Ceiling:5.2f}")

        elif cmd == 'suggest':
            # Suggest top candidates per position
            print("Top candidates per position:")
            for p, n in slots_rem.items():
                if n > 0:
                    pool = df[df['POS_SIMPLE']==p]
                    top = pool.nlargest(n, 'Ceiling')
                    for _, r in top.iterrows():
                        print(f"  {p} slot: {r.Player:25s} → ${r.Ceiling:5.2f}")
            if util_rem > 0:
                print("  Util slot:")
                ut = df.nlargest(util_rem, 'Ceiling')
                for _, r in ut.iterrows():
                    print(f"    {r.Player:25s} → ${r.Ceiling:5.2f}")

        else:
            print("Commands: win, lost, lookup, suggest.")

    print("Good luck in your draft!")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python auction_values.py <per-game-csv>", file=sys.stderr)
        sys.exit(1)
    main(sys.argv[1])
