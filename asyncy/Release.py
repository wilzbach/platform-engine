from asyncy.enums.ReleaseState import ReleaseState


class Release:

    def __init__(self, app_uuid: str, version: int, environment: dict,
                 stories: dict, maintenance: bool, app_dns: str,
                 state: ReleaseState, deleted: bool, owner_uuid: str):
        self.app_id = app_uuid
        self.version = version
        self.environment = environment
        self.stories = stories
        self.maintenance = maintenance
        self.app_dns = app_dns
        self.state = state
        self.deleted = deleted
        self.owner_uuid = owner_uuid
