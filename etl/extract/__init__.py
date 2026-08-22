from . import commons, martj42, sofascore, wikipedia


def run(force=False, force_profiles=False):
    """Pull every source.

    `force_profiles` re-reads only the player profiles and club form — the
    fields that change between matches (club, league, market value, contract).
    Everything else about a played match is settled, so a narrower refresh keeps
    the request count to the couple of hundred that can actually differ.
    """
    wikipedia.run(force=force)
    martj42.run(force=force)
    sofascore.run(force=force, force_profiles=force_profiles)
    commons.run(force=force)
