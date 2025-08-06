from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any

from app.schemas.submission import TestSubmissionRequest, TestSubmissionResponse
from app.services.sandbox_service import SandboxService, sandbox_service
from app.services.user_state_service import UserStateService
from app.services.content_loader import load_json_content
from app.config.dependency_injection import get_user_state_service
from app.database import get_db

router = APIRouter()

@router.post("/submit-test", response_model=TestSubmissionResponse)
def submit_test(
    *,
    db: Session = Depends(get_db),
    submission_in: TestSubmissionRequest,
    user_state_service: UserStateService = Depends(get_user_state_service)
) -> Any:
    """
    接收用户代码提交，进行评测，更新BKT模型，并返回结果。
    """
    # 1. 加载测试内容
    try:
        test_task_data = load_json_content("test_tasks", submission_in.topic_id)
        checkpoints = test_task_data.get("checkpoints", [])
    except HTTPException as e:
        if e.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Topic '{submission_in.topic_id}' not found.")
        raise e

    # 2. 执行代码评测
    # 注意：这里的sandbox_service是直接导入的单例，如果未来需要更复杂的依赖管理，
    # 也可以像user_state_service一样通过Depends注入。
    evaluation_result = sandbox_service.run_evaluation(
        user_code=submission_in.code.dict(),
        checkpoints=checkpoints
    )

    # 3. 更新学生模型
    user_state_service.update_bkt_on_submission(
        participant_id=submission_in.participant_id,
        topic_id=submission_in.topic_id,
        is_correct=evaluation_result["passed"]
    )
    
    # 4. 触发一次快照检查（可选但推荐）
    # 这确保了BKT模型更新后，状态能及时被保存
    user_state_service._maybe_create_snapshot(submission_in.participant_id, db)

    # 5. 返回评测结果
    return evaluation_result