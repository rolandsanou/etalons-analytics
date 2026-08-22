"""The one place an analysis registers itself.

Adding an analysis to the pipeline means adding ONE entry here. `marts.run()`
writes every declared mart, and `site.py` merges every declared site fragment
into the JSON document the dashboard fetches. Nothing else needs editing on the
Python side — see docs/ARCHITECTURE.md.

Each entry:
    name      short id, shown in build logs
    marts     [(filename, fields, builder)] -> builder() returns a list of dicts
    site      {document: {key: builder}}    -> merged into site/data/<document>.json
    doc       one line describing what the analysis answers (used by the docs)
"""

from . import coaches, leadership, performance, pipeline, resilience, style

ANALYSES = [
    {
        "name": "performance",
        "doc": "Team goal timing, player importance components and bench impact.",
        "marts": [
            ("team_timeline.csv", performance.TIMELINE_FIELDS, performance.timeline_bins),
            ("player_importance.csv", performance.IMPORTANCE_FIELDS, performance.importance),
            ("bench_impact.csv", performance.BENCH_FIELDS, performance.bench),
        ],
        "site": {
            "team": {"timeline": performance.timeline_json},
            "pool": {"importance": performance.importance, "bench": performance.bench},
        },
    },
    {
        "name": "leadership",
        "doc": "Captaincy records and goalkeeper comparison.",
        "marts": [
            ("captains.csv", leadership.CAPTAIN_FIELDS, leadership.captains),
            ("goalkeepers.csv", leadership.GK_FIELDS, leadership.goalkeepers),
        ],
        "site": {"team": {"captains": leadership.captains,
                          "goalkeepers": leadership.goalkeepers}},
    },
    {
        "name": "coaches",
        "doc": "Record per head-coach tenure, with the Elo swing over the spell.",
        "marts": [("coach_eras.csv", coaches.ERA_FIELDS, coaches.build_coach_eras)],
        "site": {"history": {"coaches": coaches.build_coach_eras}},
    },
    {
        "name": "pipeline",
        "doc": "Youth cohorts (U-17/U-20) and their graduation to the senior team.",
        "marts": [("pipeline.csv", pipeline.COHORT_FIELDS, pipeline.cohorts)],
        "site": {"team": {"pipeline": pipeline.pipeline_json}},
    },
    {
        "name": "style",
        "doc": "Playing-style axes vs the opponents faced, by tercile and by half.",
        "marts": [("team_style.csv", style.STYLE_FIELDS, style.build_style)],
        "site": {"team": {"style": style.style_json}},
    },
    {
        "name": "resilience",
        "doc": "Deficit ladder, response after conceding, output by game state.",
        "marts": [
            ("resilience.csv", resilience.RESILIENCE_FIELDS, resilience.build_resilience),
            ("clutch_players.csv", resilience.CLUTCH_FIELDS, resilience.build_clutch),
        ],
        "site": {"team": {"resilience": resilience.resilience_json}},
    },
]


def site_fragments(document):
    """{key: builder} contributed to site/data/<document>.json by all analyses."""
    out = {}
    for entry in ANALYSES:
        out.update(entry["site"].get(document, {}))
    return out
