import anthropic
import os
from pydantic import BaseModel, Field, field_validator
from typing import List
import json
import time
import re
import logging
from .config import get_config, compute_weighted_score

# Configure logging
logger = logging.getLogger(__name__)

class ToolAnalysis(BaseModel):
    """Structured output for tool analysis"""
    name: str = Field(description="Tool or technology name")
    description: str = Field(description="Concise description (2-3 sentences)")
    category: str = Field(description="Primary category")
    cx_relevance_score: int = Field(description="CX relevance score 1-10", ge=1, le=10)
    integration_score: int = Field(description="Integration ease score 1-10", ge=1, le=10)
    overall_score: float = Field(description="Overall score")
    key_features: List[str] = Field(description="Top 3-5 key features")
    use_cases: List[str] = Field(description="Primary CX use cases")
    integrations: List[str] = Field(description="Notable integrations")
    radar_position: str = Field(description="One of: Adopt, Trial, Assess, Hold")
    cost_rating: str = Field(description="One of: $, $$, $$$, $$$$")
    pricing_model: str = Field(description="E.g., Per seat, Usage-based, Enterprise")
    reasoning: str = Field(description="Brief explanation of radar position and scores")
    
    @field_validator('cx_relevance_score', 'integration_score')
    @classmethod
    def clamp_scores(cls, v):
        """Clamp scores to valid range 1-10"""
        return max(1, min(10, int(v)))
    
    @field_validator('radar_position')
    @classmethod
    def validate_position(cls, v):
        """Normalize radar position to valid values"""
        valid = ['Adopt', 'Trial', 'Assess', 'Hold']
        v_clean = v.strip()
        if v_clean in valid:
            return v_clean
        # Try to match case-insensitively
        for pos in valid:
            if v_clean.lower() == pos.lower():
                return pos
        logger.warning(f"Invalid radar_position '{v}', defaulting to 'Assess'")
        return 'Assess'
    
    @field_validator('cost_rating')
    @classmethod
    def validate_cost(cls, v):
        """Normalize cost rating"""
        valid = ['$', '$$', '$$$', '$$$$']
        v_clean = v.strip()
        if v_clean in valid:
            return v_clean
        logger.warning(f"Invalid cost_rating '{v}', defaulting to '$$'")
        return '$$'

class TechAnalyzer:
    def __init__(self, api_key: str, model: str = None):
        self.client = anthropic.Anthropic(api_key=api_key)
        # Default to claude-3-haiku-20240307, allow override via env
        self.model = model or os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
        
        # Load config for categories and scoring
        self.config = get_config()
        self.categories = self.config.get('categories', [
            "CRM", "Helpdesk/Support", "Analytics", "Knowledge Base",
            "Chat/Messaging", "Feedback/Survey", "Workforce Management",
            "AI/Automation", "Integration Platform", "Voice/Phone", "Other"
        ])
    
    def _extract_json(self, text: str) -> str:
        """Extract JSON from text, handling code fences and markdown"""
        # Remove markdown code fences
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        
        # Try to find JSON object boundaries
        start = text.find('{')
        end = text.rfind('}')
        
        if start != -1 and end != -1 and end > start:
            return text[start:end+1]
        
        return text.strip()
    
    def _call_api_with_retry(self, messages: list, max_retries: int = 3) -> str:
        """Call Anthropic API with exponential backoff retry logic"""
        for attempt in range(max_retries):
            try:
                message = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    temperature=0.3,
                    messages=messages
                )
                return message.content[0].text
            except anthropic.APIStatusError as e:
                # Retry on 429 (rate limit) and 5xx errors
                if e.status_code == 429 or (e.status_code >= 500 and e.status_code < 600):
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) + (attempt * 0.1)  # Exponential backoff
                        logger.warning(f"API error {e.status_code}, retrying in {wait_time:.1f}s (attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                raise
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + (attempt * 0.1)
                    logger.warning(f"Error calling API, retrying in {wait_time:.1f}s (attempt {attempt + 1}/{max_retries}): {e}")
                    time.sleep(wait_time)
                    continue
                raise
        
        raise Exception("Max retries exceeded")
    
    def analyze_tool(self, content: str, source_url: str = "") -> ToolAnalysis:
        """Analyze a tool and return structured output"""
        
        system_prompt = f"""You are a CX technology analyst for the Tools For Humanity Customer Experience team.

Your focus is on tools that help us:
- Provide excellent customer support
- Understand customer needs and satisfaction
- Streamline support workflows
- Enable our team to work efficiently
- Scale our customer operations

Analyze tools based on their value specifically for customer experience teams.

CATEGORIES: {', '.join(self.categories)}

SCORING CRITERIA (1-10):
- CX Relevance: Direct impact on customer satisfaction, support efficiency, insights
- Integration: API availability, common integrations, technical accessibility

RADAR POSITIONS:
- Adopt: Mature, proven, strong ROI, recommended for immediate use
- Trial: Promising, worth testing, emerging leaders, good for pilot
- Assess: Interesting, monitor developments, not ready yet, emerging
- Hold: Declining, better alternatives exist, poor fit, or immature

COST RATINGS:
- $: <$50/user/month or free tier suitable
- $$: $50-150/user/month
- $$$: $150-500/user/month
- $$$$: >$500/user/month or enterprise only

Calculate overall_score using weighted average based on configuration (default: 60% CX, 40% Integration).

Return ONLY valid JSON matching this exact structure (no markdown, no explanation):
{{
    "name": "string",
    "description": "string",
    "category": "string (from categories list)",
    "cx_relevance_score": 1-10,
    "integration_score": 1-10,
    "overall_score": float,
    "key_features": ["string"],
    "use_cases": ["string"],
    "integrations": ["string"],
    "radar_position": "Adopt|Trial|Assess|Hold",
    "cost_rating": "$|$$|$$$|$$$$",
    "pricing_model": "string",
    "reasoning": "string"
}}"""
        
        user_prompt = f"Analyze this tool/technology:\n\n{content}\n\nSource: {source_url}"
        
        messages = [
            {
                "role": "user",
                "content": f"{system_prompt}\n\n{user_prompt}"
            }
        ]
        
        try:
            response_text = self._call_api_with_retry(messages)
            
            # Extract and parse JSON
            json_text = self._extract_json(response_text)
            data = json.loads(json_text)
            
            # Validate and coerce with Pydantic
            analysis = ToolAnalysis(**data)
            
            # Compute weighted overall_score from config
            analysis.overall_score = compute_weighted_score(
                analysis.cx_relevance_score,
                analysis.integration_score,
                self.config
            )
            
            return analysis
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            logger.error(f"Response text: {response_text[:500]}")
            raise ValueError(f"Failed to parse JSON response from AI: {e}")
        except Exception as e:
            logger.error(f"Error analyzing tool: {e}")
            raise
    
    def compare_tools(self, tools_data: List[dict]) -> str:
        """Generate a comparison of multiple tools"""
        
        tools_info = "\n\n---\n\n".join([
            f"**{tool['name']}**\n"
            f"Category: {tool.get('category', 'N/A')}\n"
            f"Description: {tool.get('description', 'N/A')}\n"
            f"Radar Position: {tool.get('radar_position', 'N/A')}\n"
            f"Scores: CX={tool.get('cx_relevance_score', 'N/A')}, "
            f"Integration={tool.get('integration_score', 'N/A')}"
            for tool in tools_data
        ])
        
        prompt = f"""You are a CX technology analyst for Tools For Humanity. Provide an objective comparison.

Compare these tools for a CX team. Focus on:
- Best use cases for each
- Key differentiators
- Recommendations based on team size/needs

Tools to compare:
{tools_info}

Provide a clear, structured comparison in markdown."""
        
        messages = [{"role": "user", "content": prompt}]
        response_text = self._call_api_with_retry(messages)
        return response_text