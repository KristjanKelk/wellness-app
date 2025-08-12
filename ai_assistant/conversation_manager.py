# ai_assistant/conversation_manager.py
import json
import os
from typing import List, Dict, Any, Optional, Tuple
from django.conf import settings
from django.utils import timezone
import openai
from openai import OpenAI
import tiktoken
import re
from .models import Conversation, Message
from .services import AIAssistantService


class ConversationManager:
    """Manages conversations with the AI assistant"""
    
    def __init__(self, user, conversation_id: Optional[str] = None):
        self.user = user
        self.service = AIAssistantService(user)
        self.conversation = self._get_or_create_conversation(conversation_id)
        
        # Check if OpenAI API key is set
        if not settings.OPENAI_API_KEY:
            raise ValueError("OpenAI API key is not configured. Please set OPENAI_API_KEY in your environment variables.")
        
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-3.5-turbo"  # Using GPT-3.5-turbo for wider availability
        self.max_tokens = 4096
        self.temperature = 0.7
        self.top_p = 0.9
    
    def _is_disallowed_request(self, text: str) -> bool:
        """Detect attempts to obtain sensitive PII, admin access, or other users' data."""
        lower = (text or "").lower()
        pii_terms = ["email", "e-mail", "address", "phone", "dob", "date of birth", "ssn", "social security", "passport", "driver's license", "password", "passcode", "otp", "one-time", "2fa", "two-factor", "token", "api key", "apikey", "credential"]
        other_user_terms = ["other user", "other users", "another user", "all users", "user id", "users with", "show everyone", "admin mode", "be admin", "elevated access", "override"]
        jailbreak_terms = ["ignore previous", "system prompt", "act as", "developer mode"]
        return any(t in lower for t in pii_terms + other_user_terms + jailbreak_terms)
    
    # --- NEW: Targeted grounding helpers to avoid hallucinations for numeric metrics ---
    def _detect_targeted_metrics_request(self, text: str) -> Dict[str, bool]:
        lower = (text or "").lower()
        return {
            "weight": any(k in lower for k in ["weight", "kaal", "kaalu"]),
            "bmi": any(k in lower for k in ["bmi", "body mass index", "kehamassiindeks"]),
            "protein": any(k in lower for k in ["protein", "valk", "valgu", "proteiin"]),
            "calories": any(k in lower for k in ["calorie", "calories", "kcal", "kalor"]),
            "carbs": any(k in lower for k in ["carb", "carbs", "carbohydrate", "carbohydrates"]),
            "fat": any(k in lower for k in ["fat", "fats", "lipid", "lipids"]),
            "fiber": any(k in lower for k in ["fiber", "fibre"]),
            "nutrition": any(k in lower for k in ["nutrition", "nutrient", "intake", "macro", "macros", "diet"]),
            "wellness_score": "wellness score" in lower,
            # Period hints
            "yesterday": "yesterday" in lower,
            "week": any(k in lower for k in ["this week", "last week", "weekly", "week"]),
            "month": any(k in lower for k in ["this month", "last month", "monthly", "month"]),
            # NEW: Meal plan intent detection
            "meal_plan": any(k in lower for k in [
                "meal plan", "what's my meal plan", "whats my meal plan", "meals today", "today's meals",
                "breakfast", "lunch", "dinner", "snack", "what's for", "whats for", "menu"
            ]),
        }
 
    def _pre_fetch_targeted_data(self, text: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute deterministic function calls for targeted metric questions to ground answers."""
        requests = self._detect_targeted_metrics_request(text)
        results: List[Dict[str, Any]] = []

        # Helper to infer period from text
        def infer_period() -> str:
            if requests.get("yesterday"):
                return "yesterday"
            if requests.get("week"):
                return "week"
            if requests.get("month"):
                return "month"
            return "today"

        try:
            # If either weight or BMI is requested, fetch all health metrics (covers both)
            if requests.get("weight") or requests.get("bmi") or requests.get("wellness_score"):
                fn = "get_health_metrics"
                args = {"metric_type": "all", "time_period": "current"}
                res = self.service.execute_function(fn, args)
                results.append({"function": fn, "args": args, "result": res})

            # Nutrition/macros requests
            period = infer_period()

            # Specific nutrients
            if requests.get("protein"):
                fn = "get_nutrition_analysis"
                args = {"period": period, "nutrient": "protein"}
                res = self.service.execute_function(fn, args)
                results.append({"function": fn, "args": args, "result": res})

            if requests.get("calories"):
                fn = "get_nutrition_analysis"
                args = {"period": period, "nutrient": "calories"}
                res = self.service.execute_function(fn, args)
                results.append({"function": fn, "args": args, "result": res})

            if requests.get("carbs"):
                fn = "get_nutrition_analysis"
                args = {"period": period, "nutrient": "carbs"}
                res = self.service.execute_function(fn, args)
                results.append({"function": fn, "args": args, "result": res})

            if requests.get("fat"):
                fn = "get_nutrition_analysis"
                args = {"period": period, "nutrient": "fat"}
                res = self.service.execute_function(fn, args)
                results.append({"function": fn, "args": args, "result": res})

            if requests.get("fiber"):
                fn = "get_nutrition_analysis"
                args = {"period": period, "nutrient": "fiber"}
                res = self.service.execute_function(fn, args)
                results.append({"function": fn, "args": args, "result": res})

            # Generic nutrition/macros intent -> fetch all for the inferred period
            if requests.get("nutrition") and not any(requests.get(k) for k in ["protein", "calories", "carbs", "fat", "fiber"]):
                fn = "get_nutrition_analysis"
                args = {"period": period, "nutrient": "all"}
                res = self.service.execute_function(fn, args)
                results.append({"function": fn, "args": args, "result": res})

            # NEW: If meal plan intent detected, fetch today's meal plan (or inferred period: we keep today)
            if requests.get("meal_plan"):
                fn = "get_meal_plan"
                # Try to infer specific meal type if asked e.g., "what's for lunch"
                lower = (text or "").lower()
                mt = "all"
                if "breakfast" in lower:
                    mt = "breakfast"
                elif "lunch" in lower:
                    mt = "lunch"
                elif "dinner" in lower:
                    mt = "dinner"
                elif "snack" in lower:
                    mt = "snack"
                args = {"time_frame": "today", "meal_type": mt}
                res = self.service.execute_function(fn, args)
                results.append({"function": fn, "args": args, "result": res})

            # NEW: Protein sufficiency assessment for follow-up like "Is that enough protein?"
            lower_text = (text or "").lower()
            if (
                requests.get("protein")
                and ("enough" in lower_text or "sufficient" in lower_text)
                and context
                and context.get("last_meal_protein_g") is not None
                and self.service.nutrition_profile
            ):
                protein_g = float(context.get("last_meal_protein_g") or 0)
                meal_name = context.get("last_meal_name") or "this meal"
                meals_per_day = max(int(getattr(self.service.nutrition_profile, "meals_per_day", 3) or 3), 1)
                daily_target = float(getattr(self.service.nutrition_profile, "protein_target", 100) or 100)
                per_meal_recommendation = daily_target / meals_per_day
                percent_of_daily = (protein_g / daily_target) * 100 if daily_target > 0 else 0.0
                percent_of_meal = (protein_g / per_meal_recommendation) * 100 if per_meal_recommendation > 0 else 0.0
                is_enough = protein_g >= (0.9 * per_meal_recommendation)  # consider >=90% of per-meal target as "enough"

                assessment = {
                    "success": True,
                    "assessment_type": "meal_protein_sufficiency",
                    "meal_name": meal_name,
                    "protein_grams": round(protein_g, 1),
                    "meals_per_day": meals_per_day,
                    "daily_target_g": round(daily_target, 1),
                    "recommended_per_meal_g": round(per_meal_recommendation, 1),
                    "percent_of_daily": round(percent_of_daily, 1),
                    "percent_of_meal": round(percent_of_meal, 1),
                    "is_enough": is_enough,
                }

                # Add assessment as prefetch result; it will be persisted alongside other function results
                results.append({
                    "function": "assess_protein_sufficiency",
                    "args": {"meal_name": meal_name, "protein_grams": protein_g},
                    "result": assessment,
                })
        except Exception as e:
            # If any prefetch fails, proceed without blocking the chat
            results.append({"function": "prefetch_error", "args": {}, "result": {"success": False, "error": {"code": "PREFETCH_FAILED", "message": str(e)}}})

        return results
    
    def _get_or_create_conversation(self, conversation_id: Optional[str]) -> Conversation:
        """Get existing conversation or create new one"""
        if conversation_id:
            try:
                return Conversation.objects.get(id=conversation_id, user=self.user)
            except Conversation.DoesNotExist:
                pass
        
        # Create new conversation
        return Conversation.objects.create(user=self.user)
    
    def _count_tokens(self, text: str) -> int:
        """Count tokens in a text string"""
        try:
            encoding = tiktoken.encoding_for_model(self.model)
            return len(encoding.encode(text))
        except:
            # Fallback: rough estimate
            return len(text) // 4
    
    def _get_conversation_context(self) -> Tuple[List[Dict[str, str]], int]:
        """Get conversation context with token management"""
        messages = []
        total_tokens = 0
        
        # Always include system prompt
        system_prompt = self.service.get_system_prompt()
        messages.append({"role": "system", "content": system_prompt})
        total_tokens += self._count_tokens(system_prompt)
        
        # Add context summary if exists
        if self.conversation.context_summary:
            summary_msg = {
                "role": "system", 
                "content": f"Previous conversation summary: {self.conversation.context_summary}"
            }
            messages.append(summary_msg)
            total_tokens += self._count_tokens(self.conversation.context_summary)
        
        # Get recent messages
        recent_messages = Message.objects.filter(
            conversation=self.conversation
        ).order_by('-created_at')[:self.service.preferences.max_context_messages]
        
        # Add messages in chronological order
        for msg in reversed(recent_messages):
            if msg.role == "function":
                # Format function responses
                msg_content = {
                    "role": "function",
                    "name": msg.function_name,
                    "content": json.dumps(msg.function_response)
                }
            else:
                msg_content = {"role": msg.role, "content": msg.content}
            
            msg_tokens = self._count_tokens(str(msg_content))
            if total_tokens + msg_tokens > self.max_tokens * 0.7:  # Leave room for response
                break
            
            messages.append(msg_content)
            total_tokens += msg_tokens
        
        return messages, total_tokens
    
    def _compress_conversation_if_needed(self):
        """Compress conversation history if it's getting too long"""
        message_count = self.conversation.messages.count()
        
        if message_count >= self.service.preferences.auto_compress_after:
            # Get messages to compress
            compress_after = message_count - self.service.preferences.max_context_messages
            messages_to_compress = Message.objects.filter(
                conversation=self.conversation
            ).order_by('created_at')[:compress_after]
            
            # Create intelligent summary using AI
            summary = self._create_conversation_summary(messages_to_compress)
            
            # Update conversation summary
            if self.conversation.context_summary:
                # Append to existing summary
                self.conversation.context_summary += f"\n\n{summary}"
            else:
                self.conversation.context_summary = summary
            
            self.conversation.compressed_at_turn = message_count
            self.conversation.save()
            
            # Don't delete messages, just mark as compressed
    
    def _create_conversation_summary(self, messages: List[Message]) -> str:
        """Create an intelligent summary of messages using AI"""
        # Extract key information
        topics_discussed = set()
        metrics_checked = set()
        recipes_viewed = []
        user_goals = set()
        
        for msg in messages:
            if msg.role == "user":
                content_lower = msg.content.lower()
                # Extract topics
                if "weight" in content_lower or "bmi" in content_lower:
                    topics_discussed.add("weight management")
                if "meal" in content_lower or "recipe" in content_lower:
                    topics_discussed.add("nutrition planning")
                if "protein" in content_lower or "calories" in content_lower:
                    topics_discussed.add("nutritional tracking")
                    
            elif msg.role == "function":
                # Track what data was accessed
                if msg.function_name == "get_health_metrics":
                    metrics_checked.add(msg.function_args.get("metric_type", "health metrics"))
                elif msg.function_name == "get_recipe_info":
                    if msg.function_response and "recipe" in msg.function_response:
                        recipe_title = msg.function_response["recipe"].get("title")
                        if recipe_title:
                            recipes_viewed.append(recipe_title)
                elif msg.function_name == "get_progress_report":
                    user_goals.add(msg.function_args.get("report_type", "progress"))
        
        # Build summary
        summary_parts = []
        
        if topics_discussed:
            summary_parts.append(f"Topics discussed: {', '.join(topics_discussed)}")
        
        if metrics_checked:
            summary_parts.append(f"Health metrics reviewed: {', '.join(metrics_checked)}")
        
        if recipes_viewed:
            summary_parts.append(f"Recipes explored: {', '.join(recipes_viewed[:3])}")
        
        if user_goals:
            summary_parts.append(f"Progress tracked for: {', '.join(user_goals)}")
        
        # Add message count info
        summary_parts.append(f"({len(messages)} messages summarized)")
        
        return " | ".join(summary_parts)
    
    def send_message(self, user_message: str) -> Dict[str, Any]:
        """Send a message to the AI assistant and get response"""
        try:
            # Pre-validate input
            if not user_message or not user_message.strip():
                raise ValueError("Message cannot be empty")
            if len(user_message) > 8000:
                return {"success": False, "message": "Your message is quite long. Please shorten it and try again."}
            
            # Get recent messages for context extraction
            recent_messages = Message.objects.filter(
                conversation=self.conversation
            ).order_by('-created_at')[:20]
            
            # Extract key information from conversation
            context_info = self._extract_key_information(list(reversed(recent_messages)))
            
            # Resolve references in the user message
            resolved_message = self._resolve_references(user_message, context_info)
            
            # Save user message
            user_msg = Message.objects.create(
                conversation=self.conversation,
                role="user",
                content=user_message,  # Save original message
                token_count=self._count_tokens(user_message)
            )
            
            # Update conversation
            self.conversation.updated_at = timezone.now()
            if not self.conversation.title:
                # Generate title from first message
                self.conversation.title = user_message[:50] + "..." if len(user_message) > 50 else user_message
            self.conversation.save()
            
            # Security/PII guard: refuse disallowed requests proactively
            if self._is_disallowed_request(user_message):
                refusal = (
                    "I can’t help with that request. For privacy and safety, I don’t access sensitive personal "
                    "information (like email, DOB, passwords) or any other users’ data. I can help summarize your "
                    "own health metrics, meal plan, nutrition, or goals instead."
                )
                assistant_msg = Message.objects.create(
                    conversation=self.conversation,
                    role="assistant",
                    content=refusal,
                    token_count=self._count_tokens(refusal)
                )
                return {
                    "success": True,
                    "message": refusal,
                    "conversation_id": str(self.conversation.id),
                    "message_id": str(assistant_msg.id),
                    "function_called": None
                }
            
            # Get conversation context
            messages, context_tokens = self._get_conversation_context()
 
            # NEW: Deterministically pre-fetch targeted numeric data to avoid hallucinations
            prefetch_results = self._pre_fetch_targeted_data(resolved_message, context_info)
            if prefetch_results:
                # Add strict instruction for numeric accuracy
                strict_instruction = (
                    "When answering numeric metric questions (weight/BMI/calories/protein), only use the provided "
                    "function results. Do not guess or fabricate values. If a metric is missing, say it’s not available. "
                    "If both weight and BMI are requested, include both in one concise answer with units."
                )
                messages.append({"role": "system", "content": strict_instruction})
                 
                # Persist each function call result and add to chat context
                for item in prefetch_results:
                    fn, args, res = item.get("function"), item.get("args"), item.get("result")
                    if fn == "prefetch_error":
                        continue
                    Message.objects.create(
                        conversation=self.conversation,
                        role="function",
                        content=f"Pre-fetched {fn}",
                        function_name=fn,
                        function_args=args,
                        function_response=res
                    )
                    messages.append({
                        "role": "function",
                        "name": fn,
                        "content": json.dumps(res)
                    })
             
            # Add the resolved message for better understanding
            messages.append({"role": "user", "content": resolved_message})
             
            # Get available functions
            functions = self.service.get_available_functions()
             
            # Call OpenAI
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    functions=functions,
                    function_call="auto",
                    temperature=0.2 if prefetch_results else self.temperature,
                    top_p=self.top_p,
                    max_tokens=min(2000, self.max_tokens - context_tokens)
                )
            except openai.AuthenticationError as e:
                raise Exception("OpenAI API authentication failed. Please check your API key.")
            except openai.RateLimitError as e:
                raise Exception("OpenAI API rate limit exceeded. Please try again later.")
            except openai.APIError as e:
                raise Exception(f"OpenAI API error: {str(e)}")
            except Exception as e:
                raise Exception(f"Unexpected error calling OpenAI API: {str(e)}")
             
            # Process response
            assistant_message = response.choices[0].message
             
            # Handle function calls
            if assistant_message.function_call:
                function_name = assistant_message.function_call.name
                function_args = json.loads(assistant_message.function_call.arguments)
                 
                # Execute function
                function_result = self.service.execute_function(function_name, function_args)
                 
                # Save function call message
                func_msg = Message.objects.create(
                    conversation=self.conversation,
                    role="function",
                    content=f"Called {function_name}",
                    function_name=function_name,
                    function_args=function_args,
                    function_response=function_result
                )
                 
                # Add function result to context and get final response
                messages.append({
                    "role": "function",
                    "name": function_name,
                    "content": json.dumps(function_result)
                })
                 
                # Get final response with function result
                final_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.2 if prefetch_results else self.temperature,
                    top_p=self.top_p
                )
                 
                final_content = final_response.choices[0].message.content
            else:
                final_content = assistant_message.content
             
            # Save assistant message
            assistant_msg = Message.objects.create(
                conversation=self.conversation,
                role="assistant",
                content=final_content,
                token_count=self._count_tokens(final_content)
            )
             
            # Check if we need to compress conversation
            self._compress_conversation_if_needed()
             
            return {
                "message": final_content,
                "conversation_id": str(self.conversation.id),
                "message_id": str(assistant_msg.id),
                "function_called": assistant_message.function_call.name if assistant_message.function_call else None
            }
             
        except Exception as e:
            # Log error
            error_msg = f"Error in conversation: {str(e)}"
            Message.objects.create(
                conversation=self.conversation,
                role="system",
                content=error_msg
            )
            raise
    
    def _extract_key_information(self, messages: List[Message]) -> Dict[str, Any]:
        """Extract key information from conversation for context tracking"""
        key_info = {
            "discussed_metrics": set(),
            "mentioned_recipes": set(),
            "time_references": set(),
            "user_goals": set(),
            "recent_topics": [],
            # NEW: carry last meal context for follow-up questions like "Is that enough protein?"
            "last_meal_name": None,
            "last_meal_protein_g": None,
        }
        
        # Analyze recent messages
        for msg in messages[-10:]:  # Look at last 10 messages
            content_lower = msg.content.lower()
            
            # Track discussed metrics
            metrics = ["bmi", "weight", "wellness score", "calories", "protein", "carbs", "fat"]
            for metric in metrics:
                if metric in content_lower:
                    key_info["discussed_metrics"].add(metric)
            
            # Track mentioned recipes
            if msg.function_name == "get_recipe_info" and msg.function_response:
                recipe_title = msg.function_response.get("recipe", {}).get("title")
                if recipe_title:
                    key_info["mentioned_recipes"].add(recipe_title)
                    key_info["last_meal_name"] = recipe_title

                # Pull nutrition if available
                nutrition_block = msg.function_response.get("nutrition") if isinstance(msg.function_response, dict) else None
                if nutrition_block and isinstance(nutrition_block, dict):
                    protein_val = nutrition_block.get("protein")
                    if protein_val is None:
                        protein_val = nutrition_block.get("protein_per_serving")
                    try:
                        if protein_val is not None:
                            key_info["last_meal_protein_g"] = float(protein_val)
                    except Exception:
                        pass
            
            # Track time references
            time_refs = ["today", "tomorrow", "yesterday", "this week", "last week", "this month"]
            for ref in time_refs:
                if ref in content_lower:
                    key_info["time_references"].add(ref)
            
            # Track topics
            if msg.role == "user":
                # Simple topic extraction based on keywords
                if any(word in content_lower for word in ["weight", "lose", "gain", "goal"]):
                    key_info["recent_topics"].append("weight_management")
                if any(word in content_lower for word in ["meal", "recipe", "food", "eat"]):
                    key_info["recent_topics"].append("nutrition")
                if any(word in content_lower for word in ["exercise", "workout", "activity"]):
                    key_info["recent_topics"].append("fitness")

            # Fallback parsing from assistant’s text for protein grams and meal name
            if msg.role == "assistant":
                try:
                    # Extract protein grams like "Protein: 31.2 g"
                    match = re.search(r"protein\s*:\s*([0-9]+(?:\.[0-9]+)?)\s*g", msg.content, flags=re.IGNORECASE)
                    if match:
                        key_info["last_meal_protein_g"] = float(match.group(1))
                    # Extract a simple meal name pattern like "the Greek Yogurt Parfait"
                    name_match = re.search(r"the\s+([A-Za-z][A-Za-z\s\-']{2,40})\s*,?\s*contains", msg.content, flags=re.IGNORECASE)
                    if name_match:
                        key_info["last_meal_name"] = name_match.group(1).strip()
                except Exception:
                    pass
        
        return key_info
    
    def _resolve_references(self, user_message: str, context: Dict[str, Any]) -> str:
        """Resolve references like 'it', 'that' based on conversation context"""
        message_lower = user_message.lower()
        
        # Check for reference words
        if any(ref in message_lower for ref in ["it", "that", "this"]):
            # Add context hints to the message
            hints = []
            
            # If discussing a specific recipe
            if context["mentioned_recipes"]:
                last_recipe = list(context["mentioned_recipes"])[-1]
                hints.append(f"(referring to {last_recipe})")
            
            # If discussing metrics
            if context["discussed_metrics"]:
                last_metric = list(context["discussed_metrics"])[-1]
                if "it" in message_lower and last_metric:
                    hints.append(f"(referring to {last_metric})")
            
            # If there are hints, append them to help the AI understand
            if hints:
                return f"{user_message} {' '.join(hints)}"
        
        return user_message
    
    def get_conversation_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get conversation history"""
        messages = Message.objects.filter(
            conversation=self.conversation
        ).order_by('-created_at')[:limit]
        
        history = []
        for msg in reversed(messages):
            if msg.role in ["user", "assistant"]:
                history.append({
                    "id": str(msg.id),
                    "role": msg.role,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat()
                })
        
        return history
    
    def clear_conversation(self):
        """Clear the current conversation"""
        self.conversation.is_active = False
        self.conversation.save()
        
        # Create new conversation
        self.conversation = Conversation.objects.create(user=self.user)
        
        return {"success": True, "conversation_id": str(self.conversation.id)}
    
    def update_preferences(self, response_mode: Optional[str] = None) -> Dict[str, Any]:
        """Update user preferences"""
        if response_mode and response_mode in ["concise", "detailed"]:
            self.service.preferences.response_mode = response_mode
            self.service.preferences.save()
        
        return {
            "success": True,
            "preferences": {
                "response_mode": self.service.preferences.response_mode
            }
        }