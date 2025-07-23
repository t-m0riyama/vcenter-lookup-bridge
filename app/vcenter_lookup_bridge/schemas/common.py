from pydantic import BaseModel, Field
from typing import Generic, TypeVar, Optional
from datetime import datetime, UTC

T = TypeVar("T")


class PaginationInfo(BaseModel):
    """ページネーション情報"""

    totalCount: int = Field(description="総件数")
    offset: int = Field(description="現在のオフセット")
    limit: int = Field(description="取得件数制限")
    hasNext: bool = Field(description="次のページが存在するか")
    hasPrevious: bool = Field(description="前のページが存在するか")


class ApiResponse(BaseModel, Generic[T]):
    """APIレスポンスの標準フォーマット"""

    results: T = Field(description="実際のデータ")
    success: bool = Field(description="処理成功フラグ")
    message: Optional[str] = Field(description="メッセージ", default=None)
    pagination: Optional[PaginationInfo] = Field(
        description="ページネーション情報",
        default=None,
        example=PaginationInfo(
            totalCount=1,
            offset=0,
            limit=1000,
            hasNext=False,
            hasPrevious=False,
        ),
    )
    vcenter_ws_sessions: Optional[dict] = Field(
        description="vCenterの接続状況",
        default=None,
        example={"vcenter01": "alive", "vcenter02": "dead"},
    )
    timestamp: str = Field(description="レスポンス生成時刻")
    request_id: Optional[str] = Field(description="リクエストID", default=None)

    @classmethod
    def create(
        cls,
        results: T,
        success: bool = True,
        message: Optional[str] = None,
        pagination: Optional[PaginationInfo] = None,
        vcenter_ws_sessions: Optional[dict] = None,
        request_id: Optional[str] = None,
    ):
        return cls(
            results=results,
            success=success,
            message=message,
            pagination=pagination,
            vcenter_ws_sessions=vcenter_ws_sessions,
            timestamp=datetime.now(UTC).isoformat(),
            request_id=request_id,
        )


class ErrorResponse(BaseModel):
    """エラーレスポンスの標準フォーマット"""

    success: bool = Field(default=False, description="処理成功フラグ")
    error: dict = Field(description="エラー情報")
    message: str = Field(description="エラーメッセージ")
    timestamp: str = Field(description="エラー発生時刻")
    request_id: Optional[str] = Field(description="リクエストID", default=None)

    @classmethod
    def create(
        cls,
        errorCode: str,
        errorType: str,
        message: str,
        details: Optional[dict] = None,
        request_id: Optional[str] = None,
    ):
        return cls(
            error={"code": errorCode, "type": errorType, "details": details},
            message=message,
            timestamp=datetime.now(UTC).isoformat(),
            request_id=request_id,
        )
