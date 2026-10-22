---
pretty_name: PlayEnd
license: cc-by-nc-4.0
language:
- en
- fr
task_categories:
- tabular-classification
tags:
- timeseries
- tabular
- video-games
- event-detection
- change-point-detection
annotations_creators:
- machine-generated
- expert-generated
source_datasets:
- original
size_categories:
- 1K<n<10K
configs:
- config_name: observations
  data_files: data/observations.csv
  default: true
- config_name: sessions
  data_files: data/sessions.csv
- config_name: units
  data_files: data/units.csv
- config_name: time_segments
  data_files: data/time_segments.csv
- config_name: splits
  data_files: data/splits.csv
- config_name: features
  data_files: data/features.csv
---

# PlayEnd

PlayEnd is a dataset for detecting when a game played on a console starts and when it ends. It was recorded during
68 hours of real play in a gaming room in Kinshasa, Democratic Republic of the Congo. A Raspberry Pi took a screenshot
of the console output at random intervals of 10 to 45 seconds. A large vision-language model then described each of the
8,871 screenshots: which game is on screen, the score, the clock, the period, how many players or lives are left, and
so on. We marked the screenshot that proves the end of each game, the screenshot where each game starts, and how the
time on screen is billed: per game, by time, or not at all. Every end and every start was checked by hand.
The 25 sessions cover 17 game titles, among them EA Sports FC, Mortal Kombat 1, Fortnite and Beach Buggy Racing 2,
with 301 ends and 308 starts in total.

The data is meant for training and testing models that read a stream of screen descriptions and decide when a game
starts or is over. A gaming room needs this to charge its customers per game. The screenshots are not part of this
release.

Dataset link: [https://doi.org/10.5281/zenodo.23159321](https://doi.org/10.5281/zenodo.23159321) (Zenodo, all versions,
always the latest). This version, 1.1: doi:10.5281/zenodo.23376730.

Data card authors: Brummel D. Mayano (owner), Jordan F. Masakuna (contributor).

## Authorship

PlayEnd was made at the Department of Mathematics, Statistics and Computer Science, University of Kinshasa,
Kinshasa, Democratic Republic of the Congo, as part of a master's thesis.

| Author | ORCID |
|---|---|
| Brummel D. Mayano | [0009-0008-5433-5259](https://orcid.org/0009-0008-5433-5259) |
| Jordan F. Masakuna | [0000-0001-6165-8402](https://orcid.org/0000-0001-6165-8402) |

Brummel D. Mayano recorded the sessions, set the annotation and counting rules, did the human validation and maintains
the dataset.

Contact: Brummel D. Mayano, brummelmayano@gmail.com.

## Dataset overview

The data subjects are video games as they appear on screen, not people. Players appear only through the names that
some games write on screen (squad lists, kill feeds); these names were replaced by pseudonyms (see
[Human and other sensitive attributes](#human-and-other-sensitive-attributes)).

| | |
|---|---|
| Sessions | 25 (one per start of the capture device), from 3 to 1,184 screenshots each |
| Screenshots | 8,871, one row each in `observations.csv` |
| Recorded time | 68.1 hours (2 minutes to 9.1 hours per session) |
| Interval between screenshots | median 27.7 s; 90 % between 11.9 and 43.5 s |
| Units (games played) | 308: 301 with an observed end, 7 still running when the capture stopped |
| Time-billed segments | 21 (open worlds, missions, training modes, Fortnite creative islands, the map and dialogues of a story mode) |
| Labelled intervals | 8,846, of which 8,796 can be used for training (50 masked as uncertain) |
| Ends in usable intervals | 289 for 8,796, about 1 for 30; the other 12 ends fall on masked intervals |
| Starts | 308, one per unit; 4 on the first screenshot of a session |

Each row of `observations.csv` holds what was read on one screenshot: the game, the phase of play, the score, the
clock, the period, the progress and result, the counters that measure what is left before the end, the secondary
timers and the participants. The row also keeps the complete description as JSON and says which model wrote it. Three
columns are the labels: `unit_end_boundary` (a game ended between the previous screenshot and this one),
`unit_start_boundary` (a game starts on this screenshot) and `billing_mode` (`per_game`, `time_based` or
`not_billed`).

How the screenshots and ends are spread over the game titles:

| Game family | Screenshots | Ends | Time-billed segments | Median length of a unit |
|---|---:|---:|---:|---:|
| EA Sports FC | 2,751 | 77 | 0 | 12.3 min |
| Mortal Kombat 1 | 1,256 | 78 | 9 | 2.1 min |
| no game (console home, settings, black screen) | 1,170 | 0 | 0 | |
| Fortnite | 1,159 | 27 | 2 | 14.2 min |
| Call of Duty: Warzone | 613 | 12 | 0 | 11.1 min |
| Dragon Ball Sparking! ZERO | 459 | 21 | 0 | 6.6 min |
| Genshin Impact | 304 | 0 | 2 | |
| Beach Buggy Racing 2 | 230 | 27 | 0 | 2.3 min |
| Red Dead Redemption 2 | 185 | 0 | 2 | |
| Tekken 8 | 173 | 32 | 0 | 1.1 min |
| EA Sports UFC 5 | 127 | 12 | 0 | 2.3 min |
| Naruto Storm Connections | 119 | 7 | 0 | 2.4 min |
| Assassin's Creed Origins | 105 | 0 | 2 | |
| God of War | 95 | 0 | 1 | |
| J-Stars Victory VS+ | 68 | 4 | 3 | 3.8 min |
| Dragon Ball FighterZ | 30 | 2 | 0 | 2.9 min |
| Brawlhalla | 15 | 1 | 0 | 2.0 min |
| Demon Slayer | 12 | 1 | 0 | 2.4 min |

The length of a unit is measured from its first to its last screenshot, so it is shorter than the real game by up to
one capture interval at each end.

Screens outside play are frequent. By phase, 5,521 screenshots are in play, 1,472 on menus, 689 before a game, 396
after a game, 283 paused, 158 loading, 101 between rounds, and 251 have an unknown phase: screens with nothing readable
on them, and close-ups of fighting games with neither a HUD nor any text. By billing mode, 4,789 screenshots are billed
per game, 1,417 by time and 2,665 not at all.

Many fields are empty on purpose: a value is left empty when the screen does not show it or when it cannot be read.
The score is empty on 69 % of the rows, the main clock on 76 %, the participants on 52 %.

### Version and maintenance

This is version 1.1. It is maintained by Brummel D. Mayano. Corrections are published as new versions on Zenodo, each
with its own DOI, and the version history is kept in this card. The next planned release is a separate set of the
screenshots themselves, with player names blurred and access granted on request for non-commercial research.

Version 1.0 was published on 5 October 2026 (doi:10.5281/zenodo.23159322). Version 1.1 adds the start of each game
(`unit_start_boundary` and `started_unit_id` in `observations.csv`, three start columns in `units.csv`) and comes out
of a second review by the first author, described under [Validation](#validation). That review and the rounds after it
changed 750 observations and the end, game or billing label of 92 rows. Six games were added (308 instead of 302): a
fight restarted in Mortal Kombat 1, three matches that had been counted as one (Tekken, UFC 5, Naruto Storm
Connections), and two fights of the story mode of J-Stars Victory VS+, which are games like those of its free-fight
mode; 18 other ends moved by one or a few screenshots. The console home screen no longer carries the title of the
highlighted game, which moves 391 screenshots from Fortnite and Brawlhalla to the "no game" row. The `annotator` and
`corrector` columns now give the model name alone. Results obtained on the two versions are close but not equal;
please say which version you used.

## Example data points

A typical row, during a football match (selected columns):

| Column | Value |
|---|---|
| `session_id`, `frame_id` | `session_110294230cc748c29baea627984009e2`, 48 |
| `t_s`, `delta_t_s` | 1336.889997511, 35.140389570 |
| `game_title`, `game_family` | EA Sports FC 26, EA Sports FC |
| `phase`, `screen_type` | active, gameplay |
| `score_a`, `score_b`, `score_type` | 0, 0, goals |
| `clock_display`, `clock_seconds` | 6:44, 404 |
| `participant_a`, `participant_b` | Paris SG, Manchester City |
| `counters_status` | none |
| `unit_end_boundary`, `boundary_applicable` | 0, true |
| `unit_start_boundary` | 0 (the match started on screenshot 47) |
| `current_unit_id`, `billing_mode` | U03, per_game |

Less typical rows are common enough to matter. In session `110294`, screenshot 651 already shows a new Mortal Kombat 1
fight (`current_unit_id = U23`). It is the first screenshot proving that the previous fight is over, so it carries
`unit_end_boundary = 1` and `ended_unit_id = U22`; it is also where the new fight starts (`unit_start_boundary = 1`,
`started_unit_id = U23`). 225 of the 301 ends have no end screen in the data and are proved in this way, by what comes
next: a menu, the console home screen, a new game.

In Mortal Kombat 1 training, the clock shows `∞` and there is no round marker; these screenshots are billed by time
(`billing_mode = time_based`) and there is no end to detect. On a Fortnite waiting island before the battle bus, 94
players may be listed as remaining, yet no game has started (`billing_mode = not_billed`). The first screenshot of each
session has no end label, because no screenshot comes before it (`unit_end_boundary` empty,
`boundary_applicable = false`); it still carries a start when a game is already running on it. Black screens and
console menus keep their place in the sequence, with most fields empty, and a model has to learn that nothing ends
there.

## Motivations and intended use

In a gaming room in Kinshasa, customers pay for each game they play. Counting games by hand is error-prone, and the
games differ: a football match ends with a final whistle, a fight with a knockout screen, a battle royale when the
player is eliminated or wins. We built this dataset for a counter that works across games. In the planned system, a
small vision-language model on the capture device describes each screenshot, and a detector reads the descriptions in
order and signals each game. Our first detectors signalled the end of each game; we now count a game at its start,
once several screenshots confirm it, and the start labels were added for this. Billing rules are applied after that,
outside the model.

Suitable uses:

- training and evaluating models that detect game starts and ends in a sequence of screen descriptions, with
  irregular time steps and many missing values;
- research on event and change-point detection in sequences of structured observations;
- studying how errors in machine-generated descriptions affect a downstream detector.

Uses we advise against:

- identifying, tracking or profiling the players or the customers of the room;
- billing customers automatically without human review: a false end makes a customer pay for one game too many,
  which is the worst error for this application;
- assuming that results transfer to other rooms, consoles or games without testing on them first;
- commercial use, which the license does not allow.

## Access, retention and deletion

The dataset is open under the Creative Commons Attribution-NonCommercial 4.0 license (CC BY-NC 4.0). The license
covers our work only: the observations, labels and documentation. The games, their names and their on-screen content
belong to their publishers. The official copy is on Zenodo (doi:10.5281/zenodo.23159321, which always leads to the
latest version). The file `croissant.json` describes the same package for software, in the Croissant format
(specification 1.1, with the Responsible AI vocabulary): files and their SHA-256, columns and types, keys between
tables, labels and folds.

If someone recognises themselves in the data and wants something removed, they can write to the contact address above.
The rows concerned will be removed or pseudonymised again in the next version.

## Provenance

A Raspberry Pi Zero 2 W was connected to the HDMI output of the console through a MacroSilicon MS2109 USB capture
device. During each session it saved full JPEG screenshots (1280 x 720 pixels, quality 90) at random intervals drawn
between 10 and 45 seconds, with the time of reception from the system's monotonic clock. The capture program, its
settings and its SHA-256 hash are recorded for each session (`sessions.csv`, `capture_program_sha256`).

The recordings were made in September 2026. The device had neither a battery-backed clock nor a network connection,
so its calendar clock restarted at the time of its last shutdown each time it was switched on. The calendar dates
stored by the device are therefore wrong, the real days cannot be recovered, and the gap between two sessions is
unknown. The monotonic clock, which counts from the start of the device, is reliable within a session. For these
reasons the dataset contains no calendar time: `t_s` counts seconds from the first screenshot of each session.

The customers of the room were told about the capture and agreed orally. Some of them agreed to play games that were
rare in the first recordings so that these games would be represented.

### Collection criteria

Sessions with at least one screenshot were kept. One session recorded no screenshot and is not included. Of eight
sessions recorded later, we annotated only the one that adds rarely played games (`fdb79549`, with Beach Buggy Racing 2,
J-Stars Victory VS+, God of War and Assassin's Creed Origins). The other seven were left out: three are empty, one has
five screenshots, and three are mostly EA Sports FC and Fortnite, which were already the most frequent titles.

### Relationship to the source

The source is the screen, but the published rows are descriptions of the screen written by a model, not pixel data.
This makes the dataset small and free of personal images, and it matches what the counter receives on the device. The
cost is that every value depends on the reading of the model: a misread score or a wrong game title becomes part of
the input. The human validation below measures how often this happens.

## Human and other sensitive attributes

The data contains no images, faces or voices, but three kinds of information could relate to people.

Some games write the names of real players on screen: Fortnite and Warzone squads, kill feeds, spectator banners, the
PlayStation sign-in screen. We replaced 82 real names with stable pseudonyms (`player_001`, `player_002`...) in every
table and in `observation_json`. A name is matched as a whole word without regard to case, so a player shown as
`Rex_77` in a squad list and as `REX_77` in a kill feed (an invented name) gets the same pseudonym. Names of game
characters and teams (Scorpion, Paris SG) are kept. The authors keep the list of real names privately. Under the
European guidelines on pseudonymisation, pseudonymised data still count as personal data while such a list exists, and
we handle the list with that in mind.

Calendar times would show when customers were in the room; none are published. The room is in Kinshasa and is not
named.

## Extended use

The observations follow a written contract (version 2.1) that applies to any game, so other recordings described with
the same contract can be added. Recordings from other rooms should keep their sessions separate and should not be
mixed into the folds below without saying so.

When sampling, keep whole sessions and keep their order. Removing screenshots from inside a session changes the time
steps that a sequence model sees; if that is the aim (to simulate a slower capture, for instance), recompute
`delta_t_s` from `t_s` afterwards.

### Use in machine learning

Each session is one sequence, ordered by `frame_id`. A recurrent model should start each session from a fresh state
and should never carry its state from one session to the next: the sessions are separate starts of the device, and
the time between them is unknown.

The end label of a row describes the interval between the previous screenshot and this one, and the end is placed on
the first screenshot that proves it. This is the information an online detector has: it needs to see the new
screenshot before it can say that something changed. `boundary_applicable` tells which rows to use in the loss and in
the evaluation (false on the first row of each session and on the 50 intervals judged uncertain, 12 of which contain
an end whose exact place could not be settled).

The start label is placed on the first gameplay screenshot of a game whose HUD can be read (score, clock, lap, place,
lives, players left). It marks the first observation of the new segment, as change points do in the benchmark of
van den Burg and Williams ("An Evaluation of Change Point Detection Algorithms", 2020). A game already running on
the first screenshot of a session starts there; this happens 4 times. The start is known on every row, so
`boundary_applicable` does not apply to it.

The classes are very unbalanced (289 ends among 8,796 usable intervals, about 1 for 30; 308 starts among 8,871
screenshots), and the titles are unequally represented. Accuracy is not a useful measure here: a model that never
predicts an end is right on 96.7 % of the usable intervals and counts no game at all.

`splits.csv` assigns each session to one of five folds. A session never appears in two folds. The folds are those of
version 1.0, kept so that results stay comparable. They were balanced on the number of ends and of screenshots
together, as far as whole sessions allow; one session (`f0067594`) holds 23 % of
all ends, so the balance cannot be exact.

| Fold | Sessions | Screenshots | Ends |
|---:|---:|---:|---:|
| 1 | 3 | 1,234 | 79 |
| 2 | 5 | 1,843 | 57 |
| 3 | 5 | 2,218 | 45 |
| 4 | 6 | 1,859 | 58 |
| 5 | 6 | 1,717 | 62 |

With only 25 sessions, we suggest using these folds to tune a model (for example the decision threshold) and holding
out one session at a time for the final evaluation, so that each model is trained on as much data as possible.

A minimal way to read the data with pandas:

```python
import pandas as pd

obs = pd.read_csv("data/observations.csv")
obs = obs.merge(pd.read_csv("data/splits.csv"), on="session_id")

for session_id, sequence in obs.groupby("session_id"):
    sequence = sequence.sort_values("frame_id")
    target = sequence["unit_end_boundary"]   # empty (NaN) on the first screenshot
    usable = sequence["boundary_applicable"]  # False where the target must be ignored
    starts = sequence["unit_start_boundary"]  # 1 on the screenshot where a game starts
```

`features.csv` has the same rows, in the same order, encoded as the 262 inputs of our GRU (encoding version 4.0,
described in `dictionary/feature_spec.json`).

## Transformations

A script in the project's code repository (`python -m playend.dataset.export`) produces the published files from the
original annotations, then reads them back to check keys, times, labels and pseudonyms.

`t_s` is the time since the first screenshot of the session and `delta_t_s` the time since the previous one. Both come
from the monotonic clock in nanoseconds and are written with nine decimals, so differences between rows are exact.
Player names are replaced as described above.

When an observation was corrected after its first reading, the published row uses the corrected version and names the
correction in `corrected_by`; 4,701 rows come from such corrections. The first readings are kept in the project
archive and are never overwritten. The fields used for counting are copied from the JSON description into their own
columns, while lists that can be long (all participants, all secondary timers) stay complete in `observation_json`.
The billing labels were recorded in French (`partie`, `temps`, `hors_jeu`) and are published as `per_game`,
`time_based` and `not_billed`.

`features.csv` applies a fixed transform to each numeric value, sign(x) log(1 + |x|), adds a 0/1 column saying
whether the value is known, and turns categories into one-hot columns. No statistic is learned from the data, so
nothing leaks from held-out sessions. The features are computed from the published rows alone and are identical to
those computed on the private data with the real names.

## Annotations and labeling

The screen descriptions are machine-generated. Two large vision-language models acted as annotators, one after the
other. GPT-6 Luna, used in Codex, made the first readings of 2,085 screenshots; Claude Opus 5.5, used in Claude Code,
read the other 6,786 and made every later correction. The model that read a screenshot is named in the `annotator`
column, and the model that corrected it in `corrector`; both columns give the name of the model alone.

Both models followed the same written observation contract (version 2.0, later 2.1), which has rules for each game.
The round markers of a fighting game go into the score. The goal minutes shown after a goal are not the match clock. A
participant is recorded only if its name is written on screen, never guessed from a logo or a face. When a value could
not be read, it was left empty.

GPT-6 Luna read each screenshot at full size, and its lots were audited against the images afterwards. Claude Opus 5.5
read the score, the clock and the period of every screenshot it described on a zoomed crop of the score area, and
looked at the full screenshot for banners, menus and doubtful cases.

Version 2.1 added the counters that measure what is left before the end: players or teams remaining, lives, round
slots, series wins. The 3,049 screenshots first described in version 2.0 were read again for these counters, and all
rows now follow version 2.1. A counter is empty with `counters_status = unknown` only when the game hides it at that
moment (189 rows).

Claude Opus 5.5 first placed the ends of games and the time-billed segments. The counting rules were set by the first
author:

- a game that is restarted or quit counts as a complete game;
- a game still running when the capture stopped has no end;
- games and modes without an end (open worlds, missions, Mortal Kombat 1 training, Fortnite creative islands) are
  billed by time and have no end;
- Fortnite in split screen is one game, and a waiting island left before the battle bus is not a game;
- in Beach Buggy Racing 2 each race is a game;
- a simulated match (EA Sports FC career mode) is not counted;
- idle time, when a death screen or a menu stays on until the game is abandoned, is not billed;
- a game starts on its first gameplay screenshot whose HUD can be read, and a game already running when the capture
  starts begins on the first screenshot (added in version 1.1).

One more rule belongs to the billing step and does not change the labels: a game restarted or quit after less than
60 seconds of play (15 seconds for fighting games) is not charged, but its end is still marked.

The first author then checked every end and every time-billed segment by hand in a local tool showing the start of the
game, its last screenshot, the screenshot that proves the end and the one after it. For version 1.1, the starts were
placed by the written rule and checked in the same tool (see below).

## Validation

The human validation was done by the first author between 2 and 4 October 2026, on version 1.0. It covered all 295
ends, all 19 time-billed segments and a sample of 576 observations, drawn at about 5 % per game (at least 15 per game
when possible) and mostly from screenshots in play.

| Checked | Confirmed | Wrong | Doubtful |
|---|---:|---:|---:|
| Ends of games | 282 | 5 | 8 |
| Time-billed segments | 19 | 0 | 0 |
| Sampled observations | 540 | 16 | 20 |

The wrong ends were corrected before release, by corrections stored apart from the original annotations. In the
observation sample, most problems were not misread values. 16 concerned participant names, most of them inferred from a
logo or a face instead of being written on screen, and 12 the race position in split screen; both were handled by
changing the convention. Two periods were wrong, and the other doubtful cases were questions about conventions (one
of them on a game title taken from neighbouring screenshots). None concerned the score or the clock. After this, 302
screenshots whose participant names might not have been written on screen were read again, and 185 of them were
corrected. The observations themselves were not all checked one by one: their `observation_review_status` stays
`proposed_pending_human_review`, while every label is `human_verified`.

A second review was done on 13 October 2026, for version 1.1, after we looked screenshot by screenshot at the ends
that our first detectors missed. Each proposal was shown with its screenshots in the same local tool, and the first
author accepted or refused it.

| Proposals | Accepted | Refused |
|---|---:|---:|
| Ends to move or add | 18 | 1 |
| Found by the start counter | 5 | 1 |
| Observations to correct | 19 (42 rows) | 2 |
| Annotation conventions | 15 (550 rows) | 1 |
| Starts not on the first screenshot of a game | 19 | 6 |

The corrected observations were mostly screens read as black although they could be read, one of them a result
screen; result screens left unmarked; and two round knock-outs in Tekken noted as the result of the match. The
conventions settle screens that the annotating model had noted in different ways from one session to another: the
console home screen, after-match menus, close-ups without a HUD, spectator mode in Fortnite. The refused convention
would have kept the fighter names of selection screens as participants; the first author ruled the other way, since
players can still change fighters at that point, and the names were removed from 61 rows.

A third round came from the start counter (see below). It flagged a missing boundary in Tekken, in UFC 5 and in Naruto
Storm Connections, a misread score in Mortal Kombat 1, the screen where the stage is chosen, and the story mode of
J-Stars, which we bill by time. The first author accepted the boundaries, the score and the stage screen (11 rows),
and refused to keep the story mode at time billing: its fights are games.

A fourth round, on 14 October 2026, came from the screen classifier of our small model. Its predictions on
screenshots it had not been trained on disagreed with the annotation on 213 screenshots, between gameplay and cutscene.
Most were errors of the classifier, but the annotating model had noted some kinds of screenshots both ways: close-ups
of EA Sports FC with the score banner on screen, special attacks of fighting games with the health bars on screen,
match views without the banner. The first author accepted four conventions: a HUD of the match on screen means
gameplay, and no HUD and no game text means cutscene, with the phase left unknown when the screenshot does not show
it. We read again every cutscene of the games billed per game and every EA Sports FC gameplay screenshot without a
value, and corrected 56 rows; 10 of them broke conventions accepted the day before (menus over a match, selection
screens). No label changed. The first author then chose to read the score banner that EA Sports FC shows at the
bottom of the screen at kickoff and after a goal, which the annotating model had always left aside: 26 rows gained
a score, and three wide kickoff views without any HUD became cutscenes. The kickoff banner of one session showed that a new match had begun one screenshot after the previous one
was last seen, and that three screenshots read as menus between matches were in fact the pause menu of the new
match. The first author accepted the four boundary changes that followed: one end and three starts moved, and one
screenshot joined its game.

For the six starts that the first author refused, the first author placed them: four games already running on the
first screenshot of a session start there, and two Beach Buggy Racing 2 races start on their first screenshot. The
other 278 starts fall on the first screenshot of a game, which had been checked with the game itself.

## Sampling methods

The screenshots are a sample in time of each session, taken at random intervals so that the capture does not lock onto
the rhythm of any game. The sessions are not a random sample of the room's activity: they depend on when the device
was running, and some customers chose rarely played titles on purpose. The share of each title in the data therefore
says little about what is played in the room.

## Known applications and benchmarks

PlayEnd was built for the multi-game counter of the first author's master's thesis, which extends the single-game
counter of Mayano, Yan-Mol and Masakuna (2025). No model results are published with this version. For evaluation we
recommend precision (to protect customers from false charges), recall (for the room's revenue) and false detections
per hour of play, reported per game family, and counting a detection one screenshot late as correct. The same measures
apply to starts and to ends.

## Terms of art

| Term | Meaning in this card |
|---|---|
| Session | One continuous recording, from one start of the capture device to its stop. |
| Unit | One game played: a football match, a fight, a race, a battle royale round. Identified by `unit_id` within its session. |
| End | The interval in which a unit ends, placed on the first screenshot that proves it. |
| Start | The first screenshot of a unit on which play and a readable HUD are seen. |
| Time-billed segment | A stretch of play in a game or mode with no end, billed by its duration. |
| Observation | The description of one screenshot written by a vision-language model under the observation contract. |
| HUD | The information drawn over the game image: score, clock, counters, names. |
| Correction | A later reading that replaces an observation; the first reading is kept. |

## Reflections on the data

The dataset comes from one room, recorded in September 2026, and from the games played there. EA Sports FC, Fortnite
and Mortal Kombat 1 account for 58 % of the screenshots, while five titles have fewer than 100. Results on rare titles
rest on very few games.

Most ends have no end screen in the data (225 of 301). With a screenshot every 28 seconds on average, the final
whistle or the knockout is often missed, and the end is established by the next thing seen, such as a menu or a new
kickoff at 0-0. This is the hard part of the task. It is also where a detector can be wrong in a way that costs
customers money.

Starts are easier to see. On 239 of the 308 starts, the screenshot already shows the opening values: 0-0, lap 1, or
60 players or more left in a battle royale. Most of the others are games without a score (Dragon Ball Sparking! ZERO,
EA Sports UFC 5) or Warzone games first seen after the landing. A detector can therefore look for the opening of a
game instead of its end, and use the end only as a second sign.

The observations are model outputs. In our validation sample the score and the clock had no error, while names and
split-screen views had several. On some cutscenes and loading screens, the game title was taken from the neighbouring
screenshots rather than from the screenshot alone; we left these values as they are.

Recorded lengths are coarse. A unit seen on a single screenshot has a measured length of zero, and short restarts can
fall entirely between two screenshots.

## Citation

If you use PlayEnd, please cite the dataset and the paper it builds on:

```bibtex
@misc{mayano2026playend,
  author = {Mayano, Brummel D. and Masakuna, Jordan F.},
  title  = {{PlayEnd}: Console Play Sessions from a Kinshasa Gaming Room for End-of-Game Detection},
  year   = {2026},
  version = {1.1},
  publisher = {Zenodo},
  doi    = {10.5281/zenodo.23159321},
  note   = {Department of Mathematics, Statistics and Computer Science, University of Kinshasa}
}

@article{mayano2025counter,
  author  = {Mayano, Brummel D. and Yan-Mol, L. L. and Masakuna, Jordan F.},
  title   = {Intelligent Match Counter in a Video Game Arena},
  journal = {IEEE Access},
  volume  = {13},
  pages   = {32320--32328},
  year    = {2025},
  doi     = {10.1109/ACCESS.2025.3542425}
}
```
