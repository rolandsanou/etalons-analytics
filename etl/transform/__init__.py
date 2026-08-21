from . import appearances, elo, matches, players


def run():
    matches.run()
    elo.run()
    registry, callups = players.build()
    appearances.run(registry)
    players.enrich(registry)
    players.write(registry, callups)
