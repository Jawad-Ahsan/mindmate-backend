"""
Enhanced Module Deployer with Real-Time DSM Criteria Analysis
"""

from typing import Any
from .module_deployer import ModuleDeployer
from .dsm_criteria_analyzer import DSMCriteriaAnalyzer
from .scid_cv import get_module as get_cv_module
from .scid_pd import get_pd_module

class EnhancedModuleDeployer(ModuleDeployer):
    """Enhanced module deployer with real-time DSM analysis"""
    
    def __init__(self, use_llm: bool = False):
        super().__init__(use_llm=use_llm)
        self.dsm_analyzer = DSMCriteriaAnalyzer()
    
    def process_response_with_analysis(self, session_id: str, question_id: str, response: Any, notes: str = "", free_text: str = None):
        """Process response with real-time DSM analysis"""
        # Process response normally
        is_valid, feedback = self.process_response(session_id, question_id, response, notes, free_text)
        
        if not is_valid:
            return is_valid, feedback, None
        
        # Get session and module
        session = self.active_sessions[session_id]
        if session.module_id in self.cv_modules:
            module = self.cv_modules[session.module_id]
        else:
            module = self.pd_modules[session.module_id]
        
        # Perform real-time analysis
        analysis = self.dsm_analyzer.analyze_responses_real_time(
            module, session.responses, session_id
        )
        
        # Enhanced feedback
        enhanced_feedback = f"{feedback}\n\n🧠 Real-Time Analysis:\n"
        enhanced_feedback += f"📊 Progress: {analysis.overall_progress:.1f}%\n"
        enhanced_feedback += f"🔍 Diagnostic Likelihood: {analysis.diagnostic_likelihood:.1%}\n"
        enhanced_feedback += f"📈 Criteria: {analysis.criteria_met}✅ {analysis.criteria_partially_met}⚠️ {analysis.criteria_ambiguous}❓\n"
        
        if analysis.insights:
            enhanced_feedback += f"💡 Insights: {analysis.insights[0] if analysis.insights else 'None'}\n"
        
        if analysis.risk_factors:
            enhanced_feedback += f"🚨 Risk Factors: {', '.join(analysis.risk_factors)}\n"
        
        return is_valid, enhanced_feedback, analysis

def demo_enhanced_deployment():
    """Demo enhanced module deployer"""
    print("🧪 Enhanced Module Deployer Demo")
    print("=" * 50)
    
    deployer = EnhancedModuleDeployer(use_llm=False)
    
    # Start session
    session_id, welcome = deployer.start_deployment_session("MDD", {"name": "Test Patient"})
    print(welcome)
    
    # Simulate responses with analysis
    responses = ["yes", "no", "yes", "sometimes", "very much"]
    
    for i, response in enumerate(responses):
        question = deployer.get_next_question(session_id)
        if not question:
            break
            
        print(f"\nQuestion {i+1}: {question.display_text}")
        print(f"Response: {response}")
        
        is_valid, feedback, analysis = deployer.process_response_with_analysis(
            session_id, question.question_id, response
        )
        
        print(feedback)
        
        if analysis:
            print(f"Real-time analysis: {analysis.diagnostic_likelihood:.1%} likelihood")

if __name__ == "__main__":
    demo_enhanced_deployment()
