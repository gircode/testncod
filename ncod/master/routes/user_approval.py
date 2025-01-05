from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from ..models.user import User, UserStatus
from ..core.auth import get_current_admin_user
from ..core.exceptions import ValidationError
from ..schemas.user import UserApprovalResponse, UserListResponse, ApprovalAction

router = APIRouter(prefix="/api/users", tags=["user-approval"])


@router.get("/pending", response_model=List[UserListResponse])
async def get_pending_users(
    current_admin: User = Depends(get_current_admin_user),
) -> List[Dict[str, Any]]:
    """获取待审批用户列表"""
    try:
        users = await User.get_pending_users()
        return [user.to_dict() for user in users]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/{user_id}/approve", response_model=UserApprovalResponse)
async def approve_user(
    user_id: int, current_admin: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """审批通过用户"""
    try:
        user = await User.get(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        await user.approve(current_admin.id)
        return {
            "success": True,
            "message": f"User {user.username} has been approved",
            "user": user.to_dict(),
        }

    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/{user_id}/reject", response_model=UserApprovalResponse)
async def reject_user(
    user_id: int, current_admin: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """拒绝用户申请"""
    try:
        user = await User.get(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        await user.reject()
        return {
            "success": True,
            "message": f"User {user.username} has been rejected",
            "user": user.to_dict(),
        }

    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/{user_id}/status", response_model=UserApprovalResponse)
async def update_user_status(
    user_id: int,
    action: ApprovalAction,
    current_admin: User = Depends(get_current_admin_user),
) -> Dict[str, Any]:
    """更新用户状态"""
    try:
        user = await User.get(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        if action == ApprovalAction.ENABLE:
            await user.enable()
            message = f"User {user.username} has been enabled"
        elif action == ApprovalAction.DISABLE:
            await user.disable()
            message = f"User {user.username} has been disabled"
        else:
            raise ValidationError("Invalid action")

        return {"success": True, "message": message, "user": user.to_dict()}

    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
