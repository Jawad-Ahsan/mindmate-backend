"""
Specialist Matcher - Core Matching Logic for SMA
===============================================
Handles specialist filtering, scoring, and ranking based on patient preferences
"""

from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import and_, or_, func, desc, asc
from datetime import datetime, timedelta, timezone
import logging
import uuid

from models.sql_models.specialist_models import (
    Specialists, SpecialistsAuthInfo, SpecialistSpecializations,
    ApprovalStatusEnum, EmailVerificationStatusEnum, AvailabilityStatusEnum
)
from models.sql_models.appointments_model import Appointment, AppointmentStatusEnum
from .sma_schemas import (
    SpecialistSearchRequest, DefaultPreferences,
    ConsultationMode, SortOption
)

logger = logging.getLogger(__name__)

class SpecialistMatcher:
    """Core specialist matching and ranking engine"""
    
    def __init__(self, db: Session):
        self.db = db
        
        # Default preferences when user doesn't specify
        self.default_prefs = DefaultPreferences()
        
        # Scoring weights (configurable)
        self.weights = {
            'specialization_match': 3.0,
            'language_overlap': 2.0,
            'rating_score': 1.5,
            'availability_soonness': 1.5,
            'experience_score': 1.0,
            'budget_closeness': 1.0,
            'location_match': 0.5
        }
    
    def search_specialists(self, request: SpecialistSearchRequest) -> Dict[str, Any]:
        """
        Search and rank specialists based on patient preferences
        
        Returns:
            Dict with specialists, total count, and search metadata
        """
        try:
            # Apply defaults to missing preferences
            prefs = self._apply_defaults(request)
            
            # Apply hard filters to get candidate specialists
            candidates = self._apply_hard_filters(prefs)
            logger.info(f"Hard filters returned {len(candidates)} candidates")
            
            if not candidates:
                logger.info("No candidates found with hard filters, trying relaxed filters")
                # Try with relaxed filters
                candidates = self._apply_relaxed_filters(prefs)
                logger.info(f"Relaxed filters returned {len(candidates)} candidates")
            
            # Score and rank specialists
            scored_specialists = self._score_specialists(candidates, prefs)
            
            # Apply sorting
            sorted_specialists = self._apply_sorting(scored_specialists, request.sort_by)
            
            # Apply pagination
            total_count = len(sorted_specialists)
            start_idx = (request.page - 1) * request.size
            end_idx = start_idx + request.size
            paginated_specialists = sorted_specialists[start_idx:end_idx]
            
            # Convert to response format
            specialists_data = []
            for specialist, score_data in paginated_specialists:
                specialist_data = self._convert_to_basic_info(specialist)
                specialists_data.append(specialist_data)
            
            result = {
                "specialists": specialists_data,
                "total_count": total_count,
                "page": request.page,
                "size": request.size,
                "total_pages": (total_count + request.size - 1) // request.size,
                "search_criteria": {
                    "applied_filters": prefs.dict(),
                    "total_candidates": len(candidates),
                    "scoring_weights": self.weights
                }
            }
            
            logger.info(f"Final search result: {len(specialists_data)} specialists, total count: {total_count}")
            return result
            
        except Exception as e:
            logger.error(f"Error in specialist search: {str(e)}")
            raise
    
    def get_top_specialists(self, request: SpecialistSearchRequest) -> Dict[str, Any]:
        """
        Get top N specialists with scoring rationale
        
        Returns:
            Dict with top specialists and scoring breakdown
        """
        try:
            # Apply defaults
            prefs = self._apply_defaults(request)
            
            # Get candidates
            candidates = self._apply_hard_filters(prefs)
            
            if not candidates:
                candidates = self._apply_relaxed_filters(prefs)
            
            # Score specialists
            scored_specialists = self._score_specialists(candidates, prefs)
            
            # Get top N
            top_specialists = scored_specialists[:request.limit]
            
            # Build response with rationale
            specialists_data = []
            rationale = {
                "weights_used": self.weights,
                "scoring_breakdown": []
            }
            
            for specialist, score_data in top_specialists:
                specialist_data = self._convert_to_basic_info(specialist)
                specialists_data.append(specialist_data)
                
                # Add scoring breakdown
                # The MatchingScoreBreakdown schema was removed, so this part needs to be adjusted
                # or the schema needs to be re-added if it's still needed.
                # For now, we'll just append a placeholder or remove if not used.
                # Since the schema was removed, we'll just append a placeholder.
                rationale["scoring_breakdown"].append({
                    "specialist_id": specialist.id,
                    "total_score": score_data['total_score'],
                    "specialization_match": score_data['specialization_match'],
                    "language_overlap": score_data['language_overlap'],
                    "rating_score": score_data['rating_score'],
                    "availability_soonness": score_data['availability_soonness'],
                    "experience_score": score_data['experience_score'],
                    "budget_closeness": score_data['budget_closeness'],
                    "location_match": score_data['location_match'],
                    "factors": score_data['factors']
                })
            
            return {
                "specialists": specialists_data,
                "rationale": rationale,
                "search_criteria": prefs.dict()
            }
            
        except Exception as e:
            logger.error(f"Error getting top specialists: {str(e)}")
            raise
    
    def _apply_defaults(self, request: SpecialistSearchRequest) -> SpecialistSearchRequest:
        """Apply default preferences to missing fields"""
        prefs_dict = request.dict()
        
        # Apply defaults for missing values
        if not prefs_dict.get('consultation_mode'):
            prefs_dict['consultation_mode'] = self.default_prefs.consultation_mode
        
        if not prefs_dict.get('languages'):
            prefs_dict['languages'] = self.default_prefs.languages
        
        if not prefs_dict.get('budget_max'):
            prefs_dict['budget_max'] = self.default_prefs.budget_max
        
        if not prefs_dict.get('city'):
            prefs_dict['city'] = self.default_prefs.city
        
        if not prefs_dict.get('specialist_type'):
            prefs_dict['specialist_type'] = self.default_prefs.specialist_type
        
        if not prefs_dict.get('specializations'):
            prefs_dict['specializations'] = self.default_prefs.specializations
        
        return SpecialistSearchRequest(**prefs_dict)
    
    def _apply_hard_filters(self, prefs: SpecialistSearchRequest) -> List[Specialists]:
        """Apply hard filters to get candidate specialists"""
        # Use selectinload to avoid JSON field issues in distinct
        query = self.db.query(Specialists).options(
            selectinload(Specialists.auth_info),
            selectinload(Specialists.specializations)
        ).join(
            SpecialistsAuthInfo
        ).filter(
            # Core verification filters
            Specialists.approval_status == ApprovalStatusEnum.APPROVED,
            SpecialistsAuthInfo.email_verification_status == EmailVerificationStatusEnum.VERIFIED,
            Specialists.is_deleted == False
        )
        
        # Availability status filter - temporarily commented out for testing
        # query = query.filter(
        #     Specialists.availability_status == AvailabilityStatusEnum.ACCEPTING_NEW_PATIENTS
        # )
        
        # Consultation mode filter
        if prefs.consultation_mode:
            # For now, assume all specialists support online
            # In a real implementation, you'd check consultation_modes array
            if prefs.consultation_mode == ConsultationMode.IN_PERSON:
                # For in-person, we might need additional checks
                pass
        
        # City filter for in-person consultations
        if (prefs.consultation_mode == ConsultationMode.IN_PERSON and 
            prefs.city):
            query = query.filter(Specialists.city.ilike(f"%{prefs.city}%"))
        
        # Budget filter (hard cap)
        if prefs.budget_max:
            query = query.filter(
                or_(
                    Specialists.consultation_fee <= prefs.budget_max,
                    Specialists.consultation_fee.is_(None)
                )
            )
        
        # Specialist type filter
        if prefs.specialist_type:
            query = query.filter(Specialists.specialist_type == prefs.specialist_type)
        
        # Language filter
        if prefs.languages:
            # For now, assume all specialists speak English/Urdu
            # In a real implementation, you'd check languages_spoken array
            pass
        
        # Specialization filter
        if prefs.specializations:
            query = query.join(SpecialistSpecializations).filter(
                SpecialistSpecializations.specialization.in_(prefs.specializations)
            )
        
        # Availability filter (has at least one free slot in next 21 days)
        if prefs.available_from or prefs.available_to:
            # This would require joining with availability/slots table
            # For now, we'll skip this filter
            pass
        
        try:
            # Use distinct on id to avoid JSON field comparison issues
            specialists = query.distinct(Specialists.id).all()
            logger.info(f"Found {len(specialists)} specialists after hard filters")
            for spec in specialists:
                logger.info(f"Specialist: {spec.id}, approval: {spec.approval_status}, verified: {spec.auth_info.email_verification_status if spec.auth_info else 'No auth info'}")
            return specialists
        except Exception as e:
            logger.warning(f"Distinct on id failed, trying alternative approach: {str(e)}")
            # Fallback: use a subquery approach to avoid JSON field issues
            try:
                # Get distinct specialist IDs first
                specialist_ids = self.db.query(Specialists.id).join(
                    SpecialistsAuthInfo
                ).filter(
                    Specialists.approval_status == ApprovalStatusEnum.APPROVED,
                    SpecialistsAuthInfo.email_verification_status == EmailVerificationStatusEnum.VERIFIED,
                    Specialists.is_deleted == False
                ).distinct().all()
                
                # Then get full specialist objects
                specialist_ids_list = [sid[0] for sid in specialist_ids]
                return self.db.query(Specialists).options(
                    selectinload(Specialists.auth_info),
                    selectinload(Specialists.specializations)
                ).filter(Specialists.id.in_(specialist_ids_list)).all()
            except Exception as e2:
                logger.error(f"Alternative approach also failed: {str(e2)}")
                # Last resort: return all without distinct
                return query.all()
    
    def _apply_relaxed_filters(self, prefs: SpecialistSearchRequest) -> List[Specialists]:
        """Apply relaxed filters when no matches found with strict filters"""
        logger.info("Applying relaxed filters for specialist search")
        
        # Use selectinload to avoid JSON field issues in distinct
        query = self.db.query(Specialists).options(
            selectinload(Specialists.auth_info),
            selectinload(Specialists.specializations)
        ).join(
            SpecialistsAuthInfo
        ).filter(
            # Core verification filters (keep these)
            Specialists.approval_status == ApprovalStatusEnum.APPROVED,
            SpecialistsAuthInfo.email_verification_status == EmailVerificationStatusEnum.VERIFIED,
            Specialists.is_deleted == False
        )
        
        # Remove availability status filter
        # Remove city filter
        # Remove budget filter
        # Keep only essential filters
        
        try:
            # Use distinct on id to avoid JSON field comparison issues
            return query.distinct(Specialists.id).all()
        except Exception as e:
            logger.warning(f"Distinct on id failed, trying alternative approach: {str(e)}")
            # Fallback: use a subquery approach to avoid JSON field issues
            try:
                # Get distinct specialist IDs first
                specialist_ids = self.db.query(Specialists.id).join(
                    SpecialistsAuthInfo
                ).filter(
                    Specialists.approval_status == ApprovalStatusEnum.APPROVED,
                    SpecialistsAuthInfo.email_verification_status == EmailVerificationStatusEnum.VERIFIED,
                    Specialists.is_deleted == False
                ).distinct().all()
                
                # Then get full specialist objects
                specialist_ids_list = [sid[0] for sid in specialist_ids]
                return self.db.query(Specialists).options(
                    selectinload(Specialists.auth_info),
                    selectinload(Specialists.specializations)
                ).filter(Specialists.id.in_(specialist_ids_list)).all()
            except Exception as e2:
                logger.error(f"Alternative approach also failed: {str(e2)}")
                # Last resort: return all without distinct
                return query.all()
    
    def _score_specialists(self, specialists: List[Specialists], prefs: SpecialistSearchRequest) -> List[Tuple[Specialists, Dict[str, Any]]]:
        """Score specialists based on preferences"""
        scored_specialists = []
        
        for specialist in specialists:
            score_data = self._calculate_score(specialist, prefs)
            scored_specialists.append((specialist, score_data))
        
        # Sort by total score (descending)
        scored_specialists.sort(key=lambda x: x[1]['total_score'], reverse=True)
        
        return scored_specialists
    
    def _calculate_score(self, specialist: Specialists, prefs: SpecialistSearchRequest) -> Dict[str, Any]:
        """Calculate comprehensive score for a specialist"""
        
        # Specialization match
        specialization_match = self._calculate_specialization_match(specialist, prefs.specializations)
        
        # Language overlap
        language_overlap = self._calculate_language_overlap(specialist, prefs.languages)
        
        # Rating score
        rating_score = self._calculate_rating_score(specialist)
        
        # Availability soonness
        availability_soonness = self._calculate_availability_soonness(specialist)
        
        # Experience score
        experience_score = self._calculate_experience_score(specialist)
        
        # Budget closeness
        budget_closeness = self._calculate_budget_closeness(specialist, prefs.budget_max)
        
        # Location match
        location_match = self._calculate_location_match(specialist, prefs.city, prefs.consultation_mode)
        
        # Calculate total score
        total_score = (
            self.weights['specialization_match'] * specialization_match +
            self.weights['language_overlap'] * language_overlap +
            self.weights['rating_score'] * rating_score +
            self.weights['availability_soonness'] * availability_soonness +
            self.weights['experience_score'] * experience_score +
            self.weights['budget_closeness'] * budget_closeness +
            self.weights['location_match'] * location_match
        )
        
        # Build factors list for transparency
        factors = self._build_factors_list(specialist, prefs, {
            'specialization_match': specialization_match,
            'language_overlap': language_overlap,
            'rating_score': rating_score,
            'availability_soonness': availability_soonness,
            'experience_score': experience_score,
            'budget_closeness': budget_closeness,
            'location_match': location_match
        })
        
        return {
            'total_score': total_score,
            'specialization_match': specialization_match,
            'language_overlap': language_overlap,
            'rating_score': rating_score,
            'availability_soonness': availability_soonness,
            'experience_score': experience_score,
            'budget_closeness': budget_closeness,
            'location_match': location_match,
            'factors': factors
        }
    
    def _calculate_specialization_match(self, specialist: Specialists, required_specializations: Optional[List[str]]) -> float:
        """Calculate specialization match score"""
        if not required_specializations:
            return 1.0  # No preference means perfect match
        
        # Get specialist's specializations
        specialist_specs = [spec.specialization.value for spec in specialist.specializations]
        
        # Check for overlap
        overlap = set(required_specializations) & set(specialist_specs)
        
        if overlap:
            return 1.0
        else:
            return 0.0
    
    def _calculate_language_overlap(self, specialist: Specialists, preferred_languages: Optional[List[str]]) -> float:
        """Calculate language overlap score"""
        if not preferred_languages:
            return 1.0  # No preference means perfect match
        
        # For now, assume all specialists speak English/Urdu
        # In a real implementation, you'd check specialist.languages_spoken
        specialist_languages = ["English", "Urdu"]
        
        # Calculate overlap ratio
        intersection = set(preferred_languages) & set(specialist_languages)
        union = set(preferred_languages) | set(specialist_languages)
        
        if union:
            return len(intersection) / len(union)
        else:
            return 0.0
    
    def _calculate_rating_score(self, specialist: Specialists) -> float:
        """Calculate rating score (normalized to 0-1)"""
        if not specialist.average_rating:
            return 0.5  # Neutral score for no ratings
        
        return float(specialist.average_rating) / 5.0
    
    def _calculate_availability_soonness(self, specialist: Specialists) -> float:
        """Calculate availability soonness score"""
        # For now, return a default score
        # In a real implementation, you'd check actual availability slots
        return 0.7  # Assume moderate availability
    
    def _calculate_experience_score(self, specialist: Specialists) -> float:
        """Calculate experience score (normalized to 0-1)"""
        years = specialist.years_experience or 0
        return min(years / 10.0, 1.0)  # Cap at 10 years
    
    def _calculate_budget_closeness(self, specialist: Specialists, budget_max: Optional[float]) -> float:
        """Calculate budget closeness score"""
        if not budget_max:
            return 1.0  # No budget constraint means perfect match
        
        if not specialist.consultation_fee:
            return 0.5  # Neutral score for unknown fee
        
        fee = float(specialist.consultation_fee)
        
        if fee <= budget_max:
            # Within budget: cheaper is better
            return 1.0 - (fee / budget_max) * 0.5
        else:
            # Over budget: small penalty
            return 0.1
    
    def _calculate_location_match(self, specialist: Specialists, preferred_city: Optional[str], consultation_mode: Optional[ConsultationMode]) -> float:
        """Calculate location match score"""
        if consultation_mode == ConsultationMode.ONLINE:
            return 1.0  # Location doesn't matter for online
        
        if not preferred_city:
            return 0.5  # Neutral score for no city preference
        
        if specialist.city and specialist.city.lower() == preferred_city.lower():
            return 1.0
        else:
            return 0.0
    
    def _build_factors_list(self, specialist: Specialists, prefs: SpecialistSearchRequest, scores: Dict[str, float]) -> List[str]:
        """Build human-readable factors list for transparency"""
        factors = []
        
        # Specialization factors
        if prefs.specializations and scores['specialization_match'] > 0:
            specialist_specs = [spec.specialization.value for spec in specialist.specializations]
            overlap = set(prefs.specializations) & set(specialist_specs)
            if overlap:
                factors.append(f"Matches specializations: {', '.join(overlap)}")
        
        # Language factors
        if prefs.languages and scores['language_overlap'] > 0:
            factors.append(f"Speaks preferred languages")
        
        # Rating factors
        if specialist.average_rating:
            factors.append(f"High rating: {specialist.average_rating}/5.0")
        
        # Experience factors
        if specialist.years_experience:
            factors.append(f"Experienced: {specialist.years_experience} years")
        
        # Budget factors
        if prefs.budget_max and specialist.consultation_fee:
            if float(specialist.consultation_fee) <= prefs.budget_max:
                factors.append(f"Within budget: PKR {specialist.consultation_fee}")
        
        # Location factors
        if prefs.consultation_mode == ConsultationMode.IN_PERSON and prefs.city:
            if specialist.city and specialist.city.lower() == prefs.city.lower():
                factors.append(f"Same city: {specialist.city}")
        
        return factors
    
    def _apply_sorting(self, scored_specialists: List[Tuple[Specialists, Dict[str, Any]]], sort_by: SortOption) -> List[Tuple[Specialists, Dict[str, Any]]]:
        """Apply sorting to scored specialists"""
        if sort_by == SortOption.BEST_MATCH:
            # Already sorted by total score
            return scored_specialists
        elif sort_by == SortOption.FEE_LOW:
            return sorted(scored_specialists, key=lambda x: float(x[0].consultation_fee or 0))
        elif sort_by == SortOption.FEE_HIGH:
            return sorted(scored_specialists, key=lambda x: float(x[0].consultation_fee or 0), reverse=True)
        elif sort_by == SortOption.RATING_HIGH:
            return sorted(scored_specialists, key=lambda x: float(x[0].average_rating or 0), reverse=True)
        elif sort_by == SortOption.EXPERIENCE_HIGH:
            return sorted(scored_specialists, key=lambda x: int(x[0].years_experience or 0), reverse=True)
        else:
            return scored_specialists
    
    def _convert_to_basic_info(self, specialist: Specialists) -> Dict[str, Any]:
        """Convert specialist to basic info format"""
        return {
            "id": specialist.id,
            "full_name": specialist.full_name,
            "specialist_type": specialist.specialist_type.value if specialist.specialist_type else "Not Specified",
            "years_experience": specialist.years_experience,
            "bio": specialist.bio,
            "consultation_fee": float(specialist.consultation_fee) if specialist.consultation_fee else None,
            "languages_spoken": specialist.languages_spoken or ["English", "Urdu"],
            "specializations": [spec.specialization.value for spec in specialist.specializations] if specialist.specializations else [],
            "city": specialist.city,
            "clinic_name": specialist.clinic_name,
            "profile_image_url": specialist.profile_image_url,
            "website_url": specialist.website_url,
            "availability_status": specialist.availability_status.value if specialist.availability_status else "Not Specified",
            "average_rating": float(specialist.average_rating) if specialist.average_rating else 0.0,
            "total_reviews": specialist.total_reviews,
            "total_appointments": specialist.total_appointments,
            "is_approved": specialist.is_approved,
            "can_practice": specialist.can_practice
        }
