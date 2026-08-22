from . import commons, martj42, sofascore, wikipedia


def run(force=False):
    wikipedia.run(force=force)
    martj42.run(force=force)
    sofascore.run(force=force)
    commons.run(force=force)
