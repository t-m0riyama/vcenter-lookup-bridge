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
    success: bool = Field(
        description="処理成功フラグ (true|false)",
        example=True,
    )
    message: Optional[str] = Field(
        description="メッセージ",
        default=None,
        example="正常に処理が完了しました。",
    )
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
    vcenterWsSessions: Optional[dict] = Field(
        description="vCenterの接続状況",
        default=None,
        example={"vcenter01": "alive", "vcenter02": "dead"},
    )
    timestamp: str = Field(
        description="レスポンス生成時刻",
        example="2025-07-24T10:00:00.000000+09:00",
    )
    requestId: Optional[str] = Field(
        description="リクエストID",
        default=None,
        example="9dc4cec3-5fae-4402-a47f-04499cfefad0",
    )

    @classmethod
    def create(
        cls,
        results: T,
        success: bool = True,
        message: Optional[str] = None,
        pagination: Optional[PaginationInfo] = None,
        vcenterWsSessions: Optional[dict] = None,
        requestId: Optional[str] = None,
    ):
        return cls(
            results=results,
            success=success,
            message=message,
            pagination=pagination,
            vcenterWsSessions=vcenterWsSessions,
            timestamp=datetime.now(UTC).isoformat(),
            requestId=requestId,
        )


class ErrorResponse(BaseModel):
    """エラーレスポンスの標準フォーマット"""

    success: bool = Field(
        description="処理成功フラグ (true|false)",
        example=True,
    )
    error: dict = Field(description="エラー情報")
    message: Optional[str] = Field(
        description="エラーメッセージ",
        default=None,
        example="処理中にエラーが発生しました。",
    )
    timestamp: str = Field(
        description="レスポンス生成時刻",
        example="2025-07-24T10:00:00.000000+09:00",
    )
    requestId: Optional[str] = Field(
        description="リクエストID",
        default=None,
        example="9dc4cec3-5fae-4402-a47f-04499cfefad0",
    )

    @classmethod
    def create(
        cls,
        errorCode: str,
        errorType: str,
        message: str,
        details: Optional[dict] = None,
        requestId: Optional[str] = None,
    ):
        return cls(
            error={"code": errorCode, "type": errorType, "details": details},
            message=message,
            timestamp=datetime.now(UTC).isoformat(),
            requestId=requestId,
        )
