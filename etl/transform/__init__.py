from . import (appearances, clubform, elo, incidents, matches, penalties,
               players, timeline, youth)


def run():
    matches.run()
    elo.run()
    registry, callups = players.build()
    appearances.run(registry)
    incidents.run(registry)
    penalties.run(registry)
    timeline.run()
    players.enrich(registry)
    players.write(registry, callups)
    youth.run(registry)
    clubform.run(registry)
