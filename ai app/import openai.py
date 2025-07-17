import os
import json
import openai
from dotenv import load_dotenv
from typing import Dict, List, Optional

# Load environment variables
load_dotenv()

class PromptCraftAgent:
    """
    AI writing prompt generator with 4-layer architecture:
    1. Input Understanding
    2. State Tracking
    3. Task Planning
    4. Output Generation
    """
    
    def __init__(self):
        self._initialize_openai()
        self.memory = {
            'user_preferences': {
                'last_niches': [],
                'frequent_tones': [],
                'recent_topics': []
            },
            'session_history': []
        }
        self.max_memory_items = 5
    
    def _initialize_openai(self):
        """Initialize OpenAI API with proper error handling"""
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        openai.api_key = self.api_key
        self.model = "gpt-3.5-turbo"
        
        # Test API connection
        try:
            openai.Model.list()
        except Exception as e:
            raise ConnectionError(f"OpenAI API connection failed: {str(e)}")

    def parse_input(self, user_input: str) -> Dict:
        """
        Layer 1: Input Understanding
        Extracts structured data from user's natural language input
        """
        system_msg = """Analyze the writing prompt request and return JSON with:
        - niche (e.g., food, tech)
        - tone (e.g., serious, humorous)
        - constraints (list)
        - audience (if mentioned)"""
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            parsed = json.loads(response.choices[0].message.content)
            self._log_to_session('input_parsed', parsed)
            return parsed
            
        except Exception as e:
            self._log_to_session('error', str(e))
            return {
                "niche": "general",
                "tone": "neutral",
                "constraints": [],
                "error": str(e)
            }

    def update_memory(self, parsed_input: Dict) -> Dict:
        """
        Layer 2: State Tracker
        Maintains conversation context and user preferences
        """
        try:
            # Update niche history
            if 'niche' in parsed_input:
                self.memory['user_preferences']['last_niches'] = (
                    [parsed_input['niche']] + 
                    self.memory['user_preferences']['last_niches']
                )[:self.max_memory_items]
            
            # Update tone preferences
            if 'tone' in parsed_input:
                self.memory['user_preferences']['frequent_tones'] = (
                    [parsed_input['tone']] + 
                    self.memory['user_preferences']['frequent_tones']
                )[:self.max_memory_items]
            
            self._log_to_session('memory_updated', self.memory)
            return self.memory
            
        except Exception as e:
            self._log_to_session('error', str(e))
            return self.memory

    def plan_prompts(self, parsed_input: Dict) -> str:
        """
        Layer 3: Task Planner
        Generates strategy for creating prompts based on inputs and memory
        """
        try:
            plan_template = """Generate writing prompts by:
            1. Combining {niche} niche with {tone} tone
            2. Avoiding recent topics: {recent_topics}
            3. Considering these constraints: {constraints}
            4. Targeting {audience} audience if specified"""
            
            plan = plan_template.format(
                niche=parsed_input.get('niche', 'general'),
                tone=parsed_input.get('tone', 'neutral'),
                recent_topics=self.memory['user_preferences']['recent_topics'][:3],
                constraints=parsed_input.get('constraints', 'none'),
                audience=parsed_input.get('audience', 'general')
            )
            
            self._log_to_session('plan_created', plan)
            return plan
            
        except Exception as e:
            self._log_to_session('error', str(e))
            return "Generate diverse writing prompts"

    def generate_output(self, plan: str) -> str:
        """
        Layer 4: Output Generator
        Creates final formatted output for user
        """
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": plan},
                    {"role": "user", "content": """Format as:
                    **Main Prompt** (bold)
                    - Variation 1 (bullet)
                    - Variation 2 (bullet)
                    *Follow-up Question* (italic)"""}
                ],
                temperature=0.7
            )
            
            output = response.choices[0].message.content
            self._update_topic_memory(output)
            self._log_to_session('output_generated', output)
            return output
            
        except Exception as e:
            self._log_to_session('error', str(e))
            return "**Error generating prompts**\nPlease try again later."

    def _update_topic_memory(self, output: str):
        """Extracts keywords from output to avoid repetition"""
        try:
            if '**' in output:
                main_topic = output.split('**')[1].split('**')[0]
                self.memory['user_preferences']['recent_topics'] = (
                    [main_topic] + 
                    self.memory['user_preferences']['recent_topics']
                )[:self.max_memory_items]
        except:
            pass

    def _log_to_session(self, event_type: str, data):
        """Logs events for debugging"""
        self.memory['session_history'].append({
            'type': event_type,
            'data': data,
            'timestamp': str(datetime.now())
        })

    def run_agent(self, user_input: str) -> str:
        """Orchestrates the 4-layer workflow"""
        print(f"\n{'='*50}\nProcessing: '{user_input}'")
        
        # Layer 1: Input Understanding
        parsed_input = self.parse_input(user_input)
        print(f"\n[Input Parsed]\n{json.dumps(parsed_input, indent=2)}")
        
        # Layer 2: State Tracking
        self.update_memory(parsed_input)
        print(f"\n[Memory State]\n{json.dumps(self.memory, indent=2)}")
        
        # Layer 3: Task Planning
        plan = self.plan_prompts(parsed_input)
        print(f"\n[Generation Plan]\n{plan}")
        
        # Layer 4: Output Generation
        output = self.generate_output(plan)
        print(f"\n[Final Output]\n{output}")
        
        return output


if __name__ == "__main__":
    from datetime import datetime
    
    # Initialize agent
    agent = PromptCraftAgent()
    
    # Sample conversation
    test_inputs = [
        "Give me a funny prompt about vegan baking for Instagram",
        "Serious tech prompt about AI ethics for professionals",
        "Travel writing idea about hidden gems in Europe"
    ]
    
    for input_text in test_inputs:
        agent.run_agent(input_text)
        print("\n" + "="*50 + "\n")