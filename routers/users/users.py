from fastapi import APIRouter, Depends, HTTPException, status

from routers.authentication.authenticate import (
	get_current_user_from_token,
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me")
async def get_me(current_user_data: dict = Depends(get_current_user_from_token)):
	user = current_user_data["user"]
	user_type = current_user_data["user_type"]
	auth_info = current_user_data.get("auth_info")

	base = {
		"user_id": str(user.id),
		"email": user.email,
		"first_name": user.first_name,
		"last_name": user.last_name,
		"full_name": f"{user.first_name} {user.last_name}",
		"user_type": user_type,
	}

	if user_type == "patient":
		base.update({
			"verification_status": "verified" if getattr(auth_info, "is_verified", False) else "pending",
			"last_login": getattr(auth_info, "last_login", None),
		})
	elif user_type == "specialist":
		from models.sql_models.specialist_models import ApprovalStatusEnum
		verification = getattr(auth_info, "email_verification_status", None)
		approval = getattr(user, "approval_status", None)
		base.update({
			"verification_status": str(getattr(verification, "value", verification)) if verification else "unknown",
			"approval_status": str(getattr(approval, "value", approval)) if approval else "unknown",
			"last_login": getattr(auth_info, "last_login", None),
		})
	else:
		base.update({
			"verification_status": "verified",
			"last_login": getattr(user, "last_login", None),
		})

	return base


