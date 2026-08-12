from app.models.system import System


def create_system(system: System) -> System:
    """
    Creates a system.

    For now, the service only validates and returns
    the system received from the API layer.

    Persistence will be implemented later.
    """
    return system