from fastapi import APIRouter
# from .auth.register_admin import router as admin_router
# from .auth.register_patient import router as patient_router
# from .auth.register_specialist import router as specialist_router
# from .auth.login import router as login_router
# from .auth.verify_email import router as verify_email_router
# from .auth.reset_password import router as reset_password_router
# from .oauth import router as oauth_router


# # User Management
# from .auth.get_users import router as get_users_router



# #Admin Management
# from .admin.admin_management import admin_management_router as admin_manager_router

# #Specialist Management
# from .admin.specialists_management import router as specialist_manager_router

# from .forum.forum_router import router as forum_router

# from .agents_routes.assessment_routes import router as assessment_router

# from .agents_routes.tpa_routes import router as tpa_router

# from .agents_routes.appointments_routes import router as appointment_manager_router

# from .agents_routes.preferences_routes import router as preferences_router

# from .agents_routes.da_routes import router as da_router

# from .agents_routes.pima_router import router as pima_router
# from .authentication.patient_login import router as patient_authentication_router


from .registeration.register import router as registeration_router
from .registeration.register_patient import router as minimal_patient_registration_router
from .registeration.verify_email import router as email_verification_router
from .authentication.authenticate import router as user_auth_router
from .specialist_routes.complete_profile import router as profile_completion_router
from .users import router as users_router
from .questionnaires import router as questionnaires_router
from .chat import router as chat_router
from .journal import router as journal_router
from .forum import router as forum_router
from .admin import router as admin_router

# Create main auth router
router = APIRouter()



router.include_router(registeration_router)
router.include_router(minimal_patient_registration_router)

router.include_router(email_verification_router)

router.include_router(user_auth_router)

router.include_router(profile_completion_router)
router.include_router(users_router)
router.include_router(questionnaires_router)
router.include_router(chat_router)
router.include_router(journal_router)
router.include_router(forum_router)
router.include_router(admin_router)

# router.include_router(patient_authentication_router)
# router.include_router(admin_router)            # Creates "auth" tag
# router.include_router(patient_router)          # Creates "auth" tag
# router.include_router(specialist_router)        # Creates "auth" tag
# router.include_router(login_router)            # Creates "auth" tag  
# router.include_router(verify_email_router)     # Creates "auth" tag
# router.include_router(reset_password_router)  # Creates "auth" tag
# # router.include_router(oauth_router, prefix="/oauth", tags=["oauth"])

# #User management
# router.include_router(get_users_router, prefix="/users")

# router.include_router(admin_manager_router)  
# router.include_router(specialist_manager_router)

# #mindMate Forum
# router.include_router(forum_router)


# #assesssment

# router.include_router(assessment_router)

# router.include_router(tpa_router)

# router.include_router(appointment_manager_router)

# router.include_router(preferences_router)

# router.include_router(da_router)

# router.include_router(pima_router)

#
# Health check endpoint
# @router.get("/health")
# async def auth_health_check():
#     """Health check endpoint for auth service"""
#     from datetime import datetime, timezone
#     import logging
#     
#     logger = logging.getLogger(__name__)
#     
#     try:
#         # Clean expired states during health check
#         # from .oauth import clean_expired_states, oauth_configured, oauth_states
#         clean_expired_states()
#         
#         return {
#             "status": "healthy",
#             "oauth_configured": oauth_configured,
#             "active_oauth_states": len(oauth_states),
#             "timestamp": datetime.now(timezone.utc).isoformat(),
#             "version": "2.0.0"
#         }
#     except Exception as e:
#         logger.error(f"Health check error: {e}")
#         return {
#             "status": "unhealthy",
#             "error": str(e),
#             "timestamp": datetime.now(timezone.utc).isoformat()
#         }
        
        