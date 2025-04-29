from typing import Dict, List, Any, Optional, Tuple, Union
import json
from datetime import datetime
import uuid

from config.logging_config import get_logger
from .llm_wrapper import default_llm, LLMResponse
from memory import memory_manager

logger = get_logger(__name__)


class AgentPlanner:
    def __init__(self, agent_id: str, model: Optional[str] = None) -> None:
        self.agent_id = agent_id
        self.llm = default_llm
        self.model = model
    
    async def create_plan(
        self,
        goal: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        try:
            context = context or {}
            messages = self._build_planning_messages(goal, context)
            
            plan_data = await self.llm.generate_json(
                messages=messages,
                model=self.model,
            )
            
            # Validate and normalize plan
            plan = self._normalize_plan(plan_data, goal)
            
            # Store the plan in short-term memory
            await memory_manager.add_memory(
                agent_id=self.agent_id,
                text=json.dumps(plan),
                metadata={
                    "type": "plan",
                    "goal": goal,
                },
                memory_type="short_term",
            )
            
            return plan
        except Exception as e:
            logger.error(f"Error creating plan: {str(e)}")
            return self._fallback_plan(goal)
    
    async def refine_plan(
        self,
        plan: Dict[str, Any],
        goal: str,
        context: Dict[str, Any],
        current_step: int,
        result: Optional[str] = None,
        error: Optional[str] = None,
    ) -> Dict[str, Any]:
        try:
            messages = self._build_refinement_messages(plan, goal, context, current_step, result, error)
            
            refined_data = await self.llm.generate_json(
                messages=messages,
                model=self.model,
            )
            
            # If model returned a completely new plan
            if "steps" in refined_data and "goal" in refined_data:
                refined_plan = self._normalize_plan(refined_data, goal)
            else:
                # Update specific parts of the existing plan
                refined_plan = plan.copy()
                
                # Update remaining steps if provided
                if "next_steps" in refined_data:
                    # Replace remaining steps
                    remaining_idx = current_step
                    refined_plan["steps"] = plan["steps"][:remaining_idx] + refined_data["next_steps"]
                
                # Update reasoning if provided
                if "reasoning" in refined_data:
                    refined_plan["reasoning"] = refined_data["reasoning"]
                
                if "thought" in refined_data:
                    refined_plan["thought"] = refined_data["thought"]
            
            # Store the refined plan
            await memory_manager.add_memory(
                agent_id=self.agent_id,
                text=json.dumps(refined_plan),
                metadata={
                    "type": "refined_plan",
                    "goal": goal,
                    "current_step": current_step,
                },
                memory_type="short_term",
            )
            
            return refined_plan
        except Exception as e:
            logger.error(f"Error refining plan: {str(e)}")
            return plan  # Return original plan on error
    
    async def reflect_on_task(
        self,
        goal: str,
        plan: Dict[str, Any],
        results: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        try:
            context = context or {}
            messages = self._build_reflection_messages(goal, plan, results, context)
            
            reflection_data = await self.llm.generate_json(
                messages=messages,
                model=self.model,
            )
            
            # Store reflection in long-term memory
            await memory_manager.add_memory(
                agent_id=self.agent_id,
                text=json.dumps(reflection_data),
                metadata={
                    "type": "reflection",
                    "goal": goal,
                },
                memory_type="long_term",
            )
            
            return reflection_data
        except Exception as e:
            logger.error(f"Error creating reflection: {str(e)}")
            return {
                "success": False,
                "reasoning": f"Failed to reflect on task: {str(e)}",
                "learning": "No learning could be generated due to an error.",
                "next_steps": []
            }
    
    def _build_planning_messages(
        self,
        goal: str,
        context: Dict[str, Any],
    ) -> List[Dict[str, str]]:
        available_tools = context.get("available_tools", [])
        tools_desc = "\n".join([f"- {t['name']}: {t['description']}" for t in available_tools])
        
        system_message = f"""You are an autonomous agent tasked with planning how to achieve a goal.
Given a goal, create a step-by-step plan to achieve it.

You have the following tools available:
{tools_desc}

Consider:
1. What information you need to gather
2. What actions to take and in what order
3. How to handle potential errors or edge cases

Respond with a JSON object containing the following fields:
{{
  "goal": "the overall goal",
  "thought": "your reasoning about the approach",
  "steps": [
    {{ 
      "id": 1,
      "description": "specific action to take",
      "tool": "optional tool to use for this step",
      "tool_args": {{}} 
    }},
    ...
  ]
}}"""
        
        user_message = f"Goal: {goal}\n\n"
        
        # Add context if available
        if "recent_tasks" in context:
            user_message += "Recent tasks:\n"
            for task in context["recent_tasks"]:
                user_message += f"- {task['goal']}: {task['status']}\n"
        
        if "memories" in context and context["memories"]:
            user_message += "\nRelevant memories:\n"
            for memory in context["memories"]:
                user_message += f"- {memory['text']}\n"
        
        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
    
    def _build_refinement_messages(
        self,
        plan: Dict[str, Any],
        goal: str,
        context: Dict[str, Any],
        current_step: int,
        result: Optional[str] = None,
        error: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        steps_json = json.dumps(plan["steps"], indent=2)
        
        system_message = """You are an autonomous agent refining a plan based on new information.
Analyze the execution results of the current step and determine if the plan needs adjustment.

Respond with either:
1. A complete new plan JSON if major changes are needed:
{
  "goal": "the goal",
  "thought": "your new reasoning",
  "steps": [array of step objects]
}

2. OR just the modified parts:
{
  "reasoning": "why changes are needed",
  "next_steps": [array of new steps to replace remaining steps]
}"""
        
        user_message = f"""Goal: {goal}

Current plan:
{steps_json}

Current step: {current_step} - {plan['steps'][current_step]['description'] if current_step < len(plan['steps']) else 'N/A'}

Execution result: {result or 'N/A'}
Error: {error or 'None'}

Should the plan be adjusted based on this information? If so, provide the updated plan or next steps."""
        
        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
    
    def _build_reflection_messages(
        self,
        goal: str,
        plan: Dict[str, Any],
        results: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, str]]:
        context = context or {}
        
        # Format the results
        results_text = ""
        for i, result in enumerate(results):
            step_desc = plan["steps"][i]["description"] if i < len(plan["steps"]) else "Unknown step"
            status = "Success" if result.get("success", False) else "Failed"
            result_text = result.get("result", "No result")
            error_text = result.get("error", "None")
            
            results_text += f"Step {i+1}: {step_desc}\n"
            results_text += f"Status: {status}\n"
            results_text += f"Result: {result_text}\n"
            if error_text != "None":
                results_text += f"Error: {error_text}\n"
            results_text += "\n"
        
        system_message = """You are an autonomous agent reflecting on a completed task.
Analyze the execution and results of the task to generate insights.

Respond with a JSON object containing the following fields:
{
  "success": boolean indicating overall success,
  "reasoning": "your analysis of what went well and what didn't",
  "learning": "key lessons or insights from this task",
  "next_steps": ["suggestions for follow-up actions or improvements"]
}"""
        
        user_message = f"""Goal: {goal}

Plan: 
{json.dumps(plan, indent=2)}

Results:
{results_text}

Please reflect on this task execution, analyzing the approach, results, and what could be improved."""
        
        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
    
    def _normalize_plan(self, plan_data: Dict[str, Any], goal: str) -> Dict[str, Any]:
        try:
            normalized = {
                "id": str(uuid.uuid4()),
                "goal": plan_data.get("goal", goal),
                "thought": plan_data.get("thought", "No initial reasoning provided"),
                "created_at": datetime.now().isoformat(),
                "steps": []
            }
            
            # Normalize steps
            steps = plan_data.get("steps", [])
            for i, step in enumerate(steps):
                normalized_step = {
                    "id": step.get("id", i + 1),
                    "description": step.get("description", f"Step {i+1}"),
                    "tool": step.get("tool"),
                    "tool_args": step.get("tool_args", {})
                }
                normalized["steps"].append(normalized_step)
            
            return normalized
        except Exception as e:
            logger.error(f"Error normalizing plan: {str(e)}")
            return self._fallback_plan(goal)
    
    def _fallback_plan(self, goal: str) -> Dict[str, Any]:
        return {
            "id": str(uuid.uuid4()),
            "goal": goal,
            "thought": "Failed to create a detailed plan. Using fallback simple plan.",
            "created_at": datetime.now().isoformat(),
            "steps": [
                {
                    "id": 1,
                    "description": f"Analyze the goal: {goal}",
                    "tool": None,
                    "tool_args": {}
                },
                {
                    "id": 2,
                    "description": "Search for relevant information",
                    "tool": "web_search",
                    "tool_args": {"query": goal, "num_results": 3}
                },
                {
                    "id": 3,
                    "description": "Summarize findings and report results",
                    "tool": None,
                    "tool_args": {}
                }
            ]
        }