"""
Advanced Scoring Service with Graduated Scoring System
Implements multiple scoring strategies for different criterion types
✅ FIXED: Added score_resume method to actually calculate and save scores
"""
import logging
from typing import Dict, Any, List, Optional
from decimal import Decimal

logger = logging.getLogger(__name__)


class ScoringEngine:
    """
    Advanced scoring engine that supports multiple scoring strategies:
    - Ranged scoring for numeric values
    - Categorical scoring for skill levels
    - Boolean scoring for yes/no criteria
    - Text matching for keywords
    """
    
    def __init__(self):
        self.scorers = {
            'ranged_number': self._score_ranged_number,
            'graded_category': self._score_graded_category,
            'boolean': self._score_boolean,
            'text_match': self._score_text_match
        }
    
    def score_resume(self, db, resume_id: int, extracted_data: Dict[str, Any], position_id: int) -> Dict[str, Any]:
        """
        ✅ FIXED: Main method to score a resume against position criteria
        
        Args:
            db: Database session
            resume_id: Resume ID
            extracted_data: Data extracted from resume
            position_id: Position ID
            
        Returns:
            Dictionary with scoring results
        """
        from database.models import Position, Score, ResumeScore, Criterion
        
        try:
            # Get position and its criteria
            position = db.query(Position).filter_by(id=position_id).first()
            if not position:
                raise ValueError(f"Position {position_id} not found")
            
            criteria = position.criteria
            if not criteria:
                logger.warning(f"No criteria defined for position {position_id}")
                return {'message': 'No criteria defined for scoring'}
            
            # Calculate score for each criterion
            individual_scores = []
            score_details = []
            
            for criterion in criteria:
                # Map criterion key to extracted data field
                extracted_value = self._get_extracted_value(extracted_data, criterion.criterion_key)
                
                # Calculate score
                score_result = self.calculate_score(
                    criterion={
                        'data_type': criterion.data_type,
                        'weight': criterion.weight,
                        'config_json': criterion.config_json or {},
                        'criterion_key': criterion.criterion_key
                    },
                    extracted_value=extracted_value
                )
                
                # Save individual score to database
                score = Score(
                    resume_id=resume_id,
                    criterion_id=criterion.id,
                    awarded_points=score_result['awarded_points'],
                    max_points=score_result['max_points'],
                    score_multiplier=score_result['score_multiplier'],
                    extracted_value=str(extracted_value) if extracted_value is not None else None,
                    reasoning=score_result['reasoning']
                )
                db.add(score)
                
                individual_scores.append(score_result)
                score_details.append({
                    'criterion_name': criterion.criterion_name,
                    'criterion_key': criterion.criterion_key,
                    **score_result
                })
                
                logger.info(f"Scored {criterion.criterion_name}: {score_result['awarded_points']}/{score_result['max_points']}")
            
            # Calculate aggregate score
            aggregate_result = self.calculate_aggregate_score(
                individual_scores,
                threshold_percentage=position.threshold_percentage or 75
            )
            
            # Save aggregate score to database
            resume_score = ResumeScore(
                resume_id=resume_id,
                total_score=aggregate_result['total_score'],
                max_possible_score=aggregate_result['max_possible_score'],
                percentage=aggregate_result['percentage'],
                status=aggregate_result['status'],
                overall_assessment=aggregate_result['overall_assessment']
            )
            db.add(resume_score)
            
            # Commit all scores
            db.commit()
            
            logger.info(f"Resume {resume_id} scored: {aggregate_result['percentage']}% - {aggregate_result['status']}")
            
            return {
                'aggregate': aggregate_result,
                'details': score_details
            }
            
        except Exception as e:
            logger.error(f"Error scoring resume {resume_id}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    def _get_extracted_value(self, extracted_data: Dict[str, Any], criterion_key: str) -> Any:
        """
        Get value from extracted data based on criterion key
        
        Maps criterion keys to extracted data fields
        """
        # Direct mapping
        if criterion_key in extracted_data:
            return extracted_data[criterion_key]
        
        # Common mappings
        key_mappings = {
            'years_experience': 'work_experience_years',
            'experience_years': 'work_experience_years',
            'education': 'education_level',
            'education_degree': 'education_level',
            'field_of_study': 'education_field',
            'job_title': 'last_job_title',
            'company': 'last_company',
            'stability': 'job_stability_months',
            'industry': 'industry_type',
            'responsibility': 'responsibility_level',
            'sepidar': 'sepidar_skill',
            'excel': 'excel_skill',
            'office': 'office_skill',
            'english': 'english_level',
            'financial_reports': 'financial_reports_experience',
            'cost_calculation': 'cost_calculation_experience',
            'warehouse': 'warehouse_experience',
            'organization': 'organization_type',
            'software': 'software_skills'
        }
        
        # Check mapped keys
        for key, mapped_key in key_mappings.items():
            if criterion_key.lower() == key:
                return extracted_data.get(mapped_key)
        
        # Check partial matches
        for data_key, value in extracted_data.items():
            if criterion_key.lower() in data_key.lower() or data_key.lower() in criterion_key.lower():
                return value
        
        return None
    
    def calculate_score(
        self, 
        criterion: Dict[str, Any],
        extracted_value: Any
    ) -> Dict[str, Any]:
        """
        Calculate score for a criterion based on extracted value
        
        Args:
            criterion: Criterion configuration including type, weight, and config
            extracted_value: Value extracted from resume
            
        Returns:
            Dictionary with score details
        """
        data_type = criterion.get('data_type')
        weight = criterion.get('weight', 0)
        config = criterion.get('config_json', {})
        
        if data_type not in self.scorers:
            logger.warning(f"Unknown data type: {data_type}")
            return {
                'awarded_points': 0,
                'max_points': weight,
                'score_multiplier': 0,
                'reasoning': f'Unknown criterion type: {data_type}'
            }
        
        # Get scorer function
        scorer = self.scorers[data_type]
        
        try:
            result = scorer(extracted_value, weight, config)
            result['max_points'] = weight
            return result
        except Exception as e:
            logger.error(f"Scoring error for {criterion.get('criterion_key')}: {str(e)}")
            return {
                'awarded_points': 0,
                'max_points': weight,
                'score_multiplier': 0,
                'reasoning': f'Error calculating score: {str(e)}'
            }
    
    def _score_ranged_number(
        self, 
        value: Any, 
        weight: int, 
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Score numeric values using graduated ranges
        
        Example config:
        {
            "scoring_type": "ranged",
            "ranges": [
                {"min": 10, "max": 999, "score_multiplier": 1.0, "label": "Expert"},
                {"min": 5, "max": 9, "score_multiplier": 0.85, "label": "Senior"},
                {"min": 2, "max": 4, "score_multiplier": 0.6, "label": "Qualified"},
                {"min": 0, "max": 1, "score_multiplier": 0.15, "label": "Junior"}
            ],
            "unit": "years"
        }
        """
        ranges = config.get('ranges', [])
        unit = config.get('unit', '')
        
        # Handle null or invalid values
        if value is None or value == '':
            return {
                'awarded_points': 0,
                'score_multiplier': 0,
                'reasoning': 'No value provided'
            }
        
        # Convert to number
        try:
            numeric_value = float(value)
        except (ValueError, TypeError):
            return {
                'awarded_points': 0,
                'score_multiplier': 0,
                'reasoning': f'Invalid numeric value: {value}'
            }
        
        # Find matching range
        for range_config in ranges:
            min_val = range_config.get('min', 0)
            max_val = range_config.get('max', 999999)
            
            if min_val <= numeric_value <= max_val:
                multiplier = range_config.get('score_multiplier', 0)
                label = range_config.get('label', 'N/A')
                awarded = weight * multiplier
                
                return {
                    'awarded_points': round(awarded, 2),
                    'score_multiplier': multiplier,
                    'reasoning': f'Value {numeric_value} {unit} falls in "{label}" range (×{multiplier:.0%})'
                }
        
        # No range matched (shouldn't happen with proper config)
        return {
            'awarded_points': 0,
            'score_multiplier': 0,
            'reasoning': f'Value {numeric_value} {unit} outside all defined ranges'
        }
    
    def _score_graded_category(
        self, 
        value: Any, 
        weight: int, 
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Score categorical values with different weights per level
        
        Example config:
        {
            "scoring_type": "categorical",
            "levels": {
                "Advanced": 1.0,
                "Intermediate": 0.65,
                "Basic": 0.2,
                "None": 0.0
            },
            "min_required": "Intermediate"
        }
        """
        levels = config.get('levels', {})
        min_required = config.get('min_required')
        
        if value is None or value == '':
            return {
                'awarded_points': 0,
                'score_multiplier': 0,
                'reasoning': 'No skill level provided'
            }
        
        # Normalize value (case-insensitive matching)
        value_str = str(value).strip()
        
        # Try exact match first
        if value_str in levels:
            multiplier = levels[value_str]
            awarded = weight * multiplier
            
            meets_requirement = (
                min_required is None or 
                self._compare_skill_levels(value_str, min_required, levels) >= 0
            )
            
            return {
                'awarded_points': round(awarded, 2),
                'score_multiplier': multiplier,
                'reasoning': f'Skill level "{value_str}" (×{multiplier:.0%})' + 
                           ('' if meets_requirement else f' - below minimum requirement "{min_required}"')
            }
        
        # Try case-insensitive match
        for level_key, multiplier in levels.items():
            if level_key.lower() == value_str.lower():
                awarded = weight * multiplier
                
                meets_requirement = (
                    min_required is None or 
                    self._compare_skill_levels(level_key, min_required, levels) >= 0
                )
                
                return {
                    'awarded_points': round(awarded, 2),
                    'score_multiplier': multiplier,
                    'reasoning': f'Skill level "{level_key}" (×{multiplier:.0%})' +
                               ('' if meets_requirement else f' - below minimum requirement "{min_required}"')
                }
        
        # No match found
        return {
            'awarded_points': 0,
            'score_multiplier': 0,
            'reasoning': f'Unknown skill level "{value_str}" - not in defined categories'
        }
    
    def _compare_skill_levels(
        self, 
        level1: str, 
        level2: str, 
        levels_dict: Dict[str, float]
    ) -> int:
        """
        Compare two skill levels
        Returns: 1 if level1 > level2, 0 if equal, -1 if level1 < level2
        """
        score1 = levels_dict.get(level1, 0)
        score2 = levels_dict.get(level2, 0)
        
        if score1 > score2:
            return 1
        elif score1 < score2:
            return -1
        else:
            return 0
    
    def _score_boolean(
        self, 
        value: Any, 
        weight: int, 
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Score boolean (yes/no) criteria
        
        Example config:
        {
            "scoring_type": "binary",
            "true_value": 1.0,
            "false_value": 0.0
        }
        """
        true_multiplier = config.get('true_value', 1.0)
        false_multiplier = config.get('false_value', 0.0)
        
        # Handle various boolean representations
        if value is None:
            has_experience = False
        elif isinstance(value, bool):
            has_experience = value
        elif isinstance(value, str):
            has_experience = value.lower() in ['yes', 'true', '1', 'بله', 'دارد']
        else:
            has_experience = bool(value)
        
        multiplier = true_multiplier if has_experience else false_multiplier
        awarded = weight * multiplier
        
        return {
            'awarded_points': round(awarded, 2),
            'score_multiplier': multiplier,
            'reasoning': f'{"Has" if has_experience else "Does not have"} experience (×{multiplier:.0%})'
        }
    
    def _score_text_match(
        self, 
        value: Any, 
        weight: int, 
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Score based on keyword matching in text
        
        Example config:
        {
            "scoring_type": "keyword_match",
            "required_keywords": ["Accounting", "Finance"],
            "preferred_keywords": ["Trading", "Import"],
            "match_type": "any"  # or "all"
        }
        """
        required_keywords = config.get('required_keywords', [])
        preferred_keywords = config.get('preferred_keywords', [])
        match_type = config.get('match_type', 'any')
        
        if value is None or value == '':
            return {
                'awarded_points': 0,
                'score_multiplier': 0,
                'reasoning': 'No text provided'
            }
        
        text = str(value).lower()
        
        # Check required keywords
        if required_keywords:
            required_matches = sum(
                1 for keyword in required_keywords 
                if keyword.lower() in text
            )
            
            if match_type == 'all':
                required_met = required_matches == len(required_keywords)
            else:  # 'any'
                required_met = required_matches > 0
            
            if required_met:
                multiplier = 1.0
                matched_keywords = [k for k in required_keywords if k.lower() in text]
                reasoning = f'Matches required keywords: {", ".join(matched_keywords)}'
            else:
                multiplier = 0.0
                reasoning = f'Does not match required keywords (needed: {", ".join(required_keywords)})'
        
        # Check preferred keywords (bonus scoring)
        elif preferred_keywords:
            preferred_matches = sum(
                1 for keyword in preferred_keywords 
                if keyword.lower() in text
            )
            
            if preferred_matches > 0:
                # Give partial credit for preferred keywords
                multiplier = min(1.0, 0.5 + (0.5 * preferred_matches / len(preferred_keywords)))
                matched_keywords = [k for k in preferred_keywords if k.lower() in text]
                reasoning = f'Matches preferred keywords: {", ".join(matched_keywords)} (×{multiplier:.0%})'
            else:
                multiplier = 0.3  # Minimal points for having any text
                reasoning = 'No preferred keywords matched (minimal score)'
        
        else:
            # No keywords defined, give full points if text exists
            multiplier = 1.0
            reasoning = 'Text provided (no specific keywords required)'
        
        awarded = weight * multiplier
        
        return {
            'awarded_points': round(awarded, 2),
            'score_multiplier': multiplier,
            'reasoning': reasoning
        }
    
    def calculate_aggregate_score(
        self, 
        individual_scores: List[Dict[str, Any]],
        threshold_percentage: int = 75
    ) -> Dict[str, Any]:
        """
        Calculate aggregate score from individual criterion scores
        
        Args:
            individual_scores: List of individual score results
            threshold_percentage: Minimum percentage to qualify
            
        Returns:
            Aggregate score summary
        """
        total_awarded = sum(
            Decimal(str(score.get('awarded_points', 0))) 
            for score in individual_scores
        )
        
        total_possible = sum(
            score.get('max_points', 0) 
            for score in individual_scores
        )
        
        if total_possible > 0:
            percentage = float((total_awarded / Decimal(str(total_possible))) * 100)
        else:
            percentage = 0
        
        status = 'Qualified' if percentage >= threshold_percentage else 'Rejected'
        
        # Generate assessment
        assessment = self._generate_assessment(
            individual_scores, 
            percentage, 
            threshold_percentage,
            status
        )
        
        return {
            'total_score': float(total_awarded),
            'max_possible_score': total_possible,
            'percentage': round(percentage, 2),
            'status': status,
            'threshold': threshold_percentage,
            'overall_assessment': assessment
        }
    
    def _generate_assessment(
        self,
        individual_scores: List[Dict[str, Any]],
        percentage: float,
        threshold: int,
        status: str
    ) -> str:
        """Generate human-readable assessment"""
        
        # Count strong and weak points
        strong_points = [
            s for s in individual_scores 
            if s.get('score_multiplier', 0) >= 0.8
        ]
        
        weak_points = [
            s for s in individual_scores 
            if s.get('score_multiplier', 0) < 0.5
        ]
        
        assessment_parts = []
        
        # Overall status
        if status == 'Qualified':
            if percentage >= 90:
                assessment_parts.append("**Excellent candidate** - Exceeds requirements significantly.")
            elif percentage >= 80:
                assessment_parts.append("**Strong candidate** - Meets all key requirements.")
            else:
                assessment_parts.append("**Qualified candidate** - Meets minimum requirements.")
        else:
            gap = threshold - percentage
            assessment_parts.append(f"**Below threshold** by {gap:.1f} percentage points.")
        
        # Strengths
        if strong_points:
            assessment_parts.append(
                f"Strengths: Excellent performance in {len(strong_points)} criteria."
            )
        
        # Weaknesses
        if weak_points:
            assessment_parts.append(
                f"Areas for improvement: {len(weak_points)} criteria below expectations."
            )
        
        return " ".join(assessment_parts)


# Singleton instance
scoring_engine = ScoringEngine()