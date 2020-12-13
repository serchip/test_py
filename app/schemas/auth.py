from pydantic import BaseModel


class CreateBalanceSchema(BaseModel):
    """
    Model for balance create
    """
    username: str
