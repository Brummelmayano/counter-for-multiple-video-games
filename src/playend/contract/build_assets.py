"""Regenerate the teacher prompt and the machine-readable contract files from the rule texts.

Run it after any change to timer_rules.txt, counter_rules.txt or the contract code:
    python -m playend.contract.build_assets
"""

import json
from pathlib import Path

from .contract import empty_observation, output_schema
from .temporal import feature_spec

HERE = Path(__file__).resolve().parent
PROMPT = HERE / "prompts" / "06_prompt_VLM_universel_COMPACT_STABLE_v1.txt"
PROMPT_BASE = HERE / "prompts" / "sources" / "06_before_secondary_timers.txt"


def teacher_prompt(template):
    """The 2.0 prompt with the current timer and counter rules and the JSON template put in place."""
    timers = (HERE / "timer_rules.txt").read_text()
    counters = (HERE / "counter_rules.txt").read_text()
    text = PROMPT_BASE.read_text()
    start, end = text.index("# 10. CLOCK / TIMER"), text.index("# 11.")
    text = text[:start] + "# 10. CLOCK / TIMER\n\n" + timers + "\n" + text[end:]
    start = text.index("# 13. RESULT")
    text = text[:start] + "# 12b. SECONDARY COUNTERS\n\n" + counters + "\n" + text[start:]
    start, end = text.index("# REQUIRED JSON SCHEMA"), text.index("FINAL CHECK BEFORE OUTPUT:")
    text = text[:start] + "# REQUIRED JSON SCHEMA\n\n" + template + "\n\n" + text[end:]
    heading = "OBSERVATION CONTRACT 2.1 — active revision (historical filename retained)\n\n"
    text = text.replace("ROLE\n", heading + "ROLE\n", 1)
    text = text.replace(
        "`score.additional_scores` is the ONLY field allowed to contain a variable JSON object, and only for directly "
        'visible auxiliary score information. Prefer keys:\n`"games"`, `"sets"`, `"tiebreak"`, `"point_labels"`.',
        '`score.additional_scores` is null or an object with exactly the four keys `"games"`, `"sets"`, `"tiebreak"`, '
        '`"point_labels"`. Each value is a two-element A/B array of number/text/null. Use [null,null] for an '
        "unobserved pair; include only directly visible values. No other keys are permitted in contract 2.1.",
    )
    return text.replace(
        "- Is the output exactly",
        "- Are secondary timers recorded separately, with null distinct from []?\n"
        "- Are secondary counters (players/teams remaining, lives, displayed target, series) recorded, "
        "without kills, damage, money or XP, with null distinct from []?\n"
        "- Is the output exactly",
    )


def assets():
    template = json.dumps(empty_observation(), ensure_ascii=False, indent=2)
    return {
        PROMPT: teacher_prompt(template),
        HERE / "observation_v2.schema.json": json.dumps(output_schema(), indent=2) + "\n",
        HERE / "observation_v2.template.json": template + "\n",
        HERE / "gru_feature_spec_v4.json": json.dumps(feature_spec(), indent=2) + "\n",
    }


if __name__ == "__main__":
    for path, content in assets().items():
        path.write_text(content, encoding="utf-8")
        print(path)
