# Historical Backtest — Grounding Swarm Predictions

Every prediction thesis claims a historical pattern. This file grounds those claims
against actual data, including cases where the pattern FAILED.

## PRED-0001: SPY BEAR (-5% to -10%, 3m)
### Thesis pattern: CAPE >35 + oil shock → negative equity returns

**Supporting evidence:**
| Period | CAPE | Oil shock? | S&P 500 3m return | S&P 500 12m return |
|--------|------|------------|-------------------|--------------------|
| 1973 Q4 | ~18 | Yes (embargo) | -12% | -40% |
| 1990 Q3 | ~17 | Yes (Gulf War) | -14% | -20% |
| 2000 Q1 | ~44 | No | -2% | -13% |
| 2008 Q3 | ~22 | Yes (oil spike) | -29% | -43% |

**Counterevidence (where pattern failed):**
| Period | CAPE | Oil shock? | S&P 500 3m return | Note |
|--------|------|------------|-------------------|------|
| 1979 Q2 | ~10 | Yes (Iran revolution) | +5% | Stocks rose despite oil shock |
| 2021 Q4 | ~38 | No | -5% then +15% | High CAPE but V-shaped recovery |
| 1997 Q4 | ~35 | No | +12% | High CAPE, 3 more years of bull run |

**Honest base rate:** CAPE >35 sample is TINY (n=3 periods: 1929, 1997-2000, 2021+).
Oil shock + any CAPE: 3 of 4 times negative at 3m (75%). But 1979 was positive.
Combined CAPE >35 + oil shock: n=0 (never happened before). This is a NOVEL regime.
**Calibration adjustment:** Confidence 0.60 may be correct — we're extrapolating from
small samples into a novel combination.

Sources: Shiller CAPE data (multpl.com), S&P 500 historical (macrotrends.net),
Hamilton 2011 "Historical Oil Shocks" (UCSD)

---

## PRED-0002: XLE BULL (+5% to +15%, 3m)
### Thesis pattern: Energy sector outperforms during supply-driven oil shocks

**Supporting evidence:**
| Period | Oil driver | XLE/Energy 3m | Broad market 3m |
|--------|-----------|---------------|-----------------|
| 2022 Q1 | Russia-Ukraine supply | +24% | -5% |
| 2026 Q1 (current) | Iran/Hormuz supply | +22% YTD | flat |

**Counterevidence (CRITICAL):**
| Period | Oil driver | XLE/Energy 3m | Note |
|--------|-----------|---------------|------|
| 2008 Q3-Q4 | Demand destruction | **-66%** | Oil spike then collapse; XLE peaked May 2008 at $91 → $35 by early 2009 |
| 2020 Q1 | Demand collapse | **-50%** | COVID demand destruction destroyed energy sector |
| 2014-2015 | Supply glut (shale) | -30% | Supply-side but in reverse |

**Key distinction:** Supply shocks (embargo, Hormuz) vs demand-driven oil spikes behave
DIFFERENTLY for energy stocks. 2022 Russia-Ukraine = supply shock = XLE +24%.
2008 = demand-driven spike then demand destruction = XLE -66%.
Current situation: SUPPLY shock (Hormuz closure). But if it triggers recession via
stagflation → demand destruction → energy crashes too (2008 pattern).
**Risk the thesis underweights:** Recession turns supply shock into demand destruction.
**Calibration adjustment:** Confidence 0.65 may be too high. If recession probability >30%,
the 2008 analog dominates. Suggest 0.55.

Sources: XLE historical (stockanalysis.com), oil shock taxonomy (Hamilton, UCSD),
Russia-Ukraine energy impact (IEA 2022)

---

## PRED-0003: TLT BULL (+3% to +8%, 1m)
### Thesis pattern: Flight to safety during equity drawdowns

**Supporting evidence:**
| Period | SPY drawdown | TLT 1m return | Mechanism |
|--------|-------------|---------------|-----------|
| 2020 Mar | -34% | **+20%** | Classic flight to safety; Fed cut to 0% |
| 2018 Dec | -19% | +6% | Rate pause expectations |
| 2011 Aug | -16% | +12% | S&P downgrade → Treasury rally (paradox) |

**Counterevidence (CRITICAL — this is where the thesis is weakest):**
| Period | SPY drawdown | TLT return | Note |
|--------|-------------|------------|------|
| 2022 | -25% | **-31%** | Stocks AND bonds fell together. Inflation killed the hedge. |
| 1970s stagflation | multiple drawdowns | bonds lost 40%+ real | Stagflation = worst environment for bonds |

**The 2022 lesson is devastating for this prediction.** When inflation is the PRIMARY
driver (not growth fear), bonds do NOT rally during equity selloffs. The stock-bond
correlation flips positive. TLT lost HALF its value from Jan 2022 to Oct 2023.

Current situation: OIL-DRIVEN STAGFLATION. This is closer to 2022 than to 2020.
The 10Y yield is RISING (4.39%) despite equity weakness — this means the flight-to-safety
mechanism is NOT working. This is a bearish signal for TLT, not bullish.

**Calibration adjustment:** Original confidence 0.55 is likely TOO HIGH given that:
(1) current regime resembles 2022 more than 2020, (2) yields are rising not falling,
(3) stagflation is bonds' worst-case scenario. Honest confidence: 0.40.
This prediction may be WRONG. The backtest says so.

Sources: TLT historical (morningstar.com), stock-bond correlation research (AQR 2022),
1970s bond bear market (Dimson, Marsh & Staunton)

---

## PRED-0004: GLD BULL (+5% to +12%, 3m)
### Thesis pattern: Gold outperforms during stagflation

**Supporting evidence (STRONGEST of all predictions):**
| Period | Regime | Gold annual return | S&P 500 annual return |
|--------|--------|-------------------|-----------------------|
| 1973-1979 | Stagflation | **+35%/yr** | -1%/yr |
| 1979-1980 | Peak stagflation | **+120%** | +18% |
| All stagflation periods | Avg | **+19.16%/yr** | mixed |
| 2020-2024 | Geopolitical + inflation | +65% total | +45% total |

**Counterevidence:**
| Period | Regime | Gold return | Note |
|--------|--------|-------------|------|
| 2022 Mar-Oct | Rate hikes | **-20%** | Fed hiking killed gold despite inflation |
| 2013 | Taper tantrum | -28% | Strong dollar + rate expectations crushed gold |
| 1981-2000 | Disinflation | -50% real | Gold's 20-year bear market |

**Key nuance:** Gold loves inflation but HATES rate hikes + strong dollar.
If the Fed responds aggressively to stagflation (like Volcker 1980), gold crashes.
If the Fed is PARALYZED (can't hike because recession, can't cut because inflation),
gold rallies. Current Fed: paralyzed (stagflation bind). This favors gold.

Central bank gold buying is an additional structural tailwind (BIS data: 2022-2025
record buying by China, India, Turkey, Poland).

**Calibration adjustment:** Confidence 0.70 is supported by historical base rates.
Multiple independent drivers (stagflation + geopolitical + central bank buying).
Biggest risk: surprise Fed hawkishness (Volcker redux). Currently unlikely.

Sources: CME Group gold/stagflation analysis, World Gold Council data,
BIS central bank reserve diversification reports

---

## PRED-0005: QQQ BEAR (-8% to -15%, 3m)
### Thesis pattern: Tech underperforms during rate rises + valuation compression

**Supporting evidence:**
| Period | 10Y yield move | QQQ drawdown | CAPE level |
|--------|---------------|-------------|------------|
| 2000-2002 | flat to down | **-83%** | ~44 |
| 2022 | +2.5% (0→4.5%) | **-33%** | ~35 |
| 2018 Q4 | +0.5% | -23% | ~30 |

**Counterevidence:**
| Period | 10Y yield move | QQQ return | Note |
|--------|---------------|-----------|------|
| 2023-2024 | high but stable | **+55%** | AI narrative overcame rate headwind |
| 2016-2017 | rising (+1%) | +33% | Tax cut expectations dominated |

**Key distinction:** QQQ is extremely sensitive to the NARRATIVE driver.
When a compelling growth story exists (AI 2023-24, internet 1998-99), valuation
doesn't matter until it suddenly does. Current narrative: AI BIFURCATING
(infrastructure up, software down). This is the beginning of discrimination,
not the beginning of a new bull narrative.

**QQQ max drawdown is 83%** — the left tail is much fatter than SPY.
Current forward P/E ~34 is elevated but not extreme by post-2020 standards.

**Calibration adjustment:** Confidence 0.60 is reasonable. The 2023-24 counterexample
shows that narrative can override rates for extended periods. But the current narrative
is weakening, not strengthening.

Sources: Nasdaq historical (nasdaq.com), QQQ drawdown data (portfolioslab.com),
Fed funds rate history (FRED)

---

## PRED-0006: BTC BULL (+15% to +30%, 3m)
### Thesis pattern: Bitcoin decorrelates from risk assets during sovereign/currency-stress events

**Supporting evidence:**
| Period | Macro regime | BTC 3m return | SPY 3m return | Decorrelated? |
|--------|-------------|---------------|---------------|---------------|
| 2020 Q2-Q4 | Massive fiscal expansion | +170% | +20% | YES — BTC outperformed 8x |
| 2023 Q1 | SVB banking crisis | +70% | +7% | YES — BTC rallied on bank-distrust |
| 2024 Q1 | ETF approval + halving | +65% | +10% | Partial — both rallied but BTC 6x |

**Counterevidence (CRITICAL):**
| Period | Macro regime | BTC 3m return | Note |
|--------|-------------|---------------|------|
| 2022 Q2 | Fed hikes + risk-off | **-58%** | BTC correlated perfectly with QQQ; "digital gold" thesis failed |
| 2021 Q2 | China mining ban | -40% | Regulatory risk crushed BTC specifically |
| 2018 Q4 | Crypto winter | -45% | Internal crypto-market dynamics dominated macro |

**Key distinction:** BTC decorrelates during FISCAL crises (banking, sovereign debt, currency)
but RE-correlates during MONETARY TIGHTENING crises (Fed hiking). Current: Fed is ON HOLD (3.5-3.75%),
not hiking. This favors decorrelation.
**Calibration:** 0.55. The decorrelation thesis is sound for current regime (fiscal stress, not
monetary tightening). But BTC is volatile enough that a -20% drawdown within any 3m period
is structurally probable regardless of thesis.

Sources: Bitcoin historical (coingecko.com), BTC-SPY correlation studies (Arcane Research),
SVB banking crisis impact (CoinDesk), Fed rates (FRED)

---

## PRED-0007: DXY BEAR (-3% to -7%, 3m)
### Thesis pattern: Dollar weakens when Fed is on hold during stagflation

**Supporting evidence:**
| Period | Fed stance | DXY 3m change | Macro regime |
|--------|-----------|---------------|--------------|
| 1977-1978 | On hold during inflation | -8% | Pre-Volcker stagflation |
| 2004 Q1 | Low rates, fiscal deficit | -5% | Iraq war spending + trade deficit |
| 2011 Q3 | Operation Twist (easing) | -4% | Post-crisis, fiscal expansion |

**Counterevidence:**
| Period | Fed stance | DXY change | Note |
|--------|-----------|------------|------|
| 2022 | Aggressive hiking | **+15%** | Rate differential drove massive DXY rally |
| 2014-2015 | Tapering → hiking | +25% | Dollar strengthened on relative tightening |
| Gulf War 1991 | Mixed | +3% | Short-term safe-haven bid for USD during conflict |

**Key distinction:** DXY movement is driven primarily by RATE DIFFERENTIALS, not safe-haven flows.
When Fed hikes (2022, 2014), DXY rallies regardless of geopolitics. When Fed holds or eases
(1977, 2004, 2011), DXY weakens. Current: Fed ON HOLD at 3.5-3.75%, projecting one cut in 2026.
ECB and others may hold or cut less, narrowing differential.
**Risk:** If Hormuz crisis triggers USD repatriation (foreign holders selling assets for USD),
short-term rally possible. But medium-term, fiscal deficit expansion from war spending is USD-negative.
**Calibration:** 0.60. Rate differential argument is strong; timing risk from safe-haven flows.

Sources: DXY historical (tradingview.com), Fed funds rate (FRED), Rate differentials (BIS)

---

## PRED-0008: VIX BULL (spike to 35-45, 3m)
### Thesis pattern: VIX underprices tail risk during escalating military conflicts

**Supporting evidence:**
| Period | Trigger | VIX pre-event | VIX peak | Days to peak |
|--------|---------|--------------|----------|--------------|
| 2022 Feb-Mar | Russia-Ukraine invasion | 20 | 36 | 14 |
| 2020 Feb-Mar | COVID pandemic | 15 | 82 | 30 |
| 2011 Aug | US debt downgrade | 18 | 48 | 7 |
| 2008 Sep-Oct | Lehman Brothers | 25 | 80 | 30 |

**Counterevidence:**
| Period | Trigger | VIX pre | VIX peak | Note |
|--------|---------|---------|----------|------|
| 2003 Iraq War | US invasion begins | 28 | 34 | VIX was already elevated; spike was modest |
| 2019 Iran tensions | Soleimani assassination | 14 | 19 | Brief spike, quick decay — crisis contained |
| 2014 Crimea | Russia annexation | 14 | 22 | Modest — crisis didn't escalate to supply disruption |

**Pattern:** VIX spikes correlate with ECONOMIC MECHANISM of crisis, not geopolitical intensity.
2022 Russia-Ukraine spiked VIX to 36 because of energy supply disruption. 2019 Soleimani had
minimal VIX impact because no economic mechanism beyond brief oil spike.
Current: Hormuz closure is 5x the supply disruption of Russia-Ukraine. Economic mechanism is present
and escalating. VIX at 27 prices in ~1.7% daily moves, but 10mbpd supply loss is unprecedented.
**Calibration:** 0.50. Timing VIX spikes is hard. Thesis is that VIX UNDERPRICES the current
tail risk, but the spike could come from any catalyst — escalation, recession signal, or earnings miss.

Sources: VIX historical (CBOE), Conflict-VIX studies (IMF WP), Oil supply disruption history (IEA)

---

## Backtest Summary

| Pred | Historical support | Historical failure cases | Honest confidence | Original |
|------|-------------------|------------------------|-------------------|----------|
| PRED-0001 SPY BEAR | 3/4 oil shock periods bearish | 1979 positive; CAPE>35+oil is n=0 | 0.60 | 0.60 |
| PRED-0002 XLE BULL | Supply shocks bullish (2022) | 2008 demand destruction -66% | **0.55** | 0.65 |
| PRED-0003 TLT BULL | Flight to safety works 3/4 | **2022 stagflation: -31%** | **0.40** | 0.55 |
| PRED-0004 GLD BULL | Stagflation gold +19%/yr | 2022 Fed hikes -20% | 0.70 | 0.70 |
| PRED-0005 QQQ BEAR | Rate rise + high CAPE = drawdown | 2023-24 AI narrative override | 0.60 | 0.60 |
| PRED-0006 BTC BULL | Decorrelates in fiscal crises | **2022: -58% correlated with QQQ** | 0.55 | 0.55 |
| PRED-0007 DXY BEAR | Weakens when Fed on hold + deficit | 2022 DXY +15% on rate diff | 0.60 | 0.60 |
| PRED-0008 VIX BULL | Economic-mechanism crises spike VIX | 2003 Iraq: modest spike despite war | 0.50 | 0.50 |

**Portfolio-level note:** 8 predictions, mean confidence 0.56. Directional bias: 5 bearish (SPY, QQQ, DXY)
or inflation-hedge (GLD, BTC, XLE, VIX). Only XLE is bullish on a non-inflation asset. This portfolio
is HEAVILY positioned for stagflation. If a peace deal reopens Hormuz, most predictions flip.
That concentrated exposure is itself a risk — the Sanhedrin unanimity pattern (L-1289) applies
to our OWN predictions.
