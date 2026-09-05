class ServiceNowService:
    """
    ServiceNowService is responsible for interacting with the ServiceNow API.
    It provides methods to create, update, and retrieve incidents from ServiceNow.
    """

    def __init__(self, instance_url: str, username: str, password: str):
        self.instance_url = instance_url
        self.username = username
        self.password = password
