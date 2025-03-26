from pydantic import BaseModel, Field


class HealthcheckResponseSchema (BaseModel):
    status: str = Field(
        description="サービスのステータスを示します。(ok|ng)",
        example="ok",
    )
    vcenter_session_status: str | None = Field(
        description="vCenterへのセッションのステータスを示します。(ok|ng)",
        example="ok"
    )
    model_config = {"extra": "forbid"}
