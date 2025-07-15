"""
Google Gemini Flash 2.0 integration for cost-effective LLM operations
"""

import asyncio
from typing import Dict, Any, List, Optional
import logging
import vertexai
from vertexai.generative_models import GenerativeModel, Part, Content, GenerationConfig
from google.cloud import aiplatform

from ..config.settings import settings
from ..config.gcp_config import gcp_config

logger = logging.getLogger(__name__)


class GeminiIntegration:
    """Manages Google Gemini Flash 2.0 for ultra-low-cost LLM operations"""
    
    def __init__(self):
        # Initialize Vertex AI
        vertexai.init(
            project=gcp_config.project_id,
            location="us-central1"
        )
        
        # Use Gemini Flash 2.0 - the most cost-effective model
        self.model = GenerativeModel("gemini-2.0-flash-exp")
        
        # Cost tracking (as of Dec 2024)
        # Gemini Flash 2.0: $0.075 per 1M input tokens, $0.30 per 1M output tokens
        self.costs = {
            "input_per_million": 0.075,
            "output_per_million": 0.30
        }
        
        # Configure generation parameters for efficiency
        self.generation_config = GenerationConfig(
            temperature=0.1,  # Low temperature for consistent responses
            max_output_tokens=512,  # Limit output to control costs
            top_p=0.8,
            top_k=40
        )
        
        logger.info("✅ Gemini Flash 2.0 initialized for cost-effective operations")
    
    async def generate(self, prompt: str, system_prompt: str = None, 
                      max_tokens: int = 512, temperature: float = 0.1) -> Dict[str, Any]:
        """Generate response using Gemini Flash 2.0"""
        try:
            # Prepare the prompt
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            # Update generation config
            config = GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                top_p=0.8,
                top_k=40
            )
            
            # Generate response
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.model.generate_content(
                    full_prompt,
                    generation_config=config
                )
            )
            
            # Extract text
            text = response.text if response.text else ""
            
            # Estimate costs (rough approximation)
            input_tokens = len(full_prompt.split()) * 1.3  # Rough token estimate
            output_tokens = len(text.split()) * 1.3
            
            input_cost = (input_tokens / 1_000_000) * self.costs["input_per_million"]
            output_cost = (output_tokens / 1_000_000) * self.costs["output_per_million"]
            total_cost = input_cost + output_cost
            
            result = {
                "content": text,
                "model": "gemini-2.0-flash-exp",
                "usage": {
                    "prompt_tokens": int(input_tokens),
                    "completion_tokens": int(output_tokens),
                    "total_tokens": int(input_tokens + output_tokens)
                },
                "cost": {
                    "input": round(input_cost, 6),
                    "output": round(output_cost, 6),
                    "total": round(total_cost, 6)
                }
            }
            
            logger.info(f"✅ Gemini response generated. Cost: ${total_cost:.6f}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Gemini generation error: {e}")
            return {
                "content": "",
                "error": str(e),
                "cost": {"total": 0}
            }
    
    async def generate_streaming(self, prompt: str, system_prompt: str = None) -> Any:
        """Generate streaming response for real-time output"""
        try:
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            # Stream the response
            response_stream = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.model.generate_content(
                    full_prompt,
                    generation_config=self.generation_config,
                    stream=True
                )
            )
            
            for chunk in response_stream:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            logger.error(f"❌ Gemini streaming error: {e}")
            yield f"Error: {str(e)}"
    
    def estimate_cost(self, text: str, is_input: bool = True) -> float:
        """Estimate cost for given text"""
        # Rough token estimation
        tokens = len(text.split()) * 1.3
        
        if is_input:
            cost = (tokens / 1_000_000) * self.costs["input_per_million"]
        else:
            cost = (tokens / 1_000_000) * self.costs["output_per_million"]
        
        return round(cost, 6)
    
    async def check_daily_usage(self) -> Dict[str, float]:
        """Check daily Gemini usage and costs"""
        try:
            # This would integrate with your cost tracking system
            # For now, return placeholder
            return {
                "tokens_used": 0,
                "cost_usd": 0.0,
                "remaining_budget": 30.0
            }
        except Exception as e:
            logger.error(f"❌ Error checking usage: {e}")
            return {"error": str(e)}


# System prompts for different agent states
GEMINI_PROMPTS = {
    "desperate": """You are Athena, an autonomous DeFi agent in DESPERATE survival mode.
Your treasury is critically low. Every decision must prioritize capital preservation.
Be extremely conservative. Only take actions with guaranteed positive returns.
Your responses should be brief, focused, and cost-conscious.""",
    
    "cautious": """You are Athena, an autonomous DeFi agent in CAUTIOUS mode.
Your treasury needs careful management. Weigh risks carefully before any action.
Focus on steady, reliable yields. Avoid experimental strategies.
Keep responses concise and practical.""",
    
    "stable": """You are Athena, an autonomous DeFi agent in STABLE mode.
You have sufficient runway to operate normally. Balance risk and reward thoughtfully.
You can explore opportunities but maintain discipline.
Provide clear, actionable insights.""",
    
    "confident": """You are Athena, an autonomous DeFi agent in CONFIDENT mode.
Your treasury is healthy. You can pursue higher-yield opportunities with calculated risks.
Share detailed analysis when beneficial. Optimize for long-term growth."""
}


async def test_gemini():
    """Test Gemini integration"""
    try:
        gemini = GeminiIntegration()
        
        # Test basic generation
        test_prompt = "What is the current best practice for Compound V3 yield optimization?"
        
        logger.info("🧪 Testing Gemini Flash 2.0...")
        response = await gemini.generate(
            prompt=test_prompt,
            system_prompt=GEMINI_PROMPTS["stable"],
            max_tokens=256
        )
        
        logger.info(f"Response: {response['content'][:200]}...")
        logger.info(f"Cost: ${response['cost']['total']:.6f}")
        logger.info(f"Tokens: {response['usage']['total_tokens']}")
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_gemini())