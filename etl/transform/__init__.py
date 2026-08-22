from . import (appearances, clubform, elo, fixtures, incidents, matches,
               penalties, photos, players, records, teamstats, timeline,
               youth)


def run():
    matches.run()
    elo.run()
    records.run()
    registry, callups = players.build()
    appearances.run(registry)
    incidents.run(registry)
    penalties.run(registry)
    timeline.run()
    teamstats.run()
    players.enrich(registry)
    players.write(registry, callups)
    youth.run(registry)
    clubform.run(registry)
    fixtures.run()
    photos.run()
