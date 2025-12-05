"""
FIXED Nova Sonic Exit Interview Backend - STAY ON QUESTION UNTIL VALID ANSWER
Fixed: Don't move to next question until valid answer is received for current question
"""

from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Date, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from pydantic import BaseModel, EmailStr, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timezone, timedelta
import os
from dotenv import load_dotenv
import boto3
import uuid
import json
import asyncio
import base64
import traceback
import re
from collections import Counter

from aws_sdk_bedrock_runtime.client import BedrockRuntimeClient, InvokeModelWithBidirectionalStreamOperationInput
from aws_sdk_bedrock_runtime.models import InvokeModelWithBidirectionalStreamInputChunk, BidirectionalInputPayloadPart
from aws_sdk_bedrock_runtime.config import Config
from smithy_aws_core.identity.environment import EnvironmentCredentialsResolver

load_dotenv()

# ==================== DATABASE SETUP ====================
DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ==================== DATABASE MODELS ====================
class Employee(Base):
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    department = Column(String(50))
    last_working_date = Column(Date)
    status = Column(String(20), default="Resigned")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    exit_interview = relationship("ExitInterview", back_populates="employee", uselist=False)

class ExitInterview(Base):
    __tablename__ = "exit_interviews"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    form_token = Column(String(255), unique=True, nullable=False)
    completed = Column(Boolean, default=False)
    questions_json = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    employee = relationship("Employee", back_populates="exit_interview")
    responses = relationship("InterviewResponse", back_populates="interview")

class InterviewResponse(Base):
    __tablename__ = "interview_responses"
    
    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey("exit_interviews.id"))
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    interview = relationship("ExitInterview", back_populates="responses")

# ==================== PYDANTIC SCHEMAS ====================
class EmployeeCreate(BaseModel):
    name: str
    email: EmailStr
    department: str
    last_working_date: date
    questions: Optional[List[str]] = None
    
    @field_validator('name')
    def name_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()

class EmployeeResponse(BaseModel):
    id: int
    name: str
    email: str
    department: str
    last_working_date: date
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class InterviewResponseDetail(BaseModel):
    id: int
    question: str
    answer: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# ==================== BEDROCK VALIDATION & CLEANING ====================
def validate_and_clean_answer(raw_answer: str, question: str) -> tuple[bool, str]:
    """
    Use Bedrock to validate AND clean the answer
    Returns: (is_valid, cleaned_answer)
    """
    try:
        if not raw_answer or len(raw_answer.strip()) < 1:
            return False, ""
        
        # Additional pre-validation checks
        answer_lower = raw_answer.lower().strip()
        
        # Check for common non-answers
        non_answers = [
            "i don't know", "no comment", "i prefer not to say",
            "pass", "skip", "next question", "i don't want to answer",
            "are you there", "can you hear me", "do you copy"
        ]
        
        if any(non_answer in answer_lower for non_answer in non_answers):
            return False, ""
        
        # Check if it's just a rating without context
        if answer_lower in ["1", "2", "3", "4", "5", "one", "two", "three", "four", "five"]:
            return False, "Rating without context"
        
        # Check for very short answers that are likely incomplete
        if len(raw_answer.split()) < 1:
            return False, ""
        
        bedrock = boto3.client('bedrock-runtime', region_name=os.getenv("AWS_REGION", "us-east-1"))
        
        prompt = f"""Analyze if this is a valid answer to the question. Then clean it if valid.

Question: {question}
User Response: {raw_answer}

Instructions:
1. Check if this is a REAL ANSWER or just a request for repetition/clarification
2. Invalid responses include: "sorry", "repeat", "didn't hear", "come again", "pardon", etc.
3. If VALID, extract and clean the answer (remove filler words, greetings)


Respond in this exact format:
VALID: [cleaned answer]
OR
INVALID

Your response:"""

        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 150,
            "temperature": 0.1,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        })
        
        response = bedrock.invoke_model(
            body=body,
            modelId="arn:aws:bedrock:us-east-1:762233739050:inference-profile/us.anthropic.claude-3-5-sonnet-20240620-v1:0",
            accept="application/json",
            contentType="application/json"
        )
        
        response_body = json.loads(response.get('body').read())
        result = response_body.get('content', [{}])[0].get('text', '').strip()
        
        if result.startswith("VALID:"):
            cleaned = result.replace("VALID:", "").strip()
            return True, cleaned
        else:
            return False, ""
    
    except Exception as e:
        print(f"⚠️ Bedrock validation error: {e} - using fallback")
        # Enhanced fallback validation
        invalid_phrases = [
            "sorry", "repeat", "didn't hear", "come again", "pardon",
            "what was", "can you say", "didn't understand", "breaking up",
            "are you there", "can you hear me", "i can't hear", "do you copy",
            "didn't get", "didn't understand", "don't understand", "what do you mean",
            "what does that mean", "can you repeat", "say again", "what did you say",
            "i didn't get that", "i didn't get you", "didn't get you"
        ]
        
        # Check for very short answers
        if len(raw_answer.split()) < 1:
            return False, ""
        
        # Check for answers that indicate the user didn't understand the question
        if any(phrase in raw_answer.lower() for phrase in ["didn't get", "didn't understand", "don't understand", "what do you mean", "what does that mean"]):
            return False, ""
        
        raw_lower = raw_answer.lower()
        if any(phrase in raw_lower for phrase in invalid_phrases):
            return False, ""
        return True, raw_answer.strip()

# ==================== NOVA SONIC CLIENT ====================
class NovaInterviewClient:
    def __init__(self, employee_name: str, questions: List[str], websocket: WebSocket, db: Session, interview_id: int, region='us-east-1'):
        self.model_id = 'amazon.nova-sonic-v1:0'
        self.region = region
        self.employee_name = employee_name
        self.questions = questions
        self.websocket = websocket
        self.db = db
        self.interview_id = interview_id
        self.client = None
        self.stream = None
        self.is_active = False
        
        self.prompt_name = str(uuid.uuid4())
        self.system_content_name = str(uuid.uuid4())
        self.audio_content_name = str(uuid.uuid4())
        
        # ===== STATE TRACKING =====
        self.current_q_idx = -1
        self.user_answer_buffer = ""
        self.saved_responses = set()
        self.last_nova_text = ""
        self.waiting_for_answer = False
        self.question_text_buffer = []
        self.silence_counter = 0
        self.last_user_text_time = None
        self.silence_detection_task = None
        self.answer_complete = False  # Flag to track if answer is complete
        self.last_question_time = None
        self.expected_next_question = 0  # Track which question we expect next
        
        # ===== DYNAMIC QUESTION MATCHING =====
        self.question_keywords = self._extract_all_question_keywords()
        self.question_vectors = self._create_question_vectors()
    
    def _initialize_client(self):
        """Initialize Bedrock client"""
        resolver = EnvironmentCredentialsResolver()
        config = Config(
            endpoint_uri=f"https://bedrock-runtime.{self.region}.amazonaws.com",
            region=self.region,
            aws_credentials_identity_resolver=resolver
        )
        self.client = BedrockRuntimeClient(config=config)
        print("✅ Bedrock client initialized")
    
    async def send_event(self, event_json):
        """Send event to stream"""
        event = InvokeModelWithBidirectionalStreamInputChunk(
            value=BidirectionalInputPayloadPart(bytes_=event_json.encode('utf-8'))
        )
        await self.stream.input_stream.send(event)
    
    def _extract_all_question_keywords(self):
        """Extract keywords for all questions"""
        all_keywords = []
        for question in self.questions:
            keywords = self._extract_question_keywords(question)
            all_keywords.append(keywords)
        return all_keywords
    
    def _extract_question_keywords(self, question: str) -> List[str]:
        """Extract unique keywords from question for matching"""
        # Remove common words and punctuation
        common_words = {
            'the', 'a', 'an', 'is', 'was', 'were', 'are', 'your', 'you', 'to', 
            'in', 'on', 'at', 'of', 'for', 'with', 'did', 'do', 'does', 'would', 
            'could', 'should', 'and', 'that', 'have', 'this', 'will', 'would', 
            'should', 'could', 'be', 'it', 'not', 'or', 'but', 'if', 'as', 'by'
        }
        
        # Remove punctuation and convert to lowercase
        clean_question = re.sub(r'[^\w\s]', '', question.lower())
        words = clean_question.split()
        
        # Filter out common words and short words
        keywords = [w for w in words if len(w) > 3 and w not in common_words]
        
        # Return unique keywords
        return list(set(keywords))
    
    def _create_question_vectors(self):
        """Create frequency vectors for each question"""
        vectors = []
        for keywords in self.question_keywords:
            vector = Counter(keywords)
            vectors.append(vector)
        return vectors
    
    def _match_nova_question(self, nova_text: str) -> int:
        """Match Nova's question to our question list using dynamic matching"""
        nova_lower = nova_text.lower()
        
        # Clean the Nova text
        clean_nova = re.sub(r'[^\w\s]', '', nova_lower)
        nova_words = clean_nova.split()
        nova_vector = Counter(nova_words)
        
        best_match_idx = -1
        best_match_score = 0
        
        # Calculate similarity with each question
        for idx, question_vector in enumerate(self.question_vectors):
            if idx in self.saved_responses:
                continue  # Skip already answered questions
            
            # Calculate Jaccard similarity
            intersection = sum((nova_vector & question_vector).values())
            union = sum((nova_vector | question_vector).values())
            
            if union == 0:
                similarity = 0
            else:
                similarity = intersection / union
            
            # Additional bonus for exact keyword matches
            keyword_matches = sum(1 for kw in self.question_keywords[idx] if kw in nova_lower)
            keyword_bonus = keyword_matches / len(self.question_keywords[idx]) if self.question_keywords[idx] else 0
            
            # Combined score
            combined_score = (similarity * 0.6) + (keyword_bonus * 0.4)
            
            if combined_score > best_match_score and combined_score >= 0.3:  # Lowered threshold
                best_match_score = combined_score
                best_match_idx = idx
        
        if best_match_idx >= 0:
            print(f"✅ Matched Q{best_match_idx + 1} with {best_match_score:.0%} confidence")
        else:
            print(f"⚠️ No question match found in: {nova_text[:60]}...")
        
        return best_match_idx
    
    def _is_repetition(self, new_text: str, existing_buffer: str) -> bool:
        """Check if new text is likely a repetition of existing content"""
        if not existing_buffer:
            return False
        
        # Simple check for exact repetition
        if new_text.lower() in existing_buffer.lower():
            return True
        
        # Check if it's a very short fragment that might be a repetition
        if len(new_text.split()) < 3 and new_text.lower() in existing_buffer.lower():
            return True
        
        return False
    
    def _is_repetition_request(self, text: str) -> bool:
        """Check if the user is asking for repetition"""
        repetition_phrases = [
            "come again", "repeat", "say again", "what did you say", 
            "didn't hear", "didn't get that", "didn't understand",
            "can you repeat", "pardon", "sorry", "could you repeat",
            "couldn't get you", "didn't get you", "don't understand", "can't understand"
        ]
        
        text_lower = text.lower()
        return any(phrase in text_lower for phrase in repetition_phrases)
    
    def _is_technical_issue(self, text: str) -> bool:
        """Check if the user is reporting a technical issue"""
        technical_phrases = [
            "can't hear", "voice breaking", "audio issue", "technical issue",
            "voice is breaking", "can't hear your voice", "audio problem"
        ]
        
        text_lower = text.lower()
        return any(phrase in text_lower for phrase in technical_phrases)
    
    async def _check_for_silence(self):
        """Check if there's been silence long enough to consider the answer complete"""
        if not self.waiting_for_answer or not self.last_user_text_time or self.answer_complete:
            return False
        
        silence_duration = datetime.now(timezone.utc) - self.last_user_text_time
        # If silence for more than 5 seconds and we have at least 4 words, consider answer complete
        if silence_duration.total_seconds() > 5:
            word_count = len(self.user_answer_buffer.split())
            if word_count >= 4:
                # Additional check: make sure the answer doesn't indicate confusion
                answer_lower = self.user_answer_buffer.lower()
                confusion_phrases = [
                    "didn't get", "didn't understand", "don't understand", 
                    "what do you mean", "what does that mean", "can you repeat",
                    "say again", "what did you say", "i didn't get that"
                ]
                
                if not any(phrase in answer_lower for phrase in confusion_phrases):
                    return True
        return False
    
    async def _silence_detection_loop(self):
        """Background task to detect silence and save answers"""
        while self.is_active:
            await asyncio.sleep(1)  # Check every second
            
            if await self._check_for_silence() and self.user_answer_buffer.strip():
                if self.current_q_idx >= 0 and self.current_q_idx not in self.saved_responses:
                    print(f"\n🔇 SILENCE DETECTED - Saving answer for Q{self.current_q_idx + 1}")
                    success = await self._save_response_to_db(
                        self.current_q_idx,
                        self.questions[self.current_q_idx],
                        self.user_answer_buffer.strip()
                    )
                    if success:
                        self.answer_complete = True
                        self.user_answer_buffer = ""
                        self.last_user_text_time = None
                    else:
                        # Reset buffer but stay on the same question
                        print(f"⚠️ Answer not valid, resetting buffer but staying on Q{self.current_q_idx + 1}")
                        self.user_answer_buffer = ""
                        self.last_user_text_time = None
                        self.answer_complete = False
    
    async def start_session(self):
        """Start Nova Sonic session"""
        if not self.client:
            self._initialize_client()
        
        try:
            print("📡 Starting bidirectional stream...")
            self.stream = await self.client.invoke_model_with_bidirectional_stream(
                InvokeModelWithBidirectionalStreamOperationInput(model_id=self.model_id)
            )
            self.is_active = True
            print("✅ Stream started")
            
            # Start silence detection task
            self.silence_detection_task = asyncio.create_task(self._silence_detection_loop())
            
            # Session start
            await self.send_event(json.dumps({
                "event": {
                    "sessionStart": {
                        "inferenceConfiguration": {
                            "maxTokens": 1024,
                            "topP": 0.9,
                            "temperature": 0.7
                        }
                    }
                }
            }))
            
            # Prompt start with AUDIO OUTPUT
            await self.send_event(json.dumps({
                "event": {
                    "promptStart": {
                        "promptName": self.prompt_name,
                        "textOutputConfiguration": {
                            "mediaType": "text/plain"
                        },
                        "audioOutputConfiguration": {
                            "mediaType": "audio/lpcm",
                            "sampleRateHertz": 24000,
                            "sampleSizeBits": 16,
                            "channelCount": 1,
                            "voiceId": "matthew",
                            "encoding": "base64",
                            "audioType": "SPEECH"
                        }
                    }
                }
            }))
            
            # System content
            await self.send_event(json.dumps({
                "event": {
                    "contentStart": {
                        "promptName": self.prompt_name,
                        "contentName": self.system_content_name,
                        "type": "TEXT",
                        "interactive": False,
                        "role": "SYSTEM",
                        "textInputConfiguration": {
                            "mediaType": "text/plain"
                        }
                    }
                }
            }))
            
            questions_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(self.questions)])
            
            system_text = f"""You are Nova conducting an EXIT INTERVIEW with {self.employee_name}.

CRITICAL RULES:
1. Ask EXACTLY these {len(self.questions)} questions IN ORDER
2. Ask ONE question at a time
3. WAIT for the user's COMPLETE answer before moving to the next question
4. If the user asks you to repeat, repeat the SAME question again
5.Do NOT move to the next question until you receive a CLEAR, SUBSTANTIAL answer to the current question
6. Do NOT skip any questions
7. After the last question is answered, say: "Thank you for completing the exit interview. Goodbye."

QUESTIONS:
{questions_text}

Start by greeting {self.employee_name} and asking the FIRST question immediately."""

            await self.send_event(json.dumps({
                "event": {
                    "textInput": {
                        "promptName": self.prompt_name,
                        "contentName": self.system_content_name,
                        "content": system_text
                    }
                }
            }))
            
            await self.send_event(json.dumps({
                "event": {
                    "contentEnd": {
                        "promptName": self.prompt_name,
                        "contentName": self.system_content_name
                    }
                }
            }))
            
            print("✅ System prompt sent")
            asyncio.create_task(self._process_responses())
        
        except Exception as e:
            print(f"❌ Error starting session: {e}")
            traceback.print_exc()
            raise
    
    async def start_audio_input(self):
        """Start audio input"""
        await self.send_event(json.dumps({
            "event": {
                "contentStart": {
                    "promptName": self.prompt_name,
                    "contentName": self.audio_content_name,
                    "type": "AUDIO",
                    "interactive": True,
                    "role": "USER",
                    "audioInputConfiguration": {
                        "mediaType": "audio/lpcm",
                        "sampleRateHertz": 16000,
                        "sampleSizeBits": 16,
                        "channelCount": 1,
                        "audioType": "SPEECH",
                        "encoding": "base64"
                    }
                }
            }
        }))
        print("✅ Audio input started")
    
    async def send_audio_chunk(self, audio_bytes):
        """Send audio chunk"""
        if not self.is_active:
            return
        
        blob = base64.b64encode(audio_bytes).decode('utf-8')
        try:
            await self.send_event(json.dumps({
                "event": {
                    "audioInput": {
                        "promptName": self.prompt_name,
                        "contentName": self.audio_content_name,
                        "content": blob
                    }
                }
            }))
        except Exception as e:
            print(f"⚠️ Error sending audio: {e}")
    
    async def _save_response_to_db(self, q_idx: int, question: str, raw_answer: str):
        """Save response with comprehensive validation"""
        try:
            # Prevent duplicates
            if q_idx in self.saved_responses:
                print(f"⚠️ Q{q_idx + 1} already saved")
                return False
            
            # Minimum length check
            if len(raw_answer.strip()) < 1:
                print(f"⚠️ Answer too short: '{raw_answer}'")
                return False
            
            # First check if it's a repetition request
            if self._is_repetition_request(raw_answer):
                print(f"🔄 Repetition request detected, not saving as answer")
                return False
            
            # Check if it's a technical issue
            if self._is_technical_issue(raw_answer):
                print(f"🔧 Technical issue detected, not saving as answer")
                return False
            
            # USE BEDROCK FOR VALIDATION + CLEANING
            is_valid, cleaned_answer = validate_and_clean_answer(raw_answer, question)
            
            if not is_valid:
                print(f"❌ INVALID RESPONSE BLOCKED: '{raw_answer[:50]}'")
                # Notify user their response wasn't saved
                await self.websocket.send_json({
                    'type': 'validation_failed',
                    'message': 'Response was not a valid answer. Please provide a more complete answer.'
                })
                return False
            
            print(f"\n{'='*80}")
            print(f"💾 SAVING VALID RESPONSE Q{q_idx + 1}/{len(self.questions)}")
            print(f"{'='*80}")
            print(f"Question: {question}")
            print(f"Raw: {raw_answer[:80]}...")
            print(f"Cleaned: {cleaned_answer[:80]}...")
            
            # Save to DB
            db_response = InterviewResponse(
                interview_id=self.interview_id,
                question=question,
                answer=cleaned_answer
            )
            self.db.add(db_response)
            self.db.commit()
            
            self.saved_responses.add(q_idx)
            self.expected_next_question = q_idx + 1  # Update expected next question
            
            print(f"✅ SAVED Q{q_idx + 1} - Total: {len(self.saved_responses)}/{len(self.questions)}")
            print(f"{'='*80}\n")
            
            # Notify frontend
            await self.websocket.send_json({
                'type': 'response_saved',
                'q_index': q_idx,
                'question': question,
                'answer': cleaned_answer
            })
            
            return True
        
        except Exception as e:
            print(f"❌ Error saving: {e}")
            traceback.print_exc()
            try:
                self.db.rollback()
            except:
                pass
            return False
    
 

    async def _process_responses(self):
        """Process responses from Nova - NON-BLOCKING VERSION"""
        try:
            while self.is_active:
                try:
                    output = await self.stream.await_output()
                    result = await output[1].receive()
                    
                    if not result.value or not result.value.bytes_:
                        continue
                    
                    response_data = result.value.bytes_.decode('utf-8')
                    json_data = json.loads(response_data)
                    
                    if 'event' not in json_data:
                        continue
                    
                    event = json_data['event']
                    
                    # ============ TEXT OUTPUT ============
                    if 'textOutput' in event:
                        text = event['textOutput'].get('content', '')
                        role = event['textOutput'].get('role', 'ASSISTANT')
                        
                        if role == "ASSISTANT" and text.strip():
                            print(f"🤖 Nova: {text[:120]}...")
                            
                            # Send to frontend
                            await self.websocket.send_json({
                                'type': 'text',
                                'content': text,
                                'role': 'ASSISTANT'
                            })
                            
                            # Check if Nova asked a question
                            if '?' in text:
                                # Save previous answer if we have one (don't block if it fails)
                                if self.waiting_for_answer and self.user_answer_buffer.strip():
                                    if self.current_q_idx >= 0 and self.current_q_idx not in self.saved_responses:
                                        # Check if the user was asking for repetition
                                        if self._is_repetition_request(self.user_answer_buffer):
                                            print(f"🔄 User requested repetition, not saving as answer")
                                            self.user_answer_buffer = ""
                                            self.last_user_text_time = None
                                            self.answer_complete = False
                                        elif self._is_technical_issue(self.user_answer_buffer):
                                            print(f"🔧 User reported technical issue, not saving as answer")
                                            self.user_answer_buffer = ""
                                            self.last_user_text_time = None
                                            self.answer_complete = False
                                        else:
                                            # Try to save if answer is substantial enough
                                            if len(self.user_answer_buffer.strip()) >= 1 and len(self.user_answer_buffer.split()) >= 2:
                                                success = await self._save_response_to_db(
                                                    self.current_q_idx,
                                                    self.questions[self.current_q_idx],
                                                    self.user_answer_buffer.strip()
                                                )
                                                if success:
                                                    print(f"✅ Successfully saved answer for Q{self.current_q_idx + 1}")
                                                else:
                                                    print(f"⚠️ Answer validation failed for Q{self.current_q_idx + 1}, will retry")
                                                # Reset buffer regardless of success/failure
                                                self.user_answer_buffer = ""
                                                self.last_user_text_time = None
                                                self.answer_complete = False
                                            else:
                                                print(f"⚠️ Answer too short, clearing buffer")
                                                self.user_answer_buffer = ""
                                                self.last_user_text_time = None
                                                self.answer_complete = False
                                
                                # Match to question list
                                matched_idx = self._match_nova_question(text)
                                
                                # If we didn't get a match but we expect a specific question, try to use that
                                if matched_idx == -1 and self.expected_next_question < len(self.questions):
                                    print(f"⚠️ No match found, using expected question Q{self.expected_next_question + 1}")
                                    matched_idx = self.expected_next_question
                                
                                if matched_idx >= 0 and matched_idx not in self.saved_responses:
                                    # Nova asked a new question
                                    if matched_idx != self.current_q_idx:
                                        # ALWAYS move to the new question Nova is asking
                                        # Don't try to track "unanswered" questions from the past
                                        print(f"\n🔀 Moving from Q{self.current_q_idx + 1 if self.current_q_idx >= 0 else 0} to Q{matched_idx + 1}")
                                        
                                        self.current_q_idx = matched_idx
                                        self.waiting_for_answer = True
                                        self.user_answer_buffer = ""
                                        self.last_user_text_time = None
                                        self.answer_complete = False
                                        self.last_question_time = datetime.now(timezone.utc)
                                        
                                        print(f"\n❓ QUESTION {self.current_q_idx + 1}: {self.questions[self.current_q_idx][:60]}...")
                                        print(f"   Waiting for answer...\n")
                                    else:
                                        print(f"🔄 Same question Q{self.current_q_idx + 1} repeated")
                            
                            # Check for goodbye
                            elif "goodbye" in text.lower() or "thank you for completing" in text.lower():
                                print(f"\n✅ GOODBYE DETECTED")
                                
                                # Save last answer if we have one and it hasn't been saved
                                if self.waiting_for_answer and self.user_answer_buffer.strip():
                                    if self.current_q_idx >= 0 and self.current_q_idx not in self.saved_responses:
                                        # Check if the user was asking for repetition
                                        if not self._is_repetition_request(self.user_answer_buffer) and not self._is_technical_issue(self.user_answer_buffer):
                                            # Only save if we have a substantial answer
                                            if len(self.user_answer_buffer.strip()) >= 5 and len(self.user_answer_buffer.split()) >= 3:
                                                success = await self._save_response_to_db(
                                                    self.current_q_idx,
                                                    self.questions[self.current_q_idx],
                                                    self.user_answer_buffer.strip()
                                                )
                                                if not success:
                                                    print(f"⚠️ Last answer not valid, not saving")
                                            else:
                                                print(f"⚠️ Last answer too short or incomplete: '{self.user_answer_buffer}'")
                                        else:
                                            print(f"🔄 User requested repetition or reported issue at the end, not saving as answer")
                                
                                await self._finalize_interview()
                                return
                            
                            self.last_nova_text = text
                        
                        elif role == "USER" and self.waiting_for_answer and text.strip():
                            # User speaking
                            print(f"👤 User: {text[:80]}...")
                            
                            # Only add to buffer if it's a new thought (not repetition)
                            if not self._is_repetition(text, self.user_answer_buffer):
                                if self.user_answer_buffer:
                                    self.user_answer_buffer += " "
                                self.user_answer_buffer += text
                                self.last_user_text_time = datetime.now(timezone.utc)
                            
                            print(f"   [Buffer: {len(self.user_answer_buffer)} chars]")
                            
                            # Send to frontend
                            await self.websocket.send_json({
                                'type': 'text',
                                'content': text,
                                'role': 'USER'
                            })
                    
                    # ============ AUDIO OUTPUT ============
                    elif 'audioOutput' in event:
                        audio_content = event['audioOutput'].get('content', '')
                        if audio_content:
                            await self.websocket.send_json({
                                'type': 'audio',
                                'data': audio_content
                            })
                    
                    # ============ COMPLETION ============
                    elif 'completionEnd' in event:
                        print("✅ Stream completion")
                        await self._finalize_interview()
                        return
                
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    print(f"⚠️ Error in response processing: {e}")
                    traceback.print_exc()
                    continue
        
        except Exception as e:
            print(f"❌ Fatal error: {e}")
            traceback.print_exc()
            self.is_active = False
    
    async def _finalize_interview(self):
        """Finalize interview"""
        print(f"\n{'='*80}")
        print(f"🎉 INTERVIEW FINALIZATION")
        print(f"   Responses: {len(self.saved_responses)}/{len(self.questions)}")
        print(f"   Status: {'✅ COMPLETE' if len(self.saved_responses) == len(self.questions) else '⚠️ INCOMPLETE'}")
        print(f"{'='*80}\n")
        
        try:
            interview = self.db.query(ExitInterview).filter(ExitInterview.id == self.interview_id).first()
            if interview:
                interview.completed = True
                interview.employee.status = "Completed"
                self.db.commit()
        except Exception as e:
            print(f"⚠️ DB error: {e}")
        
        try:
            await self.websocket.send_json({
                'type': 'interview_complete',
                'questions_answered': len(self.saved_responses),
                'total_questions': len(self.questions)
            })
        except Exception as e:
            print(f"❌ Failed to send completion: {e}")
        
        self.is_active = False
    
    async def end_session(self):
        """End session"""
        if not self.is_active:
            return
        
        try:
            # Cancel silence detection task
            if self.silence_detection_task:
                self.silence_detection_task.cancel()
                try:
                    await self.silence_detection_task
                except asyncio.CancelledError:
                    pass
            
            await self.send_event(json.dumps({
                "event": {
                    "contentEnd": {
                        "promptName": self.prompt_name,
                        "contentName": self.audio_content_name
                    }
                }
            }))
            
            await self.send_event(json.dumps({
                "event": {
                    "promptEnd": {
                        "promptName": self.prompt_name
                    }
                }
            }))
            
            await self.send_event(json.dumps({
                "event": {
                    "sessionEnd": {}
                }
            }))
            
            await self.stream.input_stream.close()
            self.is_active = False
            print("✅ Session ended")
        
        except Exception as e:
            print(f"⚠️ Error ending session: {e}")
            self.is_active = False

# ==================== AWS SES ====================
ses_client = boto3.client('ses', region_name=os.getenv("AWS_REGION", "us-east-1"))

def send_exit_interview_email(employee_email: str, employee_name: str, form_link: str) -> bool:
    SENDER = os.getenv("SES_SENDER_EMAIL")
    SUBJECT = "🎙️ Voice Exit Interview with Nova"
    BODY_HTML = f"""
    <html><body>
        <h1>Hello {employee_name}!</h1>
        <p>Have a voice conversation with Nova for your exit interview.</p>
        <p><a href="{form_link}">Start Voice Interview</a></p>
    </body></html>
    """
    try:
        ses_client.send_email(
            Source=SENDER,
            Destination={'ToAddresses': [employee_email]},
            Message={'Subject': {'Data': SUBJECT}, 'Body': {'Html': {'Data': BODY_HTML}}}
        )
        print(f"✅ Email sent to {employee_name}")
        return True
    except Exception as e:
        print(f"❌ Email error: {e}")
        return False

def generate_unique_token() -> str:
    return str(uuid.uuid4())

def create_form_link(token: str) -> str:
    return f"{os.getenv('APP_URL', 'http://localhost:8501')}/exit_interview?token={token}"

# ==================== FASTAPI APP ====================
app = FastAPI(title="Nova Sonic Exit Interview API", version="7.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

active_sessions: Dict[str, NovaInterviewClient] = {}

# ==================== API ENDPOINTS ====================

@app.get("/")
def root():
    return {"message": "Nova Sonic Exit Interview API", "version": "7.0.0", "status": "running"}

@app.post("/api/employees", response_model=EmployeeResponse, status_code=201)
def create_employee(employee: EmployeeCreate, db: Session = Depends(get_db)):
    try:
        existing = db.query(Employee).filter(Employee.email == employee.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Employee already exists")
        
        db_employee = Employee(
            name=employee.name,
            email=employee.email,
            department=employee.department,
            last_working_date=employee.last_working_date,
            status="Resigned"
        )
        db.add(db_employee)
        db.commit()
        db.refresh(db_employee)
        
        token = generate_unique_token()
        form_link = create_form_link(token)
        
        questions_json = json.dumps(employee.questions) if employee.questions else json.dumps([
            "What was your primary reason for leaving?",
            "How would you rate your overall experience with the company on a scale of 1 to 5?",
            "How was your relationship with your manager?",
            "Did you feel valued and recognized in your role?",
            "Would you recommend our company to others? Why or why not?"
        ])
        
        db_interview = ExitInterview(
            employee_id=db_employee.id,
            form_token=token,
            completed=False,
            questions_json=questions_json
        )
        db.add(db_interview)
        db.commit()
        
        send_exit_interview_email(db_employee.email, db_employee.name, form_link)
        
        return db_employee
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/employees")
def list_employees(db: Session = Depends(get_db)):
    """Get all employees with their interview details"""
    employees = db.query(Employee).all()
    result = []
    
    for emp in employees:
        emp_dict = {
            "id": emp.id,
            "name": emp.name,
            "email": emp.email,
            "department": emp.department,
            "last_working_date": str(emp.last_working_date),
            "status": emp.status,
            "created_at": emp.created_at.isoformat() if emp.created_at else None
        }
        
        # Check if employee has an exit interview
        if emp.exit_interview:
            interview = emp.exit_interview
            emp_dict["interview"] = {
                "id": interview.id,
                "completed": bool(interview.completed),  # Ensure it's a boolean
                "questions_json": interview.questions_json,
                "created_at": interview.created_at.isoformat() if interview.created_at else None,
                "response_count": len(interview.responses) if interview.responses else 0
            }
        else:
            emp_dict["interview"] = None
        
        result.append(emp_dict)
    
    print(f"DEBUG: Returning {len(result)} employees")
    for emp in result:
        if emp['interview']:
            print(f"  - {emp['name']}: Interview ID={emp['interview']['id']}, Completed={emp['interview']['completed']}, Responses={emp['interview']['response_count']}")
    
    return result



@app.get("/api/interviews/token/{token}")
def get_interview_by_token(token: str, db: Session = Depends(get_db)):
    interview = db.query(ExitInterview).filter(ExitInterview.form_token == token).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Invalid token")
    if interview.completed:
        raise HTTPException(status_code=400, detail="Interview already completed")
    
    questions = json.loads(interview.questions_json)
    return {
        "interview_id": interview.id,
        "employee_name": interview.employee.name,
        "employee_department": interview.employee.department,
        "questions": questions,
        "total_questions": len(questions),
        "completed": interview.completed
    }

@app.websocket("/ws/interview/{token}")
async def websocket_interview(websocket: WebSocket, token: str):
    await websocket.accept()
    
    db = SessionLocal()
    session_id = str(uuid.uuid4())
    nova_client = None
    
    try:
        interview = db.query(ExitInterview).filter(ExitInterview.form_token == token).first()
        if not interview:
            await websocket.send_json({"type": "error", "message": "Invalid token"})
            return
        
        questions = json.loads(interview.questions_json)
        employee_name = interview.employee.name
        
        print(f"\n{'='*80}")
        print(f"🎙️ NEW INTERVIEW: {employee_name}")
        print(f"📋 Questions: {len(questions)}")
        print(f"{'='*80}\n")
        
        await websocket.send_json({
            "type": "session_start",
            "session_id": session_id,
            "employee_name": employee_name,
            "total_questions": len(questions),
            "timeout_seconds": 900
        })
        
        nova_client = NovaInterviewClient(
            employee_name,
            questions,
            websocket,
            db,
            interview.id,
            os.getenv("AWS_REGION", "us-east-1")
        )
        await nova_client.start_session()
        
        await asyncio.sleep(2)
        await nova_client.start_audio_input()
        
        active_sessions[session_id] = nova_client
        
        timeout_seconds = 900  # 15 minutes
        start_time = datetime.now(timezone.utc)
        
        while nova_client.is_active:
            try:
                message = await asyncio.wait_for(websocket.receive_json(), timeout=0.5)
                start_time = datetime.now(timezone.utc)
                
                if message['type'] == 'audio_chunk':
                    audio_data = base64.b64decode(message['data'])
                    await nova_client.send_audio_chunk(audio_data)
                
                elif message['type'] == 'close':
                    break
            
            except asyncio.TimeoutError:
                elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
                if elapsed > timeout_seconds:
                    print(f"⚠️ Interview timeout after {timeout_seconds}s")
                    # Notify frontend that timeout occurred
                    await websocket.send_json({
                        'type': 'timeout',
                        'message': 'Interview time limit reached'
                    })
                    # Finalize the interview
                    await nova_client._finalize_interview()
                    break
                continue
            except WebSocketDisconnect:
                print("⚠️ Client disconnected")
                break
            except Exception as e:
                print(f"⚠️ Error: {e}")
                break
    
    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc()
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except:
            pass
    finally:
        if nova_client:
            await nova_client.end_session()
        if session_id in active_sessions:
            del active_sessions[session_id]
        db.close()

@app.get("/api/interviews/{interview_id}/responses", response_model=List[InterviewResponseDetail])
def get_interview_responses(interview_id: int, db: Session = Depends(get_db)):
    """Get responses ordered by creation time"""
    return db.query(InterviewResponse).filter(
        InterviewResponse.interview_id == interview_id
    ).order_by(InterviewResponse.created_at).all()

@app.get("/api/stats")
def get_statistics(db: Session = Depends(get_db)):
    total = db.query(Employee).count()
    completed = db.query(ExitInterview).filter(ExitInterview.completed == True).count()
    return {
        "total_resignations": total,
        "completed_interviews": completed,
        "pending_interviews": total - completed,
        "completion_rate": (completed / total * 100) if total > 0 else 0
    }

def init_db():
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized!")

if __name__ == "__main__":
    init_db()
    import uvicorn
    print("\n🚀 Nova Sonic Exit Interview API v7.0.0")
    print("📡 http://0.0.0.0:8000\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)