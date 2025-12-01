"""
Advanced Scoring Service with LLM-Based Evaluation
Uses Claude AI through Liara API for intelligent candidate scoring
✅ FIXED: Better parsing and error handling
"""
import logging
import json
import re
from typing import Dict, Any, List
from decimal import Decimal

logger = logging.getLogger(__name__)


class ScoringEngine:
    """
    Advanced scoring engine using LLM for candidate evaluation
    """
    
    def __init__(self):
        pass
    
    def score_resume(self, db, resume_id: int, extracted_data: Dict[str, Any], position_id: int) -> Dict[str, Any]:
        """
        Score resume using LLM-based evaluation
        
        Args:
            db: Database session
            resume_id: Resume ID
            extracted_data: Data extracted from resume
            position_id: Position ID
            
        Returns:
            Dictionary with scoring results
        """
        from database.models import Position, Score, ResumeScore, Criterion
        from services.ai_service import ai_service
        
        try:
            # Get position and criteria
            position = db.query(Position).filter_by(id=position_id).first()
            if not position:
                raise ValueError(f"Position {position_id} not found")
            
            criteria = position.criteria
            if not criteria:
                logger.warning(f"No criteria defined for position {position_id}")
                return {'message': 'No criteria defined for scoring'}
            
            # Build scoring prompt for LLM
            prompt = self._build_scoring_prompt(position, criteria, extracted_data)
            
            # Call LLM to get scoring
            logger.info(f"Calling LLM for candidate scoring (Resume ID: {resume_id})")
            ai_response = ai_service.generate_text(prompt, max_tokens=4000)
            
            # Parse LLM response
            scoring_results = self._parse_llm_scoring_response(ai_response, criteria, db)
            
            # Save individual scores
            individual_scores = []
            for result in scoring_results['individual_scores']:
                score = Score(
                    resume_id=resume_id,
                    criterion_id=result['criterion_id'],
                    awarded_points=result['awarded_points'],
                    max_points=result['max_points'],
                    score_multiplier=result['score_multiplier'],
                    extracted_value=result.get('extracted_value'),
                    reasoning=result.get('reasoning')
                )
                db.add(score)
                individual_scores.append(result)
            
            # Calculate aggregate score
            aggregate_result = self.calculate_aggregate_score(
                individual_scores,
                threshold_percentage=position.threshold_percentage or 75
            )
            
            # Save aggregate score
            resume_score = ResumeScore(
                resume_id=resume_id,
                total_score=aggregate_result['total_score'],
                max_possible_score=aggregate_result['max_possible_score'],
                percentage=aggregate_result['percentage'],
                status=aggregate_result['status'],
                overall_assessment=aggregate_result['overall_assessment']
            )
            db.add(resume_score)
            
            db.commit()
            
            logger.info(f"Resume {resume_id} scored: {aggregate_result['percentage']:.2f}% - {aggregate_result['status']}")
            
            return {
                'aggregate': aggregate_result,
                'details': individual_scores
            }
            
        except Exception as e:
            logger.error(f"Error scoring resume {resume_id}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    def _build_scoring_prompt(self, position: Any, criteria: List[Any], extracted_data: Dict[str, Any]) -> str:
        """
        Build LLM prompt for candidate scoring
        """
        criteria_descriptions = []
        
        for criterion in criteria:
            config = criterion.config_json or {}
            
            criterion_info = f"""
Criterion: {criterion.criterion_name}
- Key: {criterion.criterion_key}
- Weight: {criterion.weight} points
- Required: {'Yes' if criterion.is_required else 'No'}
- Type: {criterion.data_type}
"""
            
            if criterion.data_type == 'ranged_number':
                ranges = config.get('ranges', [])
                if ranges:
                    criterion_info += "- Scoring Ranges:\n"
                    for r in ranges:
                        criterion_info += f"  • {r.get('min')}-{r.get('max')} {config.get('unit', '')}: {r.get('score_multiplier', 0)*100:.0f}% ({r.get('label')})\n"
            
            elif criterion.data_type == 'graded_category':
                levels = config.get('levels', {})
                if levels:
                    criterion_info += "- Skill Levels:\n"
                    for level, multiplier in levels.items():
                        criterion_info += f"  • {level}: {multiplier*100:.0f}%\n"
            
            elif criterion.data_type == 'text_match':
                keywords = config.get('required_keywords') or config.get('preferred_keywords', [])
                if keywords:
                    criterion_info += f"- Keywords: {', '.join(keywords)}\n"
                match_type = config.get('match_type', 'any')
                criterion_info += f"- Match Type: {match_type} (must have {match_type} keyword)\n"
            
            criterion_info += f"- Info: {config.get('description', 'N/A')}\n"
            criteria_descriptions.append(criterion_info)
        
        extracted_data_str = json.dumps(extracted_data, indent=2, ensure_ascii=False)
        
        prompt = f"""You are an expert HR evaluator. Score this candidate on each criterion.

POSITION: {position.title}
Description: {position.description}
Minimum Score Needed: {position.threshold_percentage}%

EVALUATION CRITERIA ({len(criteria)} total):
{chr(10).join(criteria_descriptions)}

CANDIDATE DATA (extracted from resume):
{extracted_data_str}

SCORING INSTRUCTIONS:
1. For EACH criterion in the position, assign a score multiplier (0.0 to 1.0)
2. Score multiplier = 0.0 means no points, 1.0 means full points
3. awarded_points = weight × score_multiplier
4. Provide clear reasoning for each score
5. Return ONLY valid JSON (no markdown code blocks)

IMPORTANT:
- Score ALL criteria listed in the position (do not skip any)
- For text matching: check if extracted value contains keywords
- For graded categories: match to appropriate level
- For ranges: determine which range the value falls into
- Be objective and consistent
- Mandatory criteria with 0 score must be clearly explained

RETURN ONLY THIS JSON (no markdown, no code blocks, no explanations):
{{
  "individual_scores": [
    {{
      "criterion_key": "string (must match position criterion key exactly)",
      "criterion_name": "string",
      "awarded_points": number (0 to weight),
      "score_multiplier": number (0.0 to 1.0),
      "extracted_value": "string or null (what was found in resume)",
      "reasoning": "string explaining why this score"
    }}
  ],
  "evaluation_summary": "One sentence overall assessment",
  "strengths": ["strength1", "strength2"],
  "weaknesses": ["weakness1", "weakness2"],
  "mandatory_criteria_met": true/false
}}

MUST INCLUDE ALL CRITERIA IN OUTPUT. NOW SCORE THIS CANDIDATE:"""
        
        return prompt
    
    def _parse_llm_scoring_response(self, response: str, criteria: List[Any], db) -> Dict[str, Any]:
        """
        Parse LLM scoring response and convert to database format
        """
        try:
            # Clean response
            response = response.strip()
            if response.startswith('```json'):
                response = response.replace('```json', '').replace('```', '').strip()
            elif response.startswith('```'):
                response = response.replace('```', '').strip()
            
            # Try to find JSON in response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                response = json_match.group(0)
            
            # Parse JSON
            data = json.loads(response)
            
            # Build criterion lookup (case-insensitive)
            criterion_lookup = {c.criterion_key.lower(): c for c in criteria}
            
            # Process individual scores
            individual_scores = []
            for score_data in data.get('individual_scores', []):
                criterion_key = score_data.get('criterion_key', '').lower()
                
                # Find matching criterion
                criterion = criterion_lookup.get(criterion_key)
                
                if not criterion:
                    logger.warning(f"Criterion not found: {criterion_key}, trying fuzzy match")
                    # Fuzzy matching for similar keys
                    for key, crit in criterion_lookup.items():
                        if criterion_key in key or key in criterion_key:
                            criterion = crit
                            logger.info(f"Fuzzy matched {criterion_key} to {key}")
                            break
                
                if not criterion:
                    logger.warning(f"Could not match criterion: {criterion_key}, skipping")
                    continue
                
                awarded = float(score_data.get('awarded_points', 0))
                max_pts = float(criterion.weight)
                multiplier = min(awarded / max_pts if max_pts > 0 else 0, 1.0)
                
                individual_scores.append({
                    'criterion_id': criterion.id,
                    'criterion_key': criterion.criterion_key,
                    'criterion_name': score_data.get('criterion_name', criterion.criterion_name),
                    'awarded_points': awarded,
                    'max_points': max_pts,
                    'score_multiplier': multiplier,
                    'extracted_value': score_data.get('extracted_value'),
                    'reasoning': score_data.get('reasoning', '')
                })
                
                logger.info(f"Scored {criterion.criterion_name}: {awarded:.1f}/{max_pts}")
            
            # Ensure all criteria have scores
            scored_criterion_ids = {s['criterion_id'] for s in individual_scores}
            for criterion in criteria:
                if criterion.id not in scored_criterion_ids:
                    logger.warning(f"No score for criterion {criterion.criterion_name}, assigning 0")
                    individual_scores.append({
                        'criterion_id': criterion.id,
                        'criterion_key': criterion.criterion_key,
                        'criterion_name': criterion.criterion_name,
                        'awarded_points': 0.0,
                        'max_points': float(criterion.weight),
                        'score_multiplier': 0.0,
                        'extracted_value': None,
                        'reasoning': 'Not provided by LLM'
                    })
            
            return {
                'individual_scores': individual_scores,
                'evaluation_summary': data.get('evaluation_summary', ''),
                'strengths': data.get('strengths', []),
                'weaknesses': data.get('weaknesses', []),
                'mandatory_criteria_met': data.get('mandatory_criteria_met', True)
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {str(e)}")
            logger.error(f"Response: {response[:500]}")
            raise ValueError(f"Invalid JSON from LLM: {str(e)}")
        except Exception as e:
            logger.error(f"Error parsing scoring response: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    def calculate_aggregate_score(
        self, 
        individual_scores: List[Dict[str, Any]],
        threshold_percentage: int = 75
    ) -> Dict[str, Any]:
        """
        Calculate aggregate score from individual criterion scores
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
        
        strong_points = [
            s for s in individual_scores 
            if s.get('score_multiplier', 0) >= 0.8
        ]
        
        weak_points = [
            s for s in individual_scores 
            if s.get('score_multiplier', 0) < 0.5
        ]
        
        assessment_parts = []
        
        if status == 'Qualified':
            if percentage >= 90:
                assessment_parts.append("Excellent candidate - Exceeds requirements significantly.")
            elif percentage >= 80:
                assessment_parts.append("Strong candidate - Meets all key requirements.")
            else:
                assessment_parts.append("Qualified candidate - Meets minimum requirements.")
        else:
            gap = threshold - percentage
            assessment_parts.append(f"Below threshold by {gap:.1f} percentage points.")
        
        if strong_points:
            assessment_parts.append(f"Strengths: Excellent in {len(strong_points)} criteria.")
        
        if weak_points:
            assessment_parts.append(f"Improvement areas: {len(weak_points)} criteria below target.")
        
        return " ".join(assessment_parts)


# Singleton instance
scoring_engine = ScoringEngine()