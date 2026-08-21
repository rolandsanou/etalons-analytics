from . import appearances, elo, incidents, matches, players


def run():
    matches.run()
    elo.run()
    registry, callups = players.build()
    appearances.run(registry)
    incidents.run(registry)
    players.enrich(registry)
    players.write(registry, callups)
