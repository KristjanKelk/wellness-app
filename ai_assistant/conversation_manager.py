# ai_assistant/conversation_manager.py
import json
import os
from typing import List, Dict, Any, Optional, Tuple
from django.conf import settings
from django.utils import timezone
import openai
from openai import OpenAI
import tiktoken
from .models import Conversation, Message
from .services import AIAssistantService


class ConversationManager:
    """Manages conversations with the AI assistant"""
    
    def __init__(self, user, conversation_id: Optional[str] = None):
        self.user = user
        self.service = AIAssistantService(user)
        self.conversation = self._get_or_create_conversation(conversation_id)
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4o-mini"  # Using GPT-4o mini for efficiency
        self.max_tokens = 4096
        self.temperature = 0.7
        self.top_p = 0.9
        
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
            
            # Create summary
            summary_parts = []
            for msg in messages_to_compress:
                if msg.role == "user":
                    summary_parts.append(f"User asked about: {msg.content[:100]}")
                elif msg.role == "assistant" and msg.function_name:
                    summary_parts.append(f"Assistant retrieved: {msg.function_name}")
            
            # Update conversation summary
            self.conversation.context_summary = " | ".join(summary_parts[-10:])  # Keep last 10 items
            self.conversation.compressed_at_turn = message_count
            self.conversation.save()
            
            # Don't delete messages, just mark as compressed
    
    def send_message(self, user_message: str) -> Dict[str, Any]:
        """Send a message and get AI response"""
        try:
            # Save user message
            user_msg = Message.objects.create(
                conversation=self.conversation,
                role="user",
                content=user_message,
                token_count=self._count_tokens(user_message)
            )
            
            # Update conversation
            self.conversation.updated_at = timezone.now()
            if not self.conversation.title:
                # Generate title from first message
                self.conversation.title = user_message[:50] + "..." if len(user_message) > 50 else user_message
            self.conversation.save()
            
            # Get conversation context
            messages, context_tokens = self._get_conversation_context()
            messages.append({"role": "user", "content": user_message})
            
            # Get available functions
            functions = self.service.get_available_functions()
            
            # Call OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                functions=functions,
                function_call="auto",
                temperature=self.temperature,
                top_p=self.top_p,
                max_tokens=min(2000, self.max_tokens - context_tokens)
            )
            
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
                    temperature=self.temperature,
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
            
            # Compress if needed
            self._compress_conversation_if_needed()
            
            return {
                "success": True,
                "message": final_content,
                "conversation_id": str(self.conversation.id),
                "message_id": str(assistant_msg.id)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "I apologize, but I encountered an error processing your request. Please try again."
            }
    
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