# The Rare Art of Football Greatness

**What This Is**: A data-driven look at how rare elite attacking production is in modern football  
**Dataset Window**: 2012-2025  
**The Big Question**: How rare is extraordinary attacking output, and who stands furthest above the field?

---

## The TL;DR

Using the current processed analysis data, Lionel Messi still comes out as the clearest statistical outlier.

- Messi's best season in the dataset is **2012**, with **1.70 goals + assists per 90 minutes**
- His career rate in the dataset is **1.36 G+A/90**, the highest among all qualifying attackers
- Cristiano Ronaldo, Kylian Mbappe, Erling Haaland, Luis Suarez, and Robert Lewandowski are also exceptional, but Messi remains well clear
- The report previously used older numbers. This version is aligned with the processed full-analysis data in `data/processed/`

Important context: the current processed data covers **2012-2025**, not 2005-2026.

---

## Where This Data Comes From

The analysis uses the cleaned and processed project datasets:

- **1,889,406 cleaned appearance records**
- **1,885,175 merged appearance/game/player records**
- **55,921 qualifying player-season records**
- **13,595 qualifying attacker-season records**
- **11,311 qualifying career records**
- **2,795 qualifying attacking career records**

Filtering rules:

- Season analysis includes player-seasons with **900+ minutes**
- Career analysis includes players with **3,000+ minutes**
- Attacker filtering is based on positions matching attacking labels such as `Attack`, `Forward`, `Centre-Forward`, `Winger`, `Second Striker`, `Left Winger`, and `Right Winger`

This means the "average" in this report is not the average footballer worldwide. It is the average among players who appear in the dataset, pass the minutes threshold, and are classified as attackers.

---

## By The Numbers: Single-Season Performance

For qualifying attacker seasons:

| The Stat | Current Value |
|----------|---------------|
| **Average G+A/90** | 0.476 |
| **Median G+A/90** | 0.447 |
| **Typical range, Q1-Q3** | 0.309 to 0.614 |
| **Best season in dataset** | 1.815 G+A/90, Claudio Pizarro 2012 |
| **Messi's best season** | 1.703 G+A/90, Lionel Messi 2012 |

**Plain English**: the median qualifying attacker produces about 0.45 goals plus assists per 90 minutes. The elite seasons are not just a little better; the best seasons are roughly 3 to 4 times the median output.

### Top Single Seasons

| Rank | Player | Season | G+A | Minutes | G+A/90 |
|------|--------|--------|-----|---------|--------|
| 1 | Claudio Pizarro | 2012 | 22 | 1,091 | 1.815 |
| 2 | Ricardo Pepi | 2024 | 20 | 1,054 | 1.708 |
| 3 | Lionel Messi | 2012 | 77 | 4,070 | 1.703 |
| 4 | Mario Gomez | 2012 | 23 | 1,216 | 1.702 |
| 5 | Sergio Aguero | 2013 | 40 | 2,165 | 1.663 |
| 6 | Lionel Messi | 2018 | 73 | 4,024 | 1.633 |
| 7 | Cristiano Ronaldo | 2014 | 84 | 4,641 | 1.629 |
| 8 | Luis Muriel | 2020 | 37 | 2,090 | 1.593 |
| 9 | Lionel Messi | 2014 | 89 | 5,061 | 1.583 |
| 10 | Luis Suarez | 2015 | 83 | 4,766 | 1.567 |

The highest raw rate belongs to Pizarro, but Messi's 2012 season is the strongest high-minute superstar season in the data: **77 combined goals and assists across 4,070 minutes**.

---

## How We Measure "Rare"

The analysis uses three related ideas:

**1. Z-score**

A z-score measures how many standard deviations a player is above or below the dataset average.

**2. Empirical rarity**

This asks: in the actual dataset, how many qualifying players matched or exceeded this number?

**3. Normal-model rarity**

This estimates rarity using a normal distribution. It is useful as a mathematical reference, but football performance is not perfectly normally distributed, especially at the extreme top end.

Because elite football output has a long right tail, empirical rarity is usually more trustworthy for player comparisons than the normal-model estimate.

---

## The Best Single Seasons: Elite Players Compared

### Lionel Messi - 2012

- **G+A/90**: 1.703
- **Goals + assists**: 77
- **Minutes**: 4,070
- **Empirical rarity**: about **1 in 6,798 attacker-seasons**
- **Normal-model rarity**: about **1 in 12.9 million**
- **Z-score**: 5.25 standard deviations above the season attacker mean

Messi's 2012 season is not the highest rate in the dataset, but it is the standout high-volume elite season.

### Cristiano Ronaldo - 2014

- **G+A/90**: 1.629
- **Goals + assists**: 84
- **Minutes**: 4,641
- **Best season rank**: #7 overall

Ronaldo's best season combines huge minutes with huge production. His rate is slightly below Messi's 2012 season, but his total G+A is higher.

### Erling Haaland - 2019

- **G+A/90**: 1.516
- **Goals + assists**: 28
- **Minutes**: 1,662

Haaland's best rate in the dataset comes from a smaller minutes sample than Messi or Ronaldo, but it still places him deep into elite territory.

### Robert Lewandowski - 2020

- **G+A/90**: 1.514
- **Goals + assists**: 57
- **Minutes**: 3,389

Lewandowski's 2020 season is one of the strongest high-minute striker seasons in the dataset.

### Luis Suarez - 2015

- **G+A/90**: 1.567
- **Goals + assists**: 83
- **Minutes**: 4,766

Suarez's 2015 season is ahead of Haaland and Lewandowski by rate, and it came on a very large minutes sample.

### Elite Best Seasons Summary

| Player | Best Season | G+A/90 |
|--------|-------------|--------|
| Lionel Messi | 2012 | 1.703 |
| Cristiano Ronaldo | 2014 | 1.629 |
| Luis Suarez | 2015 | 1.567 |
| Erling Haaland | 2019 | 1.516 |
| Robert Lewandowski | 2020 | 1.514 |

These elite seasons cluster around **1.51 to 1.70 G+A/90**, not 0.85 to 1.13 as the previous report stated.

---

## By The Numbers: Career Performance

For qualifying attacking careers:

| The Stat | Current Value |
|----------|---------------|
| **Average career G+A/90** | 0.463 |
| **Median career G+A/90** | 0.447 |
| **Best career G+A/90** | 1.360, Lionel Messi |
| **Players at 0.60+ career G+A/90** | 516 |
| **Players at 0.70+ career G+A/90** | 232 |
| **Players at 0.80+ career G+A/90** | 79 |
| **Players at 1.00+ career G+A/90** | 14 |

The earlier report said only 12 players reached 0.60+ career G+A/90. In the current processed data, that threshold is much less exclusive: **516 qualifying attackers** reach it. A more genuinely rare career threshold in this dataset is **1.00+ G+A/90**, reached by **14 players**.

---

## Career Tiers

These tiers use the current career dataset:

| Tier | Rule | Players | Average Rate |
|------|------|---------|--------------|
| **Legendary Elite** | 1.00+ G+A/90 | 14 | 1.113 |
| **World-Class** | 0.80 to 0.99 G+A/90 | 65 | 0.864 |
| **Elite Professional** | 0.60 to 0.79 G+A/90 | 437 | 0.681 |
| **Strong Professional** | 0.40 to 0.59 G+A/90 | 1,232 | 0.490 |
| **Role Player** | Below 0.40 G+A/90 | 1,047 | 0.307 |

The main lesson changes slightly: 0.60+ is very good, but it is not the tiny all-time group. The real separation starts around 0.80+, and the truly extreme career club is 1.00+.

---

## The Legends: Career Performance

### Messi - The Outlier

- **Career G+A/90**: 1.360
- **Rank**: #1
- **Period in dataset**: 2012 to 2025
- **Goals + assists**: 676
- **Minutes**: 44,740

Messi is the clear career leader. He is not just above average; he is more than five standard deviations above the career attacker mean.

### Kylian Mbappe - The Closest Challenger

- **Career G+A/90**: 1.204
- **Rank**: #2
- **Period in dataset**: 2015 to 2025
- **Goals + assists**: 438
- **Minutes**: 32,736

Mbappe ranks above Ronaldo and Haaland in the current career table.

### Cristiano Ronaldo - Elite Longevity

- **Career G+A/90**: 1.194
- **Rank**: #3
- **Period in dataset**: 2012 to 2022
- **Goals + assists**: 546
- **Minutes**: 41,150

Ronaldo remains one of the strongest career profiles in the dataset, combining volume and elite rate.

### Erling Haaland - The Modern Rate Monster

- **Career G+A/90**: 1.174
- **Rank**: #4
- **Period in dataset**: 2019 to 2025
- **Goals + assists**: 306
- **Minutes**: 23,456

Haaland's career is shorter than the older legends, but his rate is already historically high in this dataset.

### Luis Suarez - Peak And Volume

- **Career G+A/90**: 1.097
- **Rank**: #6
- **Period in dataset**: 2012 to 2021
- **Goals + assists**: 438
- **Minutes**: 35,950

Suarez's career rate is higher than Lewandowski's in the current processed data.

### Robert Lewandowski - The Reliable Elite

- **Career G+A/90**: 1.079
- **Rank**: #9
- **Period in dataset**: 2012 to 2025
- **Goals + assists**: 650
- **Minutes**: 54,203

Lewandowski has the largest minutes total among the top career players listed here and remains comfortably in the 1.00+ career elite group.

### Top 10 Career Attackers

| Rank | Player | Period | G+A | Minutes | G+A/90 |
|------|--------|--------|-----|---------|--------|
| 1 | Lionel Messi | 2012-2025 | 676 | 44,740 | 1.360 |
| 2 | Kylian Mbappe | 2015-2025 | 438 | 32,736 | 1.204 |
| 3 | Cristiano Ronaldo | 2012-2022 | 546 | 41,150 | 1.194 |
| 4 | Erling Haaland | 2019-2025 | 306 | 23,456 | 1.174 |
| 5 | Zlatan Ibrahimovic | 2012-2022 | 274 | 21,715 | 1.136 |
| 6 | Luis Suarez | 2012-2021 | 438 | 35,950 | 1.097 |
| 7 | Franculino | 2023-2025 | 58 | 4,788 | 1.090 |
| 8 | Sergio Aguero | 2012-2020 | 277 | 22,962 | 1.086 |
| 9 | Robert Lewandowski | 2012-2025 | 650 | 54,203 | 1.079 |
| 10 | Viktor Gyokeres | 2018-2025 | 132 | 11,071 | 1.073 |

---

## What We Actually Learned

### #1: The Average And Median Are Higher Than The Old Report Said

The old report listed a season average of 0.38 and a median of 0.30. The current processed data says:

- **Season mean**: 0.476
- **Season median**: 0.447
- **Career mean**: 0.463
- **Career median**: 0.447

So the baseline attacker in this processed dataset is more productive than the previous report suggested.

### #2: Elite Seasons Are Around 1.5+ G+A/90

The old report placed elite best seasons around 0.85 to 1.13. In the current analysis, the elite comparison group is around **1.51 to 1.70 G+A/90**.

That changes the scale of the story: the best players are not just 2 to 3 times the average. At their peaks, they can be roughly **3 to 4 times** the median qualifying attacker.

### #3: Messi Is Still The Career Outlier

The exact numbers changed, but the core conclusion did not: Messi is the strongest statistical profile in the dataset.

- His best season: **1.703 G+A/90**
- His career rate: **1.360 G+A/90**
- Career rank: **#1**
- Gap over #2 Mbappe: **0.156 G+A/90**
- Gap over #3 Ronaldo: **0.166 G+A/90**

At this level, those gaps are substantial.

### #4: Career Rarity Needs A Higher Threshold

The previous report treated 0.60+ career G+A/90 as a tiny legendary group. The current data says 516 attackers meet that mark.

Better thresholds for this dataset:

| Career Level | Players | Share |
|--------------|---------|-------|
| 0.60+ G+A/90 | 516 | 18.46% |
| 0.70+ G+A/90 | 232 | 8.30% |
| 0.80+ G+A/90 | 79 | 2.83% |
| 0.90+ G+A/90 | 29 | 1.04% |
| 1.00+ G+A/90 | 14 | 0.50% |
| 1.10+ G+A/90 | 5 | 0.18% |

In this version of the analysis, **1.00+ career G+A/90** is the cleaner "legendary elite" cutoff.

### #5: The Dataset Starts In 2012

The old report repeatedly described the analysis as 2005-2026. The processed analysis data currently runs from **2012 to 2025**.

That matters because some early Messi and Ronaldo seasons are outside the processed window. The results should be interpreted as a dataset-window analysis, not a complete career analysis from debut to retirement.

---

## Limitations

### Data Window

The current processed dataset covers **2012-2025**. It does not include the full 2005-2011 period that the old report referenced.

### 2025 Data May Be Incomplete

The processed data includes 2025, but depending on the source refresh timing, the latest season may be incomplete or still subject to updates.

### Position Classification

The attacker group depends on position labels in the player data. If a player is classified differently across sources, they may be included or excluded differently.

### Competition Context

The current rates are not adjusted for league strength, team strength, role, opponent quality, or competition type.

### Normal Distribution Assumption

Normal-model rarity becomes unstable at the extreme top end. Empirical rankings are more grounded for this dataset.

---

## The Simple Version

The report's previous numbers did not match the full analysis data. After recalculating from the processed files, the corrected headline is:

**Messi is still the rarest attacking profile in the dataset, but the actual scale is higher than the previous report stated. Elite peak seasons are around 1.5 to 1.7 G+A/90, Messi's career rate is 1.36 G+A/90, and the processed dataset covers 2012-2025.**

---

## Appendix: Current Method

1. Loaded cleaned processed data from `data/processed/`
2. Used `season_stats_cleaned.csv` for single-season analysis
3. Used `career_stats_cleaned.csv` for career analysis
4. Filtered attackers using attacking position labels
5. Applied minimum minutes thresholds:
   - 900+ minutes for season analysis
   - 3,000+ minutes for career analysis
6. Calculated goals plus assists per 90 minutes:

```text
G+A/90 = (goals + assists) / (minutes_played / 90)
```

7. Compared player rates against the relevant qualifying attacker distribution

---

**Updated**: 2026-07-09  
**Data Used**: Processed project data, 2012-2025  
**Method**: Python analysis with Pandas and SciPy  
**Bottom line**: The old report was out of sync; this version matches the current full-analysis data.
