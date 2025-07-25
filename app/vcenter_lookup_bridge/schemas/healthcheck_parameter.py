from pydantic import BaseModel, Field
from vcenter_lookup_bridge.schemas.common import ApiResponse


class HealthcheckSchema(BaseModel):
    """ヘルスチェックのスキーマ"""

    status: str = Field(
        description="サービスのステータスを示します。(ok|ng)",
        example="ok",
    )
    vcenter_service_instances: str | None = Field(
        description="vCenterへのセッションのステータスを示します。(ok|ng)", example="ok"
    )
    model_config = {"extra": "forbid"}


class HealthcheckResponseSchema(ApiResponse[HealthcheckSchema]):
    """ヘルスチェックのレスポンススキーマ"""

    pass
