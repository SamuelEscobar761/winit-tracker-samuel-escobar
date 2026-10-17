from collections.abc import Collection

from app.people.names import normalize_name


def split_surname_groups(last_name: str, particles: Collection[str]) -> tuple[str, ...]:
    """Particles such as DE or LA belong to the surname that follows them."""
    known_particles = {normalize_name(particle) for particle in particles}
    groups: list[str] = []
    pending: list[str] = []
    for token in normalize_name(last_name).split():
        pending.append(token)
        if token not in known_particles:
            groups.append(" ".join(pending))
            pending = []
    return _attach_trailing_particles(groups, pending)


def _attach_trailing_particles(groups: list[str], pending: list[str]) -> tuple[str, ...]:
    if not pending:
        return tuple(groups)
    trailing = " ".join(pending)
    if not groups:
        return (trailing,)
    return (*groups[:-1], f"{groups[-1]} {trailing}")
