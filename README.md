# WNBA-fantasy-auction-draft-tool
This repository is an active work in progress.

To use the current iteration of this app:
1. Set config options in auction.py.
2. launch app `python auction.py wnba2025_projections.csv`. This loads the app with ESPN's per game projections for their top 100 WNBA players in 2025.

## Getting player auction value
1. Compute projected fantasy score
   
   $ProjFPG_i = \sum_{c\in cats} w_c \times stat_{i,c}$
   
   $ProjFPS_i = ProjFPG_i \times EstGames_i$

3. Define a "replacement-level" baseline
   
     $VORP_i = ProjFPS_i - R_{pos(i)}$
   
5. Map VORP to dollar values

     $S = \sum_{i \in top N}max(0, VORP_i)$
   
     $Value_i = 100 \times \frac{max(0, VORP_i)}{S}$
   
7. Dynamically update budget constraint

     $BidLimit_i = B_{rem} \times \frac{max(0, VORP_i}{S_{rem}}$
   
8. Endogenously account for risk and positional scarcity
      * Discount VORP by injury history
      * Account for positional scarcity

Roadmap
1. Add "bench" player drafting.
2. Clean-up namespace
