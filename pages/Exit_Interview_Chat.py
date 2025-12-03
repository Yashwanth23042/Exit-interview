


# # # # # # # # # # # """
# # # # # # # # # # # WORKING Nova Sonic Exit Interview Backend - FULLY FIXED VERSION

# # # # # # # # # # # Installation required:
# # # # # # # # # # # pip install git+https://github.com/awslabs/aws-sdk-python-bedrock.git
# # # # # # # # # # # pip install fastapi uvicorn sqlalchemy psycopg2-binary websockets
# # # # # # # # # # # """

# # # # # # # # # # # from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
# # # # # # # # # # # from fastapi.middleware.cors import CORSMiddleware
# # # # # # # # # # # from sqlalchemy import create_engine, Column, Integer, String, Boolean, Date, DateTime, Text, ForeignKey
# # # # # # # # # # # from sqlalchemy.ext.declarative import declarative_base
# # # # # # # # # # # from sqlalchemy.orm import sessionmaker, Session, relationship
# # # # # # # # # # # from pydantic import BaseModel, EmailStr, field_validator
# # # # # # # # # # # from typing import List, Optional, Dict, Any
# # # # # # # # # # # from datetime import datetime, date
# # # # # # # # # # # import os
# # # # # # # # # # # from dotenv import load_dotenv
# # # # # # # # # # # import boto3
# # # # # # # # # # # import uuid
# # # # # # # # # # # import json
# # # # # # # # # # # import asyncio
# # # # # # # # # # # import base64
# # # # # # # # # # # import traceback
# # # # # # # # # # # import re

# # # # # # # # # # # # Import Nova Sonic experimental SDK
# # # # # # # # # # # from aws_sdk_bedrock_runtime.client import BedrockRuntimeClient, InvokeModelWithBidirectionalStreamOperationInput
# # # # # # # # # # # from aws_sdk_bedrock_runtime.models import InvokeModelWithBidirectionalStreamInputChunk, BidirectionalInputPayloadPart
# # # # # # # # # # # from aws_sdk_bedrock_runtime.config import Config
# # # # # # # # # # # from smithy_aws_core.identity.environment import EnvironmentCredentialsResolver

# # # # # # # # # # # load_dotenv()

# # # # # # # # # # # # ==================== DATABASE SETUP ====================
# # # # # # # # # # # DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

# # # # # # # # # # # engine = create_engine(DATABASE_URL)
# # # # # # # # # # # SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# # # # # # # # # # # Base = declarative_base()

# # # # # # # # # # # # ==================== DATABASE MODELS ====================
# # # # # # # # # # # class Employee(Base):
# # # # # # # # # # #     __tablename__ = "employees"
    
# # # # # # # # # # #     id = Column(Integer, primary_key=True, index=True)
# # # # # # # # # # #     name = Column(String(100), nullable=False)
# # # # # # # # # # #     email = Column(String(100), unique=True, nullable=False)
# # # # # # # # # # #     department = Column(String(50))
# # # # # # # # # # #     last_working_date = Column(Date)
# # # # # # # # # # #     status = Column(String(20), default="Resigned")
# # # # # # # # # # #     created_at = Column(DateTime, default=datetime.utcnow)
    
# # # # # # # # # # #     exit_interview = relationship("ExitInterview", back_populates="employee", uselist=False)

# # # # # # # # # # # class ExitInterview(Base):
# # # # # # # # # # #     __tablename__ = "exit_interviews"
    
# # # # # # # # # # #     id = Column(Integer, primary_key=True, index=True)
# # # # # # # # # # #     employee_id = Column(Integer, ForeignKey("employees.id"))
# # # # # # # # # # #     form_token = Column(String(255), unique=True, nullable=False)
# # # # # # # # # # #     completed = Column(Boolean, default=False)
# # # # # # # # # # #     questions_json = Column(Text)
# # # # # # # # # # #     conversation_transcript = Column(Text)
# # # # # # # # # # #     created_at = Column(DateTime, default=datetime.utcnow)
    
# # # # # # # # # # #     employee = relationship("Employee", back_populates="exit_interview")
# # # # # # # # # # #     responses = relationship("InterviewResponse", back_populates="interview")

# # # # # # # # # # # class InterviewResponse(Base):
# # # # # # # # # # #     __tablename__ = "interview_responses"
    
# # # # # # # # # # #     id = Column(Integer, primary_key=True, index=True)
# # # # # # # # # # #     interview_id = Column(Integer, ForeignKey("exit_interviews.id"))
# # # # # # # # # # #     question = Column(Text, nullable=False)
# # # # # # # # # # #     answer = Column(Text)
# # # # # # # # # # #     created_at = Column(DateTime, default=datetime.utcnow)
    
# # # # # # # # # # #     interview = relationship("ExitInterview", back_populates="responses")

# # # # # # # # # # # # ==================== PYDANTIC SCHEMAS ====================
# # # # # # # # # # # class EmployeeCreate(BaseModel):
# # # # # # # # # # #     name: str
# # # # # # # # # # #     email: EmailStr
# # # # # # # # # # #     department: str
# # # # # # # # # # #     last_working_date: date
# # # # # # # # # # #     questions: Optional[List[str]] = None
    
# # # # # # # # # # #     @field_validator('name')
# # # # # # # # # # #     def name_must_not_be_empty(cls, v):
# # # # # # # # # # #         if not v or not v.strip():
# # # # # # # # # # #             raise ValueError('Name cannot be empty')
# # # # # # # # # # #         return v.strip()

# # # # # # # # # # # class EmployeeResponse(BaseModel):
# # # # # # # # # # #     id: int
# # # # # # # # # # #     name: str
# # # # # # # # # # #     email: str
# # # # # # # # # # #     department: str
# # # # # # # # # # #     last_working_date: date
# # # # # # # # # # #     status: str
# # # # # # # # # # #     created_at: datetime
    
# # # # # # # # # # #     class Config:
# # # # # # # # # # #         from_attributes = True

# # # # # # # # # # # class InterviewStatusResponse(BaseModel):
# # # # # # # # # # #     id: int
# # # # # # # # # # #     completed: bool
# # # # # # # # # # #     form_token: str
# # # # # # # # # # #     created_at: datetime
    
# # # # # # # # # # #     class Config:
# # # # # # # # # # #         from_attributes = True

# # # # # # # # # # # class EmployeeWithInterview(BaseModel):
# # # # # # # # # # #     id: int
# # # # # # # # # # #     name: str
# # # # # # # # # # #     email: str
# # # # # # # # # # #     department: str
# # # # # # # # # # #     last_working_date: date
# # # # # # # # # # #     status: str
# # # # # # # # # # #     created_at: datetime
# # # # # # # # # # #     interview: Optional[InterviewStatusResponse] = None
    
# # # # # # # # # # #     class Config:
# # # # # # # # # # #         from_attributes = True

# # # # # # # # # # # class InterviewResponseDetail(BaseModel):
# # # # # # # # # # #     id: int
# # # # # # # # # # #     question: str
# # # # # # # # # # #     answer: str
# # # # # # # # # # #     created_at: datetime
    
# # # # # # # # # # #     class Config:
# # # # # # # # # # #         from_attributes = True

# # # # # # # # # # # # ==================== BEDROCK PROCESSING ====================
# # # # # # # # # # # def process_user_answer_with_bedrock(raw_answer: str, question: str) -> str:
# # # # # # # # # # #     """
# # # # # # # # # # #     Process user answer with Bedrock to extract relevant response
# # # # # # # # # # #     """
# # # # # # # # # # #     try:
# # # # # # # # # # #         bedrock = boto3.client('bedrock-runtime', region_name=os.getenv("AWS_REGION", "us-east-1"))
        
# # # # # # # # # # #         prompt = f"""
# # # # # # # # # # #         You are analyzing a user's response to an exit interview question. 
# # # # # # # # # # #         Your task is to extract the core answer and remove any conversational filler, greetings, or irrelevant parts.
        
# # # # # # # # # # #         Question: {question}
# # # # # # # # # # #         User Response: {raw_answer}
        
# # # # # # # # # # #         Please provide only the cleaned, relevant answer without any additional commentary:
# # # # # # # # # # #         """
        
# # # # # # # # # # #         body = json.dumps({
# # # # # # # # # # #             "inputText": prompt,
# # # # # # # # # # #             "textGenerationConfig": {
# # # # # # # # # # #                 "maxTokenCount": 100,
# # # # # # # # # # #                 "stopSequences": [],
# # # # # # # # # # #                 "temperature": 0.3,
# # # # # # # # # # #                 "topP": 0.9
# # # # # # # # # # #             }
# # # # # # # # # # #         })
        
# # # # # # # # # # #         response = bedrock.invoke_model(
# # # # # # # # # # #             body=body,
# # # # # # # # # # #             modelId="amazon.titan-text-express-v1",
# # # # # # # # # # #             accept="application/json",
# # # # # # # # # # #             contentType="application/json"
# # # # # # # # # # #         )
        
# # # # # # # # # # #         response_body = json.loads(response.get('body').read())
# # # # # # # # # # #         processed_text = response_body.get('results', [{}])[0].get('outputText', '').strip()
        
# # # # # # # # # # #         # Fallback to raw answer if processing fails
# # # # # # # # # # #         if not processed_text or len(processed_text) < 5:
# # # # # # # # # # #             return raw_answer
        
# # # # # # # # # # #         return processed_text
# # # # # # # # # # #     except Exception as e:
# # # # # # # # # # #         print(f"Error processing with Bedrock: {e}")
# # # # # # # # # # #         return raw_answer

# # # # # # # # # # # # ==================== NOVA SONIC CLIENT (FULLY FIXED) ====================
# # # # # # # # # # # class NovaInterviewClient:
# # # # # # # # # # #     def __init__(self, employee_name: str, questions: List[str], websocket: WebSocket, region='us-east-1'):
# # # # # # # # # # #         self.model_id = 'amazon.nova-sonic-v1:0'
# # # # # # # # # # #         self.region = region
# # # # # # # # # # #         self.employee_name = employee_name
# # # # # # # # # # #         self.questions = questions
# # # # # # # # # # #         self.websocket = websocket
# # # # # # # # # # #         self.client = None
# # # # # # # # # # #         self.stream = None
# # # # # # # # # # #         self.is_active = False
# # # # # # # # # # #         self.prompt_name = str(uuid.uuid4())
# # # # # # # # # # #         self.system_content_name = str(uuid.uuid4())
# # # # # # # # # # #         self.audio_content_name = str(uuid.uuid4())
# # # # # # # # # # #         self.current_question_idx = 0
# # # # # # # # # # #         self.responses = []
# # # # # # # # # # #         self.role = None
# # # # # # # # # # #         self.display_assistant_text = False
# # # # # # # # # # #         self.audio_timeout_count = 0
# # # # # # # # # # #         self.last_audio_time = None
        
# # # # # # # # # # #         # Track conversation state
# # # # # # # # # # #         self.current_answer = ""
# # # # # # # # # # #         self.current_question_asked = False
# # # # # # # # # # #         self.interview_complete = False
# # # # # # # # # # #         self.all_questions_asked = False
        
# # # # # # # # # # #     def _initialize_client(self):
# # # # # # # # # # #         """Initialize Bedrock client"""
# # # # # # # # # # #         resolver = EnvironmentCredentialsResolver()
        
# # # # # # # # # # #         config = Config(
# # # # # # # # # # #             endpoint_uri=f"https://bedrock-runtime.{self.region}.amazonaws.com",
# # # # # # # # # # #             region=self.region,
# # # # # # # # # # #             aws_credentials_identity_resolver=resolver
# # # # # # # # # # #         )
        
# # # # # # # # # # #         self.client = BedrockRuntimeClient(config=config)
# # # # # # # # # # #         print("✅ Bedrock client initialized")
    
# # # # # # # # # # #     async def send_event(self, event_json):
# # # # # # # # # # #         """Send an event to the stream"""
# # # # # # # # # # #         event = InvokeModelWithBidirectionalStreamInputChunk(
# # # # # # # # # # #             value=BidirectionalInputPayloadPart(bytes_=event_json.encode('utf-8'))
# # # # # # # # # # #         )
# # # # # # # # # # #         await self.stream.input_stream.send(event)
    
# # # # # # # # # # #     async def start_session(self):
# # # # # # # # # # #         """Start Nova Sonic session and greet user"""
# # # # # # # # # # #         if not self.client:
# # # # # # # # # # #             self._initialize_client()
        
# # # # # # # # # # #         try:
# # # # # # # # # # #             # Initialize stream
# # # # # # # # # # #             print("📡 Starting bidirectional stream...")
# # # # # # # # # # #             self.stream = await self.client.invoke_model_with_bidirectional_stream(
# # # # # # # # # # #                 InvokeModelWithBidirectionalStreamOperationInput(model_id=self.model_id)
# # # # # # # # # # #             )
# # # # # # # # # # #             self.is_active = True
# # # # # # # # # # #             print("✅ Stream started")
            
# # # # # # # # # # #             # 1. Session start
# # # # # # # # # # #             print("📤 Sending session start...")
# # # # # # # # # # #             await self.send_event(json.dumps({
# # # # # # # # # # #                 "event": {
# # # # # # # # # # #                     "sessionStart": {
# # # # # # # # # # #                         "inferenceConfiguration": {
# # # # # # # # # # #                             "maxTokens": 1024,
# # # # # # # # # # #                             "topP": 0.9,
# # # # # # # # # # #                             "temperature": 0.7
# # # # # # # # # # #                         }
# # # # # # # # # # #                     }
# # # # # # # # # # #                 }
# # # # # # # # # # #             }))
            
# # # # # # # # # # #             # 2. Prompt start with audio output config
# # # # # # # # # # #             print("📤 Sending prompt start...")
# # # # # # # # # # #             await self.send_event(json.dumps({
# # # # # # # # # # #                 "event": {
# # # # # # # # # # #                     "promptStart": {
# # # # # # # # # # #                         "promptName": self.prompt_name,
# # # # # # # # # # #                         "textOutputConfiguration": {
# # # # # # # # # # #                             "mediaType": "text/plain"
# # # # # # # # # # #                         },
# # # # # # # # # # #                         "audioOutputConfiguration": {
# # # # # # # # # # #                             "mediaType": "audio/lpcm",
# # # # # # # # # # #                             "sampleRateHertz": 24000,
# # # # # # # # # # #                             "sampleSizeBits": 16,
# # # # # # # # # # #                             "channelCount": 1,
# # # # # # # # # # #                             "voiceId": "matthew",
# # # # # # # # # # #                             "encoding": "base64",
# # # # # # # # # # #                             "audioType": "SPEECH"
# # # # # # # # # # #                         }
# # # # # # # # # # #                     }
# # # # # # # # # # #                 }
# # # # # # # # # # #             }))
            
# # # # # # # # # # #             # 3. System prompt
# # # # # # # # # # #             print("📤 Sending system prompt...")
# # # # # # # # # # #             await self.send_event(json.dumps({
# # # # # # # # # # #                 "event": {
# # # # # # # # # # #                     "contentStart": {
# # # # # # # # # # #                         "promptName": self.prompt_name,
# # # # # # # # # # #                         "contentName": self.system_content_name,
# # # # # # # # # # #                         "type": "TEXT",
# # # # # # # # # # #                         "interactive": False,
# # # # # # # # # # #                         "role": "SYSTEM",
# # # # # # # # # # #                         "textInputConfiguration": {
# # # # # # # # # # #                             "mediaType": "text/plain"
# # # # # # # # # # #                         }
# # # # # # # # # # #                     }
# # # # # # # # # # #                 }
# # # # # # # # # # #             }))
            
# # # # # # # # # # #             # Create engaging system prompt
# # # # # # # # # # #             first_question = self.questions[0] if self.questions else "Tell me about your experience"
# # # # # # # # # # #             system_text = f"""You are Nova, a friendly AI conducting an exit interview with {self.employee_name}. 
            
# # # # # # # # # # # Start by warmly greeting {self.employee_name} and then ask your first question: {first_question}

# # # # # # # # # # # Keep responses conversational, empathetic, and concise (2-3 sentences). After each answer, acknowledge it briefly and ask the next question naturally. Wait for the user to answer before asking the next question.

# # # # # # # # # # # IMPORTANT: After asking all {len(self.questions)} questions, you must end the interview by saying "Thank you for completing the exit interview. Have a great day!" and then end the session.

# # # # # # # # # # # The questions you must ask in order are:
# # # # # # # # # # # {chr(10).join([f"{i+1}. {q}" for i, q in enumerate(self.questions)])}"""
            
# # # # # # # # # # #             await self.send_event(json.dumps({
# # # # # # # # # # #                 "event": {
# # # # # # # # # # #                     "textInput": {
# # # # # # # # # # #                         "promptName": self.prompt_name,
# # # # # # # # # # #                         "contentName": self.system_content_name,
# # # # # # # # # # #                         "content": system_text
# # # # # # # # # # #                     }
# # # # # # # # # # #                 }
# # # # # # # # # # #             }))
            
# # # # # # # # # # #             await self.send_event(json.dumps({
# # # # # # # # # # #                 "event": {
# # # # # # # # # # #                     "contentEnd": {
# # # # # # # # # # #                         "promptName": self.prompt_name,
# # # # # # # # # # #                         "contentName": self.system_content_name
# # # # # # # # # # #                     }
# # # # # # # # # # #                 }
# # # # # # # # # # #             }))
            
# # # # # # # # # # #             print("✅ System prompt sent - Nova should start speaking now!")
            
# # # # # # # # # # #             # Start processing responses
# # # # # # # # # # #             asyncio.create_task(self._process_responses())
            
# # # # # # # # # # #         except Exception as e:
# # # # # # # # # # #             print(f"❌ Error starting session: {e}")
# # # # # # # # # # #             traceback.print_exc()
# # # # # # # # # # #             raise
    
# # # # # # # # # # #     async def start_audio_input(self):
# # # # # # # # # # #         """Start continuous audio input"""
# # # # # # # # # # #         print("📤 Starting audio input...")
# # # # # # # # # # #         await self.send_event(json.dumps({
# # # # # # # # # # #             "event": {
# # # # # # # # # # #                 "contentStart": {
# # # # # # # # # # #                     "promptName": self.prompt_name,
# # # # # # # # # # #                     "contentName": self.audio_content_name,
# # # # # # # # # # #                     "type": "AUDIO",
# # # # # # # # # # #                     "interactive": True,
# # # # # # # # # # #                     "role": "USER",
# # # # # # # # # # #                     "audioInputConfiguration": {
# # # # # # # # # # #                         "mediaType": "audio/lpcm",
# # # # # # # # # # #                         "sampleRateHertz": 16000,
# # # # # # # # # # #                         "sampleSizeBits": 16,
# # # # # # # # # # #                         "channelCount": 1,
# # # # # # # # # # #                         "audioType": "SPEECH",
# # # # # # # # # # #                         "encoding": "base64"
# # # # # # # # # # #                     }
# # # # # # # # # # #                 }
# # # # # # # # # # #             }
# # # # # # # # # # #         }))
# # # # # # # # # # #         print("✅ Audio input stream started - waiting for audio from client...")
    
# # # # # # # # # # #     async def send_audio_chunk(self, audio_bytes):
# # # # # # # # # # #         """Send audio chunk"""
# # # # # # # # # # #         if not self.is_active:
# # # # # # # # # # #             return
        
# # # # # # # # # # #         self.last_audio_time = datetime.utcnow()
# # # # # # # # # # #         blob = base64.b64encode(audio_bytes).decode('utf-8')
# # # # # # # # # # #         try:
# # # # # # # # # # #             await self.send_event(json.dumps({
# # # # # # # # # # #                 "event": {
# # # # # # # # # # #                     "audioInput": {
# # # # # # # # # # #                         "promptName": self.prompt_name,
# # # # # # # # # # #                         "contentName": self.audio_content_name,
# # # # # # # # # # #                         "content": blob
# # # # # # # # # # #                     }
# # # # # # # # # # #                 }
# # # # # # # # # # #             }))
# # # # # # # # # # #         except Exception as e:
# # # # # # # # # # #             print(f"⚠️ Error sending audio chunk: {e}")
    
# # # # # # # # # # #     async def _process_responses(self):
# # # # # # # # # # #         """Process responses from Nova"""
# # # # # # # # # # #         try:
# # # # # # # # # # #             while self.is_active:
# # # # # # # # # # #                 try:
# # # # # # # # # # #                     output = await self.stream.await_output()
# # # # # # # # # # #                     result = await output[1].receive()
                    
# # # # # # # # # # #                     if result.value and result.value.bytes_:
# # # # # # # # # # #                         response_data = result.value.bytes_.decode('utf-8')
# # # # # # # # # # #                         json_data = json.loads(response_data)
                        
# # # # # # # # # # #                         if 'event' in json_data:
# # # # # # # # # # #                             event = json_data['event']
                            
# # # # # # # # # # #                             # Content start
# # # # # # # # # # #                             if 'contentStart' in event:
# # # # # # # # # # #                                 self.role = event['contentStart'].get('role')
# # # # # # # # # # #                                 if 'additionalModelFields' in event['contentStart']:
# # # # # # # # # # #                                     try:
# # # # # # # # # # #                                         fields = json.loads(event['contentStart']['additionalModelFields'])
# # # # # # # # # # #                                         self.display_assistant_text = fields.get('generationStage') == 'SPECULATIVE'
# # # # # # # # # # #                                     except:
# # # # # # # # # # #                                         pass
                            
# # # # # # # # # # #                             # Text output
# # # # # # # # # # #                             elif 'textOutput' in event:
# # # # # # # # # # #                                 text = event['textOutput']['content']
# # # # # # # # # # #                                 role = event['textOutput'].get('role', 'ASSISTANT')
                                
# # # # # # # # # # #                                 if role == "ASSISTANT" and self.display_assistant_text:
# # # # # # # # # # #                                     print(f"🤖 Nova: {text}")
# # # # # # # # # # #                                     await self.websocket.send_json({
# # # # # # # # # # #                                         'type': 'text',
# # # # # # # # # # #                                         'content': text,
# # # # # # # # # # #                                         'role': 'ASSISTANT'
# # # # # # # # # # #                                     })
                                    
# # # # # # # # # # #                                     # Check if Nova is asking a question
# # # # # # # # # # #                                     if '?' in text and not self.current_question_asked:
# # # # # # # # # # #                                         self.current_question_asked = True
# # # # # # # # # # #                                         print(f"✅ Nova asked a question: {text}")
                                    
# # # # # # # # # # #                                     # Check if Nova is ending the interview
# # # # # # # # # # #                                     if "thank you for completing" in text.lower() or "have a great day" in text.lower():
# # # # # # # # # # #                                         self.interview_complete = True
# # # # # # # # # # #                                         print("✅ Nova is ending the interview")
                                        
# # # # # # # # # # #                                 elif role == "USER":
# # # # # # # # # # #                                     print(f"👤 User: {text}")
                                    
# # # # # # # # # # #                                     # Only capture if we're expecting an answer
# # # # # # # # # # #                                     if self.current_question_asked:
# # # # # # # # # # #                                         self.current_answer += text + " "
# # # # # # # # # # #                                         print(f"📝 Capturing answer: {text}")
                                    
# # # # # # # # # # #                                     await self.websocket.send_json({
# # # # # # # # # # #                                         'type': 'text',
# # # # # # # # # # #                                         'content': text,
# # # # # # # # # # #                                         'role': 'USER'
# # # # # # # # # # #                                     })
                            
# # # # # # # # # # #                             # Audio output
# # # # # # # # # # #                             elif 'audioOutput' in event:
# # # # # # # # # # #                                 audio_content = event['audioOutput']['content']
# # # # # # # # # # #                                 print(f"🔊 Sending audio chunk ({len(audio_content)} chars)")
# # # # # # # # # # #                                 await self.websocket.send_json({
# # # # # # # # # # #                                     'type': 'audio',
# # # # # # # # # # #                                     'data': audio_content
# # # # # # # # # # #                                 })
                            
# # # # # # # # # # #                             # Content end
# # # # # # # # # # #                             elif 'contentEnd' in event:
# # # # # # # # # # #                                 print("📌 Content ended")
                                
# # # # # # # # # # #                                 # If Nova finished speaking and we were expecting an answer
# # # # # # # # # # #                                 if self.role == "ASSISTANT" and self.current_question_asked:
# # # # # # # # # # #                                     # Save the captured answer
# # # # # # # # # # #                                     if self.current_answer.strip() and self.current_question_idx < len(self.questions):
# # # # # # # # # # #                                         question = self.questions[self.current_question_idx]
# # # # # # # # # # #                                         raw_answer = self.current_answer.strip()
                                        
# # # # # # # # # # #                                         # Process with Bedrock
# # # # # # # # # # #                                         processed_answer = process_user_answer_with_bedrock(raw_answer, question)
                                        
# # # # # # # # # # #                                         self.responses.append({
# # # # # # # # # # #                                             'question': question,
# # # # # # # # # # #                                             'answer': processed_answer
# # # # # # # # # # #                                         })
                                        
# # # # # # # # # # #                                         print(f"💾 Saved answer for Q{self.current_question_idx+1}: {processed_answer}")
# # # # # # # # # # #                                         self.current_question_idx += 1
                                        
# # # # # # # # # # #                                         # Check if we've answered all questions
# # # # # # # # # # #                                         if self.current_question_idx >= len(self.questions):
# # # # # # # # # # #                                             self.all_questions_asked = True
# # # # # # # # # # #                                             print(f"✅ All {len(self.questions)} questions answered")
                                    
# # # # # # # # # # #                                     # Reset for next question
# # # # # # # # # # #                                     self.current_answer = ""
# # # # # # # # # # #                                     self.current_question_asked = False
                                
# # # # # # # # # # #                                 # Check if we should end the interview
# # # # # # # # # # #                                 if self.interview_complete or self.all_questions_asked:
# # # # # # # # # # #                                     print("✅ Ending interview - all questions answered or completion detected")
# # # # # # # # # # #                                     await self.websocket.send_json({
# # # # # # # # # # #                                         'type': 'complete',
# # # # # # # # # # #                                         'responses': self.responses
# # # # # # # # # # #                                     })
# # # # # # # # # # #                                     self.is_active = False
# # # # # # # # # # #                                     return
                                
# # # # # # # # # # #                                 await self.websocket.send_json({'type': 'content_end'})
                            
# # # # # # # # # # #                             # Completion
# # # # # # # # # # #                             elif 'completionEnd' in event:
# # # # # # # # # # #                                 print("✅ Interview complete")
                                
# # # # # # # # # # #                                 # Save any final captured answer
# # # # # # # # # # #                                 if self.current_answer.strip() and self.current_question_idx < len(self.questions):
# # # # # # # # # # #                                     question = self.questions[self.current_question_idx]
# # # # # # # # # # #                                     raw_answer = self.current_answer.strip()
                                    
# # # # # # # # # # #                                     # Process with Bedrock
# # # # # # # # # # #                                     processed_answer = process_user_answer_with_bedrock(raw_answer, question)
                                    
# # # # # # # # # # #                                     self.responses.append({
# # # # # # # # # # #                                         'question': question,
# # # # # # # # # # #                                         'answer': processed_answer
# # # # # # # # # # #                                     })
                                    
# # # # # # # # # # #                                     print(f"💾 Saved final answer for Q{self.current_question_idx+1}: {processed_answer}")
# # # # # # # # # # #                                     self.current_question_idx += 1
                                
# # # # # # # # # # #                                 await self.websocket.send_json({
# # # # # # # # # # #                                     'type': 'complete',
# # # # # # # # # # #                                     'responses': self.responses
# # # # # # # # # # #                                 })
# # # # # # # # # # #                                 self.is_active = False
# # # # # # # # # # #                                 break
                
# # # # # # # # # # #                 except asyncio.TimeoutError:
# # # # # # # # # # #                     continue
# # # # # # # # # # #                 except Exception as e:
# # # # # # # # # # #                     print(f"⚠️ Error in response processing: {e}")
# # # # # # # # # # #                     continue
        
# # # # # # # # # # #         except Exception as e:
# # # # # # # # # # #             print(f"❌ Fatal error in _process_responses: {e}")
# # # # # # # # # # #             self.is_active = False
    
# # # # # # # # # # #     async def end_session(self):
# # # # # # # # # # #         """End session gracefully"""
# # # # # # # # # # #         if not self.is_active:
# # # # # # # # # # #             return
        
# # # # # # # # # # #         try:
# # # # # # # # # # #             # End audio input
# # # # # # # # # # #             await self.send_event(json.dumps({
# # # # # # # # # # #                 "event": {
# # # # # # # # # # #                     "contentEnd": {
# # # # # # # # # # #                         "promptName": self.prompt_name,
# # # # # # # # # # #                         "contentName": self.audio_content_name
# # # # # # # # # # #                     }
# # # # # # # # # # #                 }
# # # # # # # # # # #             }))
            
# # # # # # # # # # #             # End prompt
# # # # # # # # # # #             await self.send_event(json.dumps({
# # # # # # # # # # #                 "event": {
# # # # # # # # # # #                     "promptEnd": {
# # # # # # # # # # #                         "promptName": self.prompt_name
# # # # # # # # # # #                     }
# # # # # # # # # # #                 }
# # # # # # # # # # #             }))
            
# # # # # # # # # # #             # End session
# # # # # # # # # # #             await self.send_event(json.dumps({
# # # # # # # # # # #                 "event": {
# # # # # # # # # # #                     "sessionEnd": {}
# # # # # # # # # # #                 }
# # # # # # # # # # #             }))
            
# # # # # # # # # # #             await self.stream.input_stream.close()
# # # # # # # # # # #             self.is_active = False
# # # # # # # # # # #             print("✅ Session ended")
        
# # # # # # # # # # #         except Exception as e:
# # # # # # # # # # #             print(f"⚠️ Error ending session: {e}")
# # # # # # # # # # #             self.is_active = False

# # # # # # # # # # # # ==================== AWS SES ====================
# # # # # # # # # # # ses_client = boto3.client('ses', region_name=os.getenv("AWS_REGION", "us-east-1"))

# # # # # # # # # # # def send_exit_interview_email(employee_email: str, employee_name: str, form_link: str) -> bool:
# # # # # # # # # # #     SENDER = os.getenv("SES_SENDER_EMAIL")
# # # # # # # # # # #     SUBJECT = "🎙️ Voice Exit Interview with Nova"
# # # # # # # # # # #     BODY_HTML = f"""
# # # # # # # # # # #     <html><body>
# # # # # # # # # # #         <h1>Hello {employee_name}!</h1>
# # # # # # # # # # #         <p>Have a voice conversation with Nova for your exit interview.</p>
# # # # # # # # # # #         <p><a href="{form_link}">Start Voice Interview</a></p>
# # # # # # # # # # #     </body></html>
# # # # # # # # # # #     """
# # # # # # # # # # #     try:
# # # # # # # # # # #         ses_client.send_email(
# # # # # # # # # # #             Source=SENDER,
# # # # # # # # # # #             Destination={'ToAddresses': [employee_email]},
# # # # # # # # # # #             Message={'Subject': {'Data': SUBJECT}, 'Body': {'Html': {'Data': BODY_HTML}}}
# # # # # # # # # # #         )
# # # # # # # # # # #         print(f"✅ Email sent to {employee_name}")
# # # # # # # # # # #         return True
# # # # # # # # # # #     except Exception as e:
# # # # # # # # # # #         print(f"❌ Email error: {e}")
# # # # # # # # # # #         return False

# # # # # # # # # # # def generate_unique_token() -> str:
# # # # # # # # # # #     return str(uuid.uuid4())

# # # # # # # # # # # def create_form_link(token: str) -> str:
# # # # # # # # # # #     return f"{os.getenv('APP_URL', 'http://localhost:8501')}/exit_interview?token={token}"

# # # # # # # # # # # # ==================== FASTAPI APP ====================
# # # # # # # # # # # app = FastAPI(title="Nova Sonic Exit Interview API", version="4.0.0")

# # # # # # # # # # # app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# # # # # # # # # # # def get_db():
# # # # # # # # # # #     db = SessionLocal()
# # # # # # # # # # #     try:
# # # # # # # # # # #         yield db
# # # # # # # # # # #     finally:
# # # # # # # # # # #         db.close()

# # # # # # # # # # # active_sessions: Dict[str, NovaInterviewClient] = {}

# # # # # # # # # # # # ==================== API ENDPOINTS ====================

# # # # # # # # # # # @app.get("/")
# # # # # # # # # # # def root():
# # # # # # # # # # #     return {"message": "Nova Sonic Exit Interview API", "version": "4.0.0", "status": "running"}

# # # # # # # # # # # @app.post("/api/employees", response_model=EmployeeResponse, status_code=201)
# # # # # # # # # # # def create_employee(employee: EmployeeCreate, db: Session = Depends(get_db)):
# # # # # # # # # # #     try:
# # # # # # # # # # #         existing = db.query(Employee).filter(Employee.email == employee.email).first()
# # # # # # # # # # #         if existing:
# # # # # # # # # # #             raise HTTPException(status_code=400, detail="Employee already exists")
        
# # # # # # # # # # #         db_employee = Employee(
# # # # # # # # # # #             name=employee.name, email=employee.email,
# # # # # # # # # # #             department=employee.department,
# # # # # # # # # # #             last_working_date=employee.last_working_date, status="Resigned"
# # # # # # # # # # #         )
# # # # # # # # # # #         db.add(db_employee)
# # # # # # # # # # #         db.commit()
# # # # # # # # # # #         db.refresh(db_employee)
        
# # # # # # # # # # #         token = generate_unique_token()
# # # # # # # # # # #         form_link = create_form_link(token)
        
# # # # # # # # # # #         questions_json = json.dumps(employee.questions) if employee.questions else json.dumps([
# # # # # # # # # # #             "What was your primary reason for leaving?",
# # # # # # # # # # #             "How would you rate your overall experience?",
# # # # # # # # # # #             "How was your relationship with your manager?",
# # # # # # # # # # #             "Did you feel valued in your role?",
# # # # # # # # # # #             "Would you recommend our company to others?"
# # # # # # # # # # #         ])
        
# # # # # # # # # # #         db_interview = ExitInterview(
# # # # # # # # # # #             employee_id=db_employee.id, form_token=token,
# # # # # # # # # # #             completed=False, questions_json=questions_json
# # # # # # # # # # #         )
# # # # # # # # # # #         db.add(db_interview)
# # # # # # # # # # #         db.commit()
        
# # # # # # # # # # #         send_exit_interview_email(db_employee.email, db_employee.name, form_link)
        
# # # # # # # # # # #         return db_employee
# # # # # # # # # # #     except HTTPException:
# # # # # # # # # # #         raise
# # # # # # # # # # #     except Exception as e:
# # # # # # # # # # #         db.rollback()
# # # # # # # # # # #         raise HTTPException(status_code=500, detail=str(e))

# # # # # # # # # # # @app.get("/api/employees", response_model=List[EmployeeWithInterview])
# # # # # # # # # # # def list_employees(db: Session = Depends(get_db)):
# # # # # # # # # # #     employees = db.query(Employee).all()
# # # # # # # # # # #     result = []
# # # # # # # # # # #     for emp in employees:
# # # # # # # # # # #         emp_dict = {
# # # # # # # # # # #             "id": emp.id, "name": emp.name, "email": emp.email,
# # # # # # # # # # #             "department": emp.department, "last_working_date": emp.last_working_date,
# # # # # # # # # # #             "status": emp.status, "created_at": emp.created_at, "interview": None
# # # # # # # # # # #         }
# # # # # # # # # # #         if emp.exit_interview:
# # # # # # # # # # #             emp_dict["interview"] = {
# # # # # # # # # # #                 "id": emp.exit_interview.id,
# # # # # # # # # # #                 "completed": emp.exit_interview.completed,
# # # # # # # # # # #                 "form_token": emp.exit_interview.form_token,
# # # # # # # # # # #                 "created_at": emp.exit_interview.created_at
# # # # # # # # # # #             }
# # # # # # # # # # #         result.append(emp_dict)
# # # # # # # # # # #     return result

# # # # # # # # # # # @app.get("/api/interviews/token/{token}")
# # # # # # # # # # # def get_interview_by_token(token: str, db: Session = Depends(get_db)):
# # # # # # # # # # #     interview = db.query(ExitInterview).filter(ExitInterview.form_token == token).first()
# # # # # # # # # # #     if not interview:
# # # # # # # # # # #         raise HTTPException(status_code=404, detail="Invalid token")
# # # # # # # # # # #     if interview.completed:
# # # # # # # # # # #         raise HTTPException(status_code=400, detail="Interview already completed")
    
# # # # # # # # # # #     questions = json.loads(interview.questions_json)
# # # # # # # # # # #     return {
# # # # # # # # # # #         "interview_id": interview.id,
# # # # # # # # # # #         "employee_name": interview.employee.name,
# # # # # # # # # # #         "employee_department": interview.employee.department,
# # # # # # # # # # #         "questions": questions,
# # # # # # # # # # #         "total_questions": len(questions),
# # # # # # # # # # #         "completed": interview.completed
# # # # # # # # # # #     }

# # # # # # # # # # # @app.websocket("/ws/interview/{token}")
# # # # # # # # # # # async def websocket_interview(websocket: WebSocket, token: str):
# # # # # # # # # # #     await websocket.accept()
    
# # # # # # # # # # #     db = SessionLocal()
# # # # # # # # # # #     session_id = str(uuid.uuid4())
# # # # # # # # # # #     nova_client = None
    
# # # # # # # # # # #     try:
# # # # # # # # # # #         # Get interview
# # # # # # # # # # #         interview = db.query(ExitInterview).filter(ExitInterview.form_token == token).first()
# # # # # # # # # # #         if not interview:
# # # # # # # # # # #             await websocket.send_json({"type": "error", "message": "Invalid token"})
# # # # # # # # # # #             return
        
# # # # # # # # # # #         questions = json.loads(interview.questions_json)
# # # # # # # # # # #         employee_name = interview.employee.name
        
# # # # # # # # # # #         print(f"\n{'='*60}")
# # # # # # # # # # #         print(f"🎙️ Starting voice interview for {employee_name}")
# # # # # # # # # # #         print(f"📋 Questions: {len(questions)}")
# # # # # # # # # # #         print(f"{'='*60}\n")
        
# # # # # # # # # # #         # Send session start
# # # # # # # # # # #         await websocket.send_json({
# # # # # # # # # # #             "type": "session_start",
# # # # # # # # # # #             "session_id": session_id,
# # # # # # # # # # #             "employee_name": employee_name,
# # # # # # # # # # #             "total_questions": len(questions)
# # # # # # # # # # #         })
        
# # # # # # # # # # #         # Create and start Nova client
# # # # # # # # # # #         nova_client = NovaInterviewClient(employee_name, questions, websocket, os.getenv("AWS_REGION", "us-east-1"))
# # # # # # # # # # #         await nova_client.start_session()
        
# # # # # # # # # # #         # Start audio input - wait for Nova to greet
# # # # # # # # # # #         await asyncio.sleep(3)
# # # # # # # # # # #         await nova_client.start_audio_input()
        
# # # # # # # # # # #         active_sessions[session_id] = nova_client
        
# # # # # # # # # # #         print("✅ Waiting for audio from client...")
        
# # # # # # # # # # #         # Listen for audio from client with timeout
# # # # # # # # # # #         timeout_seconds = 120  # 2 minute timeout if no audio
# # # # # # # # # # #         start_time = datetime.utcnow()
        
# # # # # # # # # # #         while nova_client.is_active:
# # # # # # # # # # #             try:
# # # # # # # # # # #                 message = await asyncio.wait_for(websocket.receive_json(), timeout=0.5)
                
# # # # # # # # # # #                 # Reset timeout on any message
# # # # # # # # # # #                 start_time = datetime.utcnow()
                
# # # # # # # # # # #                 if message['type'] == 'audio_chunk':
# # # # # # # # # # #                     audio_data = base64.b64decode(message['data'])
# # # # # # # # # # #                     await nova_client.send_audio_chunk(audio_data)
# # # # # # # # # # #                     print(f"📨 Audio chunk received ({len(audio_data)} bytes)")
                
# # # # # # # # # # #                 elif message['type'] == 'close':
# # # # # # # # # # #                     print("🛑 Client requested close")
# # # # # # # # # # #                     break
            
# # # # # # # # # # #             except asyncio.TimeoutError:
# # # # # # # # # # #                 # Check if we've exceeded total timeout
# # # # # # # # # # #                 elapsed = (datetime.utcnow() - start_time).total_seconds()
# # # # # # # # # # #                 if elapsed > timeout_seconds:
# # # # # # # # # # #                     print(f"⚠️ No audio from client for {timeout_seconds}s - ending session")
# # # # # # # # # # #                     break
# # # # # # # # # # #                 continue
# # # # # # # # # # #             except WebSocketDisconnect:
# # # # # # # # # # #                 print("⚠️ WebSocket disconnected")
# # # # # # # # # # #                 break
# # # # # # # # # # #             except Exception as e:
# # # # # # # # # # #                 print(f"⚠️ Error receiving message: {e}")
# # # # # # # # # # #                 break
        
# # # # # # # # # # #         # Save responses to database
# # # # # # # # # # #         if nova_client.responses:
# # # # # # # # # # #             print(f"\n💾 Saving {len(nova_client.responses)} responses to database")
# # # # # # # # # # #             transcript = []
            
# # # # # # # # # # #             for resp in nova_client.responses:
# # # # # # # # # # #                 # Create and save response
# # # # # # # # # # #                 db_response = InterviewResponse(
# # # # # # # # # # #                     interview_id=interview.id,
# # # # # # # # # # #                     question=resp['question'],
# # # # # # # # # # #                     answer=resp['answer']
# # # # # # # # # # #                 )
# # # # # # # # # # #                 db.add(db_response)
# # # # # # # # # # #                 transcript.append(f"Q: {resp['question']}\nA: {resp['answer']}\n")
            
# # # # # # # # # # #             # Update interview status
# # # # # # # # # # #             interview.completed = True
# # # # # # # # # # #             interview.conversation_transcript = '\n'.join(transcript)
# # # # # # # # # # #             interview.employee.status = "Completed"
            
# # # # # # # # # # #             # Commit changes
# # # # # # # # # # #             db.commit()
# # # # # # # # # # #             print(f"✅ Interview saved for {employee_name}")
# # # # # # # # # # #         else:
# # # # # # # # # # #             print(f"⚠️ No responses recorded for {employee_name}")
    
# # # # # # # # # # #     except Exception as e:
# # # # # # # # # # #         print(f"❌ Error: {e}")
# # # # # # # # # # #         traceback.print_exc()
# # # # # # # # # # #         try:
# # # # # # # # # # #             await websocket.send_json({"type": "error", "message": str(e)})
# # # # # # # # # # #         except:
# # # # # # # # # # #             pass
# # # # # # # # # # #     finally:
# # # # # # # # # # #         if nova_client:
# # # # # # # # # # #             await nova_client.end_session()
# # # # # # # # # # #         if session_id in active_sessions:
# # # # # # # # # # #             del active_sessions[session_id]
# # # # # # # # # # #         db.close()

# # # # # # # # # # # @app.get("/api/interviews/{interview_id}/responses", response_model=List[InterviewResponseDetail])
# # # # # # # # # # # def get_interview_responses(interview_id: int, db: Session = Depends(get_db)):
# # # # # # # # # # #     return db.query(InterviewResponse).filter(InterviewResponse.interview_id == interview_id).all()

# # # # # # # # # # # @app.get("/api/stats")
# # # # # # # # # # # def get_statistics(db: Session = Depends(get_db)):
# # # # # # # # # # #     total = db.query(Employee).count()
# # # # # # # # # # #     completed = db.query(ExitInterview).filter(ExitInterview.completed == True).count()
# # # # # # # # # # #     return {
# # # # # # # # # # #         "total_resignations": total,
# # # # # # # # # # #         "completed_interviews": completed,
# # # # # # # # # # #         "pending_interviews": total - completed,
# # # # # # # # # # #         "completion_rate": (completed / total * 100) if total > 0 else 0
# # # # # # # # # # #     }

# # # # # # # # # # # def init_db():
# # # # # # # # # # #     Base.metadata.create_all(bind=engine)
# # # # # # # # # # #     print("✅ Database initialized!")

# # # # # # # # # # # if __name__ == "__main__":
# # # # # # # # # # #     init_db()
# # # # # # # # # # #     import uvicorn
# # # # # # # # # # #     print("\n🚀 Starting Nova Sonic Exit Interview Server")
# # # # # # # # # # #     print("📡 Backend: http://0.0.0.0:8000")
# # # # # # # # # # #     print("📖 API Docs: http://localhost:8000/docs")
# # # # # # # # # # #     print("\n⚡ Nova Sonic is ready!\n")
# # # # # # # # # # #     uvicorn.run(app, host="0.0.0.0", port=8000)





# # # # # # # # # # """
# # # # # # # # # # WORKING Nova Sonic Exit Interview Backend - FULLY FIXED VERSION

# # # # # # # # # # Installation required:
# # # # # # # # # # pip install git+https://github.com/awslabs/aws-sdk-python-bedrock.git
# # # # # # # # # # pip install fastapi uvicorn sqlalchemy psycopg2-binary websockets
# # # # # # # # # # """

# # # # # # # # # # from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
# # # # # # # # # # from fastapi.middleware.cors import CORSMiddleware
# # # # # # # # # # from sqlalchemy import create_engine, Column, Integer, String, Boolean, Date, DateTime, Text, ForeignKey
# # # # # # # # # # from sqlalchemy.ext.declarative import declarative_base
# # # # # # # # # # from sqlalchemy.orm import sessionmaker, Session, relationship
# # # # # # # # # # from pydantic import BaseModel, EmailStr, field_validator
# # # # # # # # # # from typing import List, Optional, Dict, Any
# # # # # # # # # # from datetime import datetime, date
# # # # # # # # # # import os
# # # # # # # # # # from dotenv import load_dotenv
# # # # # # # # # # import boto3
# # # # # # # # # # import uuid
# # # # # # # # # # import json
# # # # # # # # # # import asyncio
# # # # # # # # # # import base64
# # # # # # # # # # import traceback
# # # # # # # # # # import re

# # # # # # # # # # # Import Nova Sonic experimental SDK
# # # # # # # # # # from aws_sdk_bedrock_runtime.client import BedrockRuntimeClient, InvokeModelWithBidirectionalStreamOperationInput
# # # # # # # # # # from aws_sdk_bedrock_runtime.models import InvokeModelWithBidirectionalStreamInputChunk, BidirectionalInputPayloadPart
# # # # # # # # # # from aws_sdk_bedrock_runtime.config import Config
# # # # # # # # # # from smithy_aws_core.identity.environment import EnvironmentCredentialsResolver

# # # # # # # # # # load_dotenv()

# # # # # # # # # # # ==================== DATABASE SETUP ====================
# # # # # # # # # # DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

# # # # # # # # # # engine = create_engine(DATABASE_URL)
# # # # # # # # # # SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# # # # # # # # # # Base = declarative_base()

# # # # # # # # # # # ==================== DATABASE MODELS ====================
# # # # # # # # # # class Employee(Base):
# # # # # # # # # #     __tablename__ = "employees"
    
# # # # # # # # # #     id = Column(Integer, primary_key=True, index=True)
# # # # # # # # # #     name = Column(String(100), nullable=False)
# # # # # # # # # #     email = Column(String(100), unique=True, nullable=False)
# # # # # # # # # #     department = Column(String(50))
# # # # # # # # # #     last_working_date = Column(Date)
# # # # # # # # # #     status = Column(String(20), default="Resigned")
# # # # # # # # # #     created_at = Column(DateTime, default=datetime.utcnow)
    
# # # # # # # # # #     exit_interview = relationship("ExitInterview", back_populates="employee", uselist=False)

# # # # # # # # # # class ExitInterview(Base):
# # # # # # # # # #     __tablename__ = "exit_interviews"
    
# # # # # # # # # #     id = Column(Integer, primary_key=True, index=True)
# # # # # # # # # #     employee_id = Column(Integer, ForeignKey("employees.id"))
# # # # # # # # # #     form_token = Column(String(255), unique=True, nullable=False)
# # # # # # # # # #     completed = Column(Boolean, default=False)
# # # # # # # # # #     questions_json = Column(Text)
# # # # # # # # # #     conversation_transcript = Column(Text)
# # # # # # # # # #     created_at = Column(DateTime, default=datetime.utcnow)
    
# # # # # # # # # #     employee = relationship("Employee", back_populates="exit_interview")
# # # # # # # # # #     responses = relationship("InterviewResponse", back_populates="interview")

# # # # # # # # # # class InterviewResponse(Base):
# # # # # # # # # #     __tablename__ = "interview_responses"
    
# # # # # # # # # #     id = Column(Integer, primary_key=True, index=True)
# # # # # # # # # #     interview_id = Column(Integer, ForeignKey("exit_interviews.id"))
# # # # # # # # # #     question = Column(Text, nullable=False)
# # # # # # # # # #     answer = Column(Text)
# # # # # # # # # #     created_at = Column(DateTime, default=datetime.utcnow)
    
# # # # # # # # # #     interview = relationship("ExitInterview", back_populates="responses")

# # # # # # # # # # # ==================== PYDANTIC SCHEMAS ====================
# # # # # # # # # # class EmployeeCreate(BaseModel):
# # # # # # # # # #     name: str
# # # # # # # # # #     email: EmailStr
# # # # # # # # # #     department: str
# # # # # # # # # #     last_working_date: date
# # # # # # # # # #     questions: Optional[List[str]] = None
    
# # # # # # # # # #     @field_validator('name')
# # # # # # # # # #     def name_must_not_be_empty(cls, v):
# # # # # # # # # #         if not v or not v.strip():
# # # # # # # # # #             raise ValueError('Name cannot be empty')
# # # # # # # # # #         return v.strip()

# # # # # # # # # # class EmployeeResponse(BaseModel):
# # # # # # # # # #     id: int
# # # # # # # # # #     name: str
# # # # # # # # # #     email: str
# # # # # # # # # #     department: str
# # # # # # # # # #     last_working_date: date
# # # # # # # # # #     status: str
# # # # # # # # # #     created_at: datetime
    
# # # # # # # # # #     class Config:
# # # # # # # # # #         from_attributes = True

# # # # # # # # # # class InterviewStatusResponse(BaseModel):
# # # # # # # # # #     id: int
# # # # # # # # # #     completed: bool
# # # # # # # # # #     form_token: str
# # # # # # # # # #     created_at: datetime
    
# # # # # # # # # #     class Config:
# # # # # # # # # #         from_attributes = True

# # # # # # # # # # class EmployeeWithInterview(BaseModel):
# # # # # # # # # #     id: int
# # # # # # # # # #     name: str
# # # # # # # # # #     email: str
# # # # # # # # # #     department: str
# # # # # # # # # #     last_working_date: date
# # # # # # # # # #     status: str
# # # # # # # # # #     created_at: datetime
# # # # # # # # # #     interview: Optional[InterviewStatusResponse] = None
    
# # # # # # # # # #     class Config:
# # # # # # # # # #         from_attributes = True

# # # # # # # # # # class InterviewResponseDetail(BaseModel):
# # # # # # # # # #     id: int
# # # # # # # # # #     question: str
# # # # # # # # # #     answer: str
# # # # # # # # # #     created_at: datetime
    
# # # # # # # # # #     class Config:
# # # # # # # # # #         from_attributes = True

# # # # # # # # # # # ==================== BEDROCK PROCESSING ====================
# # # # # # # # # # def process_user_answer_with_bedrock(raw_answer: str, question: str) -> str:
# # # # # # # # # #     """
# # # # # # # # # #     Process user answer with Bedrock to extract relevant response and remove repetitions
# # # # # # # # # #     """
# # # # # # # # # #     try:
# # # # # # # # # #         bedrock = boto3.client('bedrock-runtime', region_name=os.getenv("AWS_REGION", "us-east-1"))
        
# # # # # # # # # #         # First, clean up obvious repetitions
# # # # # # # # # #         cleaned_answer = re.sub(r'\b(\w+)( \1\b)+', r'\1', raw_answer)  # Remove consecutive repeated words
        
# # # # # # # # # #         prompt = f"""
# # # # # # # # # #         You are analyzing a user's response to an exit interview question. 
# # # # # # # # # #         Your task is to extract the core answer and remove any conversational filler, greetings, or irrelevant parts.
# # # # # # # # # #         Also remove any repeated phrases or sentences that appear multiple times.
        
# # # # # # # # # #         Question: {question}
# # # # # # # # # #         User Response: {cleaned_answer}
        
# # # # # # # # # #         Please provide only the cleaned, relevant answer without any additional commentary:
# # # # # # # # # #         """
        
# # # # # # # # # #         body = json.dumps({
# # # # # # # # # #             "inputText": prompt,
# # # # # # # # # #             "textGenerationConfig": {
# # # # # # # # # #                 "maxTokenCount": 100,
# # # # # # # # # #                 "stopSequences": [],
# # # # # # # # # #                 "temperature": 0.3,
# # # # # # # # # #                 "topP": 0.9
# # # # # # # # # #             }
# # # # # # # # # #         })
        
# # # # # # # # # #         response = bedrock.invoke_model(
# # # # # # # # # #             body=body,
# # # # # # # # # #             modelId="amazon.titan-text-express-v1",
# # # # # # # # # #             accept="application/json",
# # # # # # # # # #             contentType="application/json"
# # # # # # # # # #         )
        
# # # # # # # # # #         response_body = json.loads(response.get('body').read())
# # # # # # # # # #         processed_text = response_body.get('results', [{}])[0].get('outputText', '').strip()
        
# # # # # # # # # #         # Fallback to cleaned answer if processing fails
# # # # # # # # # #         if not processed_text or len(processed_text) < 5:
# # # # # # # # # #             return cleaned_answer
        
# # # # # # # # # #         return processed_text
# # # # # # # # # #     except Exception as e:
# # # # # # # # # #         print(f"Error processing with Bedrock: {e}")
# # # # # # # # # #         # Fallback to basic cleaning
# # # # # # # # # #         return re.sub(r'\b(\w+)( \1\b)+', r'\1', raw_answer)

# # # # # # # # # # # ==================== NOVA SONIC CLIENT (FULLY FIXED) ====================
# # # # # # # # # # class NovaInterviewClient:
# # # # # # # # # #     def __init__(self, employee_name: str, questions: List[str], websocket: WebSocket, region='us-east-1'):
# # # # # # # # # #         self.model_id = 'amazon.nova-sonic-v1:0'
# # # # # # # # # #         self.region = region
# # # # # # # # # #         self.employee_name = employee_name
# # # # # # # # # #         self.questions = questions
# # # # # # # # # #         self.websocket = websocket
# # # # # # # # # #         self.client = None
# # # # # # # # # #         self.stream = None
# # # # # # # # # #         self.is_active = False
# # # # # # # # # #         self.prompt_name = str(uuid.uuid4())
# # # # # # # # # #         self.system_content_name = str(uuid.uuid4())
# # # # # # # # # #         self.audio_content_name = str(uuid.uuid4())
# # # # # # # # # #         self.current_question_idx = 0
# # # # # # # # # #         self.responses = []
# # # # # # # # # #         self.role = None
# # # # # # # # # #         self.display_assistant_text = False
# # # # # # # # # #         self.audio_timeout_count = 0
# # # # # # # # # #         self.last_audio_time = None
        
# # # # # # # # # #         # Track conversation state
# # # # # # # # # #         self.current_answer = ""
# # # # # # # # # #         self.current_question_asked = False
# # # # # # # # # #         self.interview_complete = False
# # # # # # # # # #         self.all_questions_asked = False
# # # # # # # # # #         self.last_user_text = ""  # To avoid duplicate user messages
        
# # # # # # # # # #     def _initialize_client(self):
# # # # # # # # # #         """Initialize Bedrock client"""
# # # # # # # # # #         resolver = EnvironmentCredentialsResolver()
        
# # # # # # # # # #         config = Config(
# # # # # # # # # #             endpoint_uri=f"https://bedrock-runtime.{self.region}.amazonaws.com",
# # # # # # # # # #             region=self.region,
# # # # # # # # # #             aws_credentials_identity_resolver=resolver
# # # # # # # # # #         )
        
# # # # # # # # # #         self.client = BedrockRuntimeClient(config=config)
# # # # # # # # # #         print("✅ Bedrock client initialized")
    
# # # # # # # # # #     async def send_event(self, event_json):
# # # # # # # # # #         """Send an event to the stream"""
# # # # # # # # # #         event = InvokeModelWithBidirectionalStreamInputChunk(
# # # # # # # # # #             value=BidirectionalInputPayloadPart(bytes_=event_json.encode('utf-8'))
# # # # # # # # # #         )
# # # # # # # # # #         await self.stream.input_stream.send(event)
    
# # # # # # # # # #     async def start_session(self):
# # # # # # # # # #         """Start Nova Sonic session and greet user"""
# # # # # # # # # #         if not self.client:
# # # # # # # # # #             self._initialize_client()
        
# # # # # # # # # #         try:
# # # # # # # # # #             # Initialize stream
# # # # # # # # # #             print("📡 Starting bidirectional stream...")
# # # # # # # # # #             self.stream = await self.client.invoke_model_with_bidirectional_stream(
# # # # # # # # # #                 InvokeModelWithBidirectionalStreamOperationInput(model_id=self.model_id)
# # # # # # # # # #             )
# # # # # # # # # #             self.is_active = True
# # # # # # # # # #             print("✅ Stream started")
            
# # # # # # # # # #             # 1. Session start
# # # # # # # # # #             print("📤 Sending session start...")
# # # # # # # # # #             await self.send_event(json.dumps({
# # # # # # # # # #                 "event": {
# # # # # # # # # #                     "sessionStart": {
# # # # # # # # # #                         "inferenceConfiguration": {
# # # # # # # # # #                             "maxTokens": 1024,
# # # # # # # # # #                             "topP": 0.9,
# # # # # # # # # #                             "temperature": 0.7
# # # # # # # # # #                         }
# # # # # # # # # #                     }
# # # # # # # # # #                 }
# # # # # # # # # #             }))
            
# # # # # # # # # #             # 2. Prompt start with audio output config
# # # # # # # # # #             print("📤 Sending prompt start...")
# # # # # # # # # #             await self.send_event(json.dumps({
# # # # # # # # # #                 "event": {
# # # # # # # # # #                     "promptStart": {
# # # # # # # # # #                         "promptName": self.prompt_name,
# # # # # # # # # #                         "textOutputConfiguration": {
# # # # # # # # # #                             "mediaType": "text/plain"
# # # # # # # # # #                         },
# # # # # # # # # #                         "audioOutputConfiguration": {
# # # # # # # # # #                             "mediaType": "audio/lpcm",
# # # # # # # # # #                             "sampleRateHertz": 24000,
# # # # # # # # # #                             "sampleSizeBits": 16,
# # # # # # # # # #                             "channelCount": 1,
# # # # # # # # # #                             "voiceId": "matthew",
# # # # # # # # # #                             "encoding": "base64",
# # # # # # # # # #                             "audioType": "SPEECH"
# # # # # # # # # #                         }
# # # # # # # # # #                     }
# # # # # # # # # #                 }
# # # # # # # # # #             }))
            
# # # # # # # # # #             # 3. System prompt
# # # # # # # # # #             print("📤 Sending system prompt...")
# # # # # # # # # #             await self.send_event(json.dumps({
# # # # # # # # # #                 "event": {
# # # # # # # # # #                     "contentStart": {
# # # # # # # # # #                         "promptName": self.prompt_name,
# # # # # # # # # #                         "contentName": self.system_content_name,
# # # # # # # # # #                         "type": "TEXT",
# # # # # # # # # #                         "interactive": False,
# # # # # # # # # #                         "role": "SYSTEM",
# # # # # # # # # #                         "textInputConfiguration": {
# # # # # # # # # #                             "mediaType": "text/plain"
# # # # # # # # # #                         }
# # # # # # # # # #                     }
# # # # # # # # # #                 }
# # # # # # # # # #             }))
            
# # # # # # # # # #             # Create engaging system prompt
# # # # # # # # # #             first_question = self.questions[0] if self.questions else "Tell me about your experience"
# # # # # # # # # #             system_text = f"""You are Nova, a friendly AI conducting an exit interview with {self.employee_name}. 
            
# # # # # # # # # # Start by warmly greeting {self.employee_name} and then ask your first question: {first_question}

# # # # # # # # # # Keep responses conversational, empathetic, and concise (2-3 sentences). After each answer, acknowledge it briefly and ask the next question naturally. Wait for the user to answer before asking the next question.

# # # # # # # # # # IMPORTANT: After asking all {len(self.questions)} questions, you must end the interview by saying "Thank you for completing the exit interview. Have a great day!" and then end the session.

# # # # # # # # # # The questions you must ask in order are:
# # # # # # # # # # {chr(10).join([f"{i+1}. {q}" for i, q in enumerate(self.questions)])}"""
            
# # # # # # # # # #             await self.send_event(json.dumps({
# # # # # # # # # #                 "event": {
# # # # # # # # # #                     "textInput": {
# # # # # # # # # #                         "promptName": self.prompt_name,
# # # # # # # # # #                         "contentName": self.system_content_name,
# # # # # # # # # #                         "content": system_text
# # # # # # # # # #                     }
# # # # # # # # # #                 }
# # # # # # # # # #             }))
            
# # # # # # # # # #             await self.send_event(json.dumps({
# # # # # # # # # #                 "event": {
# # # # # # # # # #                     "contentEnd": {
# # # # # # # # # #                         "promptName": self.prompt_name,
# # # # # # # # # #                         "contentName": self.system_content_name
# # # # # # # # # #                     }
# # # # # # # # # #                 }
# # # # # # # # # #             }))
            
# # # # # # # # # #             print("✅ System prompt sent - Nova should start speaking now!")
            
# # # # # # # # # #             # Start processing responses
# # # # # # # # # #             asyncio.create_task(self._process_responses())
            
# # # # # # # # # #         except Exception as e:
# # # # # # # # # #             print(f"❌ Error starting session: {e}")
# # # # # # # # # #             traceback.print_exc()
# # # # # # # # # #             raise
    
# # # # # # # # # #     async def start_audio_input(self):
# # # # # # # # # #         """Start continuous audio input"""
# # # # # # # # # #         print("📤 Starting audio input...")
# # # # # # # # # #         await self.send_event(json.dumps({
# # # # # # # # # #             "event": {
# # # # # # # # # #                 "contentStart": {
# # # # # # # # # #                     "promptName": self.prompt_name,
# # # # # # # # # #                     "contentName": self.audio_content_name,
# # # # # # # # # #                     "type": "AUDIO",
# # # # # # # # # #                     "interactive": True,
# # # # # # # # # #                     "role": "USER",
# # # # # # # # # #                     "audioInputConfiguration": {
# # # # # # # # # #                         "mediaType": "audio/lpcm",
# # # # # # # # # #                         "sampleRateHertz": 16000,
# # # # # # # # # #                         "sampleSizeBits": 16,
# # # # # # # # # #                         "channelCount": 1,
# # # # # # # # # #                         "audioType": "SPEECH",
# # # # # # # # # #                         "encoding": "base64"
# # # # # # # # # #                     }
# # # # # # # # # #                 }
# # # # # # # # # #             }
# # # # # # # # # #         }))
# # # # # # # # # #         print("✅ Audio input stream started - waiting for audio from client...")
    
# # # # # # # # # #     async def send_audio_chunk(self, audio_bytes):
# # # # # # # # # #         """Send audio chunk"""
# # # # # # # # # #         if not self.is_active:
# # # # # # # # # #             return
        
# # # # # # # # # #         self.last_audio_time = datetime.utcnow()
# # # # # # # # # #         blob = base64.b64encode(audio_bytes).decode('utf-8')
# # # # # # # # # #         try:
# # # # # # # # # #             await self.send_event(json.dumps({
# # # # # # # # # #                 "event": {
# # # # # # # # # #                     "audioInput": {
# # # # # # # # # #                         "promptName": self.prompt_name,
# # # # # # # # # #                         "contentName": self.audio_content_name,
# # # # # # # # # #                         "content": blob
# # # # # # # # # #                     }
# # # # # # # # # #                 }
# # # # # # # # # #             }))
# # # # # # # # # #         except Exception as e:
# # # # # # # # # #             print(f"⚠️ Error sending audio chunk: {e}")
    
# # # # # # # # # #     async def _process_responses(self):
# # # # # # # # # #         """Process responses from Nova"""
# # # # # # # # # #         try:
# # # # # # # # # #             while self.is_active:
# # # # # # # # # #                 try:
# # # # # # # # # #                     output = await self.stream.await_output()
# # # # # # # # # #                     result = await output[1].receive()
                    
# # # # # # # # # #                     if result.value and result.value.bytes_:
# # # # # # # # # #                         response_data = result.value.bytes_.decode('utf-8')
# # # # # # # # # #                         json_data = json.loads(response_data)
                        
# # # # # # # # # #                         if 'event' in json_data:
# # # # # # # # # #                             event = json_data['event']
                            
# # # # # # # # # #                             # Content start
# # # # # # # # # #                             if 'contentStart' in event:
# # # # # # # # # #                                 self.role = event['contentStart'].get('role')
# # # # # # # # # #                                 if 'additionalModelFields' in event['contentStart']:
# # # # # # # # # #                                     try:
# # # # # # # # # #                                         fields = json.loads(event['contentStart']['additionalModelFields'])
# # # # # # # # # #                                         self.display_assistant_text = fields.get('generationStage') == 'SPECULATIVE'
# # # # # # # # # #                                     except:
# # # # # # # # # #                                         pass
                            
# # # # # # # # # #                             # Text output
# # # # # # # # # #                             elif 'textOutput' in event:
# # # # # # # # # #                                 text = event['textOutput']['content']
# # # # # # # # # #                                 role = event['textOutput'].get('role', 'ASSISTANT')
                                
# # # # # # # # # #                                 if role == "ASSISTANT" and self.display_assistant_text:
# # # # # # # # # #                                     print(f"🤖 Nova: {text}")
# # # # # # # # # #                                     await self.websocket.send_json({
# # # # # # # # # #                                         'type': 'text',
# # # # # # # # # #                                         'content': text,
# # # # # # # # # #                                         'role': 'ASSISTANT'
# # # # # # # # # #                                     })
                                    
# # # # # # # # # #                                     # Check if Nova is asking a question
# # # # # # # # # #                                     if '?' in text and not self.current_question_asked:
# # # # # # # # # #                                         self.current_question_asked = True
# # # # # # # # # #                                         print(f"✅ Nova asked a question: {text}")
                                    
# # # # # # # # # #                                     # Check if Nova is ending the interview
# # # # # # # # # #                                     if "thank you for completing" in text.lower() or "have a great day" in text.lower():
# # # # # # # # # #                                         self.interview_complete = True
# # # # # # # # # #                                         print("✅ Nova is ending the interview")
                                        
# # # # # # # # # #                                 elif role == "USER":
# # # # # # # # # #                                     # Avoid duplicate user messages
# # # # # # # # # #                                     if text != self.last_user_text:
# # # # # # # # # #                                         print(f"👤 User: {text}")
# # # # # # # # # #                                         self.last_user_text = text
                                        
# # # # # # # # # #                                         # Only capture if we're expecting an answer
# # # # # # # # # #                                         if self.current_question_asked:
# # # # # # # # # #                                             # Append to current answer if not empty
# # # # # # # # # #                                             if self.current_answer:
# # # # # # # # # #                                                 self.current_answer += " "
# # # # # # # # # #                                             self.current_answer += text
# # # # # # # # # #                                             print(f"📝 Capturing answer: {text}")
                                        
# # # # # # # # # #                                         await self.websocket.send_json({
# # # # # # # # # #                                             'type': 'text',
# # # # # # # # # #                                             'content': text,
# # # # # # # # # #                                             'role': 'USER'
# # # # # # # # # #                                         })
                            
# # # # # # # # # #                             # Audio output
# # # # # # # # # #                             elif 'audioOutput' in event:
# # # # # # # # # #                                 audio_content = event['audioOutput']['content']
# # # # # # # # # #                                 print(f"🔊 Sending audio chunk ({len(audio_content)} chars)")
# # # # # # # # # #                                 await self.websocket.send_json({
# # # # # # # # # #                                     'type': 'audio',
# # # # # # # # # #                                     'data': audio_content
# # # # # # # # # #                                 })
                            
# # # # # # # # # #                             # Content end
# # # # # # # # # #                             elif 'contentEnd' in event:
# # # # # # # # # #                                 print("📌 Content ended")
                                
# # # # # # # # # #                                 # If Nova finished speaking and we were expecting an answer
# # # # # # # # # #                                 if self.role == "ASSISTANT" and self.current_question_asked:
# # # # # # # # # #                                     # Save the captured answer
# # # # # # # # # #                                     if self.current_answer.strip() and self.current_question_idx < len(self.questions):
# # # # # # # # # #                                         question = self.questions[self.current_question_idx]
# # # # # # # # # #                                         raw_answer = self.current_answer.strip()
                                        
# # # # # # # # # #                                         # Process with Bedrock
# # # # # # # # # #                                         processed_answer = process_user_answer_with_bedrock(raw_answer, question)
                                        
# # # # # # # # # #                                         self.responses.append({
# # # # # # # # # #                                             'question': question,
# # # # # # # # # #                                             'answer': processed_answer
# # # # # # # # # #                                         })
                                        
# # # # # # # # # #                                         print(f"💾 Saved answer for Q{self.current_question_idx+1}: {processed_answer}")
# # # # # # # # # #                                         self.current_question_idx += 1
                                        
# # # # # # # # # #                                         # Check if we've answered all questions
# # # # # # # # # #                                         if self.current_question_idx >= len(self.questions):
# # # # # # # # # #                                             self.all_questions_asked = True
# # # # # # # # # #                                             print(f"✅ All {len(self.questions)} questions answered")
                                    
# # # # # # # # # #                                     # Reset for next question
# # # # # # # # # #                                     self.current_answer = ""
# # # # # # # # # #                                     self.current_question_asked = False
                                
# # # # # # # # # #                                 # Check if we should end the interview
# # # # # # # # # #                                 if self.interview_complete or self.all_questions_asked:
# # # # # # # # # #                                     print("✅ Ending interview - all questions answered or completion detected")
# # # # # # # # # #                                     await self.websocket.send_json({
# # # # # # # # # #                                         'type': 'complete',
# # # # # # # # # #                                         'responses': self.responses
# # # # # # # # # #                                     })
# # # # # # # # # #                                     self.is_active = False
# # # # # # # # # #                                     return
                                
# # # # # # # # # #                                 await self.websocket.send_json({'type': 'content_end'})
                            
# # # # # # # # # #                             # Completion
# # # # # # # # # #                             elif 'completionEnd' in event:
# # # # # # # # # #                                 print("✅ Interview complete")
                                
# # # # # # # # # #                                 # Save any final captured answer
# # # # # # # # # #                                 if self.current_answer.strip() and self.current_question_idx < len(self.questions):
# # # # # # # # # #                                     question = self.questions[self.current_question_idx]
# # # # # # # # # #                                     raw_answer = self.current_answer.strip()
                                    
# # # # # # # # # #                                     # Process with Bedrock
# # # # # # # # # #                                     processed_answer = process_user_answer_with_bedrock(raw_answer, question)
                                    
# # # # # # # # # #                                     self.responses.append({
# # # # # # # # # #                                         'question': question,
# # # # # # # # # #                                         'answer': processed_answer
# # # # # # # # # #                                     })
                                    
# # # # # # # # # #                                     print(f"💾 Saved final answer for Q{self.current_question_idx+1}: {processed_answer}")
# # # # # # # # # #                                     self.current_question_idx += 1
                                
# # # # # # # # # #                                 await self.websocket.send_json({
# # # # # # # # # #                                     'type': 'complete',
# # # # # # # # # #                                     'responses': self.responses
# # # # # # # # # #                                 })
# # # # # # # # # #                                 self.is_active = False
# # # # # # # # # #                                 break
                
# # # # # # # # # #                 except asyncio.TimeoutError:
# # # # # # # # # #                     continue
# # # # # # # # # #                 except Exception as e:
# # # # # # # # # #                     print(f"⚠️ Error in response processing: {e}")
# # # # # # # # # #                     continue
        
# # # # # # # # # #         except Exception as e:
# # # # # # # # # #             print(f"❌ Fatal error in _process_responses: {e}")
# # # # # # # # # #             self.is_active = False
    
# # # # # # # # # #     async def end_session(self):
# # # # # # # # # #         """End session gracefully"""
# # # # # # # # # #         if not self.is_active:
# # # # # # # # # #             return
        
# # # # # # # # # #         try:
# # # # # # # # # #             # End audio input
# # # # # # # # # #             await self.send_event(json.dumps({
# # # # # # # # # #                 "event": {
# # # # # # # # # #                     "contentEnd": {
# # # # # # # # # #                         "promptName": self.prompt_name,
# # # # # # # # # #                         "contentName": self.audio_content_name
# # # # # # # # # #                     }
# # # # # # # # # #                 }
# # # # # # # # # #             }))
            
# # # # # # # # # #             # End prompt
# # # # # # # # # #             await self.send_event(json.dumps({
# # # # # # # # # #                 "event": {
# # # # # # # # # #                     "promptEnd": {
# # # # # # # # # #                         "promptName": self.prompt_name
# # # # # # # # # #                     }
# # # # # # # # # #                 }
# # # # # # # # # #             }))
            
# # # # # # # # # #             # End session
# # # # # # # # # #             await self.send_event(json.dumps({
# # # # # # # # # #                 "event": {
# # # # # # # # # #                     "sessionEnd": {}
# # # # # # # # # #                 }
# # # # # # # # # #             }))
            
# # # # # # # # # #             await self.stream.input_stream.close()
# # # # # # # # # #             self.is_active = False
# # # # # # # # # #             print("✅ Session ended")
        
# # # # # # # # # #         except Exception as e:
# # # # # # # # # #             print(f"⚠️ Error ending session: {e}")
# # # # # # # # # #             self.is_active = False

# # # # # # # # # # # ==================== AWS SES ====================
# # # # # # # # # # ses_client = boto3.client('ses', region_name=os.getenv("AWS_REGION", "us-east-1"))

# # # # # # # # # # def send_exit_interview_email(employee_email: str, employee_name: str, form_link: str) -> bool:
# # # # # # # # # #     SENDER = os.getenv("SES_SENDER_EMAIL")
# # # # # # # # # #     SUBJECT = "🎙️ Voice Exit Interview with Nova"
# # # # # # # # # #     BODY_HTML = f"""
# # # # # # # # # #     <html><body>
# # # # # # # # # #         <h1>Hello {employee_name}!</h1>
# # # # # # # # # #         <p>Have a voice conversation with Nova for your exit interview.</p>
# # # # # # # # # #         <p><a href="{form_link}">Start Voice Interview</a></p>
# # # # # # # # # #     </body></html>
# # # # # # # # # #     """
# # # # # # # # # #     try:
# # # # # # # # # #         ses_client.send_email(
# # # # # # # # # #             Source=SENDER,
# # # # # # # # # #             Destination={'ToAddresses': [employee_email]},
# # # # # # # # # #             Message={'Subject': {'Data': SUBJECT}, 'Body': {'Html': {'Data': BODY_HTML}}}
# # # # # # # # # #         )
# # # # # # # # # #         print(f"✅ Email sent to {employee_name}")
# # # # # # # # # #         return True
# # # # # # # # # #     except Exception as e:
# # # # # # # # # #         print(f"❌ Email error: {e}")
# # # # # # # # # #         return False

# # # # # # # # # # def generate_unique_token() -> str:
# # # # # # # # # #     return str(uuid.uuid4())

# # # # # # # # # # def create_form_link(token: str) -> str:
# # # # # # # # # #     return f"{os.getenv('APP_URL', 'http://localhost:8501')}/exit_interview?token={token}"

# # # # # # # # # # # ==================== FASTAPI APP ====================
# # # # # # # # # # app = FastAPI(title="Nova Sonic Exit Interview API", version="4.0.0")

# # # # # # # # # # app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# # # # # # # # # # def get_db():
# # # # # # # # # #     db = SessionLocal()
# # # # # # # # # #     try:
# # # # # # # # # #         yield db
# # # # # # # # # #     finally:
# # # # # # # # # #         db.close()

# # # # # # # # # # active_sessions: Dict[str, NovaInterviewClient] = {}

# # # # # # # # # # # ==================== API ENDPOINTS ====================

# # # # # # # # # # @app.get("/")
# # # # # # # # # # def root():
# # # # # # # # # #     return {"message": "Nova Sonic Exit Interview API", "version": "4.0.0", "status": "running"}

# # # # # # # # # # @app.post("/api/employees", response_model=EmployeeResponse, status_code=201)
# # # # # # # # # # def create_employee(employee: EmployeeCreate, db: Session = Depends(get_db)):
# # # # # # # # # #     try:
# # # # # # # # # #         existing = db.query(Employee).filter(Employee.email == employee.email).first()
# # # # # # # # # #         if existing:
# # # # # # # # # #             raise HTTPException(status_code=400, detail="Employee already exists")
        
# # # # # # # # # #         db_employee = Employee(
# # # # # # # # # #             name=employee.name, email=employee.email,
# # # # # # # # # #             department=employee.department,
# # # # # # # # # #             last_working_date=employee.last_working_date, status="Resigned"
# # # # # # # # # #         )
# # # # # # # # # #         db.add(db_employee)
# # # # # # # # # #         db.commit()
# # # # # # # # # #         db.refresh(db_employee)
        
# # # # # # # # # #         token = generate_unique_token()
# # # # # # # # # #         form_link = create_form_link(token)
        
# # # # # # # # # #         questions_json = json.dumps(employee.questions) if employee.questions else json.dumps([
# # # # # # # # # #             "What was your primary reason for leaving?",
# # # # # # # # # #             "How would you rate your overall experience with the company on a scale of 1 to 5?",
# # # # # # # # # #             "How was your relationship with your manager?",
# # # # # # # # # #             "Did you feel valued and recognized in your role?",
# # # # # # # # # #             "Would you recommend our company to others? Why or why not?"
# # # # # # # # # #         ])
        
# # # # # # # # # #         db_interview = ExitInterview(
# # # # # # # # # #             employee_id=db_employee.id, form_token=token,
# # # # # # # # # #             completed=False, questions_json=questions_json
# # # # # # # # # #         )
# # # # # # # # # #         db.add(db_interview)
# # # # # # # # # #         db.commit()
        
# # # # # # # # # #         send_exit_interview_email(db_employee.email, db_employee.name, form_link)
        
# # # # # # # # # #         return db_employee
# # # # # # # # # #     except HTTPException:
# # # # # # # # # #         raise
# # # # # # # # # #     except Exception as e:
# # # # # # # # # #         db.rollback()
# # # # # # # # # #         raise HTTPException(status_code=500, detail=str(e))

# # # # # # # # # # @app.get("/api/employees", response_model=List[EmployeeWithInterview])
# # # # # # # # # # def list_employees(db: Session = Depends(get_db)):
# # # # # # # # # #     employees = db.query(Employee).all()
# # # # # # # # # #     result = []
# # # # # # # # # #     for emp in employees:
# # # # # # # # # #         emp_dict = {
# # # # # # # # # #             "id": emp.id, "name": emp.name, "email": emp.email,
# # # # # # # # # #             "department": emp.department, "last_working_date": emp.last_working_date,
# # # # # # # # # #             "status": emp.status, "created_at": emp.created_at, "interview": None
# # # # # # # # # #         }
# # # # # # # # # #         if emp.exit_interview:
# # # # # # # # # #             emp_dict["interview"] = {
# # # # # # # # # #                 "id": emp.exit_interview.id,
# # # # # # # # # #                 "completed": emp.exit_interview.completed,
# # # # # # # # # #                 "form_token": emp.exit_interview.form_token,
# # # # # # # # # #                 "created_at": emp.exit_interview.created_at
# # # # # # # # # #             }
# # # # # # # # # #         result.append(emp_dict)
# # # # # # # # # #     return result

# # # # # # # # # # @app.get("/api/interviews/token/{token}")
# # # # # # # # # # def get_interview_by_token(token: str, db: Session = Depends(get_db)):
# # # # # # # # # #     interview = db.query(ExitInterview).filter(ExitInterview.form_token == token).first()
# # # # # # # # # #     if not interview:
# # # # # # # # # #         raise HTTPException(status_code=404, detail="Invalid token")
# # # # # # # # # #     if interview.completed:
# # # # # # # # # #         raise HTTPException(status_code=400, detail="Interview already completed")
    
# # # # # # # # # #     questions = json.loads(interview.questions_json)
# # # # # # # # # #     return {
# # # # # # # # # #         "interview_id": interview.id,
# # # # # # # # # #         "employee_name": interview.employee.name,
# # # # # # # # # #         "employee_department": interview.employee.department,
# # # # # # # # # #         "questions": questions,
# # # # # # # # # #         "total_questions": len(questions),
# # # # # # # # # #         "completed": interview.completed
# # # # # # # # # #     }

# # # # # # # # # # @app.websocket("/ws/interview/{token}")
# # # # # # # # # # async def websocket_interview(websocket: WebSocket, token: str):
# # # # # # # # # #     await websocket.accept()
    
# # # # # # # # # #     db = SessionLocal()
# # # # # # # # # #     session_id = str(uuid.uuid4())
# # # # # # # # # #     nova_client = None
    
# # # # # # # # # #     try:
# # # # # # # # # #         # Get interview
# # # # # # # # # #         interview = db.query(ExitInterview).filter(ExitInterview.form_token == token).first()
# # # # # # # # # #         if not interview:
# # # # # # # # # #             await websocket.send_json({"type": "error", "message": "Invalid token"})
# # # # # # # # # #             return
        
# # # # # # # # # #         questions = json.loads(interview.questions_json)
# # # # # # # # # #         employee_name = interview.employee.name
        
# # # # # # # # # #         print(f"\n{'='*60}")
# # # # # # # # # #         print(f"🎙️ Starting voice interview for {employee_name}")
# # # # # # # # # #         print(f"📋 Questions: {len(questions)}")
# # # # # # # # # #         print(f"{'='*60}\n")
        
# # # # # # # # # #         # Send session start
# # # # # # # # # #         await websocket.send_json({
# # # # # # # # # #             "type": "session_start",
# # # # # # # # # #             "session_id": session_id,
# # # # # # # # # #             "employee_name": employee_name,
# # # # # # # # # #             "total_questions": len(questions)
# # # # # # # # # #         })
        
# # # # # # # # # #         # Create and start Nova client
# # # # # # # # # #         nova_client = NovaInterviewClient(employee_name, questions, websocket, os.getenv("AWS_REGION", "us-east-1"))
# # # # # # # # # #         await nova_client.start_session()
        
# # # # # # # # # #         # Start audio input - wait for Nova to greet
# # # # # # # # # #         await asyncio.sleep(3)
# # # # # # # # # #         await nova_client.start_audio_input()
        
# # # # # # # # # #         active_sessions[session_id] = nova_client
        
# # # # # # # # # #         print("✅ Waiting for audio from client...")
        
# # # # # # # # # #         # Listen for audio from client with timeout
# # # # # # # # # #         timeout_seconds = 120  # 2 minute timeout if no audio
# # # # # # # # # #         start_time = datetime.utcnow()
        
# # # # # # # # # #         while nova_client.is_active:
# # # # # # # # # #             try:
# # # # # # # # # #                 message = await asyncio.wait_for(websocket.receive_json(), timeout=0.5)
                
# # # # # # # # # #                 # Reset timeout on any message
# # # # # # # # # #                 start_time = datetime.utcnow()
                
# # # # # # # # # #                 if message['type'] == 'audio_chunk':
# # # # # # # # # #                     audio_data = base64.b64decode(message['data'])
# # # # # # # # # #                     await nova_client.send_audio_chunk(audio_data)
# # # # # # # # # #                     print(f"📨 Audio chunk received ({len(audio_data)} bytes)")
                
# # # # # # # # # #                 elif message['type'] == 'close':
# # # # # # # # # #                     print("🛑 Client requested close")
# # # # # # # # # #                     break
            
# # # # # # # # # #             except asyncio.TimeoutError:
# # # # # # # # # #                 # Check if we've exceeded total timeout
# # # # # # # # # #                 elapsed = (datetime.utcnow() - start_time).total_seconds()
# # # # # # # # # #                 if elapsed > timeout_seconds:
# # # # # # # # # #                     print(f"⚠️ No audio from client for {timeout_seconds}s - ending session")
# # # # # # # # # #                     break
# # # # # # # # # #                 continue
# # # # # # # # # #             except WebSocketDisconnect:
# # # # # # # # # #                 print("⚠️ WebSocket disconnected")
# # # # # # # # # #                 break
# # # # # # # # # #             except Exception as e:
# # # # # # # # # #                 print(f"⚠️ Error receiving message: {e}")
# # # # # # # # # #                 break
        
# # # # # # # # # #         # Save responses to database
# # # # # # # # # #         print(f"\n💾 Processing {len(nova_client.responses)} responses for database")
# # # # # # # # # #         transcript = []
        
# # # # # # # # # #         if nova_client.responses:
# # # # # # # # # #             for resp in nova_client.responses:
# # # # # # # # # #                 # Create and save response
# # # # # # # # # #                 db_response = InterviewResponse(
# # # # # # # # # #                     interview_id=interview.id,
# # # # # # # # # #                     question=resp['question'],
# # # # # # # # # #                     answer=resp['answer']
# # # # # # # # # #                 )
# # # # # # # # # #                 db.add(db_response)
# # # # # # # # # #                 transcript.append(f"Q: {resp['question']}\nA: {resp['answer']}\n")
                
# # # # # # # # # #                 print(f"✅ Saved to DB: Q: {resp['question']}")
# # # # # # # # # #                 print(f"✅ Saved to DB: A: {resp['answer']}")
            
# # # # # # # # # #             # Update interview status
# # # # # # # # # #             interview.completed = True
# # # # # # # # # #             interview.conversation_transcript = '\n'.join(transcript)
# # # # # # # # # #             interview.employee.status = "Completed"
            
# # # # # # # # # #             # Commit changes
# # # # # # # # # #             db.commit()
# # # # # # # # # #             print(f"✅ Interview saved for {employee_name}")
# # # # # # # # # #         else:
# # # # # # # # # #             print(f"⚠️ No responses recorded for {employee_name}")
    
# # # # # # # # # #     except Exception as e:
# # # # # # # # # #         print(f"❌ Error: {e}")
# # # # # # # # # #         traceback.print_exc()
# # # # # # # # # #         try:
# # # # # # # # # #             await websocket.send_json({"type": "error", "message": str(e)})
# # # # # # # # # #         except:
# # # # # # # # # #             pass
# # # # # # # # # #     finally:
# # # # # # # # # #         if nova_client:
# # # # # # # # # #             await nova_client.end_session()
# # # # # # # # # #         if session_id in active_sessions:
# # # # # # # # # #             del active_sessions[session_id]
# # # # # # # # # #         db.close()

# # # # # # # # # # @app.get("/api/interviews/{interview_id}/responses", response_model=List[InterviewResponseDetail])
# # # # # # # # # # def get_interview_responses(interview_id: int, db: Session = Depends(get_db)):
# # # # # # # # # #     return db.query(InterviewResponse).filter(InterviewResponse.interview_id == interview_id).all()

# # # # # # # # # # @app.get("/api/stats")
# # # # # # # # # # def get_statistics(db: Session = Depends(get_db)):
# # # # # # # # # #     total = db.query(Employee).count()
# # # # # # # # # #     completed = db.query(ExitInterview).filter(ExitInterview.completed == True).count()
# # # # # # # # # #     return {
# # # # # # # # # #         "total_resignations": total,
# # # # # # # # # #         "completed_interviews": completed,
# # # # # # # # # #         "pending_interviews": total - completed,
# # # # # # # # # #         "completion_rate": (completed / total * 100) if total > 0 else 0
# # # # # # # # # #     }

# # # # # # # # # # def init_db():
# # # # # # # # # #     Base.metadata.create_all(bind=engine)
# # # # # # # # # #     print("✅ Database initialized!")

# # # # # # # # # # if __name__ == "__main__":
# # # # # # # # # #     init_db()
# # # # # # # # # #     import uvicorn
# # # # # # # # # #     print("\n🚀 Starting Nova Sonic Exit Interview Server")
# # # # # # # # # #     print("📡 Backend: http://0.0.0.0:8000")
# # # # # # # # # #     print("📖 API Docs: http://localhost:8000/docs")
# # # # # # # # # #     print("\n⚡ Nova Sonic is ready!\n")
# # # # # # # # # #     uvicorn.run(app, host="0.0.0.0", port=8000)



# # # # # # # # # """
# # # # # # # # # FIXED Nova Sonic Exit Interview Backend - PROPER DB SAVING
# # # # # # # # # Now actually saves Q&A pairs to database with Bedrock cleaning
# # # # # # # # # """

# # # # # # # # # from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
# # # # # # # # # from fastapi.middleware.cors import CORSMiddleware
# # # # # # # # # from sqlalchemy import create_engine, Column, Integer, String, Boolean, Date, DateTime, Text, ForeignKey
# # # # # # # # # from sqlalchemy.ext.declarative import declarative_base
# # # # # # # # # from sqlalchemy.orm import sessionmaker, Session, relationship
# # # # # # # # # from pydantic import BaseModel, EmailStr, field_validator
# # # # # # # # # from typing import List, Optional, Dict, Any
# # # # # # # # # from datetime import datetime, date
# # # # # # # # # import os
# # # # # # # # # from dotenv import load_dotenv
# # # # # # # # # import boto3
# # # # # # # # # import uuid
# # # # # # # # # import json
# # # # # # # # # import asyncio
# # # # # # # # # import base64
# # # # # # # # # import traceback
# # # # # # # # # import re

# # # # # # # # # from aws_sdk_bedrock_runtime.client import BedrockRuntimeClient, InvokeModelWithBidirectionalStreamOperationInput
# # # # # # # # # from aws_sdk_bedrock_runtime.models import InvokeModelWithBidirectionalStreamInputChunk, BidirectionalInputPayloadPart
# # # # # # # # # from aws_sdk_bedrock_runtime.config import Config
# # # # # # # # # from smithy_aws_core.identity.environment import EnvironmentCredentialsResolver

# # # # # # # # # load_dotenv()

# # # # # # # # # # ==================== DATABASE SETUP ====================
# # # # # # # # # DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

# # # # # # # # # engine = create_engine(DATABASE_URL)
# # # # # # # # # SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# # # # # # # # # Base = declarative_base()

# # # # # # # # # # ==================== DATABASE MODELS ====================
# # # # # # # # # class Employee(Base):
# # # # # # # # #     __tablename__ = "employees"
    
# # # # # # # # #     id = Column(Integer, primary_key=True, index=True)
# # # # # # # # #     name = Column(String(100), nullable=False)
# # # # # # # # #     email = Column(String(100), unique=True, nullable=False)
# # # # # # # # #     department = Column(String(50))
# # # # # # # # #     last_working_date = Column(Date)
# # # # # # # # #     status = Column(String(20), default="Resigned")
# # # # # # # # #     created_at = Column(DateTime, default=datetime.utcnow)
    
# # # # # # # # #     exit_interview = relationship("ExitInterview", back_populates="employee", uselist=False)

# # # # # # # # # class ExitInterview(Base):
# # # # # # # # #     __tablename__ = "exit_interviews"
    
# # # # # # # # #     id = Column(Integer, primary_key=True, index=True)
# # # # # # # # #     employee_id = Column(Integer, ForeignKey("employees.id"))
# # # # # # # # #     form_token = Column(String(255), unique=True, nullable=False)
# # # # # # # # #     completed = Column(Boolean, default=False)
# # # # # # # # #     questions_json = Column(Text)
# # # # # # # # #     created_at = Column(DateTime, default=datetime.utcnow)
    
# # # # # # # # #     employee = relationship("Employee", back_populates="exit_interview")
# # # # # # # # #     responses = relationship("InterviewResponse", back_populates="interview")

# # # # # # # # # class InterviewResponse(Base):
# # # # # # # # #     __tablename__ = "interview_responses"
    
# # # # # # # # #     id = Column(Integer, primary_key=True, index=True)
# # # # # # # # #     interview_id = Column(Integer, ForeignKey("exit_interviews.id"))
# # # # # # # # #     question = Column(Text, nullable=False)
# # # # # # # # #     answer = Column(Text, nullable=False)
# # # # # # # # #     created_at = Column(DateTime, default=datetime.utcnow)
    
# # # # # # # # #     interview = relationship("ExitInterview", back_populates="responses")

# # # # # # # # # # ==================== PYDANTIC SCHEMAS ====================
# # # # # # # # # class EmployeeCreate(BaseModel):
# # # # # # # # #     name: str
# # # # # # # # #     email: EmailStr
# # # # # # # # #     department: str
# # # # # # # # #     last_working_date: date
# # # # # # # # #     questions: Optional[List[str]] = None
    
# # # # # # # # #     @field_validator('name')
# # # # # # # # #     def name_must_not_be_empty(cls, v):
# # # # # # # # #         if not v or not v.strip():
# # # # # # # # #             raise ValueError('Name cannot be empty')
# # # # # # # # #         return v.strip()

# # # # # # # # # class EmployeeResponse(BaseModel):
# # # # # # # # #     id: int
# # # # # # # # #     name: str
# # # # # # # # #     email: str
# # # # # # # # #     department: str
# # # # # # # # #     last_working_date: date
# # # # # # # # #     status: str
# # # # # # # # #     created_at: datetime
    
# # # # # # # # #     class Config:
# # # # # # # # #         from_attributes = True

# # # # # # # # # class InterviewStatusResponse(BaseModel):
# # # # # # # # #     id: int
# # # # # # # # #     completed: bool
# # # # # # # # #     form_token: str
# # # # # # # # #     created_at: datetime
    
# # # # # # # # #     class Config:
# # # # # # # # #         from_attributes = True

# # # # # # # # # class InterviewResponseDetail(BaseModel):
# # # # # # # # #     id: int
# # # # # # # # #     question: str
# # # # # # # # #     answer: str
# # # # # # # # #     created_at: datetime
    
# # # # # # # # #     class Config:
# # # # # # # # #         from_attributes = True

# # # # # # # # # # ==================== BEDROCK ANSWER CLEANING ====================
# # # # # # # # # def clean_answer_with_bedrock(raw_answer: str, question: str) -> str:
# # # # # # # # #     """Clean answer using Bedrock - removes filler, greetings, etc."""
# # # # # # # # #     try:
# # # # # # # # #         if not raw_answer or len(raw_answer.strip()) < 2:
# # # # # # # # #             return raw_answer.strip()
        
# # # # # # # # #         bedrock = boto3.client('bedrock-runtime', region_name=os.getenv("AWS_REGION", "us-east-1"))
        
# # # # # # # # #         prompt = f"""Extract the meaningful answer from this speech transcription. Remove greetings, filler words, and conversational noise.

# # # # # # # # # Question: {question}
# # # # # # # # # Raw Answer: {raw_answer}

# # # # # # # # # Return ONLY the cleaned answer, nothing else:"""

# # # # # # # # #         body = json.dumps({
# # # # # # # # #             "inputText": prompt,
# # # # # # # # #             "textGenerationConfig": {
# # # # # # # # #                 "maxTokenCount": 100,
# # # # # # # # #                 "temperature": 0.1,
# # # # # # # # #                 "topP": 0.9
# # # # # # # # #             }
# # # # # # # # #         })
        
# # # # # # # # #         response = bedrock.invoke_model(
# # # # # # # # #             body=body,
# # # # # # # # #             modelId="amazon.titan-text-express-v1",
# # # # # # # # #             accept="application/json",
# # # # # # # # #             contentType="application/json"
# # # # # # # # #         )
        
# # # # # # # # #         response_body = json.loads(response.get('body').read())
# # # # # # # # #         cleaned = response_body.get('results', [{}])[0].get('outputText', '').strip()
        
# # # # # # # # #         return cleaned if cleaned else raw_answer.strip()
    
# # # # # # # # #     except Exception as e:
# # # # # # # # #         print(f"⚠️ Bedrock error: {e} - using raw answer")
# # # # # # # # #         return raw_answer.strip()

# # # # # # # # # # ==================== NOVA SONIC CLIENT ====================
# # # # # # # # # class NovaInterviewClient:
# # # # # # # # #     def __init__(self, employee_name: str, questions: List[str], websocket: WebSocket, db: Session, interview_id: int, region='us-east-1'):
# # # # # # # # #         self.model_id = 'amazon.nova-sonic-v1:0'
# # # # # # # # #         self.region = region
# # # # # # # # #         self.employee_name = employee_name
# # # # # # # # #         self.questions = questions
# # # # # # # # #         self.websocket = websocket
# # # # # # # # #         self.db = db
# # # # # # # # #         self.interview_id = interview_id
# # # # # # # # #         self.client = None
# # # # # # # # #         self.stream = None
# # # # # # # # #         self.is_active = False
        
# # # # # # # # #         # UUIDs for stream
# # # # # # # # #         self.prompt_name = str(uuid.uuid4())
# # # # # # # # #         self.system_content_name = str(uuid.uuid4())
# # # # # # # # #         self.audio_content_name = str(uuid.uuid4())
        
# # # # # # # # #         # State tracking
# # # # # # # # #         self.current_q_idx = 0
# # # # # # # # #         self.user_answer_buffer = ""
# # # # # # # # #         self.waiting_for_answer = False
# # # # # # # # #         self.last_user_text = ""
# # # # # # # # #         self.interview_complete = False
    
# # # # # # # # #     def _initialize_client(self):
# # # # # # # # #         """Initialize Bedrock client"""
# # # # # # # # #         resolver = EnvironmentCredentialsResolver()
# # # # # # # # #         config = Config(
# # # # # # # # #             endpoint_uri=f"https://bedrock-runtime.{self.region}.amazonaws.com",
# # # # # # # # #             region=self.region,
# # # # # # # # #             aws_credentials_identity_resolver=resolver
# # # # # # # # #         )
# # # # # # # # #         self.client = BedrockRuntimeClient(config=config)
# # # # # # # # #         print("✅ Bedrock client initialized")
    
# # # # # # # # #     async def send_event(self, event_json):
# # # # # # # # #         """Send event to stream"""
# # # # # # # # #         event = InvokeModelWithBidirectionalStreamInputChunk(
# # # # # # # # #             value=BidirectionalInputPayloadPart(bytes_=event_json.encode('utf-8'))
# # # # # # # # #         )
# # # # # # # # #         await self.stream.input_stream.send(event)
    
# # # # # # # # #     async def start_session(self):
# # # # # # # # #         """Start Nova Sonic session"""
# # # # # # # # #         if not self.client:
# # # # # # # # #             self._initialize_client()
        
# # # # # # # # #         try:
# # # # # # # # #             print("📡 Starting bidirectional stream...")
# # # # # # # # #             self.stream = await self.client.invoke_model_with_bidirectional_stream(
# # # # # # # # #                 InvokeModelWithBidirectionalStreamOperationInput(model_id=self.model_id)
# # # # # # # # #             )
# # # # # # # # #             self.is_active = True
# # # # # # # # #             print("✅ Stream started")
            
# # # # # # # # #             # Session start
# # # # # # # # #             await self.send_event(json.dumps({
# # # # # # # # #                 "event": {
# # # # # # # # #                     "sessionStart": {
# # # # # # # # #                         "inferenceConfiguration": {
# # # # # # # # #                             "maxTokens": 1024,
# # # # # # # # #                             "topP": 0.9,
# # # # # # # # #                             "temperature": 0.7
# # # # # # # # #                         }
# # # # # # # # #                     }
# # # # # # # # #                 }
# # # # # # # # #             }))
            
# # # # # # # # #             # Prompt start
# # # # # # # # #             await self.send_event(json.dumps({
# # # # # # # # #                 "event": {
# # # # # # # # #                     "promptStart": {
# # # # # # # # #                         "promptName": self.prompt_name,
# # # # # # # # #                         "textOutputConfiguration": {
# # # # # # # # #                             "mediaType": "text/plain"
# # # # # # # # #                         },
# # # # # # # # #                         "audioOutputConfiguration": {
# # # # # # # # #                             "mediaType": "audio/lpcm",
# # # # # # # # #                             "sampleRateHertz": 24000,
# # # # # # # # #                             "sampleSizeBits": 16,
# # # # # # # # #                             "channelCount": 1,
# # # # # # # # #                             "voiceId": "matthew",
# # # # # # # # #                             "encoding": "base64",
# # # # # # # # #                             "audioType": "SPEECH"
# # # # # # # # #                         }
# # # # # # # # #                     }
# # # # # # # # #                 }
# # # # # # # # #             }))
            
# # # # # # # # #             # System prompt
# # # # # # # # #             await self.send_event(json.dumps({
# # # # # # # # #                 "event": {
# # # # # # # # #                     "contentStart": {
# # # # # # # # #                         "promptName": self.prompt_name,
# # # # # # # # #                         "contentName": self.system_content_name,
# # # # # # # # #                         "type": "TEXT",
# # # # # # # # #                         "interactive": False,
# # # # # # # # #                         "role": "SYSTEM",
# # # # # # # # #                         "textInputConfiguration": {
# # # # # # # # #                             "mediaType": "text/plain"
# # # # # # # # #                         }
# # # # # # # # #                     }
# # # # # # # # #                 }
# # # # # # # # #             }))
            
# # # # # # # # #             questions_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(self.questions)])
            
# # # # # # # # #             system_text = f"""You are Nova, conducting an EXIT INTERVIEW with {self.employee_name}.

# # # # # # # # # CRITICAL:
# # # # # # # # # 1. Greet warmly ONCE at the start
# # # # # # # # # 2. Ask these {len(self.questions)} questions IN ORDER, one at a time
# # # # # # # # # 3. Wait for full answer before asking next question
# # # # # # # # # 4. After ALL questions, say EXACTLY: "Thank you for completing the exit interview. Goodbye."

# # # # # # # # # Questions to ask (in order):
# # # # # # # # # {questions_text}

# # # # # # # # # Be conversational. Wait for answers."""

# # # # # # # # #             await self.send_event(json.dumps({
# # # # # # # # #                 "event": {
# # # # # # # # #                     "textInput": {
# # # # # # # # #                         "promptName": self.prompt_name,
# # # # # # # # #                         "contentName": self.system_content_name,
# # # # # # # # #                         "content": system_text
# # # # # # # # #                     }
# # # # # # # # #                 }
# # # # # # # # #             }))
            
# # # # # # # # #             await self.send_event(json.dumps({
# # # # # # # # #                 "event": {
# # # # # # # # #                     "contentEnd": {
# # # # # # # # #                         "promptName": self.prompt_name,
# # # # # # # # #                         "contentName": self.system_content_name
# # # # # # # # #                     }
# # # # # # # # #                 }
# # # # # # # # #             }))
            
# # # # # # # # #             print("✅ System prompt sent")
# # # # # # # # #             asyncio.create_task(self._process_responses())
        
# # # # # # # # #         except Exception as e:
# # # # # # # # #             print(f"❌ Error starting session: {e}")
# # # # # # # # #             traceback.print_exc()
# # # # # # # # #             raise
    
# # # # # # # # #     async def start_audio_input(self):
# # # # # # # # #         """Start audio input"""
# # # # # # # # #         await self.send_event(json.dumps({
# # # # # # # # #             "event": {
# # # # # # # # #                 "contentStart": {
# # # # # # # # #                     "promptName": self.prompt_name,
# # # # # # # # #                     "contentName": self.audio_content_name,
# # # # # # # # #                     "type": "AUDIO",
# # # # # # # # #                     "interactive": True,
# # # # # # # # #                     "role": "USER",
# # # # # # # # #                     "audioInputConfiguration": {
# # # # # # # # #                         "mediaType": "audio/lpcm",
# # # # # # # # #                         "sampleRateHertz": 16000,
# # # # # # # # #                         "sampleSizeBits": 16,
# # # # # # # # #                         "channelCount": 1,
# # # # # # # # #                         "audioType": "SPEECH",
# # # # # # # # #                         "encoding": "base64"
# # # # # # # # #                     }
# # # # # # # # #                 }
# # # # # # # # #             }
# # # # # # # # #         }))
# # # # # # # # #         print("✅ Audio input started")
    
# # # # # # # # #     async def send_audio_chunk(self, audio_bytes):
# # # # # # # # #         """Send audio chunk"""
# # # # # # # # #         if not self.is_active:
# # # # # # # # #             return
        
# # # # # # # # #         blob = base64.b64encode(audio_bytes).decode('utf-8')
# # # # # # # # #         try:
# # # # # # # # #             await self.send_event(json.dumps({
# # # # # # # # #                 "event": {
# # # # # # # # #                     "audioInput": {
# # # # # # # # #                         "promptName": self.prompt_name,
# # # # # # # # #                         "contentName": self.audio_content_name,
# # # # # # # # #                         "content": blob
# # # # # # # # #                     }
# # # # # # # # #                 }
# # # # # # # # #             }))
# # # # # # # # #         except Exception as e:
# # # # # # # # #             print(f"⚠️ Error sending audio: {e}")
    
# # # # # # # # #     async def _save_response_to_db(self, question: str, raw_answer: str):
# # # # # # # # #         """Save response to database with Bedrock cleaning"""
# # # # # # # # #         try:
# # # # # # # # #             print(f"\n🔄 Processing Q{self.current_q_idx + 1}...")
# # # # # # # # #             print(f"   Raw: {raw_answer[:80]}...")
            
# # # # # # # # #             # Clean with Bedrock
# # # # # # # # #             cleaned_answer = clean_answer_with_bedrock(raw_answer, question)
            
# # # # # # # # #             print(f"   Cleaned: {cleaned_answer[:80]}...")
            
# # # # # # # # #             # Save to DB
# # # # # # # # #             db_response = InterviewResponse(
# # # # # # # # #                 interview_id=self.interview_id,
# # # # # # # # #                 question=question,
# # # # # # # # #                 answer=cleaned_answer
# # # # # # # # #             )
# # # # # # # # #             self.db.add(db_response)
# # # # # # # # #             self.db.commit()
            
# # # # # # # # #             print(f"✅ SAVED Q{self.current_q_idx + 1} to database")
            
# # # # # # # # #             # Notify frontend
# # # # # # # # #             await self.websocket.send_json({
# # # # # # # # #                 'type': 'response_saved',
# # # # # # # # #                 'q_index': self.current_q_idx,
# # # # # # # # #                 'question': question,
# # # # # # # # #                 'answer': cleaned_answer
# # # # # # # # #             })
            
# # # # # # # # #             self.current_q_idx += 1
# # # # # # # # #             return True
        
# # # # # # # # #         except Exception as e:
# # # # # # # # #             print(f"❌ Error saving to DB: {e}")
# # # # # # # # #             traceback.print_exc()
# # # # # # # # #             return False
    
# # # # # # # # #     async def _process_responses(self):
# # # # # # # # #         """Process responses from Nova - SAVE TO DB"""
# # # # # # # # #         try:
# # # # # # # # #             while self.is_active:
# # # # # # # # #                 try:
# # # # # # # # #                     output = await self.stream.await_output()
# # # # # # # # #                     result = await output[1].receive()
                    
# # # # # # # # #                     if result.value and result.value.bytes_:
# # # # # # # # #                         response_data = result.value.bytes_.decode('utf-8')
# # # # # # # # #                         json_data = json.loads(response_data)
                        
# # # # # # # # #                         if 'event' not in json_data:
# # # # # # # # #                             continue
                        
# # # # # # # # #                         event = json_data['event']
                        
# # # # # # # # #                         # Text output
# # # # # # # # #                         if 'textOutput' in event:
# # # # # # # # #                             text = event['textOutput']['content']
# # # # # # # # #                             role = event['textOutput'].get('role', 'ASSISTANT')
                            
# # # # # # # # #                             if role == "ASSISTANT":
# # # # # # # # #                                 print(f"🤖 Nova: {text}")
# # # # # # # # #                                 await self.websocket.send_json({
# # # # # # # # #                                     'type': 'text',
# # # # # # # # #                                     'content': text,
# # # # # # # # #                                     'role': 'ASSISTANT'
# # # # # # # # #                                 })
                                
# # # # # # # # #                                 # Check if asking question
# # # # # # # # #                                 if '?' in text:
# # # # # # # # #                                     self.waiting_for_answer = True
# # # # # # # # #                                     print(f"❓ Waiting for answer to Q{self.current_q_idx + 1}")
                                
# # # # # # # # #                                 # Check if ending
# # # # # # # # #                                 if "thank you for completing" in text.lower() and "goodbye" in text.lower():
# # # # # # # # #                                     print("✅ Nova ending interview")
# # # # # # # # #                                     await self._finalize_interview()
# # # # # # # # #                                     return
                            
# # # # # # # # #                             elif role == "USER" and self.waiting_for_answer:
# # # # # # # # #                                 # Accumulate user answer
# # # # # # # # #                                 if text != self.last_user_text and text.strip():
# # # # # # # # #                                     print(f"👤 User: {text}")
# # # # # # # # #                                     self.last_user_text = text
                                    
# # # # # # # # #                                     if self.user_answer_buffer:
# # # # # # # # #                                         self.user_answer_buffer += " "
# # # # # # # # #                                     self.user_answer_buffer += text
                                    
# # # # # # # # #                                     await self.websocket.send_json({
# # # # # # # # #                                         'type': 'text',
# # # # # # # # #                                         'content': text,
# # # # # # # # #                                         'role': 'USER'
# # # # # # # # #                                     })
                        
# # # # # # # # #                         # Audio output
# # # # # # # # #                         elif 'audioOutput' in event:
# # # # # # # # #                             audio_content = event['audioOutput']['content']
# # # # # # # # #                             await self.websocket.send_json({
# # # # # # # # #                                 'type': 'audio',
# # # # # # # # #                                 'data': audio_content
# # # # # # # # #                             })
                        
# # # # # # # # #                         # CRITICAL: Save answer when Nova finishes speaking
# # # # # # # # #                         elif 'contentEnd' in event:
# # # # # # # # #                             if self.waiting_for_answer and self.user_answer_buffer.strip():
# # # # # # # # #                                 if self.current_q_idx < len(self.questions):
# # # # # # # # #                                     question = self.questions[self.current_q_idx]
# # # # # # # # #                                     raw_answer = self.user_answer_buffer.strip()
                                    
# # # # # # # # #                                     # SAVE TO DATABASE
# # # # # # # # #                                     await self._save_response_to_db(question, raw_answer)
                                    
# # # # # # # # #                                     self.user_answer_buffer = ""
# # # # # # # # #                                     self.waiting_for_answer = False
                        
# # # # # # # # #                         # Completion
# # # # # # # # #                         elif 'completionEnd' in event:
# # # # # # # # #                             print("✅ Stream ended")
# # # # # # # # #                             await self._finalize_interview()
# # # # # # # # #                             return
                
# # # # # # # # #                 except asyncio.TimeoutError:
# # # # # # # # #                     continue
# # # # # # # # #                 except Exception as e:
# # # # # # # # #                     print(f"⚠️ Processing error: {e}")
# # # # # # # # #                     continue
        
# # # # # # # # #         except Exception as e:
# # # # # # # # #             print(f"❌ Fatal error: {e}")
# # # # # # # # #             self.is_active = False
    
# # # # # # # # #     async def _finalize_interview(self):
# # # # # # # # #         """Finalize and close interview"""
# # # # # # # # #         print(f"\n{'='*60}")
# # # # # # # # #         print(f"✅ Interview Complete: {self.current_q_idx}/{len(self.questions)}")
# # # # # # # # #         print(f"{'='*60}\n")
        
# # # # # # # # #         try:
# # # # # # # # #             # Mark as completed
# # # # # # # # #             interview = self.db.query(ExitInterview).filter(ExitInterview.id == self.interview_id).first()
# # # # # # # # #             if interview:
# # # # # # # # #                 interview.completed = True
# # # # # # # # #                 interview.employee.status = "Completed"
# # # # # # # # #                 self.db.commit()
# # # # # # # # #                 print("✅ Interview marked as completed in DB")
# # # # # # # # #         except Exception as e:
# # # # # # # # #             print(f"⚠️ Error updating interview: {e}")
        
# # # # # # # # #         await self.websocket.send_json({
# # # # # # # # #             'type': 'interview_complete',
# # # # # # # # #             'questions_answered': self.current_q_idx,
# # # # # # # # #             'total_questions': len(self.questions)
# # # # # # # # #         })
        
# # # # # # # # #         self.is_active = False
    
# # # # # # # # #     async def end_session(self):
# # # # # # # # #         """End session"""
# # # # # # # # #         if not self.is_active:
# # # # # # # # #             return
        
# # # # # # # # #         try:
# # # # # # # # #             await self.send_event(json.dumps({
# # # # # # # # #                 "event": {
# # # # # # # # #                     "contentEnd": {
# # # # # # # # #                         "promptName": self.prompt_name,
# # # # # # # # #                         "contentName": self.audio_content_name
# # # # # # # # #                     }
# # # # # # # # #                 }
# # # # # # # # #             }))
            
# # # # # # # # #             await self.send_event(json.dumps({
# # # # # # # # #                 "event": {
# # # # # # # # #                     "promptEnd": {
# # # # # # # # #                         "promptName": self.prompt_name
# # # # # # # # #                     }
# # # # # # # # #                 }
# # # # # # # # #             }))
            
# # # # # # # # #             await self.send_event(json.dumps({
# # # # # # # # #                 "event": {
# # # # # # # # #                     "sessionEnd": {}
# # # # # # # # #                 }
# # # # # # # # #             }))
            
# # # # # # # # #             await self.stream.input_stream.close()
# # # # # # # # #             self.is_active = False
# # # # # # # # #             print("✅ Session ended")
        
# # # # # # # # #         except Exception as e:
# # # # # # # # #             print(f"⚠️ Error ending: {e}")
# # # # # # # # #             self.is_active = False

# # # # # # # # # # ==================== AWS SES ====================
# # # # # # # # # ses_client = boto3.client('ses', region_name=os.getenv("AWS_REGION", "us-east-1"))

# # # # # # # # # def send_exit_interview_email(employee_email: str, employee_name: str, form_link: str) -> bool:
# # # # # # # # #     SENDER = os.getenv("SES_SENDER_EMAIL")
# # # # # # # # #     SUBJECT = "🎙️ Voice Exit Interview with Nova"
# # # # # # # # #     BODY_HTML = f"""
# # # # # # # # #     <html><body>
# # # # # # # # #         <h1>Hello {employee_name}!</h1>
# # # # # # # # #         <p>Have a voice conversation with Nova for your exit interview.</p>
# # # # # # # # #         <p><a href="{form_link}">Start Voice Interview</a></p>
# # # # # # # # #     </body></html>
# # # # # # # # #     """
# # # # # # # # #     try:
# # # # # # # # #         ses_client.send_email(
# # # # # # # # #             Source=SENDER,
# # # # # # # # #             Destination={'ToAddresses': [employee_email]},
# # # # # # # # #             Message={'Subject': {'Data': SUBJECT}, 'Body': {'Html': {'Data': BODY_HTML}}}
# # # # # # # # #         )
# # # # # # # # #         print(f"✅ Email sent to {employee_name}")
# # # # # # # # #         return True
# # # # # # # # #     except Exception as e:
# # # # # # # # #         print(f"❌ Email error: {e}")
# # # # # # # # #         return False

# # # # # # # # # def generate_unique_token() -> str:
# # # # # # # # #     return str(uuid.uuid4())

# # # # # # # # # def create_form_link(token: str) -> str:
# # # # # # # # #     return f"{os.getenv('APP_URL', 'http://localhost:8501')}/exit_interview?token={token}"

# # # # # # # # # # ==================== FASTAPI APP ====================
# # # # # # # # # app = FastAPI(title="Nova Sonic Exit Interview API", version="5.1.0")

# # # # # # # # # app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# # # # # # # # # def get_db():
# # # # # # # # #     db = SessionLocal()
# # # # # # # # #     try:
# # # # # # # # #         yield db
# # # # # # # # #     finally:
# # # # # # # # #         db.close()

# # # # # # # # # active_sessions: Dict[str, NovaInterviewClient] = {}

# # # # # # # # # # ==================== API ENDPOINTS ====================

# # # # # # # # # @app.get("/")
# # # # # # # # # def root():
# # # # # # # # #     return {"message": "Nova Sonic Exit Interview API", "version": "5.1.0", "status": "running"}

# # # # # # # # # @app.post("/api/employees", response_model=EmployeeResponse, status_code=201)
# # # # # # # # # def create_employee(employee: EmployeeCreate, db: Session = Depends(get_db)):
# # # # # # # # #     try:
# # # # # # # # #         existing = db.query(Employee).filter(Employee.email == employee.email).first()
# # # # # # # # #         if existing:
# # # # # # # # #             raise HTTPException(status_code=400, detail="Employee already exists")
        
# # # # # # # # #         db_employee = Employee(
# # # # # # # # #             name=employee.name,
# # # # # # # # #             email=employee.email,
# # # # # # # # #             department=employee.department,
# # # # # # # # #             last_working_date=employee.last_working_date,
# # # # # # # # #             status="Resigned"
# # # # # # # # #         )
# # # # # # # # #         db.add(db_employee)
# # # # # # # # #         db.commit()
# # # # # # # # #         db.refresh(db_employee)
        
# # # # # # # # #         token = generate_unique_token()
# # # # # # # # #         form_link = create_form_link(token)
        
# # # # # # # # #         questions_json = json.dumps(employee.questions) if employee.questions else json.dumps([
# # # # # # # # #             "What was your primary reason for leaving?",
# # # # # # # # #             "How would you rate your overall experience with the company on a scale of 1 to 5?",
# # # # # # # # #             "How was your relationship with your manager?",
# # # # # # # # #             "Did you feel valued and recognized in your role?",
# # # # # # # # #             "Would you recommend our company to others? Why or why not?"
# # # # # # # # #         ])
        
# # # # # # # # #         db_interview = ExitInterview(
# # # # # # # # #             employee_id=db_employee.id,
# # # # # # # # #             form_token=token,
# # # # # # # # #             completed=False,
# # # # # # # # #             questions_json=questions_json
# # # # # # # # #         )
# # # # # # # # #         db.add(db_interview)
# # # # # # # # #         db.commit()
        
# # # # # # # # #         send_exit_interview_email(db_employee.email, db_employee.name, form_link)
        
# # # # # # # # #         return db_employee
# # # # # # # # #     except HTTPException:
# # # # # # # # #         raise
# # # # # # # # #     except Exception as e:
# # # # # # # # #         db.rollback()
# # # # # # # # #         raise HTTPException(status_code=500, detail=str(e))

# # # # # # # # # @app.get("/api/employees", response_model=List[EmployeeResponse])
# # # # # # # # # def list_employees(db: Session = Depends(get_db)):
# # # # # # # # #     return db.query(Employee).all()

# # # # # # # # # @app.get("/api/interviews/token/{token}")
# # # # # # # # # def get_interview_by_token(token: str, db: Session = Depends(get_db)):
# # # # # # # # #     interview = db.query(ExitInterview).filter(ExitInterview.form_token == token).first()
# # # # # # # # #     if not interview:
# # # # # # # # #         raise HTTPException(status_code=404, detail="Invalid token")
# # # # # # # # #     if interview.completed:
# # # # # # # # #         raise HTTPException(status_code=400, detail="Interview already completed")
    
# # # # # # # # #     questions = json.loads(interview.questions_json)
# # # # # # # # #     return {
# # # # # # # # #         "interview_id": interview.id,
# # # # # # # # #         "employee_name": interview.employee.name,
# # # # # # # # #         "employee_department": interview.employee.department,
# # # # # # # # #         "questions": questions,
# # # # # # # # #         "total_questions": len(questions),
# # # # # # # # #         "completed": interview.completed
# # # # # # # # #     }

# # # # # # # # # @app.websocket("/ws/interview/{token}")
# # # # # # # # # async def websocket_interview(websocket: WebSocket, token: str):
# # # # # # # # #     await websocket.accept()
    
# # # # # # # # #     db = SessionLocal()
# # # # # # # # #     session_id = str(uuid.uuid4())
# # # # # # # # #     nova_client = None
    
# # # # # # # # #     try:
# # # # # # # # #         interview = db.query(ExitInterview).filter(ExitInterview.form_token == token).first()
# # # # # # # # #         if not interview:
# # # # # # # # #             await websocket.send_json({"type": "error", "message": "Invalid token"})
# # # # # # # # #             return
        
# # # # # # # # #         questions = json.loads(interview.questions_json)
# # # # # # # # #         employee_name = interview.employee.name
        
# # # # # # # # #         print(f"\n{'='*60}")
# # # # # # # # #         print(f"🎙️ Interview for {employee_name}")
# # # # # # # # #         print(f"📋 {len(questions)} questions")
# # # # # # # # #         print(f"{'='*60}\n")
        
# # # # # # # # #         await websocket.send_json({
# # # # # # # # #             "type": "session_start",
# # # # # # # # #             "session_id": session_id,
# # # # # # # # #             "employee_name": employee_name,
# # # # # # # # #             "total_questions": len(questions)
# # # # # # # # #         })
        
# # # # # # # # #         # PASS DB AND INTERVIEW_ID TO NOVA CLIENT
# # # # # # # # #         nova_client = NovaInterviewClient(
# # # # # # # # #             employee_name,
# # # # # # # # #             questions,
# # # # # # # # #             websocket,
# # # # # # # # #             db,  # ← DB session
# # # # # # # # #             interview.id,  # ← Interview ID
# # # # # # # # #             os.getenv("AWS_REGION", "us-east-1")
# # # # # # # # #         )
# # # # # # # # #         await nova_client.start_session()
        
# # # # # # # # #         await asyncio.sleep(2)
# # # # # # # # #         await nova_client.start_audio_input()
        
# # # # # # # # #         active_sessions[session_id] = nova_client
        
# # # # # # # # #         timeout_seconds = 180
# # # # # # # # #         start_time = datetime.utcnow()
        
# # # # # # # # #         while nova_client.is_active:
# # # # # # # # #             try:
# # # # # # # # #                 message = await asyncio.wait_for(websocket.receive_json(), timeout=0.5)
# # # # # # # # #                 start_time = datetime.utcnow()
                
# # # # # # # # #                 if message['type'] == 'audio_chunk':
# # # # # # # # #                     audio_data = base64.b64decode(message['data'])
# # # # # # # # #                     await nova_client.send_audio_chunk(audio_data)
                
# # # # # # # # #                 elif message['type'] == 'close':
# # # # # # # # #                     break
            
# # # # # # # # #             except asyncio.TimeoutError:
# # # # # # # # #                 elapsed = (datetime.utcnow() - start_time).total_seconds()
# # # # # # # # #                 if elapsed > timeout_seconds:
# # # # # # # # #                     print(f"⚠️ Timeout")
# # # # # # # # #                     break
# # # # # # # # #                 continue
# # # # # # # # #             except WebSocketDisconnect:
# # # # # # # # #                 print("⚠️ Disconnected")
# # # # # # # # #                 break
# # # # # # # # #             except Exception as e:
# # # # # # # # #                 print(f"⚠️ Error: {e}")
# # # # # # # # #                 break
    
# # # # # # # # #     except Exception as e:
# # # # # # # # #         print(f"❌ Error: {e}")
# # # # # # # # #         traceback.print_exc()
# # # # # # # # #         try:
# # # # # # # # #             await websocket.send_json({"type": "error", "message": str(e)})
# # # # # # # # #         except:
# # # # # # # # #             pass
# # # # # # # # #     finally:
# # # # # # # # #         if nova_client:
# # # # # # # # #             await nova_client.end_session()
# # # # # # # # #         if session_id in active_sessions:
# # # # # # # # #             del active_sessions[session_id]
# # # # # # # # #         db.close()

# # # # # # # # # @app.get("/api/interviews/{interview_id}/responses", response_model=List[InterviewResponseDetail])
# # # # # # # # # def get_interview_responses(interview_id: int, db: Session = Depends(get_db)):
# # # # # # # # #     return db.query(InterviewResponse).filter(InterviewResponse.interview_id == interview_id).all()

# # # # # # # # # @app.get("/api/stats")
# # # # # # # # # def get_statistics(db: Session = Depends(get_db)):
# # # # # # # # #     total = db.query(Employee).count()
# # # # # # # # #     completed = db.query(ExitInterview).filter(ExitInterview.completed == True).count()
# # # # # # # # #     return {
# # # # # # # # #         "total_resignations": total,
# # # # # # # # #         "completed_interviews": completed,
# # # # # # # # #         "pending_interviews": total - completed,
# # # # # # # # #         "completion_rate": (completed / total * 100) if total > 0 else 0
# # # # # # # # #     }

# # # # # # # # # def init_db():
# # # # # # # # #     Base.metadata.create_all(bind=engine)
# # # # # # # # #     print("✅ Database initialized!")

# # # # # # # # # if __name__ == "__main__":
# # # # # # # # #     init_db()
# # # # # # # # #     import uvicorn
# # # # # # # # #     print("\n🚀 Nova Sonic Exit Interview API v5.1")
# # # # # # # # #     print("📡 http://0.0.0.0:8000\n")
# # # # # # # # #     uvicorn.run(app, host="0.0.0.0", port=8000)


# # # # # # # # """
# # # # # # # # FIXED Nova Sonic Exit Interview Backend - PROPER DB SAVING
# # # # # # # # Now actually saves Q&A pairs to database with Bedrock cleaning
# # # # # # # # """

# # # # # # # # from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
# # # # # # # # from fastapi.middleware.cors import CORSMiddleware
# # # # # # # # from sqlalchemy import create_engine, Column, Integer, String, Boolean, Date, DateTime, Text, ForeignKey
# # # # # # # # from sqlalchemy.ext.declarative import declarative_base
# # # # # # # # from sqlalchemy.orm import sessionmaker, Session, relationship
# # # # # # # # from pydantic import BaseModel, EmailStr, field_validator
# # # # # # # # from typing import List, Optional, Dict, Any
# # # # # # # # from datetime import datetime, date
# # # # # # # # import os
# # # # # # # # from dotenv import load_dotenv
# # # # # # # # import boto3
# # # # # # # # import uuid
# # # # # # # # import json
# # # # # # # # import asyncio
# # # # # # # # import base64
# # # # # # # # import traceback
# # # # # # # # import re

# # # # # # # # from aws_sdk_bedrock_runtime.client import BedrockRuntimeClient, InvokeModelWithBidirectionalStreamOperationInput
# # # # # # # # from aws_sdk_bedrock_runtime.models import InvokeModelWithBidirectionalStreamInputChunk, BidirectionalInputPayloadPart
# # # # # # # # from aws_sdk_bedrock_runtime.config import Config
# # # # # # # # from smithy_aws_core.identity.environment import EnvironmentCredentialsResolver

# # # # # # # # load_dotenv()

# # # # # # # # # ==================== DATABASE SETUP ====================
# # # # # # # # DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

# # # # # # # # engine = create_engine(DATABASE_URL)
# # # # # # # # SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# # # # # # # # Base = declarative_base()

# # # # # # # # # ==================== DATABASE MODELS ====================
# # # # # # # # class Employee(Base):
# # # # # # # #     __tablename__ = "employees"
    
# # # # # # # #     id = Column(Integer, primary_key=True, index=True)
# # # # # # # #     name = Column(String(100), nullable=False)
# # # # # # # #     email = Column(String(100), unique=True, nullable=False)
# # # # # # # #     department = Column(String(50))
# # # # # # # #     last_working_date = Column(Date)
# # # # # # # #     status = Column(String(20), default="Resigned")
# # # # # # # #     created_at = Column(DateTime, default=datetime.utcnow)
    
# # # # # # # #     exit_interview = relationship("ExitInterview", back_populates="employee", uselist=False)

# # # # # # # # class ExitInterview(Base):
# # # # # # # #     __tablename__ = "exit_interviews"
    
# # # # # # # #     id = Column(Integer, primary_key=True, index=True)
# # # # # # # #     employee_id = Column(Integer, ForeignKey("employees.id"))
# # # # # # # #     form_token = Column(String(255), unique=True, nullable=False)
# # # # # # # #     completed = Column(Boolean, default=False)
# # # # # # # #     questions_json = Column(Text)
# # # # # # # #     created_at = Column(DateTime, default=datetime.utcnow)
    
# # # # # # # #     employee = relationship("Employee", back_populates="exit_interview")
# # # # # # # #     responses = relationship("InterviewResponse", back_populates="interview")

# # # # # # # # class InterviewResponse(Base):
# # # # # # # #     __tablename__ = "interview_responses"
    
# # # # # # # #     id = Column(Integer, primary_key=True, index=True)
# # # # # # # #     interview_id = Column(Integer, ForeignKey("exit_interviews.id"))
# # # # # # # #     question = Column(Text, nullable=False)
# # # # # # # #     answer = Column(Text, nullable=False)
# # # # # # # #     created_at = Column(DateTime, default=datetime.utcnow)
    
# # # # # # # #     interview = relationship("ExitInterview", back_populates="responses")

# # # # # # # # # ==================== PYDANTIC SCHEMAS ====================
# # # # # # # # class EmployeeCreate(BaseModel):
# # # # # # # #     name: str
# # # # # # # #     email: EmailStr
# # # # # # # #     department: str
# # # # # # # #     last_working_date: date
# # # # # # # #     questions: Optional[List[str]] = None
    
# # # # # # # #     @field_validator('name')
# # # # # # # #     def name_must_not_be_empty(cls, v):
# # # # # # # #         if not v or not v.strip():
# # # # # # # #             raise ValueError('Name cannot be empty')
# # # # # # # #         return v.strip()

# # # # # # # # class EmployeeResponse(BaseModel):
# # # # # # # #     id: int
# # # # # # # #     name: str
# # # # # # # #     email: str
# # # # # # # #     department: str
# # # # # # # #     last_working_date: date
# # # # # # # #     status: str
# # # # # # # #     created_at: datetime
    
# # # # # # # #     class Config:
# # # # # # # #         from_attributes = True

# # # # # # # # class InterviewStatusResponse(BaseModel):
# # # # # # # #     id: int
# # # # # # # #     completed: bool
# # # # # # # #     form_token: str
# # # # # # # #     created_at: datetime
    
# # # # # # # #     class Config:
# # # # # # # #         from_attributes = True

# # # # # # # # class InterviewResponseDetail(BaseModel):
# # # # # # # #     id: int
# # # # # # # #     question: str
# # # # # # # #     answer: str
# # # # # # # #     created_at: datetime
    
# # # # # # # #     class Config:
# # # # # # # #         from_attributes = True

# # # # # # # # # ==================== BEDROCK ANSWER CLEANING ====================
# # # # # # # # def clean_answer_with_bedrock(raw_answer: str, question: str) -> str:
# # # # # # # #     """Clean answer using Bedrock - removes filler, greetings, etc."""
# # # # # # # #     try:
# # # # # # # #         if not raw_answer or len(raw_answer.strip()) < 2:
# # # # # # # #             return raw_answer.strip()
        
# # # # # # # #         bedrock = boto3.client('bedrock-runtime', region_name=os.getenv("AWS_REGION", "us-east-1"))
        
# # # # # # # #         prompt = f"""Extract the meaningful answer from this speech transcription. Remove greetings, filler words, and conversational noise.

# # # # # # # # Question: {question}
# # # # # # # # Raw Answer: {raw_answer}

# # # # # # # # Return ONLY the cleaned answer, nothing else:"""

# # # # # # # #         body = json.dumps({
# # # # # # # #             "inputText": prompt,
# # # # # # # #             "textGenerationConfig": {
# # # # # # # #                 "maxTokenCount": 100,
# # # # # # # #                 "temperature": 0.1,
# # # # # # # #                 "topP": 0.9
# # # # # # # #             }
# # # # # # # #         })
        
# # # # # # # #         response = bedrock.invoke_model(
# # # # # # # #             body=body,
# # # # # # # #             modelId="amazon.titan-text-express-v1",
# # # # # # # #             accept="application/json",
# # # # # # # #             contentType="application/json"
# # # # # # # #         )
        
# # # # # # # #         response_body = json.loads(response.get('body').read())
# # # # # # # #         cleaned = response_body.get('results', [{}])[0].get('outputText', '').strip()
        
# # # # # # # #         return cleaned if cleaned else raw_answer.strip()
    
# # # # # # # #     except Exception as e:
# # # # # # # #         print(f"⚠️ Bedrock error: {e} - using raw answer")
# # # # # # # #         return raw_answer.strip()

# # # # # # # # # ==================== NOVA SONIC CLIENT ====================
# # # # # # # # class NovaInterviewClient:
# # # # # # # #     def __init__(self, employee_name: str, questions: List[str], websocket: WebSocket, db: Session, interview_id: int, region='us-east-1'):
# # # # # # # #         self.model_id = 'amazon.nova-sonic-v1:0'
# # # # # # # #         self.region = region
# # # # # # # #         self.employee_name = employee_name
# # # # # # # #         self.questions = questions
# # # # # # # #         self.websocket = websocket
# # # # # # # #         self.db = db
# # # # # # # #         self.interview_id = interview_id
# # # # # # # #         self.client = None
# # # # # # # #         self.stream = None
# # # # # # # #         self.is_active = False
        
# # # # # # # #         # UUIDs for stream
# # # # # # # #         self.prompt_name = str(uuid.uuid4())
# # # # # # # #         self.system_content_name = str(uuid.uuid4())
# # # # # # # #         self.audio_content_name = str(uuid.uuid4())
        
# # # # # # # #         # State tracking
# # # # # # # #         self.current_q_idx = 0
# # # # # # # #         self.user_answer_buffer = ""
# # # # # # # #         self.waiting_for_answer = False
# # # # # # # #         self.last_user_text = ""
# # # # # # # #         self.interview_complete = False
    
# # # # # # # #     def _initialize_client(self):
# # # # # # # #         """Initialize Bedrock client"""
# # # # # # # #         resolver = EnvironmentCredentialsResolver()
# # # # # # # #         config = Config(
# # # # # # # #             endpoint_uri=f"https://bedrock-runtime.{self.region}.amazonaws.com",
# # # # # # # #             region=self.region,
# # # # # # # #             aws_credentials_identity_resolver=resolver
# # # # # # # #         )
# # # # # # # #         self.client = BedrockRuntimeClient(config=config)
# # # # # # # #         print("✅ Bedrock client initialized")
    
# # # # # # # #     async def send_event(self, event_json):
# # # # # # # #         """Send event to stream"""
# # # # # # # #         event = InvokeModelWithBidirectionalStreamInputChunk(
# # # # # # # #             value=BidirectionalInputPayloadPart(bytes_=event_json.encode('utf-8'))
# # # # # # # #         )
# # # # # # # #         await self.stream.input_stream.send(event)
    
# # # # # # # #     async def start_session(self):
# # # # # # # #         """Start Nova Sonic session"""
# # # # # # # #         if not self.client:
# # # # # # # #             self._initialize_client()
        
# # # # # # # #         try:
# # # # # # # #             print("📡 Starting bidirectional stream...")
# # # # # # # #             self.stream = await self.client.invoke_model_with_bidirectional_stream(
# # # # # # # #                 InvokeModelWithBidirectionalStreamOperationInput(model_id=self.model_id)
# # # # # # # #             )
# # # # # # # #             self.is_active = True
# # # # # # # #             print("✅ Stream started")
            
# # # # # # # #             # Session start
# # # # # # # #             await self.send_event(json.dumps({
# # # # # # # #                 "event": {
# # # # # # # #                     "sessionStart": {
# # # # # # # #                         "inferenceConfiguration": {
# # # # # # # #                             "maxTokens": 1024,
# # # # # # # #                             "topP": 0.9,
# # # # # # # #                             "temperature": 0.7
# # # # # # # #                         }
# # # # # # # #                     }
# # # # # # # #                 }
# # # # # # # #             }))
            
# # # # # # # #             # Prompt start
# # # # # # # #             await self.send_event(json.dumps({
# # # # # # # #                 "event": {
# # # # # # # #                     "promptStart": {
# # # # # # # #                         "promptName": self.prompt_name,
# # # # # # # #                         "textOutputConfiguration": {
# # # # # # # #                             "mediaType": "text/plain"
# # # # # # # #                         },
# # # # # # # #                         "audioOutputConfiguration": {
# # # # # # # #                             "mediaType": "audio/lpcm",
# # # # # # # #                             "sampleRateHertz": 24000,
# # # # # # # #                             "sampleSizeBits": 16,
# # # # # # # #                             "channelCount": 1,
# # # # # # # #                             "voiceId": "matthew",
# # # # # # # #                             "encoding": "base64",
# # # # # # # #                             "audioType": "SPEECH"
# # # # # # # #                         }
# # # # # # # #                     }
# # # # # # # #                 }
# # # # # # # #             }))
            
# # # # # # # #             # System prompt
# # # # # # # #             await self.send_event(json.dumps({
# # # # # # # #                 "event": {
# # # # # # # #                     "contentStart": {
# # # # # # # #                         "promptName": self.prompt_name,
# # # # # # # #                         "contentName": self.system_content_name,
# # # # # # # #                         "type": "TEXT",
# # # # # # # #                         "interactive": False,
# # # # # # # #                         "role": "SYSTEM",
# # # # # # # #                         "textInputConfiguration": {
# # # # # # # #                             "mediaType": "text/plain"
# # # # # # # #                         }
# # # # # # # #                     }
# # # # # # # #                 }
# # # # # # # #             }))
            
# # # # # # # #             questions_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(self.questions)])
            
# # # # # # # #             system_text = f"""You are Nova, conducting an EXIT INTERVIEW with {self.employee_name}.

# # # # # # # # CRITICAL:
# # # # # # # # 1. Greet warmly ONCE at the start
# # # # # # # # 2. Ask these {len(self.questions)} questions IN ORDER, one at a time
# # # # # # # # 3. Wait for full answer before asking next question
# # # # # # # # 4. After ALL questions, say EXACTLY: "Thank you for completing the exit interview. Goodbye."

# # # # # # # # Questions to ask (in order):
# # # # # # # # {questions_text}

# # # # # # # # Be conversational. Wait for answers."""

# # # # # # # #             await self.send_event(json.dumps({
# # # # # # # #                 "event": {
# # # # # # # #                     "textInput": {
# # # # # # # #                         "promptName": self.prompt_name,
# # # # # # # #                         "contentName": self.system_content_name,
# # # # # # # #                         "content": system_text
# # # # # # # #                     }
# # # # # # # #                 }
# # # # # # # #             }))
            
# # # # # # # #             await self.send_event(json.dumps({
# # # # # # # #                 "event": {
# # # # # # # #                     "contentEnd": {
# # # # # # # #                         "promptName": self.prompt_name,
# # # # # # # #                         "contentName": self.system_content_name
# # # # # # # #                     }
# # # # # # # #                 }
# # # # # # # #             }))
            
# # # # # # # #             print("✅ System prompt sent")
# # # # # # # #             asyncio.create_task(self._process_responses())
        
# # # # # # # #         except Exception as e:
# # # # # # # #             print(f"❌ Error starting session: {e}")
# # # # # # # #             traceback.print_exc()
# # # # # # # #             raise
    
# # # # # # # #     async def start_audio_input(self):
# # # # # # # #         """Start audio input"""
# # # # # # # #         await self.send_event(json.dumps({
# # # # # # # #             "event": {
# # # # # # # #                 "contentStart": {
# # # # # # # #                     "promptName": self.prompt_name,
# # # # # # # #                     "contentName": self.audio_content_name,
# # # # # # # #                     "type": "AUDIO",
# # # # # # # #                     "interactive": True,
# # # # # # # #                     "role": "USER",
# # # # # # # #                     "audioInputConfiguration": {
# # # # # # # #                         "mediaType": "audio/lpcm",
# # # # # # # #                         "sampleRateHertz": 16000,
# # # # # # # #                         "sampleSizeBits": 16,
# # # # # # # #                         "channelCount": 1,
# # # # # # # #                         "audioType": "SPEECH",
# # # # # # # #                         "encoding": "base64"
# # # # # # # #                     }
# # # # # # # #                 }
# # # # # # # #             }
# # # # # # # #         }))
# # # # # # # #         print("✅ Audio input started")
    
# # # # # # # #     async def send_audio_chunk(self, audio_bytes):
# # # # # # # #         """Send audio chunk"""
# # # # # # # #         if not self.is_active:
# # # # # # # #             return
        
# # # # # # # #         blob = base64.b64encode(audio_bytes).decode('utf-8')
# # # # # # # #         try:
# # # # # # # #             await self.send_event(json.dumps({
# # # # # # # #                 "event": {
# # # # # # # #                     "audioInput": {
# # # # # # # #                         "promptName": self.prompt_name,
# # # # # # # #                         "contentName": self.audio_content_name,
# # # # # # # #                         "content": blob
# # # # # # # #                     }
# # # # # # # #                 }
# # # # # # # #             }))
# # # # # # # #         except Exception as e:
# # # # # # # #             print(f"⚠️ Error sending audio: {e}")
    
# # # # # # # #     async def _save_response_to_db(self, question: str, raw_answer: str):
# # # # # # # #         """Save response to database with Bedrock cleaning"""
# # # # # # # #         try:
# # # # # # # #             print(f"\n🔄 Processing Q{self.current_q_idx + 1}...")
# # # # # # # #             print(f"   Raw: {raw_answer[:80]}...")
            
# # # # # # # #             # Clean with Bedrock
# # # # # # # #             cleaned_answer = clean_answer_with_bedrock(raw_answer, question)
            
# # # # # # # #             print(f"   Cleaned: {cleaned_answer[:80]}...")
            
# # # # # # # #             # Save to DB
# # # # # # # #             db_response = InterviewResponse(
# # # # # # # #                 interview_id=self.interview_id,
# # # # # # # #                 question=question,
# # # # # # # #                 answer=cleaned_answer
# # # # # # # #             )
# # # # # # # #             self.db.add(db_response)
# # # # # # # #             self.db.commit()
            
# # # # # # # #             print(f"✅ SAVED Q{self.current_q_idx + 1} to database")
            
# # # # # # # #             # Notify frontend
# # # # # # # #             await self.websocket.send_json({
# # # # # # # #                 'type': 'response_saved',
# # # # # # # #                 'q_index': self.current_q_idx,
# # # # # # # #                 'question': question,
# # # # # # # #                 'answer': cleaned_answer
# # # # # # # #             })
            
# # # # # # # #             self.current_q_idx += 1
# # # # # # # #             return True
        
# # # # # # # #         except Exception as e:
# # # # # # # #             print(f"❌ Error saving to DB: {e}")
# # # # # # # #             traceback.print_exc()
# # # # # # # #             return False
    
# # # # # # # #     async def _process_responses(self):
# # # # # # # #         """Process responses from Nova - SAVE TO DB"""
# # # # # # # #         try:
# # # # # # # #             while self.is_active:
# # # # # # # #                 try:
# # # # # # # #                     output = await self.stream.await_output()
# # # # # # # #                     result = await output[1].receive()
                    
# # # # # # # #                     if result.value and result.value.bytes_:
# # # # # # # #                         response_data = result.value.bytes_.decode('utf-8')
# # # # # # # #                         json_data = json.loads(response_data)
                        
# # # # # # # #                         if 'event' not in json_data:
# # # # # # # #                             continue
                        
# # # # # # # #                         event = json_data['event']
                        
# # # # # # # #                         # Text output
# # # # # # # #                         if 'textOutput' in event:
# # # # # # # #                             text = event['textOutput']['content']
# # # # # # # #                             role = event['textOutput'].get('role', 'ASSISTANT')
                            
# # # # # # # #                             if role == "ASSISTANT":
# # # # # # # #                                 print(f"🤖 Nova: {text}")
# # # # # # # #                                 await self.websocket.send_json({
# # # # # # # #                                     'type': 'text',
# # # # # # # #                                     'content': text,
# # # # # # # #                                     'role': 'ASSISTANT'
# # # # # # # #                                 })
                                
# # # # # # # #                                 # Check if asking question
# # # # # # # #                                 if '?' in text:
# # # # # # # #                                     self.waiting_for_answer = True
# # # # # # # #                                     print(f"❓ Waiting for answer to Q{self.current_q_idx + 1}")
                                
# # # # # # # #                                 # Check if ending
# # # # # # # #                                 if "thank you for completing" in text.lower() and "goodbye" in text.lower():
# # # # # # # #                                     print("✅ Nova ending interview")
# # # # # # # #                                     # Save any remaining answer
# # # # # # # #                                     if self.waiting_for_answer and self.user_answer_buffer.strip():
# # # # # # # #                                         if self.current_q_idx < len(self.questions):
# # # # # # # #                                             question = self.questions[self.current_q_idx]
# # # # # # # #                                             raw_answer = self.user_answer_buffer.strip()
# # # # # # # #                                             await self._save_response_to_db(question, raw_answer)
# # # # # # # #                                     await self._finalize_interview()
# # # # # # # #                                     return
                                
# # # # # # # #                                 # Check if all questions answered
# # # # # # # #                                 if self.current_q_idx >= len(self.questions):
# # # # # # # #                                     print("✅ All questions answered - closing interview")
# # # # # # # #                                     await self._finalize_interview()
# # # # # # # #                                     return
                            
# # # # # # # #                             elif role == "USER" and self.waiting_for_answer:
# # # # # # # #                                 # Accumulate user answer
# # # # # # # #                                 if text != self.last_user_text and text.strip():
# # # # # # # #                                     print(f"👤 User: {text}")
# # # # # # # #                                     self.last_user_text = text
                                    
# # # # # # # #                                     if self.user_answer_buffer:
# # # # # # # #                                         self.user_answer_buffer += " "
# # # # # # # #                                     self.user_answer_buffer += text
                                    
# # # # # # # #                                     await self.websocket.send_json({
# # # # # # # #                                         'type': 'text',
# # # # # # # #                                         'content': text,
# # # # # # # #                                         'role': 'USER'
# # # # # # # #                                     })
                        
# # # # # # # #                         # Audio output
# # # # # # # #                         elif 'audioOutput' in event:
# # # # # # # #                             audio_content = event['audioOutput']['content']
# # # # # # # #                             await self.websocket.send_json({
# # # # # # # #                                 'type': 'audio',
# # # # # # # #                                 'data': audio_content
# # # # # # # #                             })
                        
# # # # # # # #                         # CRITICAL: Save answer when Nova finishes speaking
# # # # # # # #                         elif 'contentEnd' in event:
# # # # # # # #                             if self.waiting_for_answer and self.user_answer_buffer.strip():
# # # # # # # #                                 if self.current_q_idx < len(self.questions):
# # # # # # # #                                     question = self.questions[self.current_q_idx]
# # # # # # # #                                     raw_answer = self.user_answer_buffer.strip()
                                    
# # # # # # # #                                     # SAVE TO DATABASE
# # # # # # # #                                     await self._save_response_to_db(question, raw_answer)
                                    
# # # # # # # #                                     self.user_answer_buffer = ""
# # # # # # # #                                     self.waiting_for_answer = False
                                    
# # # # # # # #                                     # Check if all questions are now answered
# # # # # # # #                                     if self.current_q_idx >= len(self.questions):
# # # # # # # #                                         print(f"✅ All {len(self.questions)} questions answered!")
# # # # # # # #                                         await self._finalize_interview()
# # # # # # # #                                         return
                        
# # # # # # # #                         # Completion
# # # # # # # #                         elif 'completionEnd' in event:
# # # # # # # #                             print("✅ Stream ended")
# # # # # # # #                             await self._finalize_interview()
# # # # # # # #                             return
                
# # # # # # # #                 except asyncio.TimeoutError:
# # # # # # # #                     continue
# # # # # # # #                 except Exception as e:
# # # # # # # #                     print(f"⚠️ Processing error: {e}")
# # # # # # # #                     continue
        
# # # # # # # #         except Exception as e:
# # # # # # # #             print(f"❌ Fatal error: {e}")
# # # # # # # #             self.is_active = False
    
# # # # # # # #     async def _finalize_interview(self):
# # # # # # # #         """Finalize and close interview"""
# # # # # # # #         print(f"\n{'='*60}")
# # # # # # # #         print(f"✅ Interview Complete: {self.current_q_idx}/{len(self.questions)}")
# # # # # # # #         print(f"{'='*60}\n")
        
# # # # # # # #         try:
# # # # # # # #             # Mark as completed
# # # # # # # #             interview = self.db.query(ExitInterview).filter(ExitInterview.id == self.interview_id).first()
# # # # # # # #             if interview:
# # # # # # # #                 interview.completed = True
# # # # # # # #                 interview.employee.status = "Completed"
# # # # # # # #                 self.db.commit()
# # # # # # # #                 print("✅ Interview marked as completed in DB")
# # # # # # # #         except Exception as e:
# # # # # # # #             print(f"⚠️ Error updating interview: {e}")
        
# # # # # # # #         await self.websocket.send_json({
# # # # # # # #             'type': 'interview_complete',
# # # # # # # #             'questions_answered': self.current_q_idx,
# # # # # # # #             'total_questions': len(self.questions)
# # # # # # # #         })
        
# # # # # # # #         self.is_active = False
    
# # # # # # # #     async def end_session(self):
# # # # # # # #         """End session"""
# # # # # # # #         if not self.is_active:
# # # # # # # #             return
        
# # # # # # # #         try:
# # # # # # # #             await self.send_event(json.dumps({
# # # # # # # #                 "event": {
# # # # # # # #                     "contentEnd": {
# # # # # # # #                         "promptName": self.prompt_name,
# # # # # # # #                         "contentName": self.audio_content_name
# # # # # # # #                     }
# # # # # # # #                 }
# # # # # # # #             }))
            
# # # # # # # #             await self.send_event(json.dumps({
# # # # # # # #                 "event": {
# # # # # # # #                     "promptEnd": {
# # # # # # # #                         "promptName": self.prompt_name
# # # # # # # #                     }
# # # # # # # #                 }
# # # # # # # #             }))
            
# # # # # # # #             await self.send_event(json.dumps({
# # # # # # # #                 "event": {
# # # # # # # #                     "sessionEnd": {}
# # # # # # # #                 }
# # # # # # # #             }))
            
# # # # # # # #             await self.stream.input_stream.close()
# # # # # # # #             self.is_active = False
# # # # # # # #             print("✅ Session ended")
        
# # # # # # # #         except Exception as e:
# # # # # # # #             print(f"⚠️ Error ending: {e}")
# # # # # # # #             self.is_active = False

# # # # # # # # # ==================== AWS SES ====================
# # # # # # # # ses_client = boto3.client('ses', region_name=os.getenv("AWS_REGION", "us-east-1"))

# # # # # # # # def send_exit_interview_email(employee_email: str, employee_name: str, form_link: str) -> bool:
# # # # # # # #     SENDER = os.getenv("SES_SENDER_EMAIL")
# # # # # # # #     SUBJECT = "🎙️ Voice Exit Interview with Nova"
# # # # # # # #     BODY_HTML = f"""
# # # # # # # #     <html><body>
# # # # # # # #         <h1>Hello {employee_name}!</h1>
# # # # # # # #         <p>Have a voice conversation with Nova for your exit interview.</p>
# # # # # # # #         <p><a href="{form_link}">Start Voice Interview</a></p>
# # # # # # # #     </body></html>
# # # # # # # #     """
# # # # # # # #     try:
# # # # # # # #         ses_client.send_email(
# # # # # # # #             Source=SENDER,
# # # # # # # #             Destination={'ToAddresses': [employee_email]},
# # # # # # # #             Message={'Subject': {'Data': SUBJECT}, 'Body': {'Html': {'Data': BODY_HTML}}}
# # # # # # # #         )
# # # # # # # #         print(f"✅ Email sent to {employee_name}")
# # # # # # # #         return True
# # # # # # # #     except Exception as e:
# # # # # # # #         print(f"❌ Email error: {e}")
# # # # # # # #         return False

# # # # # # # # def generate_unique_token() -> str:
# # # # # # # #     return str(uuid.uuid4())

# # # # # # # # def create_form_link(token: str) -> str:
# # # # # # # #     return f"{os.getenv('APP_URL', 'http://localhost:8501')}/exit_interview?token={token}"

# # # # # # # # # ==================== FASTAPI APP ====================
# # # # # # # # app = FastAPI(title="Nova Sonic Exit Interview API", version="5.1.0")

# # # # # # # # app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# # # # # # # # def get_db():
# # # # # # # #     db = SessionLocal()
# # # # # # # #     try:
# # # # # # # #         yield db
# # # # # # # #     finally:
# # # # # # # #         db.close()

# # # # # # # # active_sessions: Dict[str, NovaInterviewClient] = {}

# # # # # # # # # ==================== API ENDPOINTS ====================

# # # # # # # # @app.get("/")
# # # # # # # # def root():
# # # # # # # #     return {"message": "Nova Sonic Exit Interview API", "version": "5.1.0", "status": "running"}

# # # # # # # # @app.post("/api/employees", response_model=EmployeeResponse, status_code=201)
# # # # # # # # def create_employee(employee: EmployeeCreate, db: Session = Depends(get_db)):
# # # # # # # #     try:
# # # # # # # #         existing = db.query(Employee).filter(Employee.email == employee.email).first()
# # # # # # # #         if existing:
# # # # # # # #             raise HTTPException(status_code=400, detail="Employee already exists")
        
# # # # # # # #         db_employee = Employee(
# # # # # # # #             name=employee.name,
# # # # # # # #             email=employee.email,
# # # # # # # #             department=employee.department,
# # # # # # # #             last_working_date=employee.last_working_date,
# # # # # # # #             status="Resigned"
# # # # # # # #         )
# # # # # # # #         db.add(db_employee)
# # # # # # # #         db.commit()
# # # # # # # #         db.refresh(db_employee)
        
# # # # # # # #         token = generate_unique_token()
# # # # # # # #         form_link = create_form_link(token)
        
# # # # # # # #         questions_json = json.dumps(employee.questions) if employee.questions else json.dumps([
# # # # # # # #             "What was your primary reason for leaving?",
# # # # # # # #             "How would you rate your overall experience with the company on a scale of 1 to 5?",
# # # # # # # #             "How was your relationship with your manager?",
# # # # # # # #             "Did you feel valued and recognized in your role?",
# # # # # # # #             "Would you recommend our company to others? Why or why not?"
# # # # # # # #         ])
        
# # # # # # # #         db_interview = ExitInterview(
# # # # # # # #             employee_id=db_employee.id,
# # # # # # # #             form_token=token,
# # # # # # # #             completed=False,
# # # # # # # #             questions_json=questions_json
# # # # # # # #         )
# # # # # # # #         db.add(db_interview)
# # # # # # # #         db.commit()
        
# # # # # # # #         send_exit_interview_email(db_employee.email, db_employee.name, form_link)
        
# # # # # # # #         return db_employee
# # # # # # # #     except HTTPException:
# # # # # # # #         raise
# # # # # # # #     except Exception as e:
# # # # # # # #         db.rollback()
# # # # # # # #         raise HTTPException(status_code=500, detail=str(e))

# # # # # # # # @app.get("/api/employees", response_model=List[EmployeeResponse])
# # # # # # # # def list_employees(db: Session = Depends(get_db)):
# # # # # # # #     return db.query(Employee).all()

# # # # # # # # @app.get("/api/interviews/token/{token}")
# # # # # # # # def get_interview_by_token(token: str, db: Session = Depends(get_db)):
# # # # # # # #     interview = db.query(ExitInterview).filter(ExitInterview.form_token == token).first()
# # # # # # # #     if not interview:
# # # # # # # #         raise HTTPException(status_code=404, detail="Invalid token")
# # # # # # # #     if interview.completed:
# # # # # # # #         raise HTTPException(status_code=400, detail="Interview already completed")
    
# # # # # # # #     questions = json.loads(interview.questions_json)
# # # # # # # #     return {
# # # # # # # #         "interview_id": interview.id,
# # # # # # # #         "employee_name": interview.employee.name,
# # # # # # # #         "employee_department": interview.employee.department,
# # # # # # # #         "questions": questions,
# # # # # # # #         "total_questions": len(questions),
# # # # # # # #         "completed": interview.completed
# # # # # # # #     }

# # # # # # # # @app.websocket("/ws/interview/{token}")
# # # # # # # # async def websocket_interview(websocket: WebSocket, token: str):
# # # # # # # #     await websocket.accept()
    
# # # # # # # #     db = SessionLocal()
# # # # # # # #     session_id = str(uuid.uuid4())
# # # # # # # #     nova_client = None
    
# # # # # # # #     try:
# # # # # # # #         interview = db.query(ExitInterview).filter(ExitInterview.form_token == token).first()
# # # # # # # #         if not interview:
# # # # # # # #             await websocket.send_json({"type": "error", "message": "Invalid token"})
# # # # # # # #             return
        
# # # # # # # #         questions = json.loads(interview.questions_json)
# # # # # # # #         employee_name = interview.employee.name
        
# # # # # # # #         print(f"\n{'='*60}")
# # # # # # # #         print(f"🎙️ Interview for {employee_name}")
# # # # # # # #         print(f"📋 {len(questions)} questions")
# # # # # # # #         print(f"{'='*60}\n")
        
# # # # # # # #         await websocket.send_json({
# # # # # # # #             "type": "session_start",
# # # # # # # #             "session_id": session_id,
# # # # # # # #             "employee_name": employee_name,
# # # # # # # #             "total_questions": len(questions)
# # # # # # # #         })
        
# # # # # # # #         # PASS DB AND INTERVIEW_ID TO NOVA CLIENT
# # # # # # # #         nova_client = NovaInterviewClient(
# # # # # # # #             employee_name,
# # # # # # # #             questions,
# # # # # # # #             websocket,
# # # # # # # #             db,  # ← DB session
# # # # # # # #             interview.id,  # ← Interview ID
# # # # # # # #             os.getenv("AWS_REGION", "us-east-1")
# # # # # # # #         )
# # # # # # # #         await nova_client.start_session()
        
# # # # # # # #         await asyncio.sleep(2)
# # # # # # # #         await nova_client.start_audio_input()
        
# # # # # # # #         active_sessions[session_id] = nova_client
        
# # # # # # # #         timeout_seconds = 180
# # # # # # # #         start_time = datetime.utcnow()
        
# # # # # # # #         while nova_client.is_active:
# # # # # # # #             try:
# # # # # # # #                 message = await asyncio.wait_for(websocket.receive_json(), timeout=0.5)
# # # # # # # #                 start_time = datetime.utcnow()
                
# # # # # # # #                 if message['type'] == 'audio_chunk':
# # # # # # # #                     audio_data = base64.b64decode(message['data'])
# # # # # # # #                     await nova_client.send_audio_chunk(audio_data)
                
# # # # # # # #                 elif message['type'] == 'close':
# # # # # # # #                     break
            
# # # # # # # #             except asyncio.TimeoutError:
# # # # # # # #                 elapsed = (datetime.utcnow() - start_time).total_seconds()
# # # # # # # #                 if elapsed > timeout_seconds:
# # # # # # # #                     print(f"⚠️ Timeout")
# # # # # # # #                     break
# # # # # # # #                 continue
# # # # # # # #             except WebSocketDisconnect:
# # # # # # # #                 print("⚠️ Disconnected")
# # # # # # # #                 break
# # # # # # # #             except Exception as e:
# # # # # # # #                 print(f"⚠️ Error: {e}")
# # # # # # # #                 break
    
# # # # # # # #     except Exception as e:
# # # # # # # #         print(f"❌ Error: {e}")
# # # # # # # #         traceback.print_exc()
# # # # # # # #         try:
# # # # # # # #             await websocket.send_json({"type": "error", "message": str(e)})
# # # # # # # #         except:
# # # # # # # #             pass
# # # # # # # #     finally:
# # # # # # # #         if nova_client:
# # # # # # # #             await nova_client.end_session()
# # # # # # # #         if session_id in active_sessions:
# # # # # # # #             del active_sessions[session_id]
# # # # # # # #         db.close()

# # # # # # # # @app.get("/api/interviews/{interview_id}/responses", response_model=List[InterviewResponseDetail])
# # # # # # # # def get_interview_responses(interview_id: int, db: Session = Depends(get_db)):
# # # # # # # #     return db.query(InterviewResponse).filter(InterviewResponse.interview_id == interview_id).all()

# # # # # # # # @app.get("/api/stats")
# # # # # # # # def get_statistics(db: Session = Depends(get_db)):
# # # # # # # #     total = db.query(Employee).count()
# # # # # # # #     completed = db.query(ExitInterview).filter(ExitInterview.completed == True).count()
# # # # # # # #     return {
# # # # # # # #         "total_resignations": total,
# # # # # # # #         "completed_interviews": completed,
# # # # # # # #         "pending_interviews": total - completed,
# # # # # # # #         "completion_rate": (completed / total * 100) if total > 0 else 0
# # # # # # # #     }

# # # # # # # # def init_db():
# # # # # # # #     Base.metadata.create_all(bind=engine)
# # # # # # # #     print("✅ Database initialized!")

# # # # # # # # if __name__ == "__main__":
# # # # # # # #     init_db()
# # # # # # # #     import uvicorn
# # # # # # # #     print("\n🚀 Nova Sonic Exit Interview API v5.1")
# # # # # # # #     print("📡 http://0.0.0.0:8000\n")
# # # # # # # #     uvicorn.run(app, host="0.0.0.0", port=8000)





# # # # # # # """
# # # # # # # FIXED Nova Sonic Exit Interview Backend - PROPERLY SAVES RESPONSES
# # # # # # # Comprehensive fix for Q&A capture and database storage
# # # # # # # """

# # # # # # # from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
# # # # # # # from fastapi.middleware.cors import CORSMiddleware
# # # # # # # from sqlalchemy import create_engine, Column, Integer, String, Boolean, Date, DateTime, Text, ForeignKey
# # # # # # # from sqlalchemy.ext.declarative import declarative_base
# # # # # # # from sqlalchemy.orm import sessionmaker, Session, relationship
# # # # # # # from pydantic import BaseModel, EmailStr, field_validator
# # # # # # # from typing import List, Optional, Dict, Any
# # # # # # # from datetime import datetime, date
# # # # # # # import os
# # # # # # # from dotenv import load_dotenv
# # # # # # # import boto3
# # # # # # # import uuid
# # # # # # # import json
# # # # # # # import asyncio
# # # # # # # import base64
# # # # # # # import traceback

# # # # # # # from aws_sdk_bedrock_runtime.client import BedrockRuntimeClient, InvokeModelWithBidirectionalStreamOperationInput
# # # # # # # from aws_sdk_bedrock_runtime.models import InvokeModelWithBidirectionalStreamInputChunk, BidirectionalInputPayloadPart
# # # # # # # from aws_sdk_bedrock_runtime.config import Config
# # # # # # # from smithy_aws_core.identity.environment import EnvironmentCredentialsResolver

# # # # # # # load_dotenv()

# # # # # # # # ==================== DATABASE SETUP ====================
# # # # # # # DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

# # # # # # # engine = create_engine(DATABASE_URL)
# # # # # # # SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# # # # # # # Base = declarative_base()

# # # # # # # # ==================== DATABASE MODELS ====================
# # # # # # # class Employee(Base):
# # # # # # #     __tablename__ = "employees"
    
# # # # # # #     id = Column(Integer, primary_key=True, index=True)
# # # # # # #     name = Column(String(100), nullable=False)
# # # # # # #     email = Column(String(100), unique=True, nullable=False)
# # # # # # #     department = Column(String(50))
# # # # # # #     last_working_date = Column(Date)
# # # # # # #     status = Column(String(20), default="Resigned")
# # # # # # #     created_at = Column(DateTime, default=datetime.utcnow)
    
# # # # # # #     exit_interview = relationship("ExitInterview", back_populates="employee", uselist=False)

# # # # # # # class ExitInterview(Base):
# # # # # # #     __tablename__ = "exit_interviews"
    
# # # # # # #     id = Column(Integer, primary_key=True, index=True)
# # # # # # #     employee_id = Column(Integer, ForeignKey("employees.id"))
# # # # # # #     form_token = Column(String(255), unique=True, nullable=False)
# # # # # # #     completed = Column(Boolean, default=False)
# # # # # # #     questions_json = Column(Text)
# # # # # # #     created_at = Column(DateTime, default=datetime.utcnow)
    
# # # # # # #     employee = relationship("Employee", back_populates="exit_interview")
# # # # # # #     responses = relationship("InterviewResponse", back_populates="interview")

# # # # # # # class InterviewResponse(Base):
# # # # # # #     __tablename__ = "interview_responses"
    
# # # # # # #     id = Column(Integer, primary_key=True, index=True)
# # # # # # #     interview_id = Column(Integer, ForeignKey("exit_interviews.id"))
# # # # # # #     question = Column(Text, nullable=False)
# # # # # # #     answer = Column(Text, nullable=False)
# # # # # # #     created_at = Column(DateTime, default=datetime.utcnow)
    
# # # # # # #     interview = relationship("ExitInterview", back_populates="responses")

# # # # # # # # ==================== PYDANTIC SCHEMAS ====================
# # # # # # # class EmployeeCreate(BaseModel):
# # # # # # #     name: str
# # # # # # #     email: EmailStr
# # # # # # #     department: str
# # # # # # #     last_working_date: date
# # # # # # #     questions: Optional[List[str]] = None
    
# # # # # # #     @field_validator('name')
# # # # # # #     def name_must_not_be_empty(cls, v):
# # # # # # #         if not v or not v.strip():
# # # # # # #             raise ValueError('Name cannot be empty')
# # # # # # #         return v.strip()

# # # # # # # class EmployeeResponse(BaseModel):
# # # # # # #     id: int
# # # # # # #     name: str
# # # # # # #     email: str
# # # # # # #     department: str
# # # # # # #     last_working_date: date
# # # # # # #     status: str
# # # # # # #     created_at: datetime
    
# # # # # # #     class Config:
# # # # # # #         from_attributes = True

# # # # # # # class InterviewResponseDetail(BaseModel):
# # # # # # #     id: int
# # # # # # #     question: str
# # # # # # #     answer: str
# # # # # # #     created_at: datetime
    
# # # # # # #     class Config:
# # # # # # #         from_attributes = True

# # # # # # # # ==================== BEDROCK ANSWER CLEANING ====================
# # # # # # # def clean_answer_with_bedrock(raw_answer: str, question: str) -> str:
# # # # # # #     """Clean answer using Bedrock - removes filler, greetings, etc."""
# # # # # # #     try:
# # # # # # #         if not raw_answer or len(raw_answer.strip()) < 2:
# # # # # # #             return raw_answer.strip()
        
# # # # # # #         bedrock = boto3.client('bedrock-runtime', region_name=os.getenv("AWS_REGION", "us-east-1"))
        
# # # # # # #         prompt = f"""Extract the meaningful answer from this speech transcription. Remove greetings, filler words, and conversational noise.

# # # # # # # Question: {question}
# # # # # # # Raw Answer: {raw_answer}

# # # # # # # Return ONLY the cleaned answer, nothing else:"""

# # # # # # #         body = json.dumps({
# # # # # # #             "inputText": prompt,
# # # # # # #             "textGenerationConfig": {
# # # # # # #                 "maxTokenCount": 100,
# # # # # # #                 "temperature": 0.1,
# # # # # # #                 "topP": 0.9
# # # # # # #             }
# # # # # # #         })
        
# # # # # # #         response = bedrock.invoke_model(
# # # # # # #             body=body,
# # # # # # #             modelId="amazon.titan-text-express-v1",
# # # # # # #             accept="application/json",
# # # # # # #             contentType="application/json"
# # # # # # #         )
        
# # # # # # #         response_body = json.loads(response.get('body').read())
# # # # # # #         cleaned = response_body.get('results', [{}])[0].get('outputText', '').strip()
        
# # # # # # #         return cleaned if cleaned else raw_answer.strip()
    
# # # # # # #     except Exception as e:
# # # # # # #         print(f"⚠️ Bedrock error: {e} - using raw answer")
# # # # # # #         return raw_answer.strip()

# # # # # # # # ==================== NOVA SONIC CLIENT ====================
# # # # # # # class NovaInterviewClient:
# # # # # # #     def __init__(self, employee_name: str, questions: List[str], websocket: WebSocket, db: Session, interview_id: int, region='us-east-1'):
# # # # # # #         self.model_id = 'amazon.nova-sonic-v1:0'
# # # # # # #         self.region = region
# # # # # # #         self.employee_name = employee_name
# # # # # # #         self.questions = questions
# # # # # # #         self.websocket = websocket
# # # # # # #         self.db = db
# # # # # # #         self.interview_id = interview_id
# # # # # # #         self.client = None
# # # # # # #         self.stream = None
# # # # # # #         self.is_active = False
        
# # # # # # #         self.prompt_name = str(uuid.uuid4())
# # # # # # #         self.system_content_name = str(uuid.uuid4())
# # # # # # #         self.audio_content_name = str(uuid.uuid4())
        
# # # # # # #         # State tracking - CRITICAL
# # # # # # #         self.current_q_idx = 0
# # # # # # #         self.user_answer_buffer = ""
# # # # # # #         self.waiting_for_answer = False
# # # # # # #         self.last_user_text = ""
# # # # # # #         self.saved_q_indices = set()  # Track which questions we've saved
    
# # # # # # #     def _initialize_client(self):
# # # # # # #         """Initialize Bedrock client"""
# # # # # # #         resolver = EnvironmentCredentialsResolver()
# # # # # # #         config = Config(
# # # # # # #             endpoint_uri=f"https://bedrock-runtime.{self.region}.amazonaws.com",
# # # # # # #             region=self.region,
# # # # # # #             aws_credentials_identity_resolver=resolver
# # # # # # #         )
# # # # # # #         self.client = BedrockRuntimeClient(config=config)
# # # # # # #         print("✅ Bedrock client initialized")
    
# # # # # # #     async def send_event(self, event_json):
# # # # # # #         """Send event to stream"""
# # # # # # #         event = InvokeModelWithBidirectionalStreamInputChunk(
# # # # # # #             value=BidirectionalInputPayloadPart(bytes_=event_json.encode('utf-8'))
# # # # # # #         )
# # # # # # #         await self.stream.input_stream.send(event)
    
# # # # # # #     async def start_session(self):
# # # # # # #         """Start Nova Sonic session"""
# # # # # # #         if not self.client:
# # # # # # #             self._initialize_client()
        
# # # # # # #         try:
# # # # # # #             print("📡 Starting bidirectional stream...")
# # # # # # #             self.stream = await self.client.invoke_model_with_bidirectional_stream(
# # # # # # #                 InvokeModelWithBidirectionalStreamOperationInput(model_id=self.model_id)
# # # # # # #             )
# # # # # # #             self.is_active = True
# # # # # # #             print("✅ Stream started")
            
# # # # # # #             await self.send_event(json.dumps({
# # # # # # #                 "event": {
# # # # # # #                     "sessionStart": {
# # # # # # #                         "inferenceConfiguration": {
# # # # # # #                             "maxTokens": 1024,
# # # # # # #                             "topP": 0.9,
# # # # # # #                             "temperature": 0.7
# # # # # # #                         }
# # # # # # #                     }
# # # # # # #                 }
# # # # # # #             }))
            
# # # # # # #             await self.send_event(json.dumps({
# # # # # # #                 "event": {
# # # # # # #                     "promptStart": {
# # # # # # #                         "promptName": self.prompt_name,
# # # # # # #                         "textOutputConfiguration": {
# # # # # # #                             "mediaType": "text/plain"
# # # # # # #                         },
# # # # # # #                         "audioOutputConfiguration": {
# # # # # # #                             "mediaType": "audio/lpcm",
# # # # # # #                             "sampleRateHertz": 24000,
# # # # # # #                             "sampleSizeBits": 16,
# # # # # # #                             "channelCount": 1,
# # # # # # #                             "voiceId": "matthew",
# # # # # # #                             "encoding": "base64",
# # # # # # #                             "audioType": "SPEECH"
# # # # # # #                         }
# # # # # # #                     }
# # # # # # #                 }
# # # # # # #             }))
            
# # # # # # #             await self.send_event(json.dumps({
# # # # # # #                 "event": {
# # # # # # #                     "contentStart": {
# # # # # # #                         "promptName": self.prompt_name,
# # # # # # #                         "contentName": self.system_content_name,
# # # # # # #                         "type": "TEXT",
# # # # # # #                         "interactive": False,
# # # # # # #                         "role": "SYSTEM",
# # # # # # #                         "textInputConfiguration": {
# # # # # # #                             "mediaType": "text/plain"
# # # # # # #                         }
# # # # # # #                     }
# # # # # # #                 }
# # # # # # #             }))
            
# # # # # # #             questions_text = "\n".join([f"Q{i+1}: {q}" for i, q in enumerate(self.questions)])
            
# # # # # # #             system_text = f"""You are Nova conducting an EXIT INTERVIEW with {self.employee_name}.

# # # # # # # INSTRUCTIONS:
# # # # # # # 1. Greet once warmly
# # # # # # # 2. Ask these {len(self.questions)} questions IN ORDER - one at a time
# # # # # # # 3. Wait for complete answer before next question
# # # # # # # 4. After Q{len(self.questions)}, say: "Thank you for completing the exit interview. Goodbye."

# # # # # # # QUESTIONS:
# # # # # # # {questions_text}

# # # # # # # Ask sequentially. Do not repeat or skip."""

# # # # # # #             await self.send_event(json.dumps({
# # # # # # #                 "event": {
# # # # # # #                     "textInput": {
# # # # # # #                         "promptName": self.prompt_name,
# # # # # # #                         "contentName": self.system_content_name,
# # # # # # #                         "content": system_text
# # # # # # #                     }
# # # # # # #                 }
# # # # # # #             }))
            
# # # # # # #             await self.send_event(json.dumps({
# # # # # # #                 "event": {
# # # # # # #                     "contentEnd": {
# # # # # # #                         "promptName": self.prompt_name,
# # # # # # #                         "contentName": self.system_content_name
# # # # # # #                     }
# # # # # # #                 }
# # # # # # #             }))
            
# # # # # # #             print("✅ System prompt sent")
# # # # # # #             asyncio.create_task(self._process_responses())
        
# # # # # # #         except Exception as e:
# # # # # # #             print(f"❌ Error starting session: {e}")
# # # # # # #             traceback.print_exc()
# # # # # # #             raise
    
# # # # # # #     async def start_audio_input(self):
# # # # # # #         """Start audio input"""
# # # # # # #         await self.send_event(json.dumps({
# # # # # # #             "event": {
# # # # # # #                 "contentStart": {
# # # # # # #                     "promptName": self.prompt_name,
# # # # # # #                     "contentName": self.audio_content_name,
# # # # # # #                     "type": "AUDIO",
# # # # # # #                     "interactive": True,
# # # # # # #                     "role": "USER",
# # # # # # #                     "audioInputConfiguration": {
# # # # # # #                         "mediaType": "audio/lpcm",
# # # # # # #                         "sampleRateHertz": 16000,
# # # # # # #                         "sampleSizeBits": 16,
# # # # # # #                         "channelCount": 1,
# # # # # # #                         "audioType": "SPEECH",
# # # # # # #                         "encoding": "base64"
# # # # # # #                     }
# # # # # # #                 }
# # # # # # #             }
# # # # # # #         }))
# # # # # # #         print("✅ Audio input started")
    
# # # # # # #     async def send_audio_chunk(self, audio_bytes):
# # # # # # #         """Send audio chunk"""
# # # # # # #         if not self.is_active:
# # # # # # #             return
        
# # # # # # #         blob = base64.b64encode(audio_bytes).decode('utf-8')
# # # # # # #         try:
# # # # # # #             await self.send_event(json.dumps({
# # # # # # #                 "event": {
# # # # # # #                     "audioInput": {
# # # # # # #                         "promptName": self.prompt_name,
# # # # # # #                         "contentName": self.audio_content_name,
# # # # # # #                         "content": blob
# # # # # # #                     }
# # # # # # #                 }
# # # # # # #             }))
# # # # # # #         except Exception as e:
# # # # # # #             print(f"⚠️ Error sending audio: {e}")
    
# # # # # # #     async def _save_response_to_db(self, q_idx: int, question: str, raw_answer: str):
# # # # # # #         """Save response to database with Bedrock cleaning"""
# # # # # # #         try:
# # # # # # #             # Prevent duplicate saves
# # # # # # #             if q_idx in self.saved_q_indices:
# # # # # # #                 print(f"⚠️ Q{q_idx + 1} already saved - skipping duplicate")
# # # # # # #                 return False
            
# # # # # # #             print(f"\n{'='*70}")
# # # # # # #             print(f"💾 SAVING Q{q_idx + 1}/{len(self.questions)} TO DATABASE")
# # # # # # #             print(f"{'='*70}")
# # # # # # #             print(f"Question: {question[:70]}...")
# # # # # # #             print(f"Raw Answer: {raw_answer[:80]}...")
            
# # # # # # #             # Clean with Bedrock
# # # # # # #             cleaned_answer = clean_answer_with_bedrock(raw_answer, question)
# # # # # # #             print(f"Cleaned Answer: {cleaned_answer[:80]}...")
            
# # # # # # #             # Save to DB
# # # # # # #             db_response = InterviewResponse(
# # # # # # #                 interview_id=self.interview_id,
# # # # # # #                 question=question,
# # # # # # #                 answer=cleaned_answer
# # # # # # #             )
# # # # # # #             self.db.add(db_response)
# # # # # # #             self.db.commit()
            
# # # # # # #             self.saved_q_indices.add(q_idx)
            
# # # # # # #             print(f"✅ Q{q_idx + 1} SAVED - Total saved: {len(self.saved_q_indices)}/{len(self.questions)}")
# # # # # # #             print(f"{'='*70}\n")
            
# # # # # # #             # Notify frontend
# # # # # # #             await self.websocket.send_json({
# # # # # # #                 'type': 'response_saved',
# # # # # # #                 'q_index': q_idx,
# # # # # # #                 'question': question,
# # # # # # #                 'answer': cleaned_answer
# # # # # # #             })
            
# # # # # # #             return True
        
# # # # # # #         except Exception as e:
# # # # # # #             print(f"❌ Error saving to DB: {e}")
# # # # # # #             traceback.print_exc()
# # # # # # #             return False
    
# # # # # # #     async def _process_responses(self):
# # # # # # #         """Process responses from Nova"""
# # # # # # #         try:
# # # # # # #             while self.is_active:
# # # # # # #                 try:
# # # # # # #                     output = await self.stream.await_output()
# # # # # # #                     result = await output[1].receive()
                    
# # # # # # #                     if result.value and result.value.bytes_:
# # # # # # #                         response_data = result.value.bytes_.decode('utf-8')
# # # # # # #                         json_data = json.loads(response_data)
                        
# # # # # # #                         if 'event' not in json_data:
# # # # # # #                             continue
                        
# # # # # # #                         event = json_data['event']
                        
# # # # # # #                         # ============ TEXT OUTPUT ============
# # # # # # #                         if 'textOutput' in event:
# # # # # # #                             text = event['textOutput']['content']
# # # # # # #                             role = event['textOutput'].get('role', 'ASSISTANT')
                            
# # # # # # #                             if role == "ASSISTANT":
# # # # # # #                                 print(f"🤖 Nova: {text}")
# # # # # # #                                 await self.websocket.send_json({
# # # # # # #                                     'type': 'text',
# # # # # # #                                     'content': text,
# # # # # # #                                     'role': 'ASSISTANT'
# # # # # # #                                 })
                                
# # # # # # #                                 # Check if asking question - THIS IS THE TRIGGER TO SAVE PREVIOUS ANSWER
# # # # # # #                                 if '?' in text and self.current_q_idx < len(self.questions):
# # # # # # #                                     # BEFORE we mark as waiting for new answer, save the OLD answer
# # # # # # #                                     if self.waiting_for_answer and self.user_answer_buffer.strip():
# # # # # # #                                         question = self.questions[self.current_q_idx]
# # # # # # #                                         raw_answer = self.user_answer_buffer.strip()
                                        
# # # # # # #                                         print(f"\n🔔 NEW QUESTION DETECTED - Saving previous answer for Q{self.current_q_idx + 1}")
                                        
# # # # # # #                                         success = await self._save_response_to_db(self.current_q_idx, question, raw_answer)
                                        
# # # # # # #                                         if success:
# # # # # # #                                             self.current_q_idx += 1
# # # # # # #                                             self.user_answer_buffer = ""
                                    
# # # # # # #                                     # NOW mark as waiting for the NEW question's answer
# # # # # # #                                     self.waiting_for_answer = True
# # # # # # #                                     print(f"❓ Q{self.current_q_idx + 1}: Waiting for answer")
                                
# # # # # # #                                 # Check if goodbye
# # # # # # #                                 if "goodbye" in text.lower():
# # # # # # #                                     print(f"\n✅✅✅ NOVA SAID GOODBYE ✅✅✅")
# # # # # # #                                     # Save any remaining answer
# # # # # # #                                     if self.waiting_for_answer and self.user_answer_buffer.strip():
# # # # # # #                                         if self.current_q_idx < len(self.questions):
# # # # # # #                                             question = self.questions[self.current_q_idx]
# # # # # # #                                             raw_answer = self.user_answer_buffer.strip()
# # # # # # #                                             await self._save_response_to_db(self.current_q_idx, question, raw_answer)
                                    
# # # # # # #                                     await self._finalize_interview()
# # # # # # #                                     return
                            
# # # # # # #                             elif role == "USER" and self.waiting_for_answer:
# # # # # # #                                 # CAPTURE USER ANSWER
# # # # # # #                                 if text != self.last_user_text and text.strip():
# # # # # # #                                     print(f"👤 User: {text}")
# # # # # # #                                     self.last_user_text = text
                                    
# # # # # # #                                     if self.user_answer_buffer:
# # # # # # #                                         self.user_answer_buffer += " "
# # # # # # #                                     self.user_answer_buffer += text
                                    
# # # # # # #                                     print(f"   [Buffer: {self.user_answer_buffer[:100]}...]")
                                    
# # # # # # #                                     await self.websocket.send_json({
# # # # # # #                                         'type': 'text',
# # # # # # #                                         'content': text,
# # # # # # #                                         'role': 'USER'
# # # # # # #                                     })
                        
# # # # # # #                         # ============ AUDIO OUTPUT ============
# # # # # # #                         elif 'audioOutput' in event:
# # # # # # #                             audio_content = event['audioOutput']['content']
# # # # # # #                             await self.websocket.send_json({
# # # # # # #                                 'type': 'audio',
# # # # # # #                                 'data': audio_content
# # # # # # #                             })
                        
# # # # # # #                         # ============ CONTENT END ============
# # # # # # #                         elif 'contentEnd' in event:
# # # # # # #                             # ContentEnd just signals end of a chunk, not used for saving anymore
# # # # # # #                             pass
                        
# # # # # # #                         # ============ COMPLETION ============
# # # # # # #                         elif 'completionEnd' in event:
# # # # # # #                             print("✅ Stream completion ended")
# # # # # # #                             await self._finalize_interview()
# # # # # # #                             return
                
# # # # # # #                 except asyncio.TimeoutError:
# # # # # # #                     continue
# # # # # # #                 except Exception as e:
# # # # # # #                     print(f"⚠️ Error: {e}")
# # # # # # #                     traceback.print_exc()
# # # # # # #                     continue
        
# # # # # # #         except Exception as e:
# # # # # # #             print(f"❌ Fatal error: {e}")
# # # # # # #             traceback.print_exc()
# # # # # # #             self.is_active = False
    
# # # # # # #     async def _finalize_interview(self):
# # # # # # #         """Finalize interview"""
# # # # # # #         print(f"\n{'='*70}")
# # # # # # #         print(f"🎉 INTERVIEW FINALIZATION")
# # # # # # #         print(f"   Questions Saved: {len(self.saved_q_indices)}/{len(self.questions)}")
# # # # # # #         print(f"   Status: {'COMPLETE' if len(self.saved_q_indices) >= len(self.questions) else 'INCOMPLETE'}")
# # # # # # #         print(f"{'='*70}\n")
        
# # # # # # #         try:
# # # # # # #             interview = self.db.query(ExitInterview).filter(ExitInterview.id == self.interview_id).first()
# # # # # # #             if interview:
# # # # # # #                 interview.completed = True
# # # # # # #                 interview.employee.status = "Completed"
# # # # # # #                 self.db.commit()
# # # # # # #                 print("✅ DB marked as completed")
# # # # # # #         except Exception as e:
# # # # # # #             print(f"⚠️ DB update error: {e}")
        
# # # # # # #         # SEND COMPLETION MESSAGE
# # # # # # #         try:
# # # # # # #             await self.websocket.send_json({
# # # # # # #                 'type': 'interview_complete',
# # # # # # #                 'questions_answered': len(self.saved_q_indices),
# # # # # # #                 'total_questions': len(self.questions)
# # # # # # #             })
# # # # # # #             print("✅ Completion message sent to frontend")
# # # # # # #         except Exception as e:
# # # # # # #             print(f"❌ Failed to send completion: {e}")
        
# # # # # # #         self.is_active = False
    
# # # # # # #     async def end_session(self):
# # # # # # #         """End session"""
# # # # # # #         if not self.is_active:
# # # # # # #             return
        
# # # # # # #         try:
# # # # # # #             await self.send_event(json.dumps({
# # # # # # #                 "event": {
# # # # # # #                     "contentEnd": {
# # # # # # #                         "promptName": self.prompt_name,
# # # # # # #                         "contentName": self.audio_content_name
# # # # # # #                     }
# # # # # # #                 }
# # # # # # #             }))
            
# # # # # # #             await self.send_event(json.dumps({
# # # # # # #                 "event": {
# # # # # # #                     "promptEnd": {
# # # # # # #                         "promptName": self.prompt_name
# # # # # # #                     }
# # # # # # #                 }
# # # # # # #             }))
            
# # # # # # #             await self.send_event(json.dumps({
# # # # # # #                 "event": {
# # # # # # #                     "sessionEnd": {}
# # # # # # #                 }
# # # # # # #             }))
            
# # # # # # #             await self.stream.input_stream.close()
# # # # # # #             self.is_active = False
# # # # # # #             print("✅ Session ended")
        
# # # # # # #         except Exception as e:
# # # # # # #             print(f"⚠️ Error ending session: {e}")
# # # # # # #             self.is_active = False

# # # # # # # # ==================== AWS SES ====================
# # # # # # # ses_client = boto3.client('ses', region_name=os.getenv("AWS_REGION", "us-east-1"))

# # # # # # # def send_exit_interview_email(employee_email: str, employee_name: str, form_link: str) -> bool:
# # # # # # #     SENDER = os.getenv("SES_SENDER_EMAIL")
# # # # # # #     SUBJECT = "🎙️ Voice Exit Interview with Nova"
# # # # # # #     BODY_HTML = f"""
# # # # # # #     <html><body>
# # # # # # #         <h1>Hello {employee_name}!</h1>
# # # # # # #         <p>Have a voice conversation with Nova for your exit interview.</p>
# # # # # # #         <p><a href="{form_link}">Start Voice Interview</a></p>
# # # # # # #     </body></html>
# # # # # # #     """
# # # # # # #     try:
# # # # # # #         ses_client.send_email(
# # # # # # #             Source=SENDER,
# # # # # # #             Destination={'ToAddresses': [employee_email]},
# # # # # # #             Message={'Subject': {'Data': SUBJECT}, 'Body': {'Html': {'Data': BODY_HTML}}}
# # # # # # #         )
# # # # # # #         print(f"✅ Email sent to {employee_name}")
# # # # # # #         return True
# # # # # # #     except Exception as e:
# # # # # # #         print(f"❌ Email error: {e}")
# # # # # # #         return False

# # # # # # # def generate_unique_token() -> str:
# # # # # # #     return str(uuid.uuid4())

# # # # # # # def create_form_link(token: str) -> str:
# # # # # # #     return f"{os.getenv('APP_URL', 'http://localhost:8501')}/exit_interview?token={token}"

# # # # # # # # ==================== FASTAPI APP ====================
# # # # # # # app = FastAPI(title="Nova Sonic Exit Interview API", version="5.2.0")

# # # # # # # app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# # # # # # # def get_db():
# # # # # # #     db = SessionLocal()
# # # # # # #     try:
# # # # # # #         yield db
# # # # # # #     finally:
# # # # # # #         db.close()

# # # # # # # active_sessions: Dict[str, NovaInterviewClient] = {}

# # # # # # # # ==================== API ENDPOINTS ====================

# # # # # # # @app.get("/")
# # # # # # # def root():
# # # # # # #     return {"message": "Nova Sonic Exit Interview API", "version": "5.2.0", "status": "running"}

# # # # # # # @app.post("/api/employees", response_model=EmployeeResponse, status_code=201)
# # # # # # # def create_employee(employee: EmployeeCreate, db: Session = Depends(get_db)):
# # # # # # #     try:
# # # # # # #         existing = db.query(Employee).filter(Employee.email == employee.email).first()
# # # # # # #         if existing:
# # # # # # #             raise HTTPException(status_code=400, detail="Employee already exists")
        
# # # # # # #         db_employee = Employee(
# # # # # # #             name=employee.name,
# # # # # # #             email=employee.email,
# # # # # # #             department=employee.department,
# # # # # # #             last_working_date=employee.last_working_date,
# # # # # # #             status="Resigned"
# # # # # # #         )
# # # # # # #         db.add(db_employee)
# # # # # # #         db.commit()
# # # # # # #         db.refresh(db_employee)
        
# # # # # # #         token = generate_unique_token()
# # # # # # #         form_link = create_form_link(token)
        
# # # # # # #         questions_json = json.dumps(employee.questions) if employee.questions else json.dumps([
# # # # # # #             "What was your primary reason for leaving?",
# # # # # # #             "How would you rate your overall experience with the company on a scale of 1 to 5?",
# # # # # # #             "How was your relationship with your manager?",
# # # # # # #             "Did you feel valued and recognized in your role?",
# # # # # # #             "Would you recommend our company to others? Why or why not?"
# # # # # # #         ])
        
# # # # # # #         db_interview = ExitInterview(
# # # # # # #             employee_id=db_employee.id,
# # # # # # #             form_token=token,
# # # # # # #             completed=False,
# # # # # # #             questions_json=questions_json
# # # # # # #         )
# # # # # # #         db.add(db_interview)
# # # # # # #         db.commit()
        
# # # # # # #         send_exit_interview_email(db_employee.email, db_employee.name, form_link)
        
# # # # # # #         return db_employee
# # # # # # #     except HTTPException:
# # # # # # #         raise
# # # # # # #     except Exception as e:
# # # # # # #         db.rollback()
# # # # # # #         raise HTTPException(status_code=500, detail=str(e))

# # # # # # # @app.get("/api/employees", response_model=List[EmployeeResponse])
# # # # # # # def list_employees(db: Session = Depends(get_db)):
# # # # # # #     return db.query(Employee).all()

# # # # # # # @app.get("/api/interviews/token/{token}")
# # # # # # # def get_interview_by_token(token: str, db: Session = Depends(get_db)):
# # # # # # #     interview = db.query(ExitInterview).filter(ExitInterview.form_token == token).first()
# # # # # # #     if not interview:
# # # # # # #         raise HTTPException(status_code=404, detail="Invalid token")
# # # # # # #     if interview.completed:
# # # # # # #         raise HTTPException(status_code=400, detail="Interview already completed")
    
# # # # # # #     questions = json.loads(interview.questions_json)
# # # # # # #     return {
# # # # # # #         "interview_id": interview.id,
# # # # # # #         "employee_name": interview.employee.name,
# # # # # # #         "employee_department": interview.employee.department,
# # # # # # #         "questions": questions,
# # # # # # #         "total_questions": len(questions),
# # # # # # #         "completed": interview.completed
# # # # # # #     }

# # # # # # # @app.websocket("/ws/interview/{token}")
# # # # # # # async def websocket_interview(websocket: WebSocket, token: str):
# # # # # # #     await websocket.accept()
    
# # # # # # #     db = SessionLocal()
# # # # # # #     session_id = str(uuid.uuid4())
# # # # # # #     nova_client = None
    
# # # # # # #     try:
# # # # # # #         interview = db.query(ExitInterview).filter(ExitInterview.form_token == token).first()
# # # # # # #         if not interview:
# # # # # # #             await websocket.send_json({"type": "error", "message": "Invalid token"})
# # # # # # #             return
        
# # # # # # #         questions = json.loads(interview.questions_json)
# # # # # # #         employee_name = interview.employee.name
        
# # # # # # #         print(f"\n{'='*70}")
# # # # # # #         print(f"🎙️ NEW INTERVIEW: {employee_name}")
# # # # # # #         print(f"📋 Questions: {len(questions)}")
# # # # # # #         print(f"{'='*70}\n")
        
# # # # # # #         await websocket.send_json({
# # # # # # #             "type": "session_start",
# # # # # # #             "session_id": session_id,
# # # # # # #             "employee_name": employee_name,
# # # # # # #             "total_questions": len(questions)
# # # # # # #         })
        
# # # # # # #         nova_client = NovaInterviewClient(
# # # # # # #             employee_name,
# # # # # # #             questions,
# # # # # # #             websocket,
# # # # # # #             db,
# # # # # # #             interview.id,
# # # # # # #             os.getenv("AWS_REGION", "us-east-1")
# # # # # # #         )
# # # # # # #         await nova_client.start_session()
        
# # # # # # #         await asyncio.sleep(2)
# # # # # # #         await nova_client.start_audio_input()
        
# # # # # # #         active_sessions[session_id] = nova_client
        
# # # # # # #         timeout_seconds = 300
# # # # # # #         start_time = datetime.utcnow()
        
# # # # # # #         while nova_client.is_active:
# # # # # # #             try:
# # # # # # #                 message = await asyncio.wait_for(websocket.receive_json(), timeout=0.5)
# # # # # # #                 start_time = datetime.utcnow()
                
# # # # # # #                 if message['type'] == 'audio_chunk':
# # # # # # #                     audio_data = base64.b64decode(message['data'])
# # # # # # #                     await nova_client.send_audio_chunk(audio_data)
                
# # # # # # #                 elif message['type'] == 'close':
# # # # # # #                     break
            
# # # # # # #             except asyncio.TimeoutError:
# # # # # # #                 elapsed = (datetime.utcnow() - start_time).total_seconds()
# # # # # # #                 if elapsed > timeout_seconds:
# # # # # # #                     print(f"⚠️ Interview timeout after {timeout_seconds}s")
# # # # # # #                     break
# # # # # # #                 continue
# # # # # # #             except WebSocketDisconnect:
# # # # # # #                 print("⚠️ Client disconnected")
# # # # # # #                 break
# # # # # # #             except Exception as e:
# # # # # # #                 print(f"⚠️ Error: {e}")
# # # # # # #                 break
    
# # # # # # #     except Exception as e:
# # # # # # #         print(f"❌ Error: {e}")
# # # # # # #         traceback.print_exc()
# # # # # # #         try:
# # # # # # #             await websocket.send_json({"type": "error", "message": str(e)})
# # # # # # #         except:
# # # # # # #             pass
# # # # # # #     finally:
# # # # # # #         if nova_client:
# # # # # # #             await nova_client.end_session()
# # # # # # #         if session_id in active_sessions:
# # # # # # #             del active_sessions[session_id]
# # # # # # #         db.close()

# # # # # # # @app.get("/api/interviews/{interview_id}/responses", response_model=List[InterviewResponseDetail])
# # # # # # # def get_interview_responses(interview_id: int, db: Session = Depends(get_db)):
# # # # # # #     return db.query(InterviewResponse).filter(InterviewResponse.interview_id == interview_id).all()

# # # # # # # @app.get("/api/stats")
# # # # # # # def get_statistics(db: Session = Depends(get_db)):
# # # # # # #     total = db.query(Employee).count()
# # # # # # #     completed = db.query(ExitInterview).filter(ExitInterview.completed == True).count()
# # # # # # #     return {
# # # # # # #         "total_resignations": total,
# # # # # # #         "completed_interviews": completed,
# # # # # # #         "pending_interviews": total - completed,
# # # # # # #         "completion_rate": (completed / total * 100) if total > 0 else 0
# # # # # # #     }

# # # # # # # def init_db():
# # # # # # #     Base.metadata.create_all(bind=engine)
# # # # # # #     print("✅ Database initialized!")

# # # # # # # if __name__ == "__main__":
# # # # # # #     init_db()
# # # # # # #     import uvicorn
# # # # # # #     print("\n🚀 Nova Sonic Exit Interview API v5.2")
# # # # # # #     print("📡 http://0.0.0.0:8000\n")
# # # # # # #     uvicorn.run(app, host="0.0.0.0", port=8000)



# # # # # # """
# # # # # # FIXED Nova Sonic Exit Interview Backend - PROPERLY SAVES RESPONSES
# # # # # # Comprehensive fix for Q&A capture and database storage
# # # # # # """

# # # # # # from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
# # # # # # from fastapi.middleware.cors import CORSMiddleware
# # # # # # from sqlalchemy import create_engine, Column, Integer, String, Boolean, Date, DateTime, Text, ForeignKey
# # # # # # from sqlalchemy.ext.declarative import declarative_base
# # # # # # from sqlalchemy.orm import sessionmaker, Session, relationship
# # # # # # from pydantic import BaseModel, EmailStr, field_validator
# # # # # # from typing import List, Optional, Dict, Any
# # # # # # from datetime import datetime, date
# # # # # # import os
# # # # # # from dotenv import load_dotenv
# # # # # # import boto3
# # # # # # import uuid
# # # # # # import json
# # # # # # import asyncio
# # # # # # import base64
# # # # # # import traceback

# # # # # # from aws_sdk_bedrock_runtime.client import BedrockRuntimeClient, InvokeModelWithBidirectionalStreamOperationInput
# # # # # # from aws_sdk_bedrock_runtime.models import InvokeModelWithBidirectionalStreamInputChunk, BidirectionalInputPayloadPart
# # # # # # from aws_sdk_bedrock_runtime.config import Config
# # # # # # from smithy_aws_core.identity.environment import EnvironmentCredentialsResolver

# # # # # # load_dotenv()

# # # # # # # ==================== DATABASE SETUP ====================
# # # # # # DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

# # # # # # engine = create_engine(DATABASE_URL)
# # # # # # SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# # # # # # Base = declarative_base()

# # # # # # # ==================== DATABASE MODELS ====================
# # # # # # class Employee(Base):
# # # # # #     __tablename__ = "employees"
    
# # # # # #     id = Column(Integer, primary_key=True, index=True)
# # # # # #     name = Column(String(100), nullable=False)
# # # # # #     email = Column(String(100), unique=True, nullable=False)
# # # # # #     department = Column(String(50))
# # # # # #     last_working_date = Column(Date)
# # # # # #     status = Column(String(20), default="Resigned")
# # # # # #     created_at = Column(DateTime, default=datetime.utcnow)
    
# # # # # #     exit_interview = relationship("ExitInterview", back_populates="employee", uselist=False)

# # # # # # class ExitInterview(Base):
# # # # # #     __tablename__ = "exit_interviews"
    
# # # # # #     id = Column(Integer, primary_key=True, index=True)
# # # # # #     employee_id = Column(Integer, ForeignKey("employees.id"))
# # # # # #     form_token = Column(String(255), unique=True, nullable=False)
# # # # # #     completed = Column(Boolean, default=False)
# # # # # #     questions_json = Column(Text)
# # # # # #     created_at = Column(DateTime, default=datetime.utcnow)
    
# # # # # #     employee = relationship("Employee", back_populates="exit_interview")
# # # # # #     responses = relationship("InterviewResponse", back_populates="interview")

# # # # # # class InterviewResponse(Base):
# # # # # #     __tablename__ = "interview_responses"
    
# # # # # #     id = Column(Integer, primary_key=True, index=True)
# # # # # #     interview_id = Column(Integer, ForeignKey("exit_interviews.id"))
# # # # # #     question = Column(Text, nullable=False)
# # # # # #     answer = Column(Text, nullable=False)
# # # # # #     created_at = Column(DateTime, default=datetime.utcnow)
    
# # # # # #     interview = relationship("ExitInterview", back_populates="responses")

# # # # # # # ==================== PYDANTIC SCHEMAS ====================
# # # # # # class EmployeeCreate(BaseModel):
# # # # # #     name: str
# # # # # #     email: EmailStr
# # # # # #     department: str
# # # # # #     last_working_date: date
# # # # # #     questions: Optional[List[str]] = None
    
# # # # # #     @field_validator('name')
# # # # # #     def name_must_not_be_empty(cls, v):
# # # # # #         if not v or not v.strip():
# # # # # #             raise ValueError('Name cannot be empty')
# # # # # #         return v.strip()

# # # # # # class EmployeeResponse(BaseModel):
# # # # # #     id: int
# # # # # #     name: str
# # # # # #     email: str
# # # # # #     department: str
# # # # # #     last_working_date: date
# # # # # #     status: str
# # # # # #     created_at: datetime
    
# # # # # #     class Config:
# # # # # #         from_attributes = True

# # # # # # class InterviewResponseDetail(BaseModel):
# # # # # #     id: int
# # # # # #     question: str
# # # # # #     answer: str
# # # # # #     created_at: datetime
    
# # # # # #     class Config:
# # # # # #         from_attributes = True

# # # # # # # ==================== BEDROCK ANSWER CLEANING ====================
# # # # # # def clean_answer_with_bedrock(raw_answer: str, question: str) -> str:
# # # # # #     """Clean answer using Bedrock - removes filler, greetings, etc."""
# # # # # #     try:
# # # # # #         if not raw_answer or len(raw_answer.strip()) < 2:
# # # # # #             return raw_answer.strip()
        
# # # # # #         bedrock = boto3.client('bedrock-runtime', region_name=os.getenv("AWS_REGION", "us-east-1"))
        
# # # # # #         prompt = f"""Extract the meaningful answer from this speech transcription. Remove greetings, filler words, and conversational noise.

# # # # # # Question: {question}
# # # # # # Raw Answer: {raw_answer}

# # # # # # Return ONLY the cleaned answer, nothing else:"""

# # # # # #         body = json.dumps({
# # # # # #             "inputText": prompt,
# # # # # #             "textGenerationConfig": {
# # # # # #                 "maxTokenCount": 100,
# # # # # #                 "temperature": 0.1,
# # # # # #                 "topP": 0.9
# # # # # #             }
# # # # # #         })
        
# # # # # #         response = bedrock.invoke_model(
# # # # # #             body=body,
# # # # # #             modelId="amazon.titan-text-express-v1",
# # # # # #             accept="application/json",
# # # # # #             contentType="application/json"
# # # # # #         )
        
# # # # # #         response_body = json.loads(response.get('body').read())
# # # # # #         cleaned = response_body.get('results', [{}])[0].get('outputText', '').strip()
        
# # # # # #         return cleaned if cleaned else raw_answer.strip()
    
# # # # # #     except Exception as e:
# # # # # #         print(f"⚠️ Bedrock error: {e} - using raw answer")
# # # # # #         return raw_answer.strip()

# # # # # # # ==================== NOVA SONIC CLIENT ====================
# # # # # # class NovaInterviewClient:
# # # # # #     def __init__(self, employee_name: str, questions: List[str], websocket: WebSocket, db: Session, interview_id: int, region='us-east-1'):
# # # # # #         self.model_id = 'amazon.nova-sonic-v1:0'
# # # # # #         self.region = region
# # # # # #         self.employee_name = employee_name
# # # # # #         self.questions = questions
# # # # # #         self.websocket = websocket
# # # # # #         self.db = db
# # # # # #         self.interview_id = interview_id
# # # # # #         self.client = None
# # # # # #         self.stream = None
# # # # # #         self.is_active = False
        
# # # # # #         self.prompt_name = str(uuid.uuid4())
# # # # # #         self.system_content_name = str(uuid.uuid4())
# # # # # #         self.audio_content_name = str(uuid.uuid4())
        
# # # # # #         # State tracking - CRITICAL
# # # # # #         self.current_q_idx = 0
# # # # # #         self.user_answer_buffer = ""
# # # # # #         self.waiting_for_answer = False
# # # # # #         self.last_user_text = ""
# # # # # #         self.saved_q_indices = set()  # Track which questions we've saved
# # # # # #         self.last_nova_question = ""  # Track the last question Nova asked to avoid duplicates
    
# # # # # #     def _initialize_client(self):
# # # # # #         """Initialize Bedrock client"""
# # # # # #         resolver = EnvironmentCredentialsResolver()
# # # # # #         config = Config(
# # # # # #             endpoint_uri=f"https://bedrock-runtime.{self.region}.amazonaws.com",
# # # # # #             region=self.region,
# # # # # #             aws_credentials_identity_resolver=resolver
# # # # # #         )
# # # # # #         self.client = BedrockRuntimeClient(config=config)
# # # # # #         print("✅ Bedrock client initialized")
    
# # # # # #     async def send_event(self, event_json):
# # # # # #         """Send event to stream"""
# # # # # #         event = InvokeModelWithBidirectionalStreamInputChunk(
# # # # # #             value=BidirectionalInputPayloadPart(bytes_=event_json.encode('utf-8'))
# # # # # #         )
# # # # # #         await self.stream.input_stream.send(event)
    
# # # # # #     async def start_session(self):
# # # # # #         """Start Nova Sonic session"""
# # # # # #         if not self.client:
# # # # # #             self._initialize_client()
        
# # # # # #         try:
# # # # # #             print("📡 Starting bidirectional stream...")
# # # # # #             self.stream = await self.client.invoke_model_with_bidirectional_stream(
# # # # # #                 InvokeModelWithBidirectionalStreamOperationInput(model_id=self.model_id)
# # # # # #             )
# # # # # #             self.is_active = True
# # # # # #             print("✅ Stream started")
            
# # # # # #             await self.send_event(json.dumps({
# # # # # #                 "event": {
# # # # # #                     "sessionStart": {
# # # # # #                         "inferenceConfiguration": {
# # # # # #                             "maxTokens": 1024,
# # # # # #                             "topP": 0.9,
# # # # # #                             "temperature": 0.7
# # # # # #                         }
# # # # # #                     }
# # # # # #                 }
# # # # # #             }))
            
# # # # # #             await self.send_event(json.dumps({
# # # # # #                 "event": {
# # # # # #                     "promptStart": {
# # # # # #                         "promptName": self.prompt_name,
# # # # # #                         "textOutputConfiguration": {
# # # # # #                             "mediaType": "text/plain"
# # # # # #                         },
# # # # # #                         "audioOutputConfiguration": {
# # # # # #                             "mediaType": "audio/lpcm",
# # # # # #                             "sampleRateHertz": 24000,
# # # # # #                             "sampleSizeBits": 16,
# # # # # #                             "channelCount": 1,
# # # # # #                             "voiceId": "matthew",
# # # # # #                             "encoding": "base64",
# # # # # #                             "audioType": "SPEECH"
# # # # # #                         }
# # # # # #                     }
# # # # # #                 }
# # # # # #             }))
            
# # # # # #             await self.send_event(json.dumps({
# # # # # #                 "event": {
# # # # # #                     "contentStart": {
# # # # # #                         "promptName": self.prompt_name,
# # # # # #                         "contentName": self.system_content_name,
# # # # # #                         "type": "TEXT",
# # # # # #                         "interactive": False,
# # # # # #                         "role": "SYSTEM",
# # # # # #                         "textInputConfiguration": {
# # # # # #                             "mediaType": "text/plain"
# # # # # #                         }
# # # # # #                     }
# # # # # #                 }
# # # # # #             }))
            
# # # # # #             questions_text = "\n".join([f"Q{i+1}: {q}" for i, q in enumerate(self.questions)])
            
# # # # # #             system_text = f"""You are Nova conducting an EXIT INTERVIEW with {self.employee_name}.

# # # # # # INSTRUCTIONS:
# # # # # # 1. Greet once warmly
# # # # # # 2. Ask these {len(self.questions)} questions IN ORDER - one at a time
# # # # # # 3. Wait for complete answer before next question
# # # # # # 4. After Q{len(self.questions)}, say: "Thank you for completing the exit interview. Goodbye."

# # # # # # QUESTIONS:
# # # # # # {questions_text}

# # # # # # Ask sequentially. Do not repeat or skip."""

# # # # # #             await self.send_event(json.dumps({
# # # # # #                 "event": {
# # # # # #                     "textInput": {
# # # # # #                         "promptName": self.prompt_name,
# # # # # #                         "contentName": self.system_content_name,
# # # # # #                         "content": system_text
# # # # # #                     }
# # # # # #                 }
# # # # # #             }))
            
# # # # # #             await self.send_event(json.dumps({
# # # # # #                 "event": {
# # # # # #                     "contentEnd": {
# # # # # #                         "promptName": self.prompt_name,
# # # # # #                         "contentName": self.system_content_name
# # # # # #                     }
# # # # # #                 }
# # # # # #             }))
            
# # # # # #             print("✅ System prompt sent")
# # # # # #             asyncio.create_task(self._process_responses())
        
# # # # # #         except Exception as e:
# # # # # #             print(f"❌ Error starting session: {e}")
# # # # # #             traceback.print_exc()
# # # # # #             raise
    
# # # # # #     async def start_audio_input(self):
# # # # # #         """Start audio input"""
# # # # # #         await self.send_event(json.dumps({
# # # # # #             "event": {
# # # # # #                 "contentStart": {
# # # # # #                     "promptName": self.prompt_name,
# # # # # #                     "contentName": self.audio_content_name,
# # # # # #                     "type": "AUDIO",
# # # # # #                     "interactive": True,
# # # # # #                     "role": "USER",
# # # # # #                     "audioInputConfiguration": {
# # # # # #                         "mediaType": "audio/lpcm",
# # # # # #                         "sampleRateHertz": 16000,
# # # # # #                         "sampleSizeBits": 16,
# # # # # #                         "channelCount": 1,
# # # # # #                         "audioType": "SPEECH",
# # # # # #                         "encoding": "base64"
# # # # # #                     }
# # # # # #                 }
# # # # # #             }
# # # # # #         }))
# # # # # #         print("✅ Audio input started")
    
# # # # # #     async def send_audio_chunk(self, audio_bytes):
# # # # # #         """Send audio chunk"""
# # # # # #         if not self.is_active:
# # # # # #             return
        
# # # # # #         blob = base64.b64encode(audio_bytes).decode('utf-8')
# # # # # #         try:
# # # # # #             await self.send_event(json.dumps({
# # # # # #                 "event": {
# # # # # #                     "audioInput": {
# # # # # #                         "promptName": self.prompt_name,
# # # # # #                         "contentName": self.audio_content_name,
# # # # # #                         "content": blob
# # # # # #                     }
# # # # # #                 }
# # # # # #             }))
# # # # # #         except Exception as e:
# # # # # #             print(f"⚠️ Error sending audio: {e}")
    
# # # # # #     async def _save_response_to_db(self, q_idx: int, question: str, raw_answer: str):
# # # # # #         """Save response to database with Bedrock cleaning"""
# # # # # #         try:
# # # # # #             # Prevent duplicate saves
# # # # # #             if q_idx in self.saved_q_indices:
# # # # # #                 print(f"⚠️ Q{q_idx + 1} already saved - skipping duplicate")
# # # # # #                 return False
            
# # # # # #             # Don't save if answer is too short or looks like Nova speaking
# # # # # #             if len(raw_answer.strip()) < 3:
# # # # # #                 print(f"⚠️ Answer too short, skipping: {raw_answer}")
# # # # # #                 return False
            
# # # # # #             # Check if this looks like a Nova response (not a user answer)
# # # # # #             raw_lower = raw_answer.lower()
# # # # # #             nova_phrases = [
# # # # # #                 "i see", "that's good", "thank you", "great to hear", "wonderful",
# # # # # #                 "i'm glad", "i appreciate", "understood", "moving on", "let's",
# # # # # #                 "now let's", "how would you", "did you", "would you recommend"
# # # # # #             ]
            
# # # # # #             if any(phrase in raw_lower for phrase in nova_phrases):
# # # # # #                 print(f"⚠️ This looks like Nova speaking, not user answer: {raw_answer}")
# # # # # #                 return False
            
# # # # # #             print(f"\n{'='*70}")
# # # # # #             print(f"💾 SAVING Q{q_idx + 1}/{len(self.questions)} TO DATABASE")
# # # # # #             print(f"{'='*70}")
# # # # # #             print(f"Question: {question[:70]}...")
# # # # # #             print(f"Raw Answer: {raw_answer[:80]}...")
            
# # # # # #             # Clean with Bedrock
# # # # # #             cleaned_answer = clean_answer_with_bedrock(raw_answer, question)
# # # # # #             print(f"Cleaned Answer: {cleaned_answer[:80]}...")
            
# # # # # #             # Save to DB
# # # # # #             db_response = InterviewResponse(
# # # # # #                 interview_id=self.interview_id,
# # # # # #                 question=question,
# # # # # #                 answer=cleaned_answer
# # # # # #             )
# # # # # #             self.db.add(db_response)
# # # # # #             self.db.commit()
            
# # # # # #             self.saved_q_indices.add(q_idx)
            
# # # # # #             print(f"✅ Q{q_idx + 1} SAVED - Total saved: {len(self.saved_q_indices)}/{len(self.questions)}")
# # # # # #             print(f"{'='*70}\n")
            
# # # # # #             # Notify frontend
# # # # # #             await self.websocket.send_json({
# # # # # #                 'type': 'response_saved',
# # # # # #                 'q_index': q_idx,
# # # # # #                 'question': question,
# # # # # #                 'answer': cleaned_answer
# # # # # #             })
            
# # # # # #             return True
        
# # # # # #         except Exception as e:
# # # # # #             print(f"❌ Error saving to DB: {e}")
# # # # # #             traceback.print_exc()
# # # # # #             return False
    
# # # # # #     async def _process_responses(self):
# # # # # #         """Process responses from Nova"""
# # # # # #         try:
# # # # # #             while self.is_active:
# # # # # #                 try:
# # # # # #                     output = await self.stream.await_output()
# # # # # #                     result = await output[1].receive()
                    
# # # # # #                     if result.value and result.value.bytes_:
# # # # # #                         response_data = result.value.bytes_.decode('utf-8')
# # # # # #                         json_data = json.loads(response_data)
                        
# # # # # #                         if 'event' not in json_data:
# # # # # #                             continue
                        
# # # # # #                         event = json_data['event']
                        
# # # # # #                         # ============ TEXT OUTPUT ============
# # # # # #                         if 'textOutput' in event:
# # # # # #                             text = event['textOutput']['content']
# # # # # #                             role = event['textOutput'].get('role', 'ASSISTANT')
                            
# # # # # #                             if role == "ASSISTANT":
# # # # # #                                 print(f"🤖 Nova: {text}")
# # # # # #                                 await self.websocket.send_json({
# # # # # #                                     'type': 'text',
# # # # # #                                     'content': text,
# # # # # #                                     'role': 'ASSISTANT'
# # # # # #                                 })
                                
# # # # # #                                 # Check if asking question - THIS IS THE TRIGGER TO SAVE PREVIOUS ANSWER
# # # # # #                                 if '?' in text and self.current_q_idx < len(self.questions):
# # # # # #                                     # Only process if this is a NEW question (not a repeat chunk of the same question)
# # # # # #                                     if text != self.last_nova_question:
# # # # # #                                         self.last_nova_question = text
                                        
# # # # # #                                         # BEFORE we mark as waiting for new answer, save the OLD answer
# # # # # #                                         if self.waiting_for_answer and self.user_answer_buffer.strip():
# # # # # #                                             question = self.questions[self.current_q_idx]
# # # # # #                                             raw_answer = self.user_answer_buffer.strip()
                                            
# # # # # #                                             print(f"\n🔔 NEW QUESTION DETECTED - Saving previous answer for Q{self.current_q_idx + 1}")
                                            
# # # # # #                                             success = await self._save_response_to_db(self.current_q_idx, question, raw_answer)
                                            
# # # # # #                                             if success:
# # # # # #                                                 self.current_q_idx += 1
# # # # # #                                                 self.user_answer_buffer = ""
                                        
# # # # # #                                         # NOW mark as waiting for the NEW question's answer
# # # # # #                                         self.waiting_for_answer = True
# # # # # #                                         print(f"❓ Q{self.current_q_idx + 1}: Waiting for answer")
                                
# # # # # #                                 # Check if goodbye
# # # # # #                                 if "goodbye" in text.lower():
# # # # # #                                     print(f"\n✅✅✅ NOVA SAID GOODBYE ✅✅✅")
# # # # # #                                     # Save any remaining answer
# # # # # #                                     if self.waiting_for_answer and self.user_answer_buffer.strip():
# # # # # #                                         if self.current_q_idx < len(self.questions):
# # # # # #                                             question = self.questions[self.current_q_idx]
# # # # # #                                             raw_answer = self.user_answer_buffer.strip()
# # # # # #                                             await self._save_response_to_db(self.current_q_idx, question, raw_answer)
                                    
# # # # # #                                     await self._finalize_interview()
# # # # # #                                     return
                            
# # # # # #                             elif role == "USER" and self.waiting_for_answer:
# # # # # #                                 # CAPTURE USER ANSWER - but NOT if it's Nova's response
# # # # # #                                 # Filter out Nova's responses that appear as USER
# # # # # #                                 if text != self.last_user_text and text.strip():
# # # # # #                                     # Don't capture if this looks like Nova's response
# # # # # #                                     text_lower = text.lower()
# # # # # #                                     is_nova_response = any(phrase in text_lower for phrase in [
# # # # # #                                         "i see",
# # # # # #                                         "that's",
# # # # # #                                         "thank you",
# # # # # #                                         "great",
# # # # # #                                         "wonderful",
# # # # # #                                         "i'm glad",
# # # # # #                                         "appreciate",
# # # # # #                                         "understood",
# # # # # #                                         "moving on",
# # # # # #                                         "let's",
# # # # # #                                         "now"
# # # # # #                                     ])
                                    
# # # # # #                                     # Only capture if it doesn't look like Nova speaking
# # # # # #                                     if not is_nova_response or len(text.split()) < 3:
# # # # # #                                         print(f"👤 User: {text}")
# # # # # #                                         self.last_user_text = text
                                        
# # # # # #                                         if self.user_answer_buffer:
# # # # # #                                             self.user_answer_buffer += " "
# # # # # #                                         self.user_answer_buffer += text
                                        
# # # # # #                                         print(f"   [Buffer: {self.user_answer_buffer[:100]}...]")
                                        
# # # # # #                                         await self.websocket.send_json({
# # # # # #                                             'type': 'text',
# # # # # #                                             'content': text,
# # # # # #                                             'role': 'USER'
# # # # # #                                         })
                        
# # # # # #                         # ============ AUDIO OUTPUT ============
# # # # # #                         elif 'audioOutput' in event:
# # # # # #                             audio_content = event['audioOutput']['content']
# # # # # #                             await self.websocket.send_json({
# # # # # #                                 'type': 'audio',
# # # # # #                                 'data': audio_content
# # # # # #                             })
                        
# # # # # #                         # ============ CONTENT END ============
# # # # # #                         elif 'contentEnd' in event:
# # # # # #                             # ContentEnd just signals end of a chunk, not used for saving anymore
# # # # # #                             pass
                        
# # # # # #                         # ============ COMPLETION ============
# # # # # #                         elif 'completionEnd' in event:
# # # # # #                             print("✅ Stream completion ended")
# # # # # #                             await self._finalize_interview()
# # # # # #                             return
                
# # # # # #                 except asyncio.TimeoutError:
# # # # # #                     continue
# # # # # #                 except Exception as e:
# # # # # #                     print(f"⚠️ Error: {e}")
# # # # # #                     traceback.print_exc()
# # # # # #                     continue
        
# # # # # #         except Exception as e:
# # # # # #             print(f"❌ Fatal error: {e}")
# # # # # #             traceback.print_exc()
# # # # # #             self.is_active = False
    
# # # # # #     async def _finalize_interview(self):
# # # # # #         """Finalize interview"""
# # # # # #         print(f"\n{'='*70}")
# # # # # #         print(f"🎉 INTERVIEW FINALIZATION")
# # # # # #         print(f"   Questions Saved: {len(self.saved_q_indices)}/{len(self.questions)}")
# # # # # #         print(f"   Status: {'COMPLETE' if len(self.saved_q_indices) >= len(self.questions) else 'INCOMPLETE'}")
# # # # # #         print(f"{'='*70}\n")
        
# # # # # #         try:
# # # # # #             interview = self.db.query(ExitInterview).filter(ExitInterview.id == self.interview_id).first()
# # # # # #             if interview:
# # # # # #                 interview.completed = True
# # # # # #                 interview.employee.status = "Completed"
# # # # # #                 self.db.commit()
# # # # # #                 print("✅ DB marked as completed")
# # # # # #         except Exception as e:
# # # # # #             print(f"⚠️ DB update error: {e}")
        
# # # # # #         # SEND COMPLETION MESSAGE
# # # # # #         try:
# # # # # #             await self.websocket.send_json({
# # # # # #                 'type': 'interview_complete',
# # # # # #                 'questions_answered': len(self.saved_q_indices),
# # # # # #                 'total_questions': len(self.questions)
# # # # # #             })
# # # # # #             print("✅ Completion message sent to frontend")
# # # # # #         except Exception as e:
# # # # # #             print(f"❌ Failed to send completion: {e}")
        
# # # # # #         self.is_active = False
    
# # # # # #     async def end_session(self):
# # # # # #         """End session"""
# # # # # #         if not self.is_active:
# # # # # #             return
        
# # # # # #         try:
# # # # # #             await self.send_event(json.dumps({
# # # # # #                 "event": {
# # # # # #                     "contentEnd": {
# # # # # #                         "promptName": self.prompt_name,
# # # # # #                         "contentName": self.audio_content_name
# # # # # #                     }
# # # # # #                 }
# # # # # #             }))
            
# # # # # #             await self.send_event(json.dumps({
# # # # # #                 "event": {
# # # # # #                     "promptEnd": {
# # # # # #                         "promptName": self.prompt_name
# # # # # #                     }
# # # # # #                 }
# # # # # #             }))
            
# # # # # #             await self.send_event(json.dumps({
# # # # # #                 "event": {
# # # # # #                     "sessionEnd": {}
# # # # # #                 }
# # # # # #             }))
            
# # # # # #             await self.stream.input_stream.close()
# # # # # #             self.is_active = False
# # # # # #             print("✅ Session ended")
        
# # # # # #         except Exception as e:
# # # # # #             print(f"⚠️ Error ending session: {e}")
# # # # # #             self.is_active = False

# # # # # # # ==================== AWS SES ====================
# # # # # # ses_client = boto3.client('ses', region_name=os.getenv("AWS_REGION", "us-east-1"))

# # # # # # def send_exit_interview_email(employee_email: str, employee_name: str, form_link: str) -> bool:
# # # # # #     SENDER = os.getenv("SES_SENDER_EMAIL")
# # # # # #     SUBJECT = "🎙️ Voice Exit Interview with Nova"
# # # # # #     BODY_HTML = f"""
# # # # # #     <html><body>
# # # # # #         <h1>Hello {employee_name}!</h1>
# # # # # #         <p>Have a voice conversation with Nova for your exit interview.</p>
# # # # # #         <p><a href="{form_link}">Start Voice Interview</a></p>
# # # # # #     </body></html>
# # # # # #     """
# # # # # #     try:
# # # # # #         ses_client.send_email(
# # # # # #             Source=SENDER,
# # # # # #             Destination={'ToAddresses': [employee_email]},
# # # # # #             Message={'Subject': {'Data': SUBJECT}, 'Body': {'Html': {'Data': BODY_HTML}}}
# # # # # #         )
# # # # # #         print(f"✅ Email sent to {employee_name}")
# # # # # #         return True
# # # # # #     except Exception as e:
# # # # # #         print(f"❌ Email error: {e}")
# # # # # #         return False

# # # # # # def generate_unique_token() -> str:
# # # # # #     return str(uuid.uuid4())

# # # # # # def create_form_link(token: str) -> str:
# # # # # #     return f"{os.getenv('APP_URL', 'http://localhost:8501')}/exit_interview?token={token}"

# # # # # # # ==================== FASTAPI APP ====================
# # # # # # app = FastAPI(title="Nova Sonic Exit Interview API", version="5.2.0")

# # # # # # app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# # # # # # def get_db():
# # # # # #     db = SessionLocal()
# # # # # #     try:
# # # # # #         yield db
# # # # # #     finally:
# # # # # #         db.close()

# # # # # # active_sessions: Dict[str, NovaInterviewClient] = {}

# # # # # # # ==================== API ENDPOINTS ====================

# # # # # # @app.get("/")
# # # # # # def root():
# # # # # #     return {"message": "Nova Sonic Exit Interview API", "version": "5.2.0", "status": "running"}

# # # # # # @app.post("/api/employees", response_model=EmployeeResponse, status_code=201)
# # # # # # def create_employee(employee: EmployeeCreate, db: Session = Depends(get_db)):
# # # # # #     try:
# # # # # #         existing = db.query(Employee).filter(Employee.email == employee.email).first()
# # # # # #         if existing:
# # # # # #             raise HTTPException(status_code=400, detail="Employee already exists")
        
# # # # # #         db_employee = Employee(
# # # # # #             name=employee.name,
# # # # # #             email=employee.email,
# # # # # #             department=employee.department,
# # # # # #             last_working_date=employee.last_working_date,
# # # # # #             status="Resigned"
# # # # # #         )
# # # # # #         db.add(db_employee)
# # # # # #         db.commit()
# # # # # #         db.refresh(db_employee)
        
# # # # # #         token = generate_unique_token()
# # # # # #         form_link = create_form_link(token)
        
# # # # # #         questions_json = json.dumps(employee.questions) if employee.questions else json.dumps([
# # # # # #             "What was your primary reason for leaving?",
# # # # # #             "How would you rate your overall experience with the company on a scale of 1 to 5?",
# # # # # #             "How was your relationship with your manager?",
# # # # # #             "Did you feel valued and recognized in your role?",
# # # # # #             "Would you recommend our company to others? Why or why not?"
# # # # # #         ])
        
# # # # # #         db_interview = ExitInterview(
# # # # # #             employee_id=db_employee.id,
# # # # # #             form_token=token,
# # # # # #             completed=False,
# # # # # #             questions_json=questions_json
# # # # # #         )
# # # # # #         db.add(db_interview)
# # # # # #         db.commit()
        
# # # # # #         send_exit_interview_email(db_employee.email, db_employee.name, form_link)
        
# # # # # #         return db_employee
# # # # # #     except HTTPException:
# # # # # #         raise
# # # # # #     except Exception as e:
# # # # # #         db.rollback()
# # # # # #         raise HTTPException(status_code=500, detail=str(e))

# # # # # # @app.get("/api/employees", response_model=List[EmployeeResponse])
# # # # # # def list_employees(db: Session = Depends(get_db)):
# # # # # #     return db.query(Employee).all()

# # # # # # @app.get("/api/interviews/token/{token}")
# # # # # # def get_interview_by_token(token: str, db: Session = Depends(get_db)):
# # # # # #     interview = db.query(ExitInterview).filter(ExitInterview.form_token == token).first()
# # # # # #     if not interview:
# # # # # #         raise HTTPException(status_code=404, detail="Invalid token")
# # # # # #     if interview.completed:
# # # # # #         raise HTTPException(status_code=400, detail="Interview already completed")
    
# # # # # #     questions = json.loads(interview.questions_json)
# # # # # #     return {
# # # # # #         "interview_id": interview.id,
# # # # # #         "employee_name": interview.employee.name,
# # # # # #         "employee_department": interview.employee.department,
# # # # # #         "questions": questions,
# # # # # #         "total_questions": len(questions),
# # # # # #         "completed": interview.completed
# # # # # #     }

# # # # # # @app.websocket("/ws/interview/{token}")
# # # # # # async def websocket_interview(websocket: WebSocket, token: str):
# # # # # #     await websocket.accept()
    
# # # # # #     db = SessionLocal()
# # # # # #     session_id = str(uuid.uuid4())
# # # # # #     nova_client = None
    
# # # # # #     try:
# # # # # #         interview = db.query(ExitInterview).filter(ExitInterview.form_token == token).first()
# # # # # #         if not interview:
# # # # # #             await websocket.send_json({"type": "error", "message": "Invalid token"})
# # # # # #             return
        
# # # # # #         questions = json.loads(interview.questions_json)
# # # # # #         employee_name = interview.employee.name
        
# # # # # #         print(f"\n{'='*70}")
# # # # # #         print(f"🎙️ NEW INTERVIEW: {employee_name}")
# # # # # #         print(f"📋 Questions: {len(questions)}")
# # # # # #         print(f"{'='*70}\n")
        
# # # # # #         await websocket.send_json({
# # # # # #             "type": "session_start",
# # # # # #             "session_id": session_id,
# # # # # #             "employee_name": employee_name,
# # # # # #             "total_questions": len(questions)
# # # # # #         })
        
# # # # # #         nova_client = NovaInterviewClient(
# # # # # #             employee_name,
# # # # # #             questions,
# # # # # #             websocket,
# # # # # #             db,
# # # # # #             interview.id,
# # # # # #             os.getenv("AWS_REGION", "us-east-1")
# # # # # #         )
# # # # # #         await nova_client.start_session()
        
# # # # # #         await asyncio.sleep(2)
# # # # # #         await nova_client.start_audio_input()
        
# # # # # #         active_sessions[session_id] = nova_client
        
# # # # # #         timeout_seconds = 900  # 15 minutes = 900 seconds
# # # # # #         start_time = datetime.utcnow()
        
# # # # # #         while nova_client.is_active:
# # # # # #             try:
# # # # # #                 message = await asyncio.wait_for(websocket.receive_json(), timeout=0.5)
# # # # # #                 start_time = datetime.utcnow()
                
# # # # # #                 if message['type'] == 'audio_chunk':
# # # # # #                     audio_data = base64.b64decode(message['data'])
# # # # # #                     await nova_client.send_audio_chunk(audio_data)
                
# # # # # #                 elif message['type'] == 'close':
# # # # # #                     break
            
# # # # # #             except asyncio.TimeoutError:
# # # # # #                 elapsed = (datetime.utcnow() - start_time).total_seconds()
# # # # # #                 if elapsed > timeout_seconds:
# # # # # #                     print(f"⚠️ Interview timeout after {timeout_seconds}s")
# # # # # #                     break
# # # # # #                 continue
# # # # # #             except WebSocketDisconnect:
# # # # # #                 print("⚠️ Client disconnected")
# # # # # #                 break
# # # # # #             except Exception as e:
# # # # # #                 print(f"⚠️ Error: {e}")
# # # # # #                 break
    
# # # # # #     except Exception as e:
# # # # # #         print(f"❌ Error: {e}")
# # # # # #         traceback.print_exc()
# # # # # #         try:
# # # # # #             await websocket.send_json({"type": "error", "message": str(e)})
# # # # # #         except:
# # # # # #             pass
# # # # # #     finally:
# # # # # #         if nova_client:
# # # # # #             await nova_client.end_session()
# # # # # #         if session_id in active_sessions:
# # # # # #             del active_sessions[session_id]
# # # # # #         db.close()

# # # # # # @app.get("/api/interviews/{interview_id}/responses", response_model=List[InterviewResponseDetail])
# # # # # # def get_interview_responses(interview_id: int, db: Session = Depends(get_db)):
# # # # # #     return db.query(InterviewResponse).filter(InterviewResponse.interview_id == interview_id).all()

# # # # # # @app.get("/api/stats")
# # # # # # def get_statistics(db: Session = Depends(get_db)):
# # # # # #     total = db.query(Employee).count()
# # # # # #     completed = db.query(ExitInterview).filter(ExitInterview.completed == True).count()
# # # # # #     return {
# # # # # #         "total_resignations": total,
# # # # # #         "completed_interviews": completed,
# # # # # #         "pending_interviews": total - completed,
# # # # # #         "completion_rate": (completed / total * 100) if total > 0 else 0
# # # # # #     }

# # # # # # def init_db():
# # # # # #     Base.metadata.create_all(bind=engine)
# # # # # #     print("✅ Database initialized!")

# # # # # # if __name__ == "__main__":
# # # # # #     init_db()
# # # # # #     import uvicorn
# # # # # #     print("\n🚀 Nova Sonic Exit Interview API v5.2")
# # # # # #     print("📡 http://0.0.0.0:8000\n")
# # # # # #     uvicorn.run(app, host="0.0.0.0", port=8000)


# # # # # """
# # # # # FIXED Nova Sonic Exit Interview Backend - PROPER Q&A RESPONSE HANDLING & AUDIO QUALITY
# # # # # Fixed: Response mismatch, audio dropping, proper question-answer pairing
# # # # # """

# # # # # from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
# # # # # from fastapi.middleware.cors import CORSMiddleware
# # # # # from sqlalchemy import create_engine, Column, Integer, String, Boolean, Date, DateTime, Text, ForeignKey
# # # # # from sqlalchemy.ext.declarative import declarative_base
# # # # # from sqlalchemy.orm import sessionmaker, Session, relationship
# # # # # from pydantic import BaseModel, EmailStr, field_validator
# # # # # from typing import List, Optional, Dict, Any
# # # # # from datetime import datetime, date
# # # # # import os
# # # # # from dotenv import load_dotenv
# # # # # import boto3
# # # # # import uuid
# # # # # import json
# # # # # import asyncio
# # # # # import base64
# # # # # import traceback

# # # # # from aws_sdk_bedrock_runtime.client import BedrockRuntimeClient, InvokeModelWithBidirectionalStreamOperationInput
# # # # # from aws_sdk_bedrock_runtime.models import InvokeModelWithBidirectionalStreamInputChunk, BidirectionalInputPayloadPart
# # # # # from aws_sdk_bedrock_runtime.config import Config
# # # # # from smithy_aws_core.identity.environment import EnvironmentCredentialsResolver

# # # # # load_dotenv()

# # # # # # ==================== DATABASE SETUP ====================
# # # # # DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

# # # # # engine = create_engine(DATABASE_URL)
# # # # # SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# # # # # Base = declarative_base()

# # # # # # ==================== DATABASE MODELS ====================
# # # # # class Employee(Base):
# # # # #     __tablename__ = "employees"
    
# # # # #     id = Column(Integer, primary_key=True, index=True)
# # # # #     name = Column(String(100), nullable=False)
# # # # #     email = Column(String(100), unique=True, nullable=False)
# # # # #     department = Column(String(50))
# # # # #     last_working_date = Column(Date)
# # # # #     status = Column(String(20), default="Resigned")
# # # # #     created_at = Column(DateTime, default=datetime.utcnow)
    
# # # # #     exit_interview = relationship("ExitInterview", back_populates="employee", uselist=False)

# # # # # class ExitInterview(Base):
# # # # #     __tablename__ = "exit_interviews"
    
# # # # #     id = Column(Integer, primary_key=True, index=True)
# # # # #     employee_id = Column(Integer, ForeignKey("employees.id"))
# # # # #     form_token = Column(String(255), unique=True, nullable=False)
# # # # #     completed = Column(Boolean, default=False)
# # # # #     questions_json = Column(Text)
# # # # #     created_at = Column(DateTime, default=datetime.utcnow)
    
# # # # #     employee = relationship("Employee", back_populates="exit_interview")
# # # # #     responses = relationship("InterviewResponse", back_populates="interview")

# # # # # class InterviewResponse(Base):
# # # # #     __tablename__ = "interview_responses"
    
# # # # #     id = Column(Integer, primary_key=True, index=True)
# # # # #     interview_id = Column(Integer, ForeignKey("exit_interviews.id"))
# # # # #     question = Column(Text, nullable=False)
# # # # #     answer = Column(Text, nullable=False)
# # # # #     created_at = Column(DateTime, default=datetime.utcnow)
    
# # # # #     interview = relationship("ExitInterview", back_populates="responses")

# # # # # # ==================== PYDANTIC SCHEMAS ====================
# # # # # class EmployeeCreate(BaseModel):
# # # # #     name: str
# # # # #     email: EmailStr
# # # # #     department: str
# # # # #     last_working_date: date
# # # # #     questions: Optional[List[str]] = None
    
# # # # #     @field_validator('name')
# # # # #     def name_must_not_be_empty(cls, v):
# # # # #         if not v or not v.strip():
# # # # #             raise ValueError('Name cannot be empty')
# # # # #         return v.strip()

# # # # # class EmployeeResponse(BaseModel):
# # # # #     id: int
# # # # #     name: str
# # # # #     email: str
# # # # #     department: str
# # # # #     last_working_date: date
# # # # #     status: str
# # # # #     created_at: datetime
    
# # # # #     class Config:
# # # # #         from_attributes = True

# # # # # class InterviewResponseDetail(BaseModel):
# # # # #     id: int
# # # # #     question_index: int
# # # # #     question: str
# # # # #     answer: str
# # # # #     created_at: datetime
    
# # # # #     class Config:
# # # # #         from_attributes = True

# # # # # # ==================== BEDROCK ANSWER CLEANING ====================
# # # # # def clean_answer_with_bedrock(raw_answer: str, question: str) -> str:
# # # # #     """Clean answer using Bedrock - removes filler, greetings, etc."""
# # # # #     try:
# # # # #         if not raw_answer or len(raw_answer.strip()) < 2:
# # # # #             return raw_answer.strip()
        
# # # # #         bedrock = boto3.client('bedrock-runtime', region_name=os.getenv("AWS_REGION", "us-east-1"))
        
# # # # #         prompt = f"""Extract the meaningful answer from this speech transcription. Remove greetings, filler words, and conversational noise.

# # # # # Question: {question}
# # # # # Raw Answer: {raw_answer}

# # # # # Return ONLY the cleaned answer, nothing else:"""

# # # # #         body = json.dumps({
# # # # #             "inputText": prompt,
# # # # #             "textGenerationConfig": {
# # # # #                 "maxTokenCount": 100,
# # # # #                 "temperature": 0.1,
# # # # #                 "topP": 0.9
# # # # #             }
# # # # #         })
        
# # # # #         response = bedrock.invoke_model(
# # # # #             body=body,
# # # # #             modelId="us.anthropic.claude-3-5-haiku-20241022-v1:0",
# # # # #             accept="application/json",
# # # # #             contentType="application/json"
# # # # #         )
        
# # # # #         response_body = json.loads(response.get('body').read())
# # # # #         cleaned = response_body.get('results', [{}])[0].get('outputText', '').strip()
        
# # # # #         return cleaned if cleaned else raw_answer.strip()
    
# # # # #     except Exception as e:
# # # # #         print(f"⚠️ Bedrock error: {e} - using raw answer")
# # # # #         return raw_answer.strip()

# # # # # # ==================== NOVA SONIC CLIENT ====================
# # # # # class NovaInterviewClient:
# # # # #     def __init__(self, employee_name: str, questions: List[str], websocket: WebSocket, db: Session, interview_id: int, region='us-east-1'):
# # # # #         self.model_id = 'amazon.nova-sonic-v1:0'
# # # # #         self.region = region
# # # # #         self.employee_name = employee_name
# # # # #         self.questions = questions
# # # # #         self.websocket = websocket
# # # # #         self.db = db
# # # # #         self.interview_id = interview_id
# # # # #         self.client = None
# # # # #         self.stream = None
# # # # #         self.is_active = False
        
# # # # #         self.prompt_name = str(uuid.uuid4())
# # # # #         self.system_content_name = str(uuid.uuid4())
# # # # #         self.audio_content_name = str(uuid.uuid4())
        
# # # # #         # ===== CRITICAL FIX: Proper state tracking =====
# # # # #         self.current_q_idx = -1  # Start at -1 before first question
# # # # #         self.user_answer_buffer = ""
# # # # #         self.nova_question_asked = False  # Track if Nova just asked a question
# # # # #         self.saved_responses = set()  # Track saved question indices
# # # # #         self.last_nova_text = ""  # Track last Nova message
# # # # #         self.accumulating_transcription = False  # Track if we're collecting user response
# # # # #         self.question_detection_cooldown = False  # Prevent duplicate detections
    
# # # # #     def _initialize_client(self):
# # # # #         """Initialize Bedrock client"""
# # # # #         resolver = EnvironmentCredentialsResolver()
# # # # #         config = Config(
# # # # #             endpoint_uri=f"https://bedrock-runtime.{self.region}.amazonaws.com",
# # # # #             region=self.region,
# # # # #             aws_credentials_identity_resolver=resolver
# # # # #         )
# # # # #         self.client = BedrockRuntimeClient(config=config)
# # # # #         print("✅ Bedrock client initialized")
    
# # # # #     async def send_event(self, event_json):
# # # # #         """Send event to stream"""
# # # # #         event = InvokeModelWithBidirectionalStreamInputChunk(
# # # # #             value=BidirectionalInputPayloadPart(bytes_=event_json.encode('utf-8'))
# # # # #         )
# # # # #         await self.stream.input_stream.send(event)
    
# # # # #     async def start_session(self):
# # # # #         """Start Nova Sonic session"""
# # # # #         if not self.client:
# # # # #             self._initialize_client()
        
# # # # #         try:
# # # # #             print("📡 Starting bidirectional stream...")
# # # # #             self.stream = await self.client.invoke_model_with_bidirectional_stream(
# # # # #                 InvokeModelWithBidirectionalStreamOperationInput(model_id=self.model_id)
# # # # #             )
# # # # #             self.is_active = True
# # # # #             print("✅ Stream started")
            
# # # # #             # Session start
# # # # #             await self.send_event(json.dumps({
# # # # #                 "event": {
# # # # #                     "sessionStart": {
# # # # #                         "inferenceConfiguration": {
# # # # #                             "maxTokens": 1024,
# # # # #                             "topP": 0.9,
# # # # #                             "temperature": 0.7
# # # # #                         }
# # # # #                     }
# # # # #                 }
# # # # #             }))
            
# # # # #             # Prompt start with AUDIO OUTPUT
# # # # #             await self.send_event(json.dumps({
# # # # #                 "event": {
# # # # #                     "promptStart": {
# # # # #                         "promptName": self.prompt_name,
# # # # #                         "textOutputConfiguration": {
# # # # #                             "mediaType": "text/plain"
# # # # #                         },
# # # # #                         "audioOutputConfiguration": {
# # # # #                             "mediaType": "audio/lpcm",
# # # # #                             "sampleRateHertz": 24000,
# # # # #                             "sampleSizeBits": 16,
# # # # #                             "channelCount": 1,
# # # # #                             "voiceId": "matthew",
# # # # #                             "encoding": "base64",
# # # # #                             "audioType": "SPEECH"
# # # # #                         }
# # # # #                     }
# # # # #                 }
# # # # #             }))
            
# # # # #             # System content
# # # # #             await self.send_event(json.dumps({
# # # # #                 "event": {
# # # # #                     "contentStart": {
# # # # #                         "promptName": self.prompt_name,
# # # # #                         "contentName": self.system_content_name,
# # # # #                         "type": "TEXT",
# # # # #                         "interactive": False,
# # # # #                         "role": "SYSTEM",
# # # # #                         "textInputConfiguration": {
# # # # #                             "mediaType": "text/plain"
# # # # #                         }
# # # # #                     }
# # # # #                 }
# # # # #             }))
            
# # # # #             questions_text = "\n".join([f"Q{i+1}: {q}" for i, q in enumerate(self.questions)])
            
# # # # #             system_text = f"""You are Nova conducting an EXIT INTERVIEW with {self.employee_name}.

# # # # # STRICT INSTRUCTIONS:
# # # # # 1. Ask EXACTLY {len(self.questions)} questions
# # # # # 2. Ask questions ONE AT A TIME in the exact order below
# # # # # 3. WAIT for the user to give a COMPLETE answer before moving to next question
# # # # # 4. After getting answer to Q{len(self.questions)}, say: "Thank you for completing the exit interview. Goodbye."
# # # # # 5. Do NOT ask follow-up questions - just acknowledge and move on

# # # # # QUESTIONS (ASK IN THIS ORDER):
# # # # # {questions_text}

# # # # # IMPORTANT: Do not deviate from these questions. Ask them sequentially."""

# # # # #             await self.send_event(json.dumps({
# # # # #                 "event": {
# # # # #                     "textInput": {
# # # # #                         "promptName": self.prompt_name,
# # # # #                         "contentName": self.system_content_name,
# # # # #                         "content": system_text
# # # # #                     }
# # # # #                 }
# # # # #             }))
            
# # # # #             await self.send_event(json.dumps({
# # # # #                 "event": {
# # # # #                     "contentEnd": {
# # # # #                         "promptName": self.prompt_name,
# # # # #                         "contentName": self.system_content_name
# # # # #                     }
# # # # #                 }
# # # # #             }))
            
# # # # #             print("✅ System prompt sent")
# # # # #             asyncio.create_task(self._process_responses())
        
# # # # #         except Exception as e:
# # # # #             print(f"❌ Error starting session: {e}")
# # # # #             traceback.print_exc()
# # # # #             raise
    
# # # # #     async def start_audio_input(self):
# # # # #         """Start audio input"""
# # # # #         await self.send_event(json.dumps({
# # # # #             "event": {
# # # # #                 "contentStart": {
# # # # #                     "promptName": self.prompt_name,
# # # # #                     "contentName": self.audio_content_name,
# # # # #                     "type": "AUDIO",
# # # # #                     "interactive": True,
# # # # #                     "role": "USER",
# # # # #                     "audioInputConfiguration": {
# # # # #                         "mediaType": "audio/lpcm",
# # # # #                         "sampleRateHertz": 16000,
# # # # #                         "sampleSizeBits": 16,
# # # # #                         "channelCount": 1,
# # # # #                         "audioType": "SPEECH",
# # # # #                         "encoding": "base64"
# # # # #                     }
# # # # #                 }
# # # # #             }
# # # # #         }))
# # # # #         print("✅ Audio input started")
    
# # # # #     async def send_audio_chunk(self, audio_bytes):
# # # # #         """Send audio chunk"""
# # # # #         if not self.is_active:
# # # # #             return
        
# # # # #         blob = base64.b64encode(audio_bytes).decode('utf-8')
# # # # #         try:
# # # # #             await self.send_event(json.dumps({
# # # # #                 "event": {
# # # # #                     "audioInput": {
# # # # #                         "promptName": self.prompt_name,
# # # # #                         "contentName": self.audio_content_name,
# # # # #                         "content": blob
# # # # #                     }
# # # # #                 }
# # # # #             }))
# # # # #         except Exception as e:
# # # # #             print(f"⚠️ Error sending audio: {e}")
    
# # # # #     async def _save_response_to_db(self, q_idx: int, question: str, raw_answer: str):
# # # # #         """Save response to database with proper validation"""
# # # # #         try:
# # # # #             # Prevent duplicate saves
# # # # #             if q_idx in self.saved_responses:
# # # # #                 print(f"⚠️ Q{q_idx + 1} already saved - skipping duplicate")
# # # # #                 return False
            
# # # # #             # Validate answer
# # # # #             if not raw_answer or len(raw_answer.strip()) < 3:
# # # # #                 print(f"⚠️ Answer too short, skipping: '{raw_answer}'")
# # # # #                 return False
            
# # # # #             # Check if answer looks like Nova speaking (not user answer)
# # # # #             nova_indicators = [
# # # # #                 "i see", "that's good", "thank you", "great to hear", "wonderful",
# # # # #                 "i'm glad", "i appreciate", "understood", "moving on", "let's",
# # # # #                 "now let's", "absolutely", "sure thing", "indeed"
# # # # #             ]
            
# # # # #             answer_lower = raw_answer.lower()
# # # # #             if any(indicator in answer_lower for indicator in nova_indicators):
# # # # #                 print(f"⚠️ Answer looks like Nova speaking: '{raw_answer}'")
# # # # #                 return False
            
# # # # #             print(f"\n{'='*80}")
# # # # #             print(f"💾 SAVING RESPONSE Q{q_idx + 1}/{len(self.questions)}")
# # # # #             print(f"{'='*80}")
# # # # #             print(f"Question: {question}")
# # # # #             print(f"Raw Answer: {raw_answer[:100]}...")
            
# # # # #             # Clean with Bedrock
# # # # #             cleaned_answer = clean_answer_with_bedrock(raw_answer, question)
# # # # #             print(f"Cleaned Answer: {cleaned_answer[:100]}...")
            
# # # # #             # Save to DB - NO question_index field
# # # # #             db_response = InterviewResponse(
# # # # #                 interview_id=self.interview_id,
# # # # #                 question=question,
# # # # #                 answer=cleaned_answer
# # # # #             )
# # # # #             self.db.add(db_response)
# # # # #             self.db.commit()
            
# # # # #             self.saved_responses.add(q_idx)
            
# # # # #             print(f"✅ Q{q_idx + 1} SAVED - Total: {len(self.saved_responses)}/{len(self.questions)}")
# # # # #             print(f"{'='*80}\n")
            
# # # # #             # Notify frontend
# # # # #             await self.websocket.send_json({
# # # # #                 'type': 'response_saved',
# # # # #                 'q_index': q_idx,
# # # # #                 'question': question,
# # # # #                 'answer': cleaned_answer
# # # # #             })
            
# # # # #             return True
        
# # # # #         except Exception as e:
# # # # #             print(f"❌ Error saving to DB: {e}")
# # # # #             traceback.print_exc()
# # # # #             # Rollback on error to fix transaction state
# # # # #             try:
# # # # #                 self.db.rollback()
# # # # #             except:
# # # # #                 pass
# # # # #             return False
    
# # # # #     def _is_nova_asking_question(self, text: str) -> bool:
# # # # #         """Detect if Nova is asking a question (contains ?)"""
# # # # #         return '?' in text and len(text) > 10
    
# # # # #     async def _process_responses(self):
# # # # #         """Process responses from Nova"""
# # # # #         try:
# # # # #             while self.is_active:
# # # # #                 try:
# # # # #                     output = await self.stream.await_output()
# # # # #                     result = await output[1].receive()
                    
# # # # #                     if not result.value or not result.value.bytes_:
# # # # #                         continue
                    
# # # # #                     response_data = result.value.bytes_.decode('utf-8')
# # # # #                     json_data = json.loads(response_data)
                    
# # # # #                     if 'event' not in json_data:
# # # # #                         continue
                    
# # # # #                     event = json_data['event']
                    
# # # # #                     # ============ TEXT OUTPUT ============
# # # # #                     if 'textOutput' in event:
# # # # #                         text = event['textOutput'].get('content', '')
# # # # #                         role = event['textOutput'].get('role', 'ASSISTANT')
                        
# # # # #                         if role == "ASSISTANT" and text.strip():
# # # # #                             print(f"🤖 Nova: {text[:150]}...")
                            
# # # # #                             # Send to frontend
# # # # #                             await self.websocket.send_json({
# # # # #                                 'type': 'text',
# # # # #                                 'content': text,
# # # # #                                 'role': 'ASSISTANT'
# # # # #                             })
                            
# # # # #                             # Check if Nova asked a NEW question (not a repeat)
# # # # #                             if self._is_nova_asking_question(text) and text != self.last_nova_text:
# # # # #                                 self.last_nova_text = text
                                
# # # # #                                 # Save previous answer if exists
# # # # #                                 if self.current_q_idx >= 0 and self.user_answer_buffer.strip():
# # # # #                                     if self.current_q_idx not in self.saved_responses:
# # # # #                                         question = self.questions[self.current_q_idx]
# # # # #                                         answer = self.user_answer_buffer.strip()
                                        
# # # # #                                         print(f"\n🔔 NEW QUESTION - Saving Q{self.current_q_idx + 1}")
# # # # #                                         await self._save_response_to_db(self.current_q_idx, question, answer)
                                
# # # # #                                 # Move to next question ONLY if we haven't already
# # # # #                                 if self.current_q_idx + 1 < len(self.questions):
# # # # #                                     self.current_q_idx += 1
# # # # #                                     self.user_answer_buffer = ""
# # # # #                                     self.accumulating_transcription = True
# # # # #                                     print(f"❓ Q{self.current_q_idx + 1}: Waiting for answer...")
                            
# # # # #                             # Check if goodbye
# # # # #                             if "goodbye" in text.lower():
# # # # #                                 print(f"\n✅✅✅ NOVA SAID GOODBYE ✅✅✅")
                                
# # # # #                                 # Save last answer
# # # # #                                 if self.current_q_idx >= 0 and self.user_answer_buffer.strip():
# # # # #                                     if self.current_q_idx not in self.saved_responses:
# # # # #                                         question = self.questions[self.current_q_idx]
# # # # #                                         answer = self.user_answer_buffer.strip()
# # # # #                                         await self._save_response_to_db(self.current_q_idx, question, answer)
                                
# # # # #                                 await self._finalize_interview()
# # # # #                                 return
                        
# # # # #                         elif role == "USER" and self.accumulating_transcription and text.strip():
# # # # #                             # This is user's speech transcribed by Nova
# # # # #                             print(f"👤 User: {text[:80]}...")
                            
# # # # #                             # Only add if it's not a repeat
# # # # #                             if text != self.last_nova_text:
# # # # #                                 if self.user_answer_buffer:
# # # # #                                     self.user_answer_buffer += " "
# # # # #                                 self.user_answer_buffer += text
                                
# # # # #                                 print(f"   [Buffer: {self.user_answer_buffer[:100]}...]")
                                
# # # # #                                 await self.websocket.send_json({
# # # # #                                     'type': 'text',
# # # # #                                     'content': text,
# # # # #                                     'role': 'USER'
# # # # #                                 })
                    
# # # # #                     # ============ AUDIO OUTPUT (HIGH QUALITY) ============
# # # # #                     elif 'audioOutput' in event:
# # # # #                         audio_content = event['audioOutput'].get('content', '')
# # # # #                         if audio_content:
# # # # #                             # Send audio directly without processing
# # # # #                             await self.websocket.send_json({
# # # # #                                 'type': 'audio',
# # # # #                                 'data': audio_content
# # # # #                             })
                    
# # # # #                     # ============ COMPLETION ============
# # # # #                     elif 'completionEnd' in event:
# # # # #                         print("✅ Stream completion ended")
# # # # #                         await self._finalize_interview()
# # # # #                         return
                
# # # # #                 except asyncio.TimeoutError:
# # # # #                     continue
# # # # #                 except Exception as e:
# # # # #                     print(f"⚠️ Error in response processing: {e}")
# # # # #                     traceback.print_exc()
# # # # #                     continue
        
# # # # #         except Exception as e:
# # # # #             print(f"❌ Fatal error: {e}")
# # # # #             traceback.print_exc()
# # # # #             self.is_active = False
    
# # # # #     async def _finalize_interview(self):
# # # # #         """Finalize interview"""
# # # # #         print(f"\n{'='*80}")
# # # # #         print(f"🎉 INTERVIEW FINALIZATION")
# # # # #         print(f"   Responses Saved: {len(self.saved_responses)}/{len(self.questions)}")
# # # # #         print(f"   Status: {'✅ COMPLETE' if len(self.saved_responses) == len(self.questions) else '⚠️ INCOMPLETE'}")
# # # # #         print(f"{'='*80}\n")
        
# # # # #         try:
# # # # #             interview = self.db.query(ExitInterview).filter(ExitInterview.id == self.interview_id).first()
# # # # #             if interview:
# # # # #                 interview.completed = True
# # # # #                 interview.employee.status = "Completed"
# # # # #                 self.db.commit()
# # # # #                 print("✅ DB marked as completed")
# # # # #         except Exception as e:
# # # # #             print(f"⚠️ DB update error: {e}")
        
# # # # #         try:
# # # # #             await self.websocket.send_json({
# # # # #                 'type': 'interview_complete',
# # # # #                 'questions_answered': len(self.saved_responses),
# # # # #                 'total_questions': len(self.questions)
# # # # #             })
# # # # #             print("✅ Completion message sent to frontend")
# # # # #         except Exception as e:
# # # # #             print(f"❌ Failed to send completion: {e}")
        
# # # # #         self.is_active = False
    
# # # # #     async def end_session(self):
# # # # #         """End session"""
# # # # #         if not self.is_active:
# # # # #             return
        
# # # # #         try:
# # # # #             await self.send_event(json.dumps({
# # # # #                 "event": {
# # # # #                     "contentEnd": {
# # # # #                         "promptName": self.prompt_name,
# # # # #                         "contentName": self.audio_content_name
# # # # #                     }
# # # # #                 }
# # # # #             }))
            
# # # # #             await self.send_event(json.dumps({
# # # # #                 "event": {
# # # # #                     "promptEnd": {
# # # # #                         "promptName": self.prompt_name
# # # # #                     }
# # # # #                 }
# # # # #             }))
            
# # # # #             await self.send_event(json.dumps({
# # # # #                 "event": {
# # # # #                     "sessionEnd": {}
# # # # #                 }
# # # # #             }))
            
# # # # #             await self.stream.input_stream.close()
# # # # #             self.is_active = False
# # # # #             print("✅ Session ended")
        
# # # # #         except Exception as e:
# # # # #             print(f"⚠️ Error ending session: {e}")
# # # # #             self.is_active = False

# # # # # # ==================== AWS SES ====================
# # # # # ses_client = boto3.client('ses', region_name=os.getenv("AWS_REGION", "us-east-1"))

# # # # # def send_exit_interview_email(employee_email: str, employee_name: str, form_link: str) -> bool:
# # # # #     SENDER = os.getenv("SES_SENDER_EMAIL")
# # # # #     SUBJECT = "🎙️ Voice Exit Interview with Nova"
# # # # #     BODY_HTML = f"""
# # # # #     <html><body>
# # # # #         <h1>Hello {employee_name}!</h1>
# # # # #         <p>Have a voice conversation with Nova for your exit interview.</p>
# # # # #         <p><a href="{form_link}">Start Voice Interview</a></p>
# # # # #     </body></html>
# # # # #     """
# # # # #     try:
# # # # #         ses_client.send_email(
# # # # #             Source=SENDER,
# # # # #             Destination={'ToAddresses': [employee_email]},
# # # # #             Message={'Subject': {'Data': SUBJECT}, 'Body': {'Html': {'Data': BODY_HTML}}}
# # # # #         )
# # # # #         print(f"✅ Email sent to {employee_name}")
# # # # #         return True
# # # # #     except Exception as e:
# # # # #         print(f"❌ Email error: {e}")
# # # # #         return False

# # # # # def generate_unique_token() -> str:
# # # # #     return str(uuid.uuid4())

# # # # # def create_form_link(token: str) -> str:
# # # # #     return f"{os.getenv('APP_URL', 'http://localhost:8501')}/exit_interview?token={token}"

# # # # # # ==================== FASTAPI APP ====================
# # # # # app = FastAPI(title="Nova Sonic Exit Interview API", version="6.0.0")

# # # # # app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# # # # # def get_db():
# # # # #     db = SessionLocal()
# # # # #     try:
# # # # #         yield db
# # # # #     finally:
# # # # #         db.close()

# # # # # active_sessions: Dict[str, NovaInterviewClient] = {}

# # # # # # ==================== API ENDPOINTS ====================

# # # # # @app.get("/")
# # # # # def root():
# # # # #     return {"message": "Nova Sonic Exit Interview API", "version": "6.0.0", "status": "running"}

# # # # # @app.post("/api/employees", response_model=EmployeeResponse, status_code=201)
# # # # # def create_employee(employee: EmployeeCreate, db: Session = Depends(get_db)):
# # # # #     try:
# # # # #         existing = db.query(Employee).filter(Employee.email == employee.email).first()
# # # # #         if existing:
# # # # #             raise HTTPException(status_code=400, detail="Employee already exists")
        
# # # # #         db_employee = Employee(
# # # # #             name=employee.name,
# # # # #             email=employee.email,
# # # # #             department=employee.department,
# # # # #             last_working_date=employee.last_working_date,
# # # # #             status="Resigned"
# # # # #         )
# # # # #         db.add(db_employee)
# # # # #         db.commit()
# # # # #         db.refresh(db_employee)
        
# # # # #         token = generate_unique_token()
# # # # #         form_link = create_form_link(token)
        
# # # # #         questions_json = json.dumps(employee.questions) if employee.questions else json.dumps([
# # # # #             # "What was your primary reason for leaving?",
# # # # #             # "How would you rate your overall experience with the company on a scale of 1 to 5?",
# # # # #             # "How was your relationship with your manager?",
# # # # #             # "Did you feel valued and recognized in your role?",
# # # # #             # "Would you recommend our company to others? Why or why not?"
# # # # #         ])
        
# # # # #         db_interview = ExitInterview(
# # # # #             employee_id=db_employee.id,
# # # # #             form_token=token,
# # # # #             completed=False,
# # # # #             questions_json=questions_json
# # # # #         )
# # # # #         db.add(db_interview)
# # # # #         db.commit()
        
# # # # #         send_exit_interview_email(db_employee.email, db_employee.name, form_link)
        
# # # # #         return db_employee
# # # # #     except HTTPException:
# # # # #         raise
# # # # #     except Exception as e:
# # # # #         db.rollback()
# # # # #         raise HTTPException(status_code=500, detail=str(e))

# # # # # @app.get("/api/employees", response_model=List[EmployeeResponse])
# # # # # def list_employees(db: Session = Depends(get_db)):
# # # # #     return db.query(Employee).all()

# # # # # @app.get("/api/interviews/token/{token}")
# # # # # def get_interview_by_token(token: str, db: Session = Depends(get_db)):
# # # # #     interview = db.query(ExitInterview).filter(ExitInterview.form_token == token).first()
# # # # #     if not interview:
# # # # #         raise HTTPException(status_code=404, detail="Invalid token")
# # # # #     if interview.completed:
# # # # #         raise HTTPException(status_code=400, detail="Interview already completed")
    
# # # # #     questions = json.loads(interview.questions_json)
# # # # #     return {
# # # # #         "interview_id": interview.id,
# # # # #         "employee_name": interview.employee.name,
# # # # #         "employee_department": interview.employee.department,
# # # # #         "questions": questions,
# # # # #         "total_questions": len(questions),
# # # # #         "completed": interview.completed
# # # # #     }

# # # # # @app.websocket("/ws/interview/{token}")
# # # # # async def websocket_interview(websocket: WebSocket, token: str):
# # # # #     await websocket.accept()
    
# # # # #     db = SessionLocal()
# # # # #     session_id = str(uuid.uuid4())
# # # # #     nova_client = None
    
# # # # #     try:
# # # # #         interview = db.query(ExitInterview).filter(ExitInterview.form_token == token).first()
# # # # #         if not interview:
# # # # #             await websocket.send_json({"type": "error", "message": "Invalid token"})
# # # # #             return
        
# # # # #         questions = json.loads(interview.questions_json)
# # # # #         employee_name = interview.employee.name
        
# # # # #         print(f"\n{'='*80}")
# # # # #         print(f"🎙️ NEW INTERVIEW: {employee_name}")
# # # # #         print(f"📋 Questions: {len(questions)}")
# # # # #         print(f"{'='*80}\n")
        
# # # # #         await websocket.send_json({
# # # # #             "type": "session_start",
# # # # #             "session_id": session_id,
# # # # #             "employee_name": employee_name,
# # # # #             "total_questions": len(questions)
# # # # #         })
        
# # # # #         nova_client = NovaInterviewClient(
# # # # #             employee_name,
# # # # #             questions,
# # # # #             websocket,
# # # # #             db,
# # # # #             interview.id,
# # # # #             os.getenv("AWS_REGION", "us-east-1")
# # # # #         )
# # # # #         await nova_client.start_session()
        
# # # # #         await asyncio.sleep(2)
# # # # #         await nova_client.start_audio_input()
        
# # # # #         active_sessions[session_id] = nova_client
        
# # # # #         timeout_seconds = 900  # 15 minutes
# # # # #         start_time = datetime.utcnow()
        
# # # # #         while nova_client.is_active:
# # # # #             try:
# # # # #                 message = await asyncio.wait_for(websocket.receive_json(), timeout=0.5)
# # # # #                 start_time = datetime.utcnow()
                
# # # # #                 if message['type'] == 'audio_chunk':
# # # # #                     audio_data = base64.b64decode(message['data'])
# # # # #                     await nova_client.send_audio_chunk(audio_data)
                
# # # # #                 elif message['type'] == 'close':
# # # # #                     break
            
# # # # #             except asyncio.TimeoutError:
# # # # #                 elapsed = (datetime.utcnow() - start_time).total_seconds()
# # # # #                 if elapsed > timeout_seconds:
# # # # #                     print(f"⚠️ Interview timeout after {timeout_seconds}s")
# # # # #                     break
# # # # #                 continue
# # # # #             except WebSocketDisconnect:
# # # # #                 print("⚠️ Client disconnected")
# # # # #                 break
# # # # #             except Exception as e:
# # # # #                 print(f"⚠️ Error: {e}")
# # # # #                 break
    
# # # # #     except Exception as e:
# # # # #         print(f"❌ Error: {e}")
# # # # #         traceback.print_exc()
# # # # #         try:
# # # # #             await websocket.send_json({"type": "error", "message": str(e)})
# # # # #         except:
# # # # #             pass
# # # # #     finally:
# # # # #         if nova_client:
# # # # #             await nova_client.end_session()
# # # # #         if session_id in active_sessions:
# # # # #             del active_sessions[session_id]
# # # # #         db.close()

# # # # # @app.get("/api/interviews/{interview_id}/responses", response_model=List[InterviewResponseDetail])
# # # # # def get_interview_responses(interview_id: int, db: Session = Depends(get_db)):
# # # # #     """Get responses ordered by creation time"""
# # # # #     return db.query(InterviewResponse).filter(
# # # # #         InterviewResponse.interview_id == interview_id
# # # # #     ).order_by(InterviewResponse.created_at).all()

# # # # # @app.get("/api/stats")
# # # # # def get_statistics(db: Session = Depends(get_db)):
# # # # #     total = db.query(Employee).count()
# # # # #     completed = db.query(ExitInterview).filter(ExitInterview.completed == True).count()
# # # # #     return {
# # # # #         "total_resignations": total,
# # # # #         "completed_interviews": completed,
# # # # #         "pending_interviews": total - completed,
# # # # #         "completion_rate": (completed / total * 100) if total > 0 else 0
# # # # #     }

# # # # # def init_db():
# # # # #     Base.metadata.create_all(bind=engine)
# # # # #     print("✅ Database initialized!")

# # # # # if __name__ == "__main__":
# # # # #     init_db()
# # # # #     import uvicorn
# # # # #     print("\n🚀 Nova Sonic Exit Interview API v6.0.0")
# # # # #     print("📡 http://0.0.0.0:8000\n")
# # # # #     uvicorn.run(app, host="0.0.0.0", port=8000)




# # # # """
# # # # FIXED Nova Sonic Exit Interview Backend - PROPER Q&A RESPONSE HANDLING & AUDIO QUALITY
# # # # Fixed: Response mismatch, audio dropping, proper question-answer pairing, repetition handling
# # # # """

# # # # from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
# # # # from fastapi.middleware.cors import CORSMiddleware
# # # # from sqlalchemy import create_engine, Column, Integer, String, Boolean, Date, DateTime, Text, ForeignKey
# # # # from sqlalchemy.ext.declarative import declarative_base
# # # # from sqlalchemy.orm import sessionmaker, Session, relationship
# # # # from pydantic import BaseModel, EmailStr, field_validator
# # # # from typing import List, Optional, Dict, Any
# # # # from datetime import datetime, date
# # # # import os
# # # # from dotenv import load_dotenv
# # # # import boto3
# # # # import uuid
# # # # import json
# # # # import asyncio
# # # # import base64
# # # # import traceback

# # # # from aws_sdk_bedrock_runtime.client import BedrockRuntimeClient, InvokeModelWithBidirectionalStreamOperationInput
# # # # from aws_sdk_bedrock_runtime.models import InvokeModelWithBidirectionalStreamInputChunk, BidirectionalInputPayloadPart
# # # # from aws_sdk_bedrock_runtime.config import Config
# # # # from smithy_aws_core.identity.environment import EnvironmentCredentialsResolver

# # # # load_dotenv()

# # # # # ==================== DATABASE SETUP ====================
# # # # DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

# # # # engine = create_engine(DATABASE_URL)
# # # # SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# # # # Base = declarative_base()

# # # # # ==================== DATABASE MODELS ====================
# # # # class Employee(Base):
# # # #     __tablename__ = "employees"
    
# # # #     id = Column(Integer, primary_key=True, index=True)
# # # #     name = Column(String(100), nullable=False)
# # # #     email = Column(String(100), unique=True, nullable=False)
# # # #     department = Column(String(50))
# # # #     last_working_date = Column(Date)
# # # #     status = Column(String(20), default="Resigned")
# # # #     created_at = Column(DateTime, default=datetime.utcnow)
    
# # # #     exit_interview = relationship("ExitInterview", back_populates="employee", uselist=False)

# # # # class ExitInterview(Base):
# # # #     __tablename__ = "exit_interviews"
    
# # # #     id = Column(Integer, primary_key=True, index=True)
# # # #     employee_id = Column(Integer, ForeignKey("employees.id"))
# # # #     form_token = Column(String(255), unique=True, nullable=False)
# # # #     completed = Column(Boolean, default=False)
# # # #     questions_json = Column(Text)
# # # #     created_at = Column(DateTime, default=datetime.utcnow)
    
# # # #     employee = relationship("Employee", back_populates="exit_interview")
# # # #     responses = relationship("InterviewResponse", back_populates="interview")

# # # # class InterviewResponse(Base):
# # # #     __tablename__ = "interview_responses"
    
# # # #     id = Column(Integer, primary_key=True, index=True)
# # # #     interview_id = Column(Integer, ForeignKey("exit_interviews.id"))
# # # #     question = Column(Text, nullable=False)
# # # #     answer = Column(Text, nullable=False)
# # # #     created_at = Column(DateTime, default=datetime.utcnow)
    
# # # #     interview = relationship("ExitInterview", back_populates="responses")

# # # # # ==================== PYDANTIC SCHEMAS ====================
# # # # class EmployeeCreate(BaseModel):
# # # #     name: str
# # # #     email: EmailStr
# # # #     department: str
# # # #     last_working_date: date
# # # #     questions: Optional[List[str]] = None
    
# # # #     @field_validator('name')
# # # #     def name_must_not_be_empty(cls, v):
# # # #         if not v or not v.strip():
# # # #             raise ValueError('Name cannot be empty')
# # # #         return v.strip()

# # # # class EmployeeResponse(BaseModel):
# # # #     id: int
# # # #     name: str
# # # #     email: str
# # # #     department: str
# # # #     last_working_date: date
# # # #     status: str
# # # #     created_at: datetime
    
# # # #     class Config:
# # # #         from_attributes = True

# # # # class InterviewResponseDetail(BaseModel):
# # # #     id: int
# # # #     question: str
# # # #     answer: str
# # # #     created_at: datetime
    
# # # #     class Config:
# # # #         from_attributes = True

# # # # # ==================== BEDROCK ANSWER CLEANING ====================
# # # # def clean_answer_with_bedrock(raw_answer: str, question: str) -> str:
# # # #     """Clean answer using Bedrock - removes filler, greetings, etc."""
# # # #     try:
# # # #         if not raw_answer or len(raw_answer.strip()) < 2:
# # # #             return raw_answer.strip()
        
# # # #         bedrock = boto3.client('bedrock-runtime', region_name=os.getenv("AWS_REGION", "us-east-1"))
        
# # # #         # FIXED: Using the correct format for Claude 3 Haiku
# # # #         prompt = f"""Extract the meaningful answer from this speech transcription. Remove greetings, filler words, and conversational noise.

# # # # Question: {question}
# # # # Raw Answer: {raw_answer}

# # # # Return ONLY the cleaned answer, nothing else:"""

# # # #         body = json.dumps({
# # # #             "anthropic_version": "bedrock-2023-05-31",
# # # #             "max_tokens": 100,
# # # #             "temperature": 0.1,
# # # #             "messages": [
# # # #                 {
# # # #                     "role": "user",
# # # #                     "content": prompt
# # # #                 }
# # # #             ]
# # # #         })
        
# # # #         response = bedrock.invoke_model(
# # # #             body=body,
# # # #             modelId="anthropic.claude-3-haiku-20240307-v1:0",
# # # #             accept="application/json",
# # # #             contentType="application/json"
# # # #         )
        
# # # #         response_body = json.loads(response.get('body').read())
# # # #         cleaned = response_body.get('content', [{}])[0].get('text', '').strip()
        
# # # #         return cleaned if cleaned else raw_answer.strip()
    
# # # #     except Exception as e:
# # # #         print(f"⚠️ Bedrock error: {e} - using raw answer")
# # # #         return raw_answer.strip()

# # # # # ==================== NOVA SONIC CLIENT ====================
# # # # class NovaInterviewClient:
# # # #     def __init__(self, employee_name: str, questions: List[str], websocket: WebSocket, db: Session, interview_id: int, region='us-east-1'):
# # # #         self.model_id = 'amazon.nova-sonic-v1:0'
# # # #         self.region = region
# # # #         self.employee_name = employee_name
# # # #         self.questions = questions
# # # #         self.websocket = websocket
# # # #         self.db = db
# # # #         self.interview_id = interview_id
# # # #         self.client = None
# # # #         self.stream = None
# # # #         self.is_active = False
        
# # # #         self.prompt_name = str(uuid.uuid4())
# # # #         self.system_content_name = str(uuid.uuid4())
# # # #         self.audio_content_name = str(uuid.uuid4())
        
# # # #         # ===== CRITICAL FIX: Enhanced state tracking =====
# # # #         self.current_q_idx = -1  # Start at -1 before first question
# # # #         self.user_answer_buffer = ""
# # # #         self.nova_question_asked = False  # Track if Nova just asked a question
# # # #         self.saved_responses = set()  # Track saved question indices
# # # #         self.last_nova_text = ""  # Track last Nova message
# # # #         self.accumulating_transcription = False  # Track if we're collecting user response
# # # #         self.question_detection_cooldown = False  # Prevent duplicate detections
# # # #         self.current_question_text = None  # Track the exact text of the current question
# # # #         self.waiting_for_answer = False  # Explicitly track if we're waiting for an answer
# # # #         self.last_question_processed = False  # Track if we've processed the last question
# # # #         self.question_in_progress = False  # Track if Nova is in the middle of asking a question
# # # #         self.question_parts = []  # Collect parts of a multi-part question
# # # #         self.non_answer_detected = False  # Track if we detected a non-answer response
        
# # # #         # Phrases that indicate user is not answering the question
# # # #         self.non_answer_phrases = [
# # # #             "sorry, repeat", "can you repeat", "repeat the question", 
# # # #             "i didn't hear", "what was the question", "could you say that again",
# # # #             "pardon", "excuse me", "i didn't understand", "sorry, i didn't get that",
# # # #             "can you say that again", "i missed that", "what did you say", "my voice is breaking",
# # # #             "your voice is breaking", "come again", "sorry come again", "voice not clear",
# # # #             "i can't hear", "i can't understand", "speak louder", "speak clearly",
# # # #             "uh come again", "sorry", "come again"
# # # #         ]
    
# # # #     def _initialize_client(self):
# # # #         """Initialize Bedrock client"""
# # # #         resolver = EnvironmentCredentialsResolver()
# # # #         config = Config(
# # # #             endpoint_uri=f"https://bedrock-runtime.{self.region}.amazonaws.com",
# # # #             region=self.region,
# # # #             aws_credentials_identity_resolver=resolver
# # # #         )
# # # #         self.client = BedrockRuntimeClient(config=config)
# # # #         print("✅ Bedrock client initialized")
    
# # # #     async def send_event(self, event_json):
# # # #         """Send event to stream"""
# # # #         event = InvokeModelWithBidirectionalStreamInputChunk(
# # # #             value=BidirectionalInputPayloadPart(bytes_=event_json.encode('utf-8'))
# # # #         )
# # # #         await self.stream.input_stream.send(event)
    
# # # #     async def start_session(self):
# # # #         """Start Nova Sonic session"""
# # # #         if not self.client:
# # # #             self._initialize_client()
        
# # # #         try:
# # # #             print("📡 Starting bidirectional stream...")
# # # #             self.stream = await self.client.invoke_model_with_bidirectional_stream(
# # # #                 InvokeModelWithBidirectionalStreamOperationInput(model_id=self.model_id)
# # # #             )
# # # #             self.is_active = True
# # # #             print("✅ Stream started")
            
# # # #             # Session start
# # # #             await self.send_event(json.dumps({
# # # #                 "event": {
# # # #                     "sessionStart": {
# # # #                         "inferenceConfiguration": {
# # # #                             "maxTokens": 1024,
# # # #                             "topP": 0.9,
# # # #                             "temperature": 0.7
# # # #                         }
# # # #                     }
# # # #                 }
# # # #             }))
            
# # # #             # Prompt start with AUDIO OUTPUT
# # # #             await self.send_event(json.dumps({
# # # #                 "event": {
# # # #                     "promptStart": {
# # # #                         "promptName": self.prompt_name,
# # # #                         "textOutputConfiguration": {
# # # #                             "mediaType": "text/plain"
# # # #                         },
# # # #                         "audioOutputConfiguration": {
# # # #                             "mediaType": "audio/lpcm",
# # # #                             "sampleRateHertz": 24000,
# # # #                             "sampleSizeBits": 16,
# # # #                             "channelCount": 1,
# # # #                             "voiceId": "matthew",
# # # #                             "encoding": "base64",
# # # #                             "audioType": "SPEECH"
# # # #                         }
# # # #                     }
# # # #                 }
# # # #             }))
            
# # # #             # System content
# # # #             await self.send_event(json.dumps({
# # # #                 "event": {
# # # #                     "contentStart": {
# # # #                         "promptName": self.prompt_name,
# # # #                         "contentName": self.system_content_name,
# # # #                         "type": "TEXT",
# # # #                         "interactive": False,
# # # #                         "role": "SYSTEM",
# # # #                         "textInputConfiguration": {
# # # #                             "mediaType": "text/plain"
# # # #                         }
# # # #                     }
# # # #                 }
# # # #             }))
            
# # # #             questions_text = "\n".join([f"Q{i+1}: {q}" for i, q in enumerate(self.questions)])
            
# # # #             system_text = f"""You are Nova conducting an EXIT INTERVIEW with {self.employee_name}.

# # # # STRICT INSTRUCTIONS:
# # # # 1. Ask EXACTLY {len(self.questions)} questions
# # # # 2. Ask questions ONE AT A TIME in the exact order below
# # # # 3. WAIT for the user to give a COMPLETE answer before moving to next question
# # # # 4. After getting answer to Q{len(self.questions)}, say: "Thank you for completing the exit interview. Goodbye."
# # # # 5. Do NOT ask follow-up questions - just acknowledge and move on
# # # # 6. If the user asks you to repeat a question, repeat the exact same question

# # # # QUESTIONS (ASK IN THIS ORDER):
# # # # {questions_text}

# # # # IMPORTANT: Do not deviate from these questions. Ask them sequentially."""

# # # #             await self.send_event(json.dumps({
# # # #                 "event": {
# # # #                     "textInput": {
# # # #                         "promptName": self.prompt_name,
# # # #                         "contentName": self.system_content_name,
# # # #                         "content": system_text
# # # #                     }
# # # #                 }
# # # #             }))
            
# # # #             await self.send_event(json.dumps({
# # # #                 "event": {
# # # #                     "contentEnd": {
# # # #                         "promptName": self.prompt_name,
# # # #                         "contentName": self.system_content_name
# # # #                     }
# # # #                 }
# # # #             }))
            
# # # #             print("✅ System prompt sent")
# # # #             asyncio.create_task(self._process_responses())
        
# # # #         except Exception as e:
# # # #             print(f"❌ Error starting session: {e}")
# # # #             traceback.print_exc()
# # # #             raise
    
# # # #     async def start_audio_input(self):
# # # #         """Start audio input"""
# # # #         await self.send_event(json.dumps({
# # # #             "event": {
# # # #                 "contentStart": {
# # # #                     "promptName": self.prompt_name,
# # # #                     "contentName": self.audio_content_name,
# # # #                     "type": "AUDIO",
# # # #                     "interactive": True,
# # # #                     "role": "USER",
# # # #                     "audioInputConfiguration": {
# # # #                         "mediaType": "audio/lpcm",
# # # #                         "sampleRateHertz": 16000,
# # # #                         "sampleSizeBits": 16,
# # # #                         "channelCount": 1,
# # # #                         "audioType": "SPEECH",
# # # #                         "encoding": "base64"
# # # #                     }
# # # #                 }
# # # #             }
# # # #         }))
# # # #         print("✅ Audio input started")
    
# # # #     async def send_audio_chunk(self, audio_bytes):
# # # #         """Send audio chunk"""
# # # #         if not self.is_active:
# # # #             return
        
# # # #         blob = base64.b64encode(audio_bytes).decode('utf-8')
# # # #         try:
# # # #             await self.send_event(json.dumps({
# # # #                 "event": {
# # # #                     "audioInput": {
# # # #                         "promptName": self.prompt_name,
# # # #                         "contentName": self.audio_content_name,
# # # #                         "content": blob
# # # #                     }
# # # #                 }
# # # #             }))
# # # #         except Exception as e:
# # # #             print(f"⚠️ Error sending audio: {e}")
    
# # # #     def _is_non_answer_response(self, text: str) -> bool:
# # # #         """Check if user response is a non-answer (like repetition request)"""
# # # #         text_lower = text.lower().strip()
# # # #         return any(phrase in text_lower for phrase in self.non_answer_phrases)
    
# # # #     def _is_valid_answer(self, text: str, question: str) -> bool:
# # # #         """Check if the response is a valid answer to the question"""
# # # #         # If it's a non-answer response, it's not valid
# # # #         if self._is_non_answer_response(text):
# # # #             return False
        
# # # #         # Check if the response is too short
# # # #         if len(text.strip()) < 3:
# # # #             return False
        
# # # #         # Check if the response looks like Nova speaking
# # # #         nova_indicators = [
# # # #             "i see", "that's good", "thank you", "great to hear", "wonderful",
# # # #             "i'm glad", "i appreciate", "understood", "moving on", "let's",
# # # #             "now let's", "absolutely", "sure thing", "indeed"
# # # #         ]
        
# # # #         text_lower = text.lower()
# # # #         if any(indicator in text_lower for indicator in nova_indicators):
# # # #             return False
        
# # # #         # Question-specific validation
# # # #         question_lower = question.lower()
        
# # # #         # For rating questions, check if there's a number or rating word
# # # #         if "rate" in question_lower and "scale" in question_lower:
# # # #             rating_words = ["one", "two", "three", "four", "five", "1", "2", "3", "4", "5", 
# # # #                            "good", "great", "excellent", "average", "poor", "fair", "bad"]
# # # #             return any(word in text_lower for word in rating_words)
        
# # # #         # For yes/no questions, check if there's a yes/no or equivalent
# # # #         if any(word in question_lower for word in ["did you", "do you", "are you", "is there", "would you"]):
# # # #             yes_no_words = ["yes", "no", "yeah", "yep", "nope", "definitely", "absolutely", 
# # # #                            "certainly", "not really", "not at all"]
# # # #             return any(word in text_lower for word in yes_no_words)
        
# # # #         # For recommendation questions, check for recommendation indicators
# # # #         if "recommend" in question_lower:
# # # #             recommend_words = ["recommend", "would", "wouldn't", "will", "won't", "suggest", "tell"]
# # # #             return any(word in text_lower for word in recommend_words)
        
# # # #         # For questions about reasons, check for explanation
# # # #         if "reason" in question_lower or "why" in question_lower:
# # # #             return len(text.split()) > 3  # Should have at least a few words
        
# # # #         # For training questions, check for training-related words
# # # #         if "training" in question_lower:
# # # #             training_words = ["training", "trained", "learn", "learned", "course", "courses", 
# # # #                             "program", "programs", "session", "sessions"]
# # # #             return any(word in text_lower for word in training_words)
        
# # # #         # For policy questions, check for policy-related words
# # # #         if "policy" in question_lower or "policies" in question_lower:
# # # #             policy_words = ["policy", "policies", "clear", "unclear", "confusing", 
# # # #                            "understand", "understood", "confused"]
# # # #             return any(word in text_lower for word in policy_words)
        
# # # #         # For relationship questions, check for relationship descriptors
# # # #         if "relationship" in question_lower and "manager" in question_lower:
# # # #             relationship_words = ["good", "great", "excellent", "poor", "bad", "supportive", 
# # # #                                  "helpful", "difficult", "challenging", "friendly", "distant"]
# # # #             return any(word in text_lower for word in relationship_words)
        
# # # #         # Default validation: just check if it's not a non-answer
# # # #         return True
    
# # # #     async def _save_response_to_db(self, q_idx: int, question: str, raw_answer: str):
# # # #         """Save response to database with proper validation"""
# # # #         try:
# # # #             # Prevent duplicate saves
# # # #             if q_idx in self.saved_responses:
# # # #                 print(f"⚠️ Q{q_idx + 1} already saved - skipping duplicate")
# # # #                 return False
            
# # # #             # Validate answer
# # # #             if not raw_answer or len(raw_answer.strip()) < 3:
# # # #                 print(f"⚠️ Answer too short, skipping: '{raw_answer}'")
# # # #                 return False
            
# # # #             # Check if it's a valid answer
# # # #             if not self._is_valid_answer(raw_answer, question):
# # # #                 print(f"⚠️ Not a valid answer, skipping: '{raw_answer}'")
# # # #                 return False
            
# # # #             print(f"\n{'='*80}")
# # # #             print(f"💾 SAVING RESPONSE Q{q_idx + 1}/{len(self.questions)}")
# # # #             print(f"{'='*80}")
# # # #             print(f"Question: {question}")
# # # #             print(f"Raw Answer: {raw_answer[:100]}...")
            
# # # #             # Clean with Bedrock
# # # #             cleaned_answer = clean_answer_with_bedrock(raw_answer, question)
# # # #             print(f"Cleaned Answer: {cleaned_answer[:100]}...")
            
# # # #             # Save to DB
# # # #             db_response = InterviewResponse(
# # # #                 interview_id=self.interview_id,
# # # #                 question=question,
# # # #                 answer=cleaned_answer
# # # #             )
# # # #             self.db.add(db_response)
# # # #             self.db.commit()
            
# # # #             self.saved_responses.add(q_idx)
            
# # # #             print(f"✅ Q{q_idx + 1} SAVED - Total: {len(self.saved_responses)}/{len(self.questions)}")
# # # #             print(f"{'='*80}\n")
            
# # # #             # Notify frontend
# # # #             await self.websocket.send_json({
# # # #                 'type': 'response_saved',
# # # #                 'q_index': q_idx,
# # # #                 'question': question,
# # # #                 'answer': cleaned_answer
# # # #             })
            
# # # #             return True
        
# # # #         except Exception as e:
# # # #             print(f"❌ Error saving to DB: {e}")
# # # #             traceback.print_exc()
# # # #             # Rollback on error to fix transaction state
# # # #             try:
# # # #                 self.db.rollback()
# # # #             except:
# # # #                 pass
# # # #             return False
    
# # # #     def _is_nova_asking_question(self, text: str) -> bool:
# # # #         """Detect if Nova is asking a question (contains ?)"""
# # # #         return '?' in text and len(text) > 10
    
# # # #     def _match_question_to_list(self, nova_question: str) -> int:
# # # #         """Match Nova's question text to our question list and return the index"""
# # # #         nova_question_lower = nova_question.lower()
        
# # # #         for i, question in enumerate(self.questions):
# # # #             # Check if the key parts of our question are in Nova's text
# # # #             question_lower = question.lower()
            
# # # #             # Special handling for multi-part questions
# # # #             if "why or why not" in question_lower and "recommend" in question_lower:
# # # #                 if "recommend" in nova_question_lower:
# # # #                     return i
            
# # # #             # For other questions, check if key phrases are present
# # # #             key_phrases = []
# # # #             for phrase in question_lower.split('?')[0].split(','):
# # # #                 phrase = phrase.strip()
# # # #                 if len(phrase) > 3:  # Only consider phrases longer than 3 chars
# # # #                     key_phrases.append(phrase)
            
# # # #             # Check if all key phrases are in Nova's question
# # # #             if all(phrase in nova_question_lower for phrase in key_phrases):
# # # #                 return i
        
# # # #         # If no match found, return -1
# # # #         return -1
    
# # # #     async def _process_responses(self):
# # # #         """Process responses from Nova"""
# # # #         try:
# # # #             while self.is_active:
# # # #                 try:
# # # #                     output = await self.stream.await_output()
# # # #                     result = await output[1].receive()
                    
# # # #                     if not result.value or not result.value.bytes_:
# # # #                         continue
                    
# # # #                     response_data = result.value.bytes_.decode('utf-8')
# # # #                     json_data = json.loads(response_data)
                    
# # # #                     if 'event' not in json_data:
# # # #                         continue
                    
# # # #                     event = json_data['event']
                    
# # # #                     # ============ TEXT OUTPUT ============
# # # #                     if 'textOutput' in event:
# # # #                         text = event['textOutput'].get('content', '')
# # # #                         role = event['textOutput'].get('role', 'ASSISTANT')
                        
# # # #                         if role == "ASSISTANT" and text.strip():
# # # #                             print(f"🤖 Nova: {text[:150]}...")
                            
# # # #                             # Send to frontend
# # # #                             await self.websocket.send_json({
# # # #                                 'type': 'text',
# # # #                                 'content': text,
# # # #                                 'role': 'ASSISTANT'
# # # #                             })
                            
# # # #                             # Check if Nova asked a question
# # # #                             if self._is_nova_asking_question(text):
# # # #                                 # If we're not in the middle of a question, start a new one
# # # #                                 if not self.question_in_progress:
# # # #                                     # If we were waiting for an answer, save it first
# # # #                                     if self.waiting_for_answer and self.user_answer_buffer.strip() and self.current_q_idx >= 0:
# # # #                                         if self.current_q_idx not in self.saved_responses:
# # # #                                             actual_question = self.questions[self.current_q_idx]
# # # #                                             answer = self.user_answer_buffer.strip()
# # # #                                             await self._save_response_to_db(self.current_q_idx, actual_question, answer)
                                    
# # # #                                     # Start tracking a new question
# # # #                                     self.question_in_progress = True
# # # #                                     self.question_parts = [text]
# # # #                                     self.last_nova_text = text
# # # #                                     self.non_answer_detected = False  # Reset non-answer flag
# # # #                                 else:
# # # #                                     # We're in the middle of a question, add this part
# # # #                                     self.question_parts.append(text)
# # # #                                     self.last_nova_text = text
                                
# # # #                                 # Try to match the complete question so far
# # # #                                 complete_question = " ".join(self.question_parts)
# # # #                                 matched_idx = self._match_question_to_list(complete_question)
                                
# # # #                                 if matched_idx >= 0:
# # # #                                     # We found a match, this is a complete question
# # # #                                     self.question_in_progress = False
# # # #                                     self.current_q_idx = matched_idx
# # # #                                     self.current_question_text = complete_question
# # # #                                     self.waiting_for_answer = True
# # # #                                     self.accumulating_transcription = True
# # # #                                     self.user_answer_buffer = ""
# # # #                                     print(f"❓ Question Q{self.current_q_idx + 1}: {complete_question}")
                            
# # # #                             # Check if goodbye
# # # #                             elif "goodbye" in text.lower():
# # # #                                 print(f"\n✅✅✅ NOVA SAID GOODBYE ✅✅✅")
                                
# # # #                                 # Save last answer if we were waiting for one
# # # #                                 if self.waiting_for_answer and self.user_answer_buffer.strip():
# # # #                                     if self.current_q_idx not in self.saved_responses and self.current_q_idx < len(self.questions):
# # # #                                         actual_question = self.questions[self.current_q_idx]
# # # #                                         answer = self.user_answer_buffer.strip()
# # # #                                         await self._save_response_to_db(self.current_q_idx, actual_question, answer)
                                
# # # #                                 await self._finalize_interview()
# # # #                                 return
                            
# # # #                             # If this is not a question and not goodbye, it might be a transition
# # # #                             # If we were in the middle of a question, consider it complete
# # # #                             elif self.question_in_progress:
# # # #                                 self.question_in_progress = False
# # # #                                 complete_question = " ".join(self.question_parts)
# # # #                                 matched_idx = self._match_question_to_list(complete_question)
                                
# # # #                                 if matched_idx >= 0:
# # # #                                     self.current_q_idx = matched_idx
# # # #                                     self.current_question_text = complete_question
# # # #                                     self.waiting_for_answer = True
# # # #                                     self.accumulating_transcription = True
# # # #                                     self.user_answer_buffer = ""
# # # #                                     print(f"❓ Question Q{self.current_q_idx + 1}: {complete_question}")
                        
# # # #                         elif role == "USER" and self.accumulating_transcription and text.strip():
# # # #                             # This is user's speech transcribed by Nova
# # # #                             print(f"👤 User: {text[:80]}...")
                            
# # # #                             # Check if this is a non-answer response
# # # #                             if self._is_non_answer_response(text):
# # # #                                 print(f"🔄 User requested repetition: {text}")
# # # #                                 # Clear the buffer and remain waiting for answer
# # # #                                 self.user_answer_buffer = ""
# # # #                                 self.non_answer_detected = True
# # # #                                 # Send to frontend but don't save as answer
# # # #                                 await self.websocket.send_json({
# # # #                                     'type': 'text',
# # # #                                     'content': text,
# # # #                                     'role': 'USER'
# # # #                                 })
# # # #                             else:
# # # #                                 # Only add if it's not a repeat of Nova's last text
# # # #                                 if text != self.last_nova_text:
# # # #                                     if self.user_answer_buffer:
# # # #                                         self.user_answer_buffer += " "
# # # #                                     self.user_answer_buffer += text
                                    
# # # #                                     print(f"   [Buffer: {self.user_answer_buffer[:100]}...]")
                                    
# # # #                                     await self.websocket.send_json({
# # # #                                         'type': 'text',
# # # #                                         'content': text,
# # # #                                         'role': 'USER'
# # # #                                     })
                    
# # # #                     # ============ AUDIO OUTPUT (HIGH QUALITY) ============
# # # #                     elif 'audioOutput' in event:
# # # #                         audio_content = event['audioOutput'].get('content', '')
# # # #                         if audio_content:
# # # #                             # Send audio directly without processing
# # # #                             await self.websocket.send_json({
# # # #                                 'type': 'audio',
# # # #                                 'data': audio_content
# # # #                             })
                    
# # # #                     # ============ COMPLETION ============
# # # #                     elif 'completionEnd' in event:
# # # #                         print("✅ Stream completion ended")
# # # #                         await self._finalize_interview()
# # # #                         return
                
# # # #                 except asyncio.TimeoutError:
# # # #                     continue
# # # #                 except Exception as e:
# # # #                     print(f"⚠️ Error in response processing: {e}")
# # # #                     traceback.print_exc()
# # # #                     continue
        
# # # #         except Exception as e:
# # # #             print(f"❌ Fatal error: {e}")
# # # #             traceback.print_exc()
# # # #             self.is_active = False
    
# # # #     async def _finalize_interview(self):
# # # #         """Finalize interview"""
# # # #         print(f"\n{'='*80}")
# # # #         print(f"🎉 INTERVIEW FINALIZATION")
# # # #         print(f"   Responses Saved: {len(self.saved_responses)}/{len(self.questions)}")
# # # #         print(f"   Status: {'✅ COMPLETE' if len(self.saved_responses) == len(self.questions) else '⚠️ INCOMPLETE'}")
# # # #         print(f"{'='*80}\n")
        
# # # #         try:
# # # #             interview = self.db.query(ExitInterview).filter(ExitInterview.id == self.interview_id).first()
# # # #             if interview:
# # # #                 interview.completed = True
# # # #                 interview.employee.status = "Completed"
# # # #                 self.db.commit()
# # # #                 print("✅ DB marked as completed")
# # # #         except Exception as e:
# # # #             print(f"⚠️ DB update error: {e}")
        
# # # #         try:
# # # #             await self.websocket.send_json({
# # # #                 'type': 'interview_complete',
# # # #                 'questions_answered': len(self.saved_responses),
# # # #                 'total_questions': len(self.questions)
# # # #             })
# # # #             print("✅ Completion message sent to frontend")
# # # #         except Exception as e:
# # # #             print(f"❌ Failed to send completion: {e}")
        
# # # #         self.is_active = False
    
# # # #     async def end_session(self):
# # # #         """End session"""
# # # #         if not self.is_active:
# # # #             return
        
# # # #         try:
# # # #             await self.send_event(json.dumps({
# # # #                 "event": {
# # # #                     "contentEnd": {
# # # #                         "promptName": self.prompt_name,
# # # #                         "contentName": self.audio_content_name
# # # #                     }
# # # #                 }
# # # #             }))
            
# # # #             await self.send_event(json.dumps({
# # # #                 "event": {
# # # #                     "promptEnd": {
# # # #                         "promptName": self.prompt_name
# # # #                     }
# # # #                 }
# # # #             }))
            
# # # #             await self.send_event(json.dumps({
# # # #                 "event": {
# # # #                     "sessionEnd": {}
# # # #                 }
# # # #             }))
            
# # # #             await self.stream.input_stream.close()
# # # #             self.is_active = False
# # # #             print("✅ Session ended")
        
# # # #         except Exception as e:
# # # #             print(f"⚠️ Error ending session: {e}")
# # # #             self.is_active = False

# # # # # ==================== AWS SES ====================
# # # # ses_client = boto3.client('ses', region_name=os.getenv("AWS_REGION", "us-east-1"))

# # # # def send_exit_interview_email(employee_email: str, employee_name: str, form_link: str) -> bool:
# # # #     SENDER = os.getenv("SES_SENDER_EMAIL")
# # # #     SUBJECT = "🎙️ Voice Exit Interview with Nova"
# # # #     BODY_HTML = f"""
# # # #     <html><body>
# # # #         <h1>Hello {employee_name}!</h1>
# # # #         <p>Have a voice conversation with Nova for your exit interview.</p>
# # # #         <p><a href="{form_link}">Start Voice Interview</a></p>
# # # #     </body></html>
# # # #     """
# # # #     try:
# # # #         ses_client.send_email(
# # # #             Source=SENDER,
# # # #             Destination={'ToAddresses': [employee_email]},
# # # #             Message={'Subject': {'Data': SUBJECT}, 'Body': {'Html': {'Data': BODY_HTML}}}
# # # #         )
# # # #         print(f"✅ Email sent to {employee_name}")
# # # #         return True
# # # #     except Exception as e:
# # # #         print(f"❌ Email error: {e}")
# # # #         return False

# # # # def generate_unique_token() -> str:
# # # #     return str(uuid.uuid4())

# # # # def create_form_link(token: str) -> str:
# # # #     return f"{os.getenv('APP_URL', 'http://localhost:8501')}/exit_interview?token={token}"

# # # # # ==================== FASTAPI APP ====================
# # # # app = FastAPI(title="Nova Sonic Exit Interview API", version="6.0.0")

# # # # app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# # # # def get_db():
# # # #     db = SessionLocal()
# # # #     try:
# # # #         yield db
# # # #     finally:
# # # #         db.close()

# # # # active_sessions: Dict[str, NovaInterviewClient] = {}

# # # # # ==================== API ENDPOINTS ====================

# # # # @app.get("/")
# # # # def root():
# # # #     return {"message": "Nova Sonic Exit Interview API", "version": "6.0.0", "status": "running"}

# # # # @app.post("/api/employees", response_model=EmployeeResponse, status_code=201)
# # # # def create_employee(employee: EmployeeCreate, db: Session = Depends(get_db)):
# # # #     try:
# # # #         existing = db.query(Employee).filter(Employee.email == employee.email).first()
# # # #         if existing:
# # # #             raise HTTPException(status_code=400, detail="Employee already exists")
        
# # # #         db_employee = Employee(
# # # #             name=employee.name,
# # # #             email=employee.email,
# # # #             department=employee.department,
# # # #             last_working_date=employee.last_working_date,
# # # #             status="Resigned"
# # # #         )
# # # #         db.add(db_employee)
# # # #         db.commit()
# # # #         db.refresh(db_employee)
        
# # # #         token = generate_unique_token()
# # # #         form_link = create_form_link(token)
        
# # # #         questions_json = json.dumps(employee.questions) if employee.questions else json.dumps([
# # # #             "What was your primary reason for leaving?",
# # # #             "How would you rate your overall experience with the company on a scale of 1 to 5?",
# # # #             "How was your relationship with your manager?",
# # # #             "Did you feel valued and recognized in your role?",
# # # #             "Would you recommend our company to others? Why or why not?",
# # # #             "Did you receive enough training?",
# # # #             "Are any company policies unclear?"
# # # #         ])
        
# # # #         db_interview = ExitInterview(
# # # #             employee_id=db_employee.id,
# # # #             form_token=token,
# # # #             completed=False,
# # # #             questions_json=questions_json
# # # #         )
# # # #         db.add(db_interview)
# # # #         db.commit()
        
# # # #         send_exit_interview_email(db_employee.email, db_employee.name, form_link)
        
# # # #         return db_employee
# # # #     except HTTPException:
# # # #         raise
# # # #     except Exception as e:
# # # #         db.rollback()
# # # #         raise HTTPException(status_code=500, detail=str(e))

# # # # @app.get("/api/employees", response_model=List[EmployeeResponse])
# # # # def list_employees(db: Session = Depends(get_db)):
# # # #     return db.query(Employee).all()

# # # # @app.get("/api/interviews/token/{token}")
# # # # def get_interview_by_token(token: str, db: Session = Depends(get_db)):
# # # #     interview = db.query(ExitInterview).filter(ExitInterview.form_token == token).first()
# # # #     if not interview:
# # # #         raise HTTPException(status_code=404, detail="Invalid token")
# # # #     if interview.completed:
# # # #         raise HTTPException(status_code=400, detail="Interview already completed")
    
# # # #     questions = json.loads(interview.questions_json)
# # # #     return {
# # # #         "interview_id": interview.id,
# # # #         "employee_name": interview.employee.name,
# # # #         "employee_department": interview.employee.department,
# # # #         "questions": questions,
# # # #         "total_questions": len(questions),
# # # #         "completed": interview.completed
# # # #     }

# # # # @app.websocket("/ws/interview/{token}")
# # # # async def websocket_interview(websocket: WebSocket, token: str):
# # # #     await websocket.accept()
    
# # # #     db = SessionLocal()
# # # #     session_id = str(uuid.uuid4())
# # # #     nova_client = None
    
# # # #     try:
# # # #         interview = db.query(ExitInterview).filter(ExitInterview.form_token == token).first()
# # # #         if not interview:
# # # #             await websocket.send_json({"type": "error", "message": "Invalid token"})
# # # #             return
        
# # # #         questions = json.loads(interview.questions_json)
# # # #         employee_name = interview.employee.name
        
# # # #         print(f"\n{'='*80}")
# # # #         print(f"🎙️ NEW INTERVIEW: {employee_name}")
# # # #         print(f"📋 Questions: {len(questions)}")
# # # #         print(f"{'='*80}\n")
        
# # # #         await websocket.send_json({
# # # #             "type": "session_start",
# # # #             "session_id": session_id,
# # # #             "employee_name": employee_name,
# # # #             "total_questions": len(questions)
# # # #         })
        
# # # #         nova_client = NovaInterviewClient(
# # # #             employee_name,
# # # #             questions,
# # # #             websocket,
# # # #             db,
# # # #             interview.id,
# # # #             os.getenv("AWS_REGION", "us-east-1")
# # # #         )
# # # #         await nova_client.start_session()
        
# # # #         await asyncio.sleep(2)
# # # #         await nova_client.start_audio_input()
        
# # # #         active_sessions[session_id] = nova_client
        
# # # #         timeout_seconds = 900  # 15 minutes
# # # #         start_time = datetime.now()
        
# # # #         while nova_client.is_active:
# # # #             try:
# # # #                 message = await asyncio.wait_for(websocket.receive_json(), timeout=0.5)
# # # #                 start_time = datetime.now()
                
# # # #                 if message['type'] == 'audio_chunk':
# # # #                     audio_data = base64.b64decode(message['data'])
# # # #                     await nova_client.send_audio_chunk(audio_data)
                
# # # #                 elif message['type'] == 'close':
# # # #                     break
            
# # # #             except asyncio.TimeoutError:
# # # #                 elapsed = (datetime.now() - start_time).total_seconds()
# # # #                 if elapsed > timeout_seconds:
# # # #                     print(f"⚠️ Interview timeout after {timeout_seconds}s")
# # # #                     break
# # # #                 continue
# # # #             except WebSocketDisconnect:
# # # #                 print("⚠️ Client disconnected")
# # # #                 break
# # # #             except Exception as e:
# # # #                 print(f"⚠️ Error: {e}")
# # # #                 break
    
# # # #     except Exception as e:
# # # #         print(f"❌ Error: {e}")
# # # #         traceback.print_exc()
# # # #         try:
# # # #             await websocket.send_json({"type": "error", "message": str(e)})
# # # #         except:
# # # #             pass
# # # #     finally:
# # # #         if nova_client:
# # # #             await nova_client.end_session()
# # # #         if session_id in active_sessions:
# # # #             del active_sessions[session_id]
# # # #         db.close()

# # # # @app.get("/api/interviews/{interview_id}/responses", response_model=List[InterviewResponseDetail])
# # # # def get_interview_responses(interview_id: int, db: Session = Depends(get_db)):
# # # #     """Get responses ordered by creation time"""
# # # #     return db.query(InterviewResponse).filter(
# # # #         InterviewResponse.interview_id == interview_id
# # # #     ).order_by(InterviewResponse.created_at).all()

# # # # @app.get("/api/stats")
# # # # def get_statistics(db: Session = Depends(get_db)):
# # # #     total = db.query(Employee).count()
# # # #     completed = db.query(ExitInterview).filter(ExitInterview.completed == True).count()
# # # #     return {
# # # #         "total_resignations": total,
# # # #         "completed_interviews": completed,
# # # #         "pending_interviews": total - completed,
# # # #         "completion_rate": (completed / total * 100) if total > 0 else 0
# # # #     }

# # # # def init_db():
# # # #     Base.metadata.create_all(bind=engine)
# # # #     print("✅ Database initialized!")

# # # # if __name__ == "__main__":
# # # #     init_db()
# # # #     import uvicorn
# # # #     print("\n🚀 Nova Sonic Exit Interview API v6.0.0")
# # # #     print("📡 http://0.0.0.0:8000\n")
# # # #     uvicorn.run(app, host="0.0.0.0", port=8000)




# # # """
# # # FIXED Nova Sonic Exit Interview Backend - COMPREHENSIVE VALIDATION
# # # Fixed: Invalid responses, misalignment, question matching, first question skip
# # # """

# # # from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
# # # from fastapi.middleware.cors import CORSMiddleware
# # # from sqlalchemy import create_engine, Column, Integer, String, Boolean, Date, DateTime, Text, ForeignKey
# # # from sqlalchemy.ext.declarative import declarative_base
# # # from sqlalchemy.orm import sessionmaker, Session, relationship
# # # from pydantic import BaseModel, EmailStr, field_validator
# # # from typing import List, Optional, Dict, Any
# # # from datetime import datetime, date
# # # import os
# # # from dotenv import load_dotenv
# # # import boto3
# # # import uuid
# # # import json
# # # import asyncio
# # # import base64
# # # import traceback

# # # from aws_sdk_bedrock_runtime.client import BedrockRuntimeClient, InvokeModelWithBidirectionalStreamOperationInput
# # # from aws_sdk_bedrock_runtime.models import InvokeModelWithBidirectionalStreamInputChunk, BidirectionalInputPayloadPart
# # # from aws_sdk_bedrock_runtime.config import Config
# # # from smithy_aws_core.identity.environment import EnvironmentCredentialsResolver

# # # load_dotenv()

# # # # ==================== DATABASE SETUP ====================
# # # DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

# # # engine = create_engine(DATABASE_URL)
# # # SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# # # Base = declarative_base()

# # # # ==================== DATABASE MODELS ====================
# # # class Employee(Base):
# # #     __tablename__ = "employees"
    
# # #     id = Column(Integer, primary_key=True, index=True)
# # #     name = Column(String(100), nullable=False)
# # #     email = Column(String(100), unique=True, nullable=False)
# # #     department = Column(String(50))
# # #     last_working_date = Column(Date)
# # #     status = Column(String(20), default="Resigned")
# # #     created_at = Column(DateTime, default=datetime.utcnow)
    
# # #     exit_interview = relationship("ExitInterview", back_populates="employee", uselist=False)

# # # class ExitInterview(Base):
# # #     __tablename__ = "exit_interviews"
    
# # #     id = Column(Integer, primary_key=True, index=True)
# # #     employee_id = Column(Integer, ForeignKey("employees.id"))
# # #     form_token = Column(String(255), unique=True, nullable=False)
# # #     completed = Column(Boolean, default=False)
# # #     questions_json = Column(Text)
# # #     created_at = Column(DateTime, default=datetime.utcnow)
    
# # #     employee = relationship("Employee", back_populates="exit_interview")
# # #     responses = relationship("InterviewResponse", back_populates="interview")

# # # class InterviewResponse(Base):
# # #     __tablename__ = "interview_responses"
    
# # #     id = Column(Integer, primary_key=True, index=True)
# # #     interview_id = Column(Integer, ForeignKey("exit_interviews.id"))
# # #     question = Column(Text, nullable=False)
# # #     answer = Column(Text, nullable=False)
# # #     created_at = Column(DateTime, default=datetime.utcnow)
    
# # #     interview = relationship("ExitInterview", back_populates="responses")

# # # # ==================== PYDANTIC SCHEMAS ====================
# # # class EmployeeCreate(BaseModel):
# # #     name: str
# # #     email: EmailStr
# # #     department: str
# # #     last_working_date: date
# # #     questions: Optional[List[str]] = None
    
# # #     @field_validator('name')
# # #     def name_must_not_be_empty(cls, v):
# # #         if not v or not v.strip():
# # #             raise ValueError('Name cannot be empty')
# # #         return v.strip()

# # # class EmployeeResponse(BaseModel):
# # #     id: int
# # #     name: str
# # #     email: str
# # #     department: str
# # #     last_working_date: date
# # #     status: str
# # #     created_at: datetime
    
# # #     class Config:
# # #         from_attributes = True

# # # class InterviewResponseDetail(BaseModel):
# # #     id: int
# # #     question: str
# # #     answer: str
# # #     created_at: datetime
    
# # #     class Config:
# # #         from_attributes = True

# # # # ==================== BEDROCK VALIDATION & CLEANING ====================
# # # def validate_and_clean_answer(raw_answer: str, question: str) -> tuple[bool, str]:
# # #     """
# # #     Use Bedrock to validate AND clean the answer
# # #     Returns: (is_valid, cleaned_answer)
# # #     """
# # #     try:
# # #         if not raw_answer or len(raw_answer.strip()) < 3:
# # #             return False, ""
        
# # #         bedrock = boto3.client('bedrock-runtime', region_name=os.getenv("AWS_REGION", "us-east-1"))
        
# # #         prompt = f"""Analyze if this is a valid answer to the question. Then clean it if valid.

# # # Question: {question}
# # # User Response: {raw_answer}

# # # Instructions:
# # # 1. Check if this is a REAL ANSWER or just a request for repetition/clarification
# # # 2. Invalid responses include: "sorry", "repeat", "didn't hear", "come again", "pardon", etc.
# # # 3. If VALID, extract and clean the answer (remove filler words, greetings)
# # # 4. If INVALID, return "INVALID"

# # # Respond in this exact format:
# # # VALID: [cleaned answer]
# # # OR
# # # INVALID

# # # Your response:"""

# # #         body = json.dumps({
# # #             "anthropic_version": "bedrock-2023-05-31",
# # #             "max_tokens": 150,
# # #             "temperature": 0.1,
# # #             "messages": [
# # #                 {
# # #                     "role": "user",
# # #                     "content": prompt
# # #                 }
# # #             ]
# # #         })
        
# # #         response = bedrock.invoke_model(
# # #             body=body,
# # #             modelId="arn:aws:bedrock:us-east-1:762233739050:inference-profile/us.anthropic.claude-3-5-sonnet-20240620-v1:0",
# # #             accept="application/json",
# # #             contentType="application/json"
# # #         )
        
# # #         response_body = json.loads(response.get('body').read())
# # #         result = response_body.get('content', [{}])[0].get('text', '').strip()
        
# # #         if result.startswith("VALID:"):
# # #             cleaned = result.replace("VALID:", "").strip()
# # #             return True, cleaned
# # #         else:
# # #             return False, ""
    
# # #     except Exception as e:
# # #         print(f"⚠️ Bedrock validation error: {e} - using fallback")
# # #         # Fallback validation
# # #         invalid_phrases = [
# # #             "sorry", "repeat", "didn't hear", "come again", "pardon",
# # #             "what was", "can you say", "didn't understand", "breaking up"
# # #         ]
# # #         raw_lower = raw_answer.lower()
# # #         if any(phrase in raw_lower for phrase in invalid_phrases):
# # #             return False, ""
# # #         return True, raw_answer.strip()

# # # # ==================== NOVA SONIC CLIENT ====================
# # # class NovaInterviewClient:
# # #     def __init__(self, employee_name: str, questions: List[str], websocket: WebSocket, db: Session, interview_id: int, region='us-east-1'):
# # #         self.model_id = 'amazon.nova-sonic-v1:0'
# # #         self.region = region
# # #         self.employee_name = employee_name
# # #         self.questions = questions
# # #         self.websocket = websocket
# # #         self.db = db
# # #         self.interview_id = interview_id
# # #         self.client = None
# # #         self.stream = None
# # #         self.is_active = False
        
# # #         self.prompt_name = str(uuid.uuid4())
# # #         self.system_content_name = str(uuid.uuid4())
# # #         self.audio_content_name = str(uuid.uuid4())
        
# # #         # ===== STATE TRACKING =====
# # #         self.current_q_idx = -1
# # #         self.user_answer_buffer = ""
# # #         self.saved_responses = set()
# # #         self.last_nova_text = ""
# # #         self.waiting_for_answer = False
# # #         self.question_text_buffer = []
# # #         self.silence_counter = 0
# # #         self.last_user_text_time = None
    
# # #     def _initialize_client(self):
# # #         """Initialize Bedrock client"""
# # #         resolver = EnvironmentCredentialsResolver()
# # #         config = Config(
# # #             endpoint_uri=f"https://bedrock-runtime.{self.region}.amazonaws.com",
# # #             region=self.region,
# # #             aws_credentials_identity_resolver=resolver
# # #         )
# # #         self.client = BedrockRuntimeClient(config=config)
# # #         print("✅ Bedrock client initialized")
    
# # #     async def send_event(self, event_json):
# # #         """Send event to stream"""
# # #         event = InvokeModelWithBidirectionalStreamInputChunk(
# # #             value=BidirectionalInputPayloadPart(bytes_=event_json.encode('utf-8'))
# # #         )
# # #         await self.stream.input_stream.send(event)
    
# # #     def _extract_question_keywords(self, question: str) -> List[str]:
# # #         """Extract unique keywords from question for matching"""
# # #         # Remove common words
# # #         common_words = {'the', 'a', 'an', 'is', 'was', 'were', 'are', 'your', 'you', 'to', 'in', 'on', 'at', 'of', 'for', 'with', 'did', 'do', 'does', 'would', 'could', 'should'}
        
# # #         words = question.lower().replace('?', '').split()
# # #         keywords = [w for w in words if len(w) > 3 and w not in common_words]
# # #         return keywords[:5]  # Top 5 keywords
    
# # #     def _match_nova_question(self, nova_text: str) -> int:
# # #         """Match Nova's question to our question list"""
# # #         nova_lower = nova_text.lower()
        
# # #         best_match_idx = -1
# # #         best_match_score = 0
        
# # #         for idx, question in enumerate(self.questions):
# # #             keywords = self._extract_question_keywords(question)
# # #             matches = sum(1 for kw in keywords if kw in nova_lower)
# # #             score = matches / len(keywords) if keywords else 0
            
# # #             if score > best_match_score and score >= 0.6:  # At least 60% match
# # #                 best_match_score = score
# # #                 best_match_idx = idx
        
# # #         if best_match_idx >= 0:
# # #             print(f"✅ Matched Q{best_match_idx + 1} with {best_match_score:.0%} confidence")
        
# # #         return best_match_idx
    
# # #     async def start_session(self):
# # #         """Start Nova Sonic session"""
# # #         if not self.client:
# # #             self._initialize_client()
        
# # #         try:
# # #             print("📡 Starting bidirectional stream...")
# # #             self.stream = await self.client.invoke_model_with_bidirectional_stream(
# # #                 InvokeModelWithBidirectionalStreamOperationInput(model_id=self.model_id)
# # #             )
# # #             self.is_active = True
# # #             print("✅ Stream started")
            
# # #             # Session start
# # #             await self.send_event(json.dumps({
# # #                 "event": {
# # #                     "sessionStart": {
# # #                         "inferenceConfiguration": {
# # #                             "maxTokens": 1024,
# # #                             "topP": 0.9,
# # #                             "temperature": 0.7
# # #                         }
# # #                     }
# # #                 }
# # #             }))
            
# # #             # Prompt start with AUDIO OUTPUT
# # #             await self.send_event(json.dumps({
# # #                 "event": {
# # #                     "promptStart": {
# # #                         "promptName": self.prompt_name,
# # #                         "textOutputConfiguration": {
# # #                             "mediaType": "text/plain"
# # #                         },
# # #                         "audioOutputConfiguration": {
# # #                             "mediaType": "audio/lpcm",
# # #                             "sampleRateHertz": 24000,
# # #                             "sampleSizeBits": 16,
# # #                             "channelCount": 1,
# # #                             "voiceId": "matthew",
# # #                             "encoding": "base64",
# # #                             "audioType": "SPEECH"
# # #                         }
# # #                     }
# # #                 }
# # #             }))
            
# # #             # System content
# # #             await self.send_event(json.dumps({
# # #                 "event": {
# # #                     "contentStart": {
# # #                         "promptName": self.prompt_name,
# # #                         "contentName": self.system_content_name,
# # #                         "type": "TEXT",
# # #                         "interactive": False,
# # #                         "role": "SYSTEM",
# # #                         "textInputConfiguration": {
# # #                             "mediaType": "text/plain"
# # #                         }
# # #                     }
# # #                 }
# # #             }))
            
# # #             questions_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(self.questions)])
            
# # #             system_text = f"""You are Nova conducting an EXIT INTERVIEW with {self.employee_name}.

# # # CRITICAL RULES:
# # # 1. Ask EXACTLY these {len(self.questions)} questions IN ORDER
# # # 2. Ask ONE question at a time
# # # 3. WAIT for the user's COMPLETE answer before moving to the next question
# # # 4. If the user asks you to repeat, repeat the SAME question again
# # # 5. Do NOT skip any questions
# # # 6. After the last question is answered, say: "Thank you for completing the exit interview. Goodbye."

# # # QUESTIONS:
# # # {questions_text}

# # # Start by greeting {self.employee_name} and asking the FIRST question immediately."""

# # #             await self.send_event(json.dumps({
# # #                 "event": {
# # #                     "textInput": {
# # #                         "promptName": self.prompt_name,
# # #                         "contentName": self.system_content_name,
# # #                         "content": system_text
# # #                     }
# # #                 }
# # #             }))
            
# # #             await self.send_event(json.dumps({
# # #                 "event": {
# # #                     "contentEnd": {
# # #                         "promptName": self.prompt_name,
# # #                         "contentName": self.system_content_name
# # #                     }
# # #                 }
# # #             }))
            
# # #             print("✅ System prompt sent")
# # #             asyncio.create_task(self._process_responses())
        
# # #         except Exception as e:
# # #             print(f"❌ Error starting session: {e}")
# # #             traceback.print_exc()
# # #             raise
    
# # #     async def start_audio_input(self):
# # #         """Start audio input"""
# # #         await self.send_event(json.dumps({
# # #             "event": {
# # #                 "contentStart": {
# # #                     "promptName": self.prompt_name,
# # #                     "contentName": self.audio_content_name,
# # #                     "type": "AUDIO",
# # #                     "interactive": True,
# # #                     "role": "USER",
# # #                     "audioInputConfiguration": {
# # #                         "mediaType": "audio/lpcm",
# # #                         "sampleRateHertz": 16000,
# # #                         "sampleSizeBits": 16,
# # #                         "channelCount": 1,
# # #                         "audioType": "SPEECH",
# # #                         "encoding": "base64"
# # #                     }
# # #                 }
# # #             }
# # #         }))
# # #         print("✅ Audio input started")
    
# # #     async def send_audio_chunk(self, audio_bytes):
# # #         """Send audio chunk"""
# # #         if not self.is_active:
# # #             return
        
# # #         blob = base64.b64encode(audio_bytes).decode('utf-8')
# # #         try:
# # #             await self.send_event(json.dumps({
# # #                 "event": {
# # #                     "audioInput": {
# # #                         "promptName": self.prompt_name,
# # #                         "contentName": self.audio_content_name,
# # #                         "content": blob
# # #                     }
# # #                 }
# # #             }))
# # #         except Exception as e:
# # #             print(f"⚠️ Error sending audio: {e}")
    
# # #     async def _save_response_to_db(self, q_idx: int, question: str, raw_answer: str):
# # #         """Save response with comprehensive validation"""
# # #         try:
# # #             # Prevent duplicates
# # #             if q_idx in self.saved_responses:
# # #                 print(f"⚠️ Q{q_idx + 1} already saved")
# # #                 return False
            
# # #             # Minimum length check
# # #             if len(raw_answer.strip()) < 5:
# # #                 print(f"⚠️ Answer too short: '{raw_answer}'")
# # #                 return False
            
# # #             # USE BEDROCK FOR VALIDATION + CLEANING
# # #             is_valid, cleaned_answer = validate_and_clean_answer(raw_answer, question)
            
# # #             if not is_valid:
# # #                 print(f"❌ INVALID RESPONSE BLOCKED: '{raw_answer[:50]}'")
# # #                 # Notify user their response wasn't saved
# # #                 await self.websocket.send_json({
# # #                     'type': 'validation_failed',
# # #                     'message': 'Response was not a valid answer (request for repetition detected)'
# # #                 })
# # #                 return False
            
# # #             print(f"\n{'='*80}")
# # #             print(f"💾 SAVING VALID RESPONSE Q{q_idx + 1}/{len(self.questions)}")
# # #             print(f"{'='*80}")
# # #             print(f"Question: {question}")
# # #             print(f"Raw: {raw_answer[:80]}...")
# # #             print(f"Cleaned: {cleaned_answer[:80]}...")
            
# # #             # Save to DB
# # #             db_response = InterviewResponse(
# # #                 interview_id=self.interview_id,
# # #                 question=question,
# # #                 answer=cleaned_answer
# # #             )
# # #             self.db.add(db_response)
# # #             self.db.commit()
            
# # #             self.saved_responses.add(q_idx)
            
# # #             print(f"✅ SAVED Q{q_idx + 1} - Total: {len(self.saved_responses)}/{len(self.questions)}")
# # #             print(f"{'='*80}\n")
            
# # #             # Notify frontend
# # #             await self.websocket.send_json({
# # #                 'type': 'response_saved',
# # #                 'q_index': q_idx,
# # #                 'question': question,
# # #                 'answer': cleaned_answer
# # #             })
            
# # #             return True
        
# # #         except Exception as e:
# # #             print(f"❌ Error saving: {e}")
# # #             traceback.print_exc()
# # #             try:
# # #                 self.db.rollback()
# # #             except:
# # #                 pass
# # #             return False
    
# # #     async def _process_responses(self):
# # #         """Process responses from Nova"""
# # #         try:
# # #             while self.is_active:
# # #                 try:
# # #                     output = await self.stream.await_output()
# # #                     result = await output[1].receive()
                    
# # #                     if not result.value or not result.value.bytes_:
# # #                         continue
                    
# # #                     response_data = result.value.bytes_.decode('utf-8')
# # #                     json_data = json.loads(response_data)
                    
# # #                     if 'event' not in json_data:
# # #                         continue
                    
# # #                     event = json_data['event']
                    
# # #                     # ============ TEXT OUTPUT ============
# # #                     if 'textOutput' in event:
# # #                         text = event['textOutput'].get('content', '')
# # #                         role = event['textOutput'].get('role', 'ASSISTANT')
                        
# # #                         if role == "ASSISTANT" and text.strip():
# # #                             print(f"🤖 Nova: {text[:120]}...")
                            
# # #                             # Send to frontend
# # #                             await self.websocket.send_json({
# # #                                 'type': 'text',
# # #                                 'content': text,
# # #                                 'role': 'ASSISTANT'
# # #                             })
                            
# # #                             # Check if Nova asked a question
# # #                             if '?' in text:
# # #                                 # Match to question list
# # #                                 matched_idx = self._match_nova_question(text)
                                
# # #                                 if matched_idx >= 0 and matched_idx not in self.saved_responses:
# # #                                     # Save previous answer if we were waiting
# # #                                     if self.waiting_for_answer and self.user_answer_buffer.strip():
# # #                                         if self.current_q_idx >= 0 and self.current_q_idx not in self.saved_responses:
# # #                                             await self._save_response_to_db(
# # #                                                 self.current_q_idx,
# # #                                                 self.questions[self.current_q_idx],
# # #                                                 self.user_answer_buffer.strip()
# # #                                             )
                                    
# # #                                     # Start new question
# # #                                     self.current_q_idx = matched_idx
# # #                                     self.waiting_for_answer = True
# # #                                     self.user_answer_buffer = ""
# # #                                     self.last_user_text_time = None
                                    
# # #                                     print(f"\n❓ QUESTION {self.current_q_idx + 1}: {self.questions[self.current_q_idx][:60]}...")
# # #                                     print(f"   Waiting for answer...\n")
                            
# # #                             # Check for goodbye
# # #                             elif "goodbye" in text.lower() or "thank you for completing" in text.lower():
# # #                                 print(f"\n✅ GOODBYE DETECTED")
                                
# # #                                 # Save last answer
# # #                                 if self.waiting_for_answer and self.user_answer_buffer.strip():
# # #                                     if self.current_q_idx >= 0 and self.current_q_idx not in self.saved_responses:
# # #                                         await self._save_response_to_db(
# # #                                             self.current_q_idx,
# # #                                             self.questions[self.current_q_idx],
# # #                                             self.user_answer_buffer.strip()
# # #                                         )
                                
# # #                                 await self._finalize_interview()
# # #                                 return
                            
# # #                             self.last_nova_text = text
                        
# # #                         elif role == "USER" and self.waiting_for_answer and text.strip():
# # #                             # User speaking
# # #                             print(f"👤 User: {text[:80]}...")
                            
# # #                             # Update buffer
# # #                             if self.user_answer_buffer:
# # #                                 self.user_answer_buffer += " "
# # #                             self.user_answer_buffer += text
# # #                             self.last_user_text_time = datetime.utcnow()
                            
# # #                             print(f"   [Buffer: {len(self.user_answer_buffer)} chars]")
                            
# # #                             await self.websocket.send_json({
# # #                                 'type': 'text',
# # #                                 'content': text,
# # #                                 'role': 'USER'
# # #                             })
                    
# # #                     # ============ AUDIO OUTPUT ============
# # #                     elif 'audioOutput' in event:
# # #                         audio_content = event['audioOutput'].get('content', '')
# # #                         if audio_content:
# # #                             await self.websocket.send_json({
# # #                                 'type': 'audio',
# # #                                 'data': audio_content
# # #                             })
                    
# # #                     # ============ COMPLETION ============
# # #                     elif 'completionEnd' in event:
# # #                         print("✅ Stream completion")
# # #                         await self._finalize_interview()
# # #                         return
                
# # #                 except asyncio.TimeoutError:
# # #                     continue
# # #                 except Exception as e:
# # #                     print(f"⚠️ Error in response processing: {e}")
# # #                     traceback.print_exc()
# # #                     continue
        
# # #         except Exception as e:
# # #             print(f"❌ Fatal error: {e}")
# # #             traceback.print_exc()
# # #             self.is_active = False
    
# # #     async def _finalize_interview(self):
# # #         """Finalize interview"""
# # #         print(f"\n{'='*80}")
# # #         print(f"🎉 INTERVIEW FINALIZATION")
# # #         print(f"   Responses: {len(self.saved_responses)}/{len(self.questions)}")
# # #         print(f"   Status: {'✅ COMPLETE' if len(self.saved_responses) == len(self.questions) else '⚠️ INCOMPLETE'}")
# # #         print(f"{'='*80}\n")
        
# # #         try:
# # #             interview = self.db.query(ExitInterview).filter(ExitInterview.id == self.interview_id).first()
# # #             if interview:
# # #                 interview.completed = True
# # #                 interview.employee.status = "Completed"
# # #                 self.db.commit()
# # #         except Exception as e:
# # #             print(f"⚠️ DB error: {e}")
        
# # #         try:
# # #             await self.websocket.send_json({
# # #                 'type': 'interview_complete',
# # #                 'questions_answered': len(self.saved_responses),
# # #                 'total_questions': len(self.questions)
# # #             })
# # #         except Exception as e:
# # #             print(f"❌ Failed to send completion: {e}")
        
# # #         self.is_active = False
    
# # #     async def end_session(self):
# # #         """End session"""
# # #         if not self.is_active:
# # #             return
        
# # #         try:
# # #             await self.send_event(json.dumps({
# # #                 "event": {
# # #                     "contentEnd": {
# # #                         "promptName": self.prompt_name,
# # #                         "contentName": self.audio_content_name
# # #                     }
# # #                 }
# # #             }))
            
# # #             await self.send_event(json.dumps({
# # #                 "event": {
# # #                     "promptEnd": {
# # #                         "promptName": self.prompt_name
# # #                     }
# # #                 }
# # #             }))
            
# # #             await self.send_event(json.dumps({
# # #                 "event": {
# # #                     "sessionEnd": {}
# # #                 }
# # #             }))
            
# # #             await self.stream.input_stream.close()
# # #             self.is_active = False
# # #             print("✅ Session ended")
        
# # #         except Exception as e:
# # #             print(f"⚠️ Error ending session: {e}")
# # #             self.is_active = False

# # # # ==================== AWS SES ====================
# # # ses_client = boto3.client('ses', region_name=os.getenv("AWS_REGION", "us-east-1"))

# # # def send_exit_interview_email(employee_email: str, employee_name: str, form_link: str) -> bool:
# # #     SENDER = os.getenv("SES_SENDER_EMAIL")
# # #     SUBJECT = "🎙️ Voice Exit Interview with Nova"
# # #     BODY_HTML = f"""
# # #     <html><body>
# # #         <h1>Hello {employee_name}!</h1>
# # #         <p>Have a voice conversation with Nova for your exit interview.</p>
# # #         <p><a href="{form_link}">Start Voice Interview</a></p>
# # #     </body></html>
# # #     """
# # #     try:
# # #         ses_client.send_email(
# # #             Source=SENDER,
# # #             Destination={'ToAddresses': [employee_email]},
# # #             Message={'Subject': {'Data': SUBJECT}, 'Body': {'Html': {'Data': BODY_HTML}}}
# # #         )
# # #         print(f"✅ Email sent to {employee_name}")
# # #         return True
# # #     except Exception as e:
# # #         print(f"❌ Email error: {e}")
# # #         return False

# # # def generate_unique_token() -> str:
# # #     return str(uuid.uuid4())

# # # def create_form_link(token: str) -> str:
# # #     return f"{os.getenv('APP_URL', 'http://localhost:8501')}/exit_interview?token={token}"

# # # # ==================== FASTAPI APP ====================
# # # app = FastAPI(title="Nova Sonic Exit Interview API", version="7.0.0")

# # # app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# # # def get_db():
# # #     db = SessionLocal()
# # #     try:
# # #         yield db
# # #     finally:
# # #         db.close()

# # # active_sessions: Dict[str, NovaInterviewClient] = {}

# # # # ==================== API ENDPOINTS ====================

# # # @app.get("/")
# # # def root():
# # #     return {"message": "Nova Sonic Exit Interview API", "version": "7.0.0", "status": "running"}

# # # @app.post("/api/employees", response_model=EmployeeResponse, status_code=201)
# # # def create_employee(employee: EmployeeCreate, db: Session = Depends(get_db)):
# # #     try:
# # #         existing = db.query(Employee).filter(Employee.email == employee.email).first()
# # #         if existing:
# # #             raise HTTPException(status_code=400, detail="Employee already exists")
        
# # #         db_employee = Employee(
# # #             name=employee.name,
# # #             email=employee.email,
# # #             department=employee.department,
# # #             last_working_date=employee.last_working_date,
# # #             status="Resigned"
# # #         )
# # #         db.add(db_employee)
# # #         db.commit()
# # #         db.refresh(db_employee)
        
# # #         token = generate_unique_token()
# # #         form_link = create_form_link(token)
        
# # #         questions_json = json.dumps(employee.questions) if employee.questions else json.dumps([
# # #             "What was your primary reason for leaving?",
# # #             "How would you rate your overall experience with the company on a scale of 1 to 5?",
# # #             "How was your relationship with your manager?",
# # #             "Did you feel valued and recognized in your role?",
# # #             "Would you recommend our company to others? Why or why not?"
# # #         ])
        
# # #         db_interview = ExitInterview(
# # #             employee_id=db_employee.id,
# # #             form_token=token,
# # #             completed=False,
# # #             questions_json=questions_json
# # #         )
# # #         db.add(db_interview)
# # #         db.commit()
        
# # #         send_exit_interview_email(db_employee.email, db_employee.name, form_link)
        
# # #         return db_employee
# # #     except HTTPException:
# # #         raise
# # #     except Exception as e:
# # #         db.rollback()
# # #         raise HTTPException(status_code=500, detail=str(e))

# # # @app.get("/api/employees", response_model=List[EmployeeResponse])
# # # def list_employees(db: Session = Depends(get_db)):
# # #     return db.query(Employee).all()

# # # @app.get("/api/interviews/token/{token}")
# # # def get_interview_by_token(token: str, db: Session = Depends(get_db)):
# # #     interview = db.query(ExitInterview).filter(ExitInterview.form_token == token).first()
# # #     if not interview:
# # #         raise HTTPException(status_code=404, detail="Invalid token")
# # #     if interview.completed:
# # #         raise HTTPException(status_code=400, detail="Interview already completed")
    
# # #     questions = json.loads(interview.questions_json)
# # #     return {
# # #         "interview_id": interview.id,
# # #         "employee_name": interview.employee.name,
# # #         "employee_department": interview.employee.department,
# # #         "questions": questions,
# # #         "total_questions": len(questions),
# # #         "completed": interview.completed
# # #     }

# # # @app.websocket("/ws/interview/{token}")
# # # async def websocket_interview(websocket: WebSocket, token: str):
# # #     await websocket.accept()
    
# # #     db = SessionLocal()
# # #     session_id = str(uuid.uuid4())
# # #     nova_client = None
    
# # #     try:
# # #         interview = db.query(ExitInterview).filter(ExitInterview.form_token == token).first()
# # #         if not interview:
# # #             await websocket.send_json({"type": "error", "message": "Invalid token"})
# # #             return
        
# # #         questions = json.loads(interview.questions_json)
# # #         employee_name = interview.employee.name
        
# # #         print(f"\n{'='*80}")
# # #         print(f"🎙️ NEW INTERVIEW: {employee_name}")
# # #         print(f"📋 Questions: {len(questions)}")
# # #         print(f"{'='*80}\n")
        
# # #         await websocket.send_json({
# # #             "type": "session_start",
# # #             "session_id": session_id,
# # #             "employee_name": employee_name,
# # #             "total_questions": len(questions)
# # #         })
        
# # #         nova_client = NovaInterviewClient(
# # #             employee_name,
# # #             questions,
# # #             websocket,
# # #             db,
# # #             interview.id,
# # #             os.getenv("AWS_REGION", "us-east-1")
# # #         )
# # #         await nova_client.start_session()
        
# # #         await asyncio.sleep(2)
# # #         await nova_client.start_audio_input()
        
# # #         active_sessions[session_id] = nova_client
        
# # #         timeout_seconds = 900  # 15 minutes
# # #         start_time = datetime.now()
        
# # #         while nova_client.is_active:
# # #             try:
# # #                 message = await asyncio.wait_for(websocket.receive_json(), timeout=0.5)
# # #                 start_time = datetime.now()
                
# # #                 if message['type'] == 'audio_chunk':
# # #                     audio_data = base64.b64decode(message['data'])
# # #                     await nova_client.send_audio_chunk(audio_data)
                
# # #                 elif message['type'] == 'close':
# # #                     break
            
# # #             except asyncio.TimeoutError:
# # #                 elapsed = (datetime.now() - start_time).total_seconds()
# # #                 if elapsed > timeout_seconds:
# # #                     print(f"⚠️ Interview timeout after {timeout_seconds}s")
# # #                     break
# # #                 continue
# # #             except WebSocketDisconnect:
# # #                 print("⚠️ Client disconnected")
# # #                 break
# # #             except Exception as e:
# # #                 print(f"⚠️ Error: {e}")
# # #                 break
    
# # #     except Exception as e:
# # #         print(f"❌ Error: {e}")
# # #         traceback.print_exc()
# # #         try:
# # #             await websocket.send_json({"type": "error", "message": str(e)})
# # #         except:
# # #             pass
# # #     finally:
# # #         if nova_client:
# # #             await nova_client.end_session()
# # #         if session_id in active_sessions:
# # #             del active_sessions[session_id]
# # #         db.close()

# # # @app.get("/api/interviews/{interview_id}/responses", response_model=List[InterviewResponseDetail])
# # # def get_interview_responses(interview_id: int, db: Session = Depends(get_db)):
# # #     """Get responses ordered by creation time"""
# # #     return db.query(InterviewResponse).filter(
# # #         InterviewResponse.interview_id == interview_id
# # #     ).order_by(InterviewResponse.created_at).all()

# # # @app.get("/api/stats")
# # # def get_statistics(db: Session = Depends(get_db)):
# # #     total = db.query(Employee).count()
# # #     completed = db.query(ExitInterview).filter(ExitInterview.completed == True).count()
# # #     return {
# # #         "total_resignations": total,
# # #         "completed_interviews": completed,
# # #         "pending_interviews": total - completed,
# # #         "completion_rate": (completed / total * 100) if total > 0 else 0
# # #     }

# # # def init_db():
# # #     Base.metadata.create_all(bind=engine)
# # #     print("✅ Database initialized!")

# # # if __name__ == "__main__":
# # #     init_db()
# # #     import uvicorn
# # #     print("\n🚀 Nova Sonic Exit Interview API v6.0.0")
# # #     print("📡 http://0.0.0.0:8000\n")
# # #     uvicorn.run(app, host="0.0.0.0", port=8000)




# # """
# # FIXED Nova Sonic Exit Interview Backend - COMPREHENSIVE VALIDATION
# # Fixed: Invalid responses, misalignment, question matching, first question skip, deprecated datetime
# # """

# # from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
# # from fastapi.middleware.cors import CORSMiddleware
# # from sqlalchemy import create_engine, Column, Integer, String, Boolean, Date, DateTime, Text, ForeignKey
# # from sqlalchemy.ext.declarative import declarative_base
# # from sqlalchemy.orm import sessionmaker, Session, relationship
# # from pydantic import BaseModel, EmailStr, field_validator
# # from typing import List, Optional, Dict, Any
# # from datetime import datetime, date, timezone, timedelta
# # import os
# # from dotenv import load_dotenv
# # import boto3
# # import uuid
# # import json
# # import asyncio
# # import base64
# # import traceback
# # import re
# # from collections import Counter

# # from aws_sdk_bedrock_runtime.client import BedrockRuntimeClient, InvokeModelWithBidirectionalStreamOperationInput
# # from aws_sdk_bedrock_runtime.models import InvokeModelWithBidirectionalStreamInputChunk, BidirectionalInputPayloadPart
# # from aws_sdk_bedrock_runtime.config import Config
# # from smithy_aws_core.identity.environment import EnvironmentCredentialsResolver

# # load_dotenv()

# # # ==================== DATABASE SETUP ====================
# # DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

# # engine = create_engine(DATABASE_URL)
# # SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# # Base = declarative_base()

# # # ==================== DATABASE MODELS ====================
# # class Employee(Base):
# #     __tablename__ = "employees"
    
# #     id = Column(Integer, primary_key=True, index=True)
# #     name = Column(String(100), nullable=False)
# #     email = Column(String(100), unique=True, nullable=False)
# #     department = Column(String(50))
# #     last_working_date = Column(Date)
# #     status = Column(String(20), default="Resigned")
# #     created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
# #     exit_interview = relationship("ExitInterview", back_populates="employee", uselist=False)

# # class ExitInterview(Base):
# #     __tablename__ = "exit_interviews"
    
# #     id = Column(Integer, primary_key=True, index=True)
# #     employee_id = Column(Integer, ForeignKey("employees.id"))
# #     form_token = Column(String(255), unique=True, nullable=False)
# #     completed = Column(Boolean, default=False)
# #     questions_json = Column(Text)
# #     created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
# #     employee = relationship("Employee", back_populates="exit_interview")
# #     responses = relationship("InterviewResponse", back_populates="interview")

# # class InterviewResponse(Base):
# #     __tablename__ = "interview_responses"
    
# #     id = Column(Integer, primary_key=True, index=True)
# #     interview_id = Column(Integer, ForeignKey("exit_interviews.id"))
# #     question = Column(Text, nullable=False)
# #     answer = Column(Text, nullable=False)
# #     created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
# #     interview = relationship("ExitInterview", back_populates="responses")

# # # ==================== PYDANTIC SCHEMAS ====================
# # class EmployeeCreate(BaseModel):
# #     name: str
# #     email: EmailStr
# #     department: str
# #     last_working_date: date
# #     questions: Optional[List[str]] = None
    
# #     @field_validator('name')
# #     def name_must_not_be_empty(cls, v):
# #         if not v or not v.strip():
# #             raise ValueError('Name cannot be empty')
# #         return v.strip()

# # class EmployeeResponse(BaseModel):
# #     id: int
# #     name: str
# #     email: str
# #     department: str
# #     last_working_date: date
# #     status: str
# #     created_at: datetime
    
# #     class Config:
# #         from_attributes = True

# # class InterviewResponseDetail(BaseModel):
# #     id: int
# #     question: str
# #     answer: str
# #     created_at: datetime
    
# #     class Config:
# #         from_attributes = True

# # # ==================== BEDROCK VALIDATION & CLEANING ====================
# # def validate_and_clean_answer(raw_answer: str, question: str) -> tuple[bool, str]:
# #     """
# #     Use Bedrock to validate AND clean the answer
# #     Returns: (is_valid, cleaned_answer)
# #     """
# #     try:
# #         if not raw_answer or len(raw_answer.strip()) < 3:
# #             return False, ""
        
# #         # Additional pre-validation checks
# #         answer_lower = raw_answer.lower().strip()
        
# #         # Check for common non-answers
# #         non_answers = [
# #             "i don't know", "no comment", "i prefer not to say",
# #             "pass", "skip", "next question", "i don't want to answer",
# #             "are you there", "can you hear me", "do you copy"
# #         ]
        
# #         if any(non_answer in answer_lower for non_answer in non_answers):
# #             return False, ""
        
# #         # Check if it's just a rating without context
# #         if answer_lower in ["1", "2", "3", "4", "5", "one", "two", "three", "four", "five"]:
# #             return False, "Rating without context"
        
# #         # Check for very short answers that are likely incomplete
# #         if len(raw_answer.split()) < 3:
# #             return False, ""
        
# #         bedrock = boto3.client('bedrock-runtime', region_name=os.getenv("AWS_REGION", "us-east-1"))
        
# #         prompt = f"""Analyze if this is a valid answer to the question. Then clean it if valid.

# # Question: {question}
# # User Response: {raw_answer}

# # Instructions:
# # 1. Check if this is a REAL ANSWER or just a request for repetition/clarification
# # 2. Invalid responses include: "sorry", "repeat", "didn't hear", "come again", "pardon", etc.
# # 3. If VALID, extract and clean the answer (remove filler words, greetings)
# # 4. If INVALID, return "INVALID"

# # Respond in this exact format:
# # VALID: [cleaned answer]
# # OR
# # INVALID

# # Your response:"""

# #         body = json.dumps({
# #             "anthropic_version": "bedrock-2023-05-31",
# #             "max_tokens": 150,
# #             "temperature": 0.1,
# #             "messages": [
# #                 {
# #                     "role": "user",
# #                     "content": prompt
# #                 }
# #             ]
# #         })
        
# #         response = bedrock.invoke_model(
# #             body=body,
# #             modelId="arn:aws:bedrock:us-east-1:762233739050:inference-profile/us.anthropic.claude-3-5-sonnet-20240620-v1:0",
# #             accept="application/json",
# #             contentType="application/json"
# #         )
        
# #         response_body = json.loads(response.get('body').read())
# #         result = response_body.get('content', [{}])[0].get('text', '').strip()
        
# #         if result.startswith("VALID:"):
# #             cleaned = result.replace("VALID:", "").strip()
# #             return True, cleaned
# #         else:
# #             return False, ""
    
# #     except Exception as e:
# #         print(f"⚠️ Bedrock validation error: {e} - using fallback")
# #         # Enhanced fallback validation
# #         invalid_phrases = [
# #             "sorry", "repeat", "didn't hear", "come again", "pardon",
# #             "what was", "can you say", "didn't understand", "breaking up",
# #             "are you there", "can you hear me", "i can't hear", "do you copy",
# #             "didn't get", "didn't understand", "don't understand", "what do you mean",
# #             "what does that mean", "can you repeat", "say again", "what did you say",
# #             "i didn't get that", "i didn't get you", "didn't get you"
# #         ]
        
# #         # Check for very short answers
# #         if len(raw_answer.split()) < 3:
# #             return False, ""
        
# #         # Check for answers that indicate the user didn't understand the question
# #         if any(phrase in raw_answer.lower() for phrase in ["didn't get", "didn't understand", "don't understand", "what do you mean", "what does that mean"]):
# #             return False, ""
        
# #         raw_lower = raw_answer.lower()
# #         if any(phrase in raw_lower for phrase in invalid_phrases):
# #             return False, ""
# #         return True, raw_answer.strip()

# # # ==================== NOVA SONIC CLIENT ====================
# # class NovaInterviewClient:
# #     def __init__(self, employee_name: str, questions: List[str], websocket: WebSocket, db: Session, interview_id: int, region='us-east-1'):
# #         self.model_id = 'amazon.nova-sonic-v1:0'
# #         self.region = region
# #         self.employee_name = employee_name
# #         self.questions = questions
# #         self.websocket = websocket
# #         self.db = db
# #         self.interview_id = interview_id
# #         self.client = None
# #         self.stream = None
# #         self.is_active = False
        
# #         self.prompt_name = str(uuid.uuid4())
# #         self.system_content_name = str(uuid.uuid4())
# #         self.audio_content_name = str(uuid.uuid4())
        
# #         # ===== STATE TRACKING =====
# #         self.current_q_idx = -1
# #         self.user_answer_buffer = ""
# #         self.saved_responses = set()
# #         self.last_nova_text = ""
# #         self.waiting_for_answer = False
# #         self.question_text_buffer = []
# #         self.silence_counter = 0
# #         self.last_user_text_time = None
# #         self.silence_detection_task = None
# #         self.answer_complete = False  # Flag to track if answer is complete
# #         self.last_question_time = None
# #         self.expected_next_question = 0  # Track which question we expect next
        
# #         # ===== DYNAMIC QUESTION MATCHING =====
# #         self.question_keywords = self._extract_all_question_keywords()
# #         self.question_vectors = self._create_question_vectors()
    
# #     def _initialize_client(self):
# #         """Initialize Bedrock client"""
# #         resolver = EnvironmentCredentialsResolver()
# #         config = Config(
# #             endpoint_uri=f"https://bedrock-runtime.{self.region}.amazonaws.com",
# #             region=self.region,
# #             aws_credentials_identity_resolver=resolver
# #         )
# #         self.client = BedrockRuntimeClient(config=config)
# #         print("✅ Bedrock client initialized")
    
# #     async def send_event(self, event_json):
# #         """Send event to stream"""
# #         event = InvokeModelWithBidirectionalStreamInputChunk(
# #             value=BidirectionalInputPayloadPart(bytes_=event_json.encode('utf-8'))
# #         )
# #         await self.stream.input_stream.send(event)
    
# #     def _extract_all_question_keywords(self):
# #         """Extract keywords for all questions"""
# #         all_keywords = []
# #         for question in self.questions:
# #             keywords = self._extract_question_keywords(question)
# #             all_keywords.append(keywords)
# #         return all_keywords
    
# #     def _extract_question_keywords(self, question: str) -> List[str]:
# #         """Extract unique keywords from question for matching"""
# #         # Remove common words and punctuation
# #         common_words = {
# #             'the', 'a', 'an', 'is', 'was', 'were', 'are', 'your', 'you', 'to', 
# #             'in', 'on', 'at', 'of', 'for', 'with', 'did', 'do', 'does', 'would', 
# #             'could', 'should', 'and', 'that', 'have', 'this', 'will', 'would', 
# #             'should', 'could', 'be', 'it', 'not', 'or', 'but', 'if', 'as', 'by'
# #         }
        
# #         # Remove punctuation and convert to lowercase
# #         clean_question = re.sub(r'[^\w\s]', '', question.lower())
# #         words = clean_question.split()
        
# #         # Filter out common words and short words
# #         keywords = [w for w in words if len(w) > 3 and w not in common_words]
        
# #         # Return unique keywords
# #         return list(set(keywords))
    
# #     def _create_question_vectors(self):
# #         """Create frequency vectors for each question"""
# #         vectors = []
# #         for keywords in self.question_keywords:
# #             vector = Counter(keywords)
# #             vectors.append(vector)
# #         return vectors
    
# #     def _match_nova_question(self, nova_text: str) -> int:
# #         """Match Nova's question to our question list using dynamic matching"""
# #         nova_lower = nova_text.lower()
        
# #         # Clean the Nova text
# #         clean_nova = re.sub(r'[^\w\s]', '', nova_lower)
# #         nova_words = clean_nova.split()
# #         nova_vector = Counter(nova_words)
        
# #         best_match_idx = -1
# #         best_match_score = 0
        
# #         # Calculate similarity with each question
# #         for idx, question_vector in enumerate(self.question_vectors):
# #             if idx in self.saved_responses:
# #                 continue  # Skip already answered questions
            
# #             # Calculate Jaccard similarity
# #             intersection = sum((nova_vector & question_vector).values())
# #             union = sum((nova_vector | question_vector).values())
            
# #             if union == 0:
# #                 similarity = 0
# #             else:
# #                 similarity = intersection / union
            
# #             # Additional bonus for exact keyword matches
# #             keyword_matches = sum(1 for kw in self.question_keywords[idx] if kw in nova_lower)
# #             keyword_bonus = keyword_matches / len(self.question_keywords[idx]) if self.question_keywords[idx] else 0
            
# #             # Combined score
# #             combined_score = (similarity * 0.6) + (keyword_bonus * 0.4)
            
# #             if combined_score > best_match_score and combined_score >= 0.3:  # Lowered threshold
# #                 best_match_score = combined_score
# #                 best_match_idx = idx
        
# #         if best_match_idx >= 0:
# #             print(f"✅ Matched Q{best_match_idx + 1} with {best_match_score:.0%} confidence")
# #         else:
# #             print(f"⚠️ No question match found in: {nova_text[:60]}...")
        
# #         return best_match_idx
    
# #     def _is_repetition(self, new_text: str, existing_buffer: str) -> bool:
# #         """Check if new text is likely a repetition of existing content"""
# #         if not existing_buffer:
# #             return False
        
# #         # Simple check for exact repetition
# #         if new_text.lower() in existing_buffer.lower():
# #             return True
        
# #         # Check if it's a very short fragment that might be a repetition
# #         if len(new_text.split()) < 3 and new_text.lower() in existing_buffer.lower():
# #             return True
        
# #         return False
    
# #     def _is_repetition_request(self, text: str) -> bool:
# #         """Check if the user is asking for repetition"""
# #         repetition_phrases = [
# #             "come again", "repeat", "say again", "what did you say", 
# #             "didn't hear", "didn't get that", "didn't understand",
# #             "can you repeat", "pardon", "sorry", "could you repeat",
# #             "couldn't get you", "didn't get you", "don't understand", "can't understand"
# #         ]
        
# #         text_lower = text.lower()
# #         return any(phrase in text_lower for phrase in repetition_phrases)
    
# #     async def _check_for_silence(self):
# #         """Check if there's been silence long enough to consider the answer complete"""
# #         if not self.waiting_for_answer or not self.last_user_text_time or self.answer_complete:
# #             return False
        
# #         silence_duration = datetime.now(timezone.utc) - self.last_user_text_time
# #         # If silence for more than 5 seconds and we have at least 4 words, consider answer complete
# #         if silence_duration.total_seconds() > 5:
# #             word_count = len(self.user_answer_buffer.split())
# #             if word_count >= 4:
# #                 # Additional check: make sure the answer doesn't indicate confusion
# #                 answer_lower = self.user_answer_buffer.lower()
# #                 confusion_phrases = [
# #                     "didn't get", "didn't understand", "don't understand", 
# #                     "what do you mean", "what does that mean", "can you repeat",
# #                     "say again", "what did you say", "i didn't get that"
# #                 ]
                
# #                 if not any(phrase in answer_lower for phrase in confusion_phrases):
# #                     return True
# #         return False
    
# #     async def _silence_detection_loop(self):
# #         """Background task to detect silence and save answers"""
# #         while self.is_active:
# #             await asyncio.sleep(1)  # Check every second
            
# #             if await self._check_for_silence() and self.user_answer_buffer.strip():
# #                 if self.current_q_idx >= 0 and self.current_q_idx not in self.saved_responses:
# #                     print(f"\n🔇 SILENCE DETECTED - Saving answer for Q{self.current_q_idx + 1}")
# #                     success = await self._save_response_to_db(
# #                         self.current_q_idx,
# #                         self.questions[self.current_q_idx],
# #                         self.user_answer_buffer.strip()
# #                     )
# #                     if success:
# #                         self.answer_complete = True
# #                         self.user_answer_buffer = ""
# #                         self.last_user_text_time = None
    
# #     async def start_session(self):
# #         """Start Nova Sonic session"""
# #         if not self.client:
# #             self._initialize_client()
        
# #         try:
# #             print("📡 Starting bidirectional stream...")
# #             self.stream = await self.client.invoke_model_with_bidirectional_stream(
# #                 InvokeModelWithBidirectionalStreamOperationInput(model_id=self.model_id)
# #             )
# #             self.is_active = True
# #             print("✅ Stream started")
            
# #             # Start silence detection task
# #             self.silence_detection_task = asyncio.create_task(self._silence_detection_loop())
            
# #             # Session start
# #             await self.send_event(json.dumps({
# #                 "event": {
# #                     "sessionStart": {
# #                         "inferenceConfiguration": {
# #                             "maxTokens": 1024,
# #                             "topP": 0.9,
# #                             "temperature": 0.7
# #                         }
# #                     }
# #                 }
# #             }))
            
# #             # Prompt start with AUDIO OUTPUT
# #             await self.send_event(json.dumps({
# #                 "event": {
# #                     "promptStart": {
# #                         "promptName": self.prompt_name,
# #                         "textOutputConfiguration": {
# #                             "mediaType": "text/plain"
# #                         },
# #                         "audioOutputConfiguration": {
# #                             "mediaType": "audio/lpcm",
# #                             "sampleRateHertz": 24000,
# #                             "sampleSizeBits": 16,
# #                             "channelCount": 1,
# #                             "voiceId": "matthew",
# #                             "encoding": "base64",
# #                             "audioType": "SPEECH"
# #                         }
# #                     }
# #                 }
# #             }))
            
# #             # System content
# #             await self.send_event(json.dumps({
# #                 "event": {
# #                     "contentStart": {
# #                         "promptName": self.prompt_name,
# #                         "contentName": self.system_content_name,
# #                         "type": "TEXT",
# #                         "interactive": False,
# #                         "role": "SYSTEM",
# #                         "textInputConfiguration": {
# #                             "mediaType": "text/plain"
# #                         }
# #                     }
# #                 }
# #             }))
            
# #             questions_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(self.questions)])
            
# #             system_text = f"""You are Nova conducting an EXIT INTERVIEW with {self.employee_name}.

# # CRITICAL RULES:
# # 1. Ask EXACTLY these {len(self.questions)} questions IN ORDER
# # 2. Ask ONE question at a time
# # 3. WAIT for the user's COMPLETE answer before moving to the next question
# # 4. If the user asks you to repeat, repeat the SAME question again
# # 5. Do NOT skip any questions
# # 6. After the last question is answered, say: "Thank you for completing the exit interview. Goodbye."

# # QUESTIONS:
# # {questions_text}

# # Start by greeting {self.employee_name} and asking the FIRST question immediately."""

# #             await self.send_event(json.dumps({
# #                 "event": {
# #                     "textInput": {
# #                         "promptName": self.prompt_name,
# #                         "contentName": self.system_content_name,
# #                         "content": system_text
# #                     }
# #                 }
# #             }))
            
# #             await self.send_event(json.dumps({
# #                 "event": {
# #                     "contentEnd": {
# #                         "promptName": self.prompt_name,
# #                         "contentName": self.system_content_name
# #                     }
# #                 }
# #             }))
            
# #             print("✅ System prompt sent")
# #             asyncio.create_task(self._process_responses())
        
# #         except Exception as e:
# #             print(f"❌ Error starting session: {e}")
# #             traceback.print_exc()
# #             raise
    
# #     async def start_audio_input(self):
# #         """Start audio input"""
# #         await self.send_event(json.dumps({
# #             "event": {
# #                 "contentStart": {
# #                     "promptName": self.prompt_name,
# #                     "contentName": self.audio_content_name,
# #                     "type": "AUDIO",
# #                     "interactive": True,
# #                     "role": "USER",
# #                     "audioInputConfiguration": {
# #                         "mediaType": "audio/lpcm",
# #                         "sampleRateHertz": 16000,
# #                         "sampleSizeBits": 16,
# #                         "channelCount": 1,
# #                         "audioType": "SPEECH",
# #                         "encoding": "base64"
# #                     }
# #                 }
# #             }
# #         }))
# #         print("✅ Audio input started")
    
# #     async def send_audio_chunk(self, audio_bytes):
# #         """Send audio chunk"""
# #         if not self.is_active:
# #             return
        
# #         blob = base64.b64encode(audio_bytes).decode('utf-8')
# #         try:
# #             await self.send_event(json.dumps({
# #                 "event": {
# #                     "audioInput": {
# #                         "promptName": self.prompt_name,
# #                         "contentName": self.audio_content_name,
# #                         "content": blob
# #                     }
# #                 }
# #             }))
# #         except Exception as e:
# #             print(f"⚠️ Error sending audio: {e}")
    
# #     async def _save_response_to_db(self, q_idx: int, question: str, raw_answer: str):
# #         """Save response with comprehensive validation"""
# #         try:
# #             # Prevent duplicates
# #             if q_idx in self.saved_responses:
# #                 print(f"⚠️ Q{q_idx + 1} already saved")
# #                 return False
            
# #             # Minimum length check
# #             if len(raw_answer.strip()) < 5:
# #                 print(f"⚠️ Answer too short: '{raw_answer}'")
# #                 return False
            
# #             # First check if it's a repetition request
# #             if self._is_repetition_request(raw_answer):
# #                 print(f"🔄 Repetition request detected, not saving as answer")
# #                 return False
            
# #             # USE BEDROCK FOR VALIDATION + CLEANING
# #             is_valid, cleaned_answer = validate_and_clean_answer(raw_answer, question)
            
# #             if not is_valid:
# #                 print(f"❌ INVALID RESPONSE BLOCKED: '{raw_answer[:50]}'")
# #                 # Notify user their response wasn't saved
# #                 await self.websocket.send_json({
# #                     'type': 'validation_failed',
# #                     'message': 'Response was not a valid answer. Please provide a more complete answer.'
# #                 })
# #                 return False
            
# #             print(f"\n{'='*80}")
# #             print(f"💾 SAVING VALID RESPONSE Q{q_idx + 1}/{len(self.questions)}")
# #             print(f"{'='*80}")
# #             print(f"Question: {question}")
# #             print(f"Raw: {raw_answer[:80]}...")
# #             print(f"Cleaned: {cleaned_answer[:80]}...")
            
# #             # Save to DB
# #             db_response = InterviewResponse(
# #                 interview_id=self.interview_id,
# #                 question=question,
# #                 answer=cleaned_answer
# #             )
# #             self.db.add(db_response)
# #             self.db.commit()
            
# #             self.saved_responses.add(q_idx)
# #             self.expected_next_question = q_idx + 1  # Update expected next question
            
# #             print(f"✅ SAVED Q{q_idx + 1} - Total: {len(self.saved_responses)}/{len(self.questions)}")
# #             print(f"{'='*80}\n")
            
# #             # Notify frontend
# #             await self.websocket.send_json({
# #                 'type': 'response_saved',
# #                 'q_index': q_idx,
# #                 'question': question,
# #                 'answer': cleaned_answer
# #             })
            
# #             return True
        
# #         except Exception as e:
# #             print(f"❌ Error saving: {e}")
# #             traceback.print_exc()
# #             try:
# #                 self.db.rollback()
# #             except:
# #                 pass
# #             return False
    
# #     async def _process_responses(self):
# #         """Process responses from Nova"""
# #         try:
# #             while self.is_active:
# #                 try:
# #                     output = await self.stream.await_output()
# #                     result = await output[1].receive()
                    
# #                     if not result.value or not result.value.bytes_:
# #                         continue
                    
# #                     response_data = result.value.bytes_.decode('utf-8')
# #                     json_data = json.loads(response_data)
                    
# #                     if 'event' not in json_data:
# #                         continue
                    
# #                     event = json_data['event']
                    
# #                     # ============ TEXT OUTPUT ============
# #                     if 'textOutput' in event:
# #                         text = event['textOutput'].get('content', '')
# #                         role = event['textOutput'].get('role', 'ASSISTANT')
                        
# #                         if role == "ASSISTANT" and text.strip():
# #                             print(f"🤖 Nova: {text[:120]}...")
                            
# #                             # Send to frontend
# #                             await self.websocket.send_json({
# #                                 'type': 'text',
# #                                 'content': text,
# #                                 'role': 'ASSISTANT'
# #                             })
                            
# #                             # Check if Nova asked a question
# #                             if '?' in text:
# #                                 # Match to question list
# #                                 matched_idx = self._match_nova_question(text)
                                
# #                                 # If we didn't get a match but we expect a specific question, try to use that
# #                                 if matched_idx == -1 and self.expected_next_question < len(self.questions):
# #                                     print(f"⚠️ No match found, using expected question Q{self.expected_next_question + 1}")
# #                                     matched_idx = self.expected_next_question
                                
# #                                 if matched_idx >= 0 and matched_idx not in self.saved_responses:
# #                                     # Save previous answer if we were waiting and have content
# #                                     if self.waiting_for_answer and self.user_answer_buffer.strip():
# #                                         # Check if the user was asking for repetition
# #                                         if self._is_repetition_request(self.user_answer_buffer):
# #                                             print(f"🔄 User requested repetition, not saving as answer")
# #                                             # Reset buffer and continue with the same question
# #                                             self.user_answer_buffer = ""
# #                                             self.last_user_text_time = None
# #                                             self.answer_complete = False
# #                                         else:
# #                                             # Try to save as a normal answer
# #                                             if len(self.user_answer_buffer.strip()) >= 5 and len(self.user_answer_buffer.split()) >= 3:
# #                                                 success = await self._save_response_to_db(
# #                                                     self.current_q_idx,
# #                                                     self.questions[self.current_q_idx],
# #                                                     self.user_answer_buffer.strip()
# #                                                 )
# #                                                 if not success:
# #                                                     # If saving failed, don't move to the next question
# #                                                     print(f"⚠️ Previous answer not valid, not moving to next question")
# #                                                     # Reset buffer to try again
# #                                                     self.user_answer_buffer = ""
# #                                                     self.last_user_text_time = None
# #                                                     self.answer_complete = False
# #                                                     return
# #                                             else:
# #                                                 print(f"⚠️ Answer too short to save: '{self.user_answer_buffer}'")
                                    
# #                                     # Only move to a new question if it's different from the current one
# #                                     if matched_idx != self.current_q_idx:
# #                                         # Start new question
# #                                         self.current_q_idx = matched_idx
# #                                         self.waiting_for_answer = True
# #                                         self.user_answer_buffer = ""  # Clear buffer for new answer
# #                                         self.last_user_text_time = None
# #                                         self.answer_complete = False  # Reset answer complete flag
# #                                         self.last_question_time = datetime.now(timezone.utc)
                                        
# #                                         print(f"\n❓ QUESTION {self.current_q_idx + 1}: {self.questions[self.current_q_idx][:60]}...")
# #                                         print(f"   Waiting for answer...\n")
# #                                     else:
# #                                         print(f"🔄 Same question detected, continuing with Q{self.current_q_idx + 1}")
                            
# #                             # Check for goodbye
# #                             elif "goodbye" in text.lower() or "thank you for completing" in text.lower():
# #                                 print(f"\n✅ GOODBYE DETECTED")
                                
# #                                 # Save last answer if we have one and it hasn't been saved
# #                                 if self.waiting_for_answer and self.user_answer_buffer.strip():
# #                                     if self.current_q_idx >= 0 and self.current_q_idx not in self.saved_responses:
# #                                         # Check if the user was asking for repetition
# #                                         if not self._is_repetition_request(self.user_answer_buffer):
# #                                             # Only save if we have a substantial answer
# #                                             if len(self.user_answer_buffer.strip()) >= 5 and len(self.user_answer_buffer.split()) >= 3:
# #                                                 await self._save_response_to_db(
# #                                                     self.current_q_idx,
# #                                                     self.questions[self.current_q_idx],
# #                                                     self.user_answer_buffer.strip()
# #                                                 )
# #                                             else:
# #                                                 print(f"⚠️ Last answer too short or incomplete: '{self.user_answer_buffer}'")
# #                                         else:
# #                                             print(f"🔄 User requested repetition at the end, not saving as answer")
                                
# #                                 await self._finalize_interview()
# #                                 return
                            
# #                             self.last_nova_text = text
                        
# #                         elif role == "USER" and self.waiting_for_answer and text.strip():
# #                             # User speaking
# #                             print(f"👤 User: {text[:80]}...")
                            
# #                             # Only add to buffer if it's a new thought (not repetition)
# #                             if not self._is_repetition(text, self.user_answer_buffer):
# #                                 if self.user_answer_buffer:
# #                                     self.user_answer_buffer += " "
# #                                 self.user_answer_buffer += text
# #                                 self.last_user_text_time = datetime.now(timezone.utc)
                            
# #                             print(f"   [Buffer: {len(self.user_answer_buffer)} chars]")
                            
# #                             # Send to frontend
# #                             await self.websocket.send_json({
# #                                 'type': 'text',
# #                                 'content': text,
# #                                 'role': 'USER'
# #                             })
                    
# #                     # ============ AUDIO OUTPUT ============
# #                     elif 'audioOutput' in event:
# #                         audio_content = event['audioOutput'].get('content', '')
# #                         if audio_content:
# #                             await self.websocket.send_json({
# #                                 'type': 'audio',
# #                                 'data': audio_content
# #                             })
                    
# #                     # ============ COMPLETION ============
# #                     elif 'completionEnd' in event:
# #                         print("✅ Stream completion")
# #                         await self._finalize_interview()
# #                         return
                
# #                 except asyncio.TimeoutError:
# #                     continue
# #                 except Exception as e:
# #                     print(f"⚠️ Error in response processing: {e}")
# #                     traceback.print_exc()
# #                     continue
        
# #         except Exception as e:
# #             print(f"❌ Fatal error: {e}")
# #             traceback.print_exc()
# #             self.is_active = False
    
# #     async def _finalize_interview(self):
# #         """Finalize interview"""
# #         print(f"\n{'='*80}")
# #         print(f"🎉 INTERVIEW FINALIZATION")
# #         print(f"   Responses: {len(self.saved_responses)}/{len(self.questions)}")
# #         print(f"   Status: {'✅ COMPLETE' if len(self.saved_responses) == len(self.questions) else '⚠️ INCOMPLETE'}")
# #         print(f"{'='*80}\n")
        
# #         try:
# #             interview = self.db.query(ExitInterview).filter(ExitInterview.id == self.interview_id).first()
# #             if interview:
# #                 interview.completed = True
# #                 interview.employee.status = "Completed"
# #                 self.db.commit()
# #         except Exception as e:
# #             print(f"⚠️ DB error: {e}")
        
# #         try:
# #             await self.websocket.send_json({
# #                 'type': 'interview_complete',
# #                 'questions_answered': len(self.saved_responses),
# #                 'total_questions': len(self.questions)
# #             })
# #         except Exception as e:
# #             print(f"❌ Failed to send completion: {e}")
        
# #         self.is_active = False
    
# #     async def end_session(self):
# #         """End session"""
# #         if not self.is_active:
# #             return
        
# #         try:
# #             # Cancel silence detection task
# #             if self.silence_detection_task:
# #                 self.silence_detection_task.cancel()
# #                 try:
# #                     await self.silence_detection_task
# #                 except asyncio.CancelledError:
# #                     pass
            
# #             await self.send_event(json.dumps({
# #                 "event": {
# #                     "contentEnd": {
# #                         "promptName": self.prompt_name,
# #                         "contentName": self.audio_content_name
# #                     }
# #                 }
# #             }))
            
# #             await self.send_event(json.dumps({
# #                 "event": {
# #                     "promptEnd": {
# #                         "promptName": self.prompt_name
# #                     }
# #                 }
# #             }))
            
# #             await self.send_event(json.dumps({
# #                 "event": {
# #                     "sessionEnd": {}
# #                 }
# #             }))
            
# #             await self.stream.input_stream.close()
# #             self.is_active = False
# #             print("✅ Session ended")
        
# #         except Exception as e:
# #             print(f"⚠️ Error ending session: {e}")
# #             self.is_active = False

# # # ==================== AWS SES ====================
# # ses_client = boto3.client('ses', region_name=os.getenv("AWS_REGION", "us-east-1"))

# # def send_exit_interview_email(employee_email: str, employee_name: str, form_link: str) -> bool:
# #     SENDER = os.getenv("SES_SENDER_EMAIL")
# #     SUBJECT = "🎙️ Voice Exit Interview with Nova"
# #     BODY_HTML = f"""
# #     <html><body>
# #         <h1>Hello {employee_name}!</h1>
# #         <p>Have a voice conversation with Nova for your exit interview.</p>
# #         <p><a href="{form_link}">Start Voice Interview</a></p>
# #     </body></html>
# #     """
# #     try:
# #         ses_client.send_email(
# #             Source=SENDER,
# #             Destination={'ToAddresses': [employee_email]},
# #             Message={'Subject': {'Data': SUBJECT}, 'Body': {'Html': {'Data': BODY_HTML}}}
# #         )
# #         print(f"✅ Email sent to {employee_name}")
# #         return True
# #     except Exception as e:
# #         print(f"❌ Email error: {e}")
# #         return False

# # def generate_unique_token() -> str:
# #     return str(uuid.uuid4())

# # def create_form_link(token: str) -> str:
# #     return f"{os.getenv('APP_URL', 'http://localhost:8501')}/exit_interview?token={token}"

# # # ==================== FASTAPI APP ====================
# # app = FastAPI(title="Nova Sonic Exit Interview API", version="7.0.0")

# # app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# # def get_db():
# #     db = SessionLocal()
# #     try:
# #         yield db
# #     finally:
# #         db.close()

# # active_sessions: Dict[str, NovaInterviewClient] = {}

# # # ==================== API ENDPOINTS ====================

# # @app.get("/")
# # def root():
# #     return {"message": "Nova Sonic Exit Interview API", "version": "7.0.0", "status": "running"}

# # @app.post("/api/employees", response_model=EmployeeResponse, status_code=201)
# # def create_employee(employee: EmployeeCreate, db: Session = Depends(get_db)):
# #     try:
# #         existing = db.query(Employee).filter(Employee.email == employee.email).first()
# #         if existing:
# #             raise HTTPException(status_code=400, detail="Employee already exists")
        
# #         db_employee = Employee(
# #             name=employee.name,
# #             email=employee.email,
# #             department=employee.department,
# #             last_working_date=employee.last_working_date,
# #             status="Resigned"
# #         )
# #         db.add(db_employee)
# #         db.commit()
# #         db.refresh(db_employee)
        
# #         token = generate_unique_token()
# #         form_link = create_form_link(token)
        
# #         questions_json = json.dumps(employee.questions) if employee.questions else json.dumps([
# #             "What was your primary reason for leaving?",
# #             "How would you rate your overall experience with the company on a scale of 1 to 5?",
# #             "How was your relationship with your manager?",
# #             "Did you feel valued and recognized in your role?",
# #             "Would you recommend our company to others? Why or why not?"
# #         ])
        
# #         db_interview = ExitInterview(
# #             employee_id=db_employee.id,
# #             form_token=token,
# #             completed=False,
# #             questions_json=questions_json
# #         )
# #         db.add(db_interview)
# #         db.commit()
        
# #         send_exit_interview_email(db_employee.email, db_employee.name, form_link)
        
# #         return db_employee
# #     except HTTPException:
# #         raise
# #     except Exception as e:
# #         db.rollback()
# #         raise HTTPException(status_code=500, detail=str(e))

# # @app.get("/api/employees", response_model=List[EmployeeResponse])
# # def list_employees(db: Session = Depends(get_db)):
# #     return db.query(Employee).all()

# # @app.get("/api/interviews/token/{token}")
# # def get_interview_by_token(token: str, db: Session = Depends(get_db)):
# #     interview = db.query(ExitInterview).filter(ExitInterview.form_token == token).first()
# #     if not interview:
# #         raise HTTPException(status_code=404, detail="Invalid token")
# #     if interview.completed:
# #         raise HTTPException(status_code=400, detail="Interview already completed")
    
# #     questions = json.loads(interview.questions_json)
# #     return {
# #         "interview_id": interview.id,
# #         "employee_name": interview.employee.name,
# #         "employee_department": interview.employee.department,
# #         "questions": questions,
# #         "total_questions": len(questions),
# #         "completed": interview.completed
# #     }

# # @app.websocket("/ws/interview/{token}")
# # async def websocket_interview(websocket: WebSocket, token: str):
# #     await websocket.accept()
    
# #     db = SessionLocal()
# #     session_id = str(uuid.uuid4())
# #     nova_client = None
    
# #     try:
# #         interview = db.query(ExitInterview).filter(ExitInterview.form_token == token).first()
# #         if not interview:
# #             await websocket.send_json({"type": "error", "message": "Invalid token"})
# #             return
        
# #         questions = json.loads(interview.questions_json)
# #         employee_name = interview.employee.name
        
# #         print(f"\n{'='*80}")
# #         print(f"🎙️ NEW INTERVIEW: {employee_name}")
# #         print(f"📋 Questions: {len(questions)}")
# #         print(f"{'='*80}\n")
        
# #         await websocket.send_json({
# #             "type": "session_start",
# #             "session_id": session_id,
# #             "employee_name": employee_name,
# #             "total_questions": len(questions)
# #         })
        
# #         nova_client = NovaInterviewClient(
# #             employee_name,
# #             questions,
# #             websocket,
# #             db,
# #             interview.id,
# #             os.getenv("AWS_REGION", "us-east-1")
# #         )
# #         await nova_client.start_session()
        
# #         await asyncio.sleep(2)
# #         await nova_client.start_audio_input()
        
# #         active_sessions[session_id] = nova_client
        
# #         timeout_seconds = 900  # 15 minutes
# #         start_time = datetime.now(timezone.utc)
        
# #         while nova_client.is_active:
# #             try:
# #                 message = await asyncio.wait_for(websocket.receive_json(), timeout=0.5)
# #                 start_time = datetime.now(timezone.utc)
                
# #                 if message['type'] == 'audio_chunk':
# #                     audio_data = base64.b64decode(message['data'])
# #                     await nova_client.send_audio_chunk(audio_data)
                
# #                 elif message['type'] == 'close':
# #                     break
            
# #             except asyncio.TimeoutError:
# #                 elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
# #                 if elapsed > timeout_seconds:
# #                     print(f"⚠️ Interview timeout after {timeout_seconds}s")
# #                     break
# #                 continue
# #             except WebSocketDisconnect:
# #                 print("⚠️ Client disconnected")
# #                 break
# #             except Exception as e:
# #                 print(f"⚠️ Error: {e}")
# #                 break
    
# #     except Exception as e:
# #         print(f"❌ Error: {e}")
# #         traceback.print_exc()
# #         try:
# #             await websocket.send_json({"type": "error", "message": str(e)})
# #         except:
# #             pass
# #     finally:
# #         if nova_client:
# #             await nova_client.end_session()
# #         if session_id in active_sessions:
# #             del active_sessions[session_id]
# #         db.close()

# # @app.get("/api/interviews/{interview_id}/responses", response_model=List[InterviewResponseDetail])
# # def get_interview_responses(interview_id: int, db: Session = Depends(get_db)):
# #     """Get responses ordered by creation time"""
# #     return db.query(InterviewResponse).filter(
# #         InterviewResponse.interview_id == interview_id
# #     ).order_by(InterviewResponse.created_at).all()

# # @app.get("/api/stats")
# # def get_statistics(db: Session = Depends(get_db)):
# #     total = db.query(Employee).count()
# #     completed = db.query(ExitInterview).filter(ExitInterview.completed == True).count()
# #     return {
# #         "total_resignations": total,
# #         "completed_interviews": completed,
# #         "pending_interviews": total - completed,
# #         "completion_rate": (completed / total * 100) if total > 0 else 0
# #     }

# # def init_db():
# #     Base.metadata.create_all(bind=engine)
# #     print("✅ Database initialized!")

# # if __name__ == "__main__":
# #     init_db()
# #     import uvicorn
# #     print("\n🚀 Nova Sonic Exit Interview API v7.0.0")
# #     print("📡 http://0.0.0.0:8000\n")
# #     uvicorn.run(app, host="0.0.0.0", port=8000)



# """
# FIXED Nova Sonic Exit Interview Backend - COMPREHENSIVE VALIDATION
# Fixed: Invalid responses, misalignment, question matching, first question skip, deprecated datetime
# """

# from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
# from fastapi.middleware.cors import CORSMiddleware
# from sqlalchemy import create_engine, Column, Integer, String, Boolean, Date, DateTime, Text, ForeignKey
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker, Session, relationship
# from pydantic import BaseModel, EmailStr, field_validator
# from typing import List, Optional, Dict, Any
# from datetime import datetime, date, timezone, timedelta
# import os
# from dotenv import load_dotenv
# import boto3
# import uuid
# import json
# import asyncio
# import base64
# import traceback
# import re
# from collections import Counter

# from aws_sdk_bedrock_runtime.client import BedrockRuntimeClient, InvokeModelWithBidirectionalStreamOperationInput
# from aws_sdk_bedrock_runtime.models import InvokeModelWithBidirectionalStreamInputChunk, BidirectionalInputPayloadPart
# from aws_sdk_bedrock_runtime.config import Config
# from smithy_aws_core.identity.environment import EnvironmentCredentialsResolver

# load_dotenv()

# # ==================== DATABASE SETUP ====================
# DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

# engine = create_engine(DATABASE_URL)
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base = declarative_base()

# # ==================== DATABASE MODELS ====================
# class Employee(Base):
#     __tablename__ = "employees"
    
#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String(100), nullable=False)
#     email = Column(String(100), unique=True, nullable=False)
#     department = Column(String(50))
#     last_working_date = Column(Date)
#     status = Column(String(20), default="Resigned")
#     created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
#     exit_interview = relationship("ExitInterview", back_populates="employee", uselist=False)

# class ExitInterview(Base):
#     __tablename__ = "exit_interviews"
    
#     id = Column(Integer, primary_key=True, index=True)
#     employee_id = Column(Integer, ForeignKey("employees.id"))
#     form_token = Column(String(255), unique=True, nullable=False)
#     completed = Column(Boolean, default=False)
#     questions_json = Column(Text)
#     created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
#     employee = relationship("Employee", back_populates="exit_interview")
#     responses = relationship("InterviewResponse", back_populates="interview")

# class InterviewResponse(Base):
#     __tablename__ = "interview_responses"
    
#     id = Column(Integer, primary_key=True, index=True)
#     interview_id = Column(Integer, ForeignKey("exit_interviews.id"))
#     question = Column(Text, nullable=False)
#     answer = Column(Text, nullable=False)
#     created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
#     interview = relationship("ExitInterview", back_populates="responses")

# # ==================== PYDANTIC SCHEMAS ====================
# class EmployeeCreate(BaseModel):
#     name: str
#     email: EmailStr
#     department: str
#     last_working_date: date
#     questions: Optional[List[str]] = None
    
#     @field_validator('name')
#     def name_must_not_be_empty(cls, v):
#         if not v or not v.strip():
#             raise ValueError('Name cannot be empty')
#         return v.strip()

# class EmployeeResponse(BaseModel):
#     id: int
#     name: str
#     email: str
#     department: str
#     last_working_date: date
#     status: str
#     created_at: datetime
    
#     class Config:
#         from_attributes = True

# class InterviewResponseDetail(BaseModel):
#     id: int
#     question: str
#     answer: str
#     created_at: datetime
    
#     class Config:
#         from_attributes = True

# # ==================== BEDROCK VALIDATION & CLEANING ====================
# def validate_and_clean_answer(raw_answer: str, question: str) -> tuple[bool, str]:
#     """
#     Use Bedrock to validate AND clean the answer
#     Returns: (is_valid, cleaned_answer)
#     """
#     try:
#         if not raw_answer or len(raw_answer.strip()) < 3:
#             return False, ""
        
#         # Additional pre-validation checks
#         answer_lower = raw_answer.lower().strip()
        
#         # Check for common non-answers
#         non_answers = [
#             "i don't know", "no comment", "i prefer not to say",
#             "pass", "skip", "next question", "i don't want to answer",
#             "are you there", "can you hear me", "do you copy"
#         ]
        
#         if any(non_answer in answer_lower for non_answer in non_answers):
#             return False, ""
        
#         # Check if it's just a rating without context
#         if answer_lower in ["1", "2", "3", "4", "5", "one", "two", "three", "four", "five"]:
#             return False, "Rating without context"
        
#         # Check for very short answers that are likely incomplete
#         if len(raw_answer.split()) < 3:
#             return False, ""
        
#         bedrock = boto3.client('bedrock-runtime', region_name=os.getenv("AWS_REGION", "us-east-1"))
        
#         prompt = f"""Analyze if this is a valid answer to the question. Then clean it if valid.

# Question: {question}
# User Response: {raw_answer}

# Instructions:
# 1. Check if this is a REAL ANSWER or just a request for repetition/clarification
# 2. Invalid responses include: "sorry", "repeat", "didn't hear", "come again", "pardon", etc.
# 3. If VALID, extract and clean the answer (remove filler words, greetings)
# 4. If INVALID, return "INVALID"

# Respond in this exact format:
# VALID: [cleaned answer]
# OR
# INVALID

# Your response:"""

#         body = json.dumps({
#             "anthropic_version": "bedrock-2023-05-31",
#             "max_tokens": 150,
#             "temperature": 0.1,
#             "messages": [
#                 {
#                     "role": "user",
#                     "content": prompt
#                 }
#             ]
#         })
        
#         response = bedrock.invoke_model(
#             body=body,
#             modelId="arn:aws:bedrock:us-east-1:762233739050:inference-profile/us.anthropic.claude-3-5-sonnet-20240620-v1:0",
#             accept="application/json",
#             contentType="application/json"
#         )
        
#         response_body = json.loads(response.get('body').read())
#         result = response_body.get('content', [{}])[0].get('text', '').strip()
        
#         if result.startswith("VALID:"):
#             cleaned = result.replace("VALID:", "").strip()
#             return True, cleaned
#         else:
#             return False, ""
    
#     except Exception as e:
#         print(f"⚠️ Bedrock validation error: {e} - using fallback")
#         # Enhanced fallback validation
#         invalid_phrases = [
#             "sorry", "repeat", "didn't hear", "come again", "pardon",
#             "what was", "can you say", "didn't understand", "breaking up",
#             "are you there", "can you hear me", "i can't hear", "do you copy",
#             "didn't get", "didn't understand", "don't understand", "what do you mean",
#             "what does that mean", "can you repeat", "say again", "what did you say",
#             "i didn't get that", "i didn't get you", "didn't get you"
#         ]
        
#         # Check for very short answers
#         if len(raw_answer.split()) < 3:
#             return False, ""
        
#         # Check for answers that indicate the user didn't understand the question
#         if any(phrase in raw_answer.lower() for phrase in ["didn't get", "didn't understand", "don't understand", "what do you mean", "what does that mean"]):
#             return False, ""
        
#         raw_lower = raw_answer.lower()
#         if any(phrase in raw_lower for phrase in invalid_phrases):
#             return False, ""
#         return True, raw_answer.strip()

# # ==================== NOVA SONIC CLIENT ====================
# class NovaInterviewClient:
#     def __init__(self, employee_name: str, questions: List[str], websocket: WebSocket, db: Session, interview_id: int, region='us-east-1'):
#         self.model_id = 'amazon.nova-sonic-v1:0'
#         self.region = region
#         self.employee_name = employee_name
#         self.questions = questions
#         self.websocket = websocket
#         self.db = db
#         self.interview_id = interview_id
#         self.client = None
#         self.stream = None
#         self.is_active = False
        
#         self.prompt_name = str(uuid.uuid4())
#         self.system_content_name = str(uuid.uuid4())
#         self.audio_content_name = str(uuid.uuid4())
        
#         # ===== STATE TRACKING =====
#         self.current_q_idx = -1
#         self.user_answer_buffer = ""
#         self.saved_responses = set()
#         self.last_nova_text = ""
#         self.waiting_for_answer = False
#         self.question_text_buffer = []
#         self.silence_counter = 0
#         self.last_user_text_time = None
#         self.silence_detection_task = None
#         self.answer_complete = False  # Flag to track if answer is complete
#         self.last_question_time = None
#         self.expected_next_question = 0  # Track which question we expect next
        
#         # ===== DYNAMIC QUESTION MATCHING =====
#         self.question_keywords = self._extract_all_question_keywords()
#         self.question_vectors = self._create_question_vectors()
    
#     def _initialize_client(self):
#         """Initialize Bedrock client"""
#         resolver = EnvironmentCredentialsResolver()
#         config = Config(
#             endpoint_uri=f"https://bedrock-runtime.{self.region}.amazonaws.com",
#             region=self.region,
#             aws_credentials_identity_resolver=resolver
#         )
#         self.client = BedrockRuntimeClient(config=config)
#         print("✅ Bedrock client initialized")
    
#     async def send_event(self, event_json):
#         """Send event to stream"""
#         event = InvokeModelWithBidirectionalStreamInputChunk(
#             value=BidirectionalInputPayloadPart(bytes_=event_json.encode('utf-8'))
#         )
#         await self.stream.input_stream.send(event)
    
#     def _extract_all_question_keywords(self):
#         """Extract keywords for all questions"""
#         all_keywords = []
#         for question in self.questions:
#             keywords = self._extract_question_keywords(question)
#             all_keywords.append(keywords)
#         return all_keywords
    
#     def _extract_question_keywords(self, question: str) -> List[str]:
#         """Extract unique keywords from question for matching"""
#         # Remove common words and punctuation
#         common_words = {
#             'the', 'a', 'an', 'is', 'was', 'were', 'are', 'your', 'you', 'to', 
#             'in', 'on', 'at', 'of', 'for', 'with', 'did', 'do', 'does', 'would', 
#             'could', 'should', 'and', 'that', 'have', 'this', 'will', 'would', 
#             'should', 'could', 'be', 'it', 'not', 'or', 'but', 'if', 'as', 'by'
#         }
        
#         # Remove punctuation and convert to lowercase
#         clean_question = re.sub(r'[^\w\s]', '', question.lower())
#         words = clean_question.split()
        
#         # Filter out common words and short words
#         keywords = [w for w in words if len(w) > 3 and w not in common_words]
        
#         # Return unique keywords
#         return list(set(keywords))
    
#     def _create_question_vectors(self):
#         """Create frequency vectors for each question"""
#         vectors = []
#         for keywords in self.question_keywords:
#             vector = Counter(keywords)
#             vectors.append(vector)
#         return vectors
    
#     def _match_nova_question(self, nova_text: str) -> int:
#         """Match Nova's question to our question list using dynamic matching"""
#         nova_lower = nova_text.lower()
        
#         # Clean the Nova text
#         clean_nova = re.sub(r'[^\w\s]', '', nova_lower)
#         nova_words = clean_nova.split()
#         nova_vector = Counter(nova_words)
        
#         best_match_idx = -1
#         best_match_score = 0
        
#         # Calculate similarity with each question
#         for idx, question_vector in enumerate(self.question_vectors):
#             if idx in self.saved_responses:
#                 continue  # Skip already answered questions
            
#             # Calculate Jaccard similarity
#             intersection = sum((nova_vector & question_vector).values())
#             union = sum((nova_vector | question_vector).values())
            
#             if union == 0:
#                 similarity = 0
#             else:
#                 similarity = intersection / union
            
#             # Additional bonus for exact keyword matches
#             keyword_matches = sum(1 for kw in self.question_keywords[idx] if kw in nova_lower)
#             keyword_bonus = keyword_matches / len(self.question_keywords[idx]) if self.question_keywords[idx] else 0
            
#             # Combined score
#             combined_score = (similarity * 0.6) + (keyword_bonus * 0.4)
            
#             if combined_score > best_match_score and combined_score >= 0.3:  # Lowered threshold
#                 best_match_score = combined_score
#                 best_match_idx = idx
        
#         if best_match_idx >= 0:
#             print(f"✅ Matched Q{best_match_idx + 1} with {best_match_score:.0%} confidence")
#         else:
#             print(f"⚠️ No question match found in: {nova_text[:60]}...")
        
#         return best_match_idx
    
#     def _is_repetition(self, new_text: str, existing_buffer: str) -> bool:
#         """Check if new text is likely a repetition of existing content"""
#         if not existing_buffer:
#             return False
        
#         # Simple check for exact repetition
#         if new_text.lower() in existing_buffer.lower():
#             return True
        
#         # Check if it's a very short fragment that might be a repetition
#         if len(new_text.split()) < 3 and new_text.lower() in existing_buffer.lower():
#             return True
        
#         return False
    
#     def _is_repetition_request(self, text: str) -> bool:
#         """Check if the user is asking for repetition"""
#         repetition_phrases = [
#             "come again", "repeat", "say again", "what did you say", 
#             "didn't hear", "didn't get that", "didn't understand",
#             "can you repeat", "pardon", "sorry", "could you repeat",
#             "couldn't get you", "didn't get you", "don't understand", "can't understand"
#         ]
        
#         text_lower = text.lower()
#         return any(phrase in text_lower for phrase in repetition_phrases)
    
#     def _is_technical_issue(self, text: str) -> bool:
#         """Check if the user is reporting a technical issue"""
#         technical_phrases = [
#             "can't hear", "voice breaking", "audio issue", "technical issue",
#             "voice is breaking", "can't hear your voice", "audio problem"
#         ]
        
#         text_lower = text.lower()
#         return any(phrase in text_lower for phrase in technical_phrases)
    
#     async def _check_for_silence(self):
#         """Check if there's been silence long enough to consider the answer complete"""
#         if not self.waiting_for_answer or not self.last_user_text_time or self.answer_complete:
#             return False
        
#         silence_duration = datetime.now(timezone.utc) - self.last_user_text_time
#         # If silence for more than 5 seconds and we have at least 4 words, consider answer complete
#         if silence_duration.total_seconds() > 5:
#             word_count = len(self.user_answer_buffer.split())
#             if word_count >= 4:
#                 # Additional check: make sure the answer doesn't indicate confusion
#                 answer_lower = self.user_answer_buffer.lower()
#                 confusion_phrases = [
#                     "didn't get", "didn't understand", "don't understand", 
#                     "what do you mean", "what does that mean", "can you repeat",
#                     "say again", "what did you say", "i didn't get that"
#                 ]
                
#                 if not any(phrase in answer_lower for phrase in confusion_phrases):
#                     return True
#         return False
    
#     async def _silence_detection_loop(self):
#         """Background task to detect silence and save answers"""
#         while self.is_active:
#             await asyncio.sleep(1)  # Check every second
            
#             if await self._check_for_silence() and self.user_answer_buffer.strip():
#                 if self.current_q_idx >= 0 and self.current_q_idx not in self.saved_responses:
#                     print(f"\n🔇 SILENCE DETECTED - Saving answer for Q{self.current_q_idx + 1}")
#                     success = await self._save_response_to_db(
#                         self.current_q_idx,
#                         self.questions[self.current_q_idx],
#                         self.user_answer_buffer.strip()
#                     )
#                     if success:
#                         self.answer_complete = True
#                         self.user_answer_buffer = ""
#                         self.last_user_text_time = None
    
#     async def start_session(self):
#         """Start Nova Sonic session"""
#         if not self.client:
#             self._initialize_client()
        
#         try:
#             print("📡 Starting bidirectional stream...")
#             self.stream = await self.client.invoke_model_with_bidirectional_stream(
#                 InvokeModelWithBidirectionalStreamOperationInput(model_id=self.model_id)
#             )
#             self.is_active = True
#             print("✅ Stream started")
            
#             # Start silence detection task
#             self.silence_detection_task = asyncio.create_task(self._silence_detection_loop())
            
#             # Session start
#             await self.send_event(json.dumps({
#                 "event": {
#                     "sessionStart": {
#                         "inferenceConfiguration": {
#                             "maxTokens": 1024,
#                             "topP": 0.9,
#                             "temperature": 0.7
#                         }
#                     }
#                 }
#             }))
            
#             # Prompt start with AUDIO OUTPUT
#             await self.send_event(json.dumps({
#                 "event": {
#                     "promptStart": {
#                         "promptName": self.prompt_name,
#                         "textOutputConfiguration": {
#                             "mediaType": "text/plain"
#                         },
#                         "audioOutputConfiguration": {
#                             "mediaType": "audio/lpcm",
#                             "sampleRateHertz": 24000,
#                             "sampleSizeBits": 16,
#                             "channelCount": 1,
#                             "voiceId": "matthew",
#                             "encoding": "base64",
#                             "audioType": "SPEECH"
#                         }
#                     }
#                 }
#             }))
            
#             # System content
#             await self.send_event(json.dumps({
#                 "event": {
#                     "contentStart": {
#                         "promptName": self.prompt_name,
#                         "contentName": self.system_content_name,
#                         "type": "TEXT",
#                         "interactive": False,
#                         "role": "SYSTEM",
#                         "textInputConfiguration": {
#                             "mediaType": "text/plain"
#                         }
#                     }
#                 }
#             }))
            
#             questions_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(self.questions)])
            
#             system_text = f"""You are Nova conducting an EXIT INTERVIEW with {self.employee_name}.

# CRITICAL RULES:
# 1. Ask EXACTLY these {len(self.questions)} questions IN ORDER
# 2. Ask ONE question at a time
# 3. WAIT for the user's COMPLETE answer before moving to the next question
# 4. If the user asks you to repeat, repeat the SAME question again
# 5. Do NOT skip any questions
# 6. After the last question is answered, say: "Thank you for completing the exit interview. Goodbye."

# QUESTIONS:
# {questions_text}

# Start by greeting {self.employee_name} and asking the FIRST question immediately."""

#             await self.send_event(json.dumps({
#                 "event": {
#                     "textInput": {
#                         "promptName": self.prompt_name,
#                         "contentName": self.system_content_name,
#                         "content": system_text
#                     }
#                 }
#             }))
            
#             await self.send_event(json.dumps({
#                 "event": {
#                     "contentEnd": {
#                         "promptName": self.prompt_name,
#                         "contentName": self.system_content_name
#                     }
#                 }
#             }))
            
#             print("✅ System prompt sent")
#             asyncio.create_task(self._process_responses())
        
#         except Exception as e:
#             print(f"❌ Error starting session: {e}")
#             traceback.print_exc()
#             raise
    
#     async def start_audio_input(self):
#         """Start audio input"""
#         await self.send_event(json.dumps({
#             "event": {
#                 "contentStart": {
#                     "promptName": self.prompt_name,
#                     "contentName": self.audio_content_name,
#                     "type": "AUDIO",
#                     "interactive": True,
#                     "role": "USER",
#                     "audioInputConfiguration": {
#                         "mediaType": "audio/lpcm",
#                         "sampleRateHertz": 16000,
#                         "sampleSizeBits": 16,
#                         "channelCount": 1,
#                         "audioType": "SPEECH",
#                         "encoding": "base64"
#                     }
#                 }
#             }
#         }))
#         print("✅ Audio input started")
    
#     async def send_audio_chunk(self, audio_bytes):
#         """Send audio chunk"""
#         if not self.is_active:
#             return
        
#         blob = base64.b64encode(audio_bytes).decode('utf-8')
#         try:
#             await self.send_event(json.dumps({
#                 "event": {
#                     "audioInput": {
#                         "promptName": self.prompt_name,
#                         "contentName": self.audio_content_name,
#                         "content": blob
#                     }
#                 }
#             }))
#         except Exception as e:
#             print(f"⚠️ Error sending audio: {e}")
    
#     async def _save_response_to_db(self, q_idx: int, question: str, raw_answer: str):
#         """Save response with comprehensive validation"""
#         try:
#             # Prevent duplicates
#             if q_idx in self.saved_responses:
#                 print(f"⚠️ Q{q_idx + 1} already saved")
#                 return False
            
#             # Minimum length check
#             if len(raw_answer.strip()) < 5:
#                 print(f"⚠️ Answer too short: '{raw_answer}'")
#                 return False
            
#             # First check if it's a repetition request
#             if self._is_repetition_request(raw_answer):
#                 print(f"🔄 Repetition request detected, not saving as answer")
#                 return False
            
#             # Check if it's a technical issue
#             if self._is_technical_issue(raw_answer):
#                 print(f"🔧 Technical issue detected, not saving as answer")
#                 return False
            
#             # USE BEDROCK FOR VALIDATION + CLEANING
#             is_valid, cleaned_answer = validate_and_clean_answer(raw_answer, question)
            
#             if not is_valid:
#                 print(f"❌ INVALID RESPONSE BLOCKED: '{raw_answer[:50]}'")
#                 # Notify user their response wasn't saved
#                 await self.websocket.send_json({
#                     'type': 'validation_failed',
#                     'message': 'Response was not a valid answer. Please provide a more complete answer.'
#                 })
#                 return False
            
#             print(f"\n{'='*80}")
#             print(f"💾 SAVING VALID RESPONSE Q{q_idx + 1}/{len(self.questions)}")
#             print(f"{'='*80}")
#             print(f"Question: {question}")
#             print(f"Raw: {raw_answer[:80]}...")
#             print(f"Cleaned: {cleaned_answer[:80]}...")
            
#             # Save to DB
#             db_response = InterviewResponse(
#                 interview_id=self.interview_id,
#                 question=question,
#                 answer=cleaned_answer
#             )
#             self.db.add(db_response)
#             self.db.commit()
            
#             self.saved_responses.add(q_idx)
#             self.expected_next_question = q_idx + 1  # Update expected next question
            
#             print(f"✅ SAVED Q{q_idx + 1} - Total: {len(self.saved_responses)}/{len(self.questions)}")
#             print(f"{'='*80}\n")
            
#             # Notify frontend
#             await self.websocket.send_json({
#                 'type': 'response_saved',
#                 'q_index': q_idx,
#                 'question': question,
#                 'answer': cleaned_answer
#             })
            
#             return True
        
#         except Exception as e:
#             print(f"❌ Error saving: {e}")
#             traceback.print_exc()
#             try:
#                 self.db.rollback()
#             except:
#                 pass
#             return False
    
#     async def _process_responses(self):
#         """Process responses from Nova"""
#         try:
#             while self.is_active:
#                 try:
#                     output = await self.stream.await_output()
#                     result = await output[1].receive()
                    
#                     if not result.value or not result.value.bytes_:
#                         continue
                    
#                     response_data = result.value.bytes_.decode('utf-8')
#                     json_data = json.loads(response_data)
                    
#                     if 'event' not in json_data:
#                         continue
                    
#                     event = json_data['event']
                    
#                     # ============ TEXT OUTPUT ============
#                     if 'textOutput' in event:
#                         text = event['textOutput'].get('content', '')
#                         role = event['textOutput'].get('role', 'ASSISTANT')
                        
#                         if role == "ASSISTANT" and text.strip():
#                             print(f"🤖 Nova: {text[:120]}...")
                            
#                             # Send to frontend
#                             await self.websocket.send_json({
#                                 'type': 'text',
#                                 'content': text,
#                                 'role': 'ASSISTANT'
#                             })
                            
#                             # Check if Nova asked a question
#                             if '?' in text:
#                                 # Match to question list
#                                 matched_idx = self._match_nova_question(text)
                                
#                                 # If we didn't get a match but we expect a specific question, try to use that
#                                 if matched_idx == -1 and self.expected_next_question < len(self.questions):
#                                     print(f"⚠️ No match found, using expected question Q{self.expected_next_question + 1}")
#                                     matched_idx = self.expected_next_question
                                
#                                 if matched_idx >= 0 and matched_idx not in self.saved_responses:
#                                     # Save previous answer if we were waiting and have content
#                                     if self.waiting_for_answer and self.user_answer_buffer.strip():
#                                         # Check if the user was asking for repetition
#                                         if self._is_repetition_request(self.user_answer_buffer):
#                                             print(f"🔄 User requested repetition, not saving as answer")
#                                             # Reset buffer and continue with the same question
#                                             self.user_answer_buffer = ""
#                                             self.last_user_text_time = None
#                                             self.answer_complete = False
#                                         elif self._is_technical_issue(self.user_answer_buffer):
#                                             print(f"🔧 User reported technical issue, not saving as answer")
#                                             # Reset buffer and continue with the same question
#                                             self.user_answer_buffer = ""
#                                             self.last_user_text_time = None
#                                             self.answer_complete = False
#                                         else:
#                                             # Try to save as a normal answer
#                                             if len(self.user_answer_buffer.strip()) >= 5 and len(self.user_answer_buffer.split()) >= 3:
#                                                 success = await self._save_response_to_db(
#                                                     self.current_q_idx,
#                                                     self.questions[self.current_q_idx],
#                                                     self.user_answer_buffer.strip()
#                                                 )
#                                                 # If saving failed, just reset buffer and continue
#                                                 # Don't block the interview
#                                                 if not success:
#                                                     print(f"⚠️ Previous answer not valid, resetting buffer")
#                                                     self.user_answer_buffer = ""
#                                                     self.last_user_text_time = None
#                                                     self.answer_complete = False
#                                             else:
#                                                 print(f"⚠️ Answer too short to save: '{self.user_answer_buffer}'")
                                    
#                                     # Only move to a new question if it's different from the current one
#                                     if matched_idx != self.current_q_idx:
#                                         # Start new question
#                                         self.current_q_idx = matched_idx
#                                         self.waiting_for_answer = True
#                                         self.user_answer_buffer = ""  # Clear buffer for new answer
#                                         self.last_user_text_time = None
#                                         self.answer_complete = False  # Reset answer complete flag
#                                         self.last_question_time = datetime.now(timezone.utc)
                                        
#                                         print(f"\n❓ QUESTION {self.current_q_idx + 1}: {self.questions[self.current_q_idx][:60]}...")
#                                         print(f"   Waiting for answer...\n")
#                                     else:
#                                         print(f"🔄 Same question detected, continuing with Q{self.current_q_idx + 1}")
                            
#                             # Check for goodbye
#                             elif "goodbye" in text.lower() or "thank you for completing" in text.lower():
#                                 print(f"\n✅ GOODBYE DETECTED")
                                
#                                 # Save last answer if we have one and it hasn't been saved
#                                 if self.waiting_for_answer and self.user_answer_buffer.strip():
#                                     if self.current_q_idx >= 0 and self.current_q_idx not in self.saved_responses:
#                                         # Check if the user was asking for repetition
#                                         if not self._is_repetition_request(self.user_answer_buffer) and not self._is_technical_issue(self.user_answer_buffer):
#                                             # Only save if we have a substantial answer
#                                             if len(self.user_answer_buffer.strip()) >= 5 and len(self.user_answer_buffer.split()) >= 3:
#                                                 await self._save_response_to_db(
#                                                     self.current_q_idx,
#                                                     self.questions[self.current_q_idx],
#                                                     self.user_answer_buffer.strip()
#                                                 )
#                                             else:
#                                                 print(f"⚠️ Last answer too short or incomplete: '{self.user_answer_buffer}'")
#                                         else:
#                                             print(f"🔄 User requested repetition or reported issue at the end, not saving as answer")
                                
#                                 await self._finalize_interview()
#                                 return
                            
#                             self.last_nova_text = text
                        
#                         elif role == "USER" and self.waiting_for_answer and text.strip():
#                             # User speaking
#                             print(f"👤 User: {text[:80]}...")
                            
#                             # Only add to buffer if it's a new thought (not repetition)
#                             if not self._is_repetition(text, self.user_answer_buffer):
#                                 if self.user_answer_buffer:
#                                     self.user_answer_buffer += " "
#                                 self.user_answer_buffer += text
#                                 self.last_user_text_time = datetime.now(timezone.utc)
                            
#                             print(f"   [Buffer: {len(self.user_answer_buffer)} chars]")
                            
#                             # Send to frontend
#                             await self.websocket.send_json({
#                                 'type': 'text',
#                                 'content': text,
#                                 'role': 'USER'
#                             })
                    
#                     # ============ AUDIO OUTPUT ============
#                     elif 'audioOutput' in event:
#                         audio_content = event['audioOutput'].get('content', '')
#                         if audio_content:
#                             await self.websocket.send_json({
#                                 'type': 'audio',
#                                 'data': audio_content
#                             })
                    
#                     # ============ COMPLETION ============
#                     elif 'completionEnd' in event:
#                         print("✅ Stream completion")
#                         await self._finalize_interview()
#                         return
                
#                 except asyncio.TimeoutError:
#                     continue
#                 except Exception as e:
#                     print(f"⚠️ Error in response processing: {e}")
#                     traceback.print_exc()
#                     continue
        
#         except Exception as e:
#             print(f"❌ Fatal error: {e}")
#             traceback.print_exc()
#             self.is_active = False
    
#     async def _finalize_interview(self):
#         """Finalize interview"""
#         print(f"\n{'='*80}")
#         print(f"🎉 INTERVIEW FINALIZATION")
#         print(f"   Responses: {len(self.saved_responses)}/{len(self.questions)}")
#         print(f"   Status: {'✅ COMPLETE' if len(self.saved_responses) == len(self.questions) else '⚠️ INCOMPLETE'}")
#         print(f"{'='*80}\n")
        
#         try:
#             interview = self.db.query(ExitInterview).filter(ExitInterview.id == self.interview_id).first()
#             if interview:
#                 interview.completed = True
#                 interview.employee.status = "Completed"
#                 self.db.commit()
#         except Exception as e:
#             print(f"⚠️ DB error: {e}")
        
#         try:
#             await self.websocket.send_json({
#                 'type': 'interview_complete',
#                 'questions_answered': len(self.saved_responses),
#                 'total_questions': len(self.questions)
#             })
#         except Exception as e:
#             print(f"❌ Failed to send completion: {e}")
        
#         self.is_active = False
    
#     async def end_session(self):
#         """End session"""
#         if not self.is_active:
#             return
        
#         try:
#             # Cancel silence detection task
#             if self.silence_detection_task:
#                 self.silence_detection_task.cancel()
#                 try:
#                     await self.silence_detection_task
#                 except asyncio.CancelledError:
#                     pass
            
#             await self.send_event(json.dumps({
#                 "event": {
#                     "contentEnd": {
#                         "promptName": self.prompt_name,
#                         "contentName": self.audio_content_name
#                     }
#                 }
#             }))
            
#             await self.send_event(json.dumps({
#                 "event": {
#                     "promptEnd": {
#                         "promptName": self.prompt_name
#                     }
#                 }
#             }))
            
#             await self.send_event(json.dumps({
#                 "event": {
#                     "sessionEnd": {}
#                 }
#             }))
            
#             await self.stream.input_stream.close()
#             self.is_active = False
#             print("✅ Session ended")
        
#         except Exception as e:
#             print(f"⚠️ Error ending session: {e}")
#             self.is_active = False

# # ==================== AWS SES ====================
# ses_client = boto3.client('ses', region_name=os.getenv("AWS_REGION", "us-east-1"))

# def send_exit_interview_email(employee_email: str, employee_name: str, form_link: str) -> bool:
#     SENDER = os.getenv("SES_SENDER_EMAIL")
#     SUBJECT = "🎙️ Voice Exit Interview with Nova"
#     BODY_HTML = f"""
#     <html><body>
#         <h1>Hello {employee_name}!</h1>
#         <p>Have a voice conversation with Nova for your exit interview.</p>
#         <p><a href="{form_link}">Start Voice Interview</a></p>
#     </body></html>
#     """
#     try:
#         ses_client.send_email(
#             Source=SENDER,
#             Destination={'ToAddresses': [employee_email]},
#             Message={'Subject': {'Data': SUBJECT}, 'Body': {'Html': {'Data': BODY_HTML}}}
#         )
#         print(f"✅ Email sent to {employee_name}")
#         return True
#     except Exception as e:
#         print(f"❌ Email error: {e}")
#         return False

# def generate_unique_token() -> str:
#     return str(uuid.uuid4())

# def create_form_link(token: str) -> str:
#     return f"{os.getenv('APP_URL', 'http://localhost:8501')}/exit_interview?token={token}"

# # ==================== FASTAPI APP ====================
# app = FastAPI(title="Nova Sonic Exit Interview API", version="7.0.0")

# app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

# active_sessions: Dict[str, NovaInterviewClient] = {}

# # ==================== API ENDPOINTS ====================

# @app.get("/")
# def root():
#     return {"message": "Nova Sonic Exit Interview API", "version": "7.0.0", "status": "running"}

# @app.post("/api/employees", response_model=EmployeeResponse, status_code=201)
# def create_employee(employee: EmployeeCreate, db: Session = Depends(get_db)):
#     try:
#         existing = db.query(Employee).filter(Employee.email == employee.email).first()
#         if existing:
#             raise HTTPException(status_code=400, detail="Employee already exists")
        
#         db_employee = Employee(
#             name=employee.name,
#             email=employee.email,
#             department=employee.department,
#             last_working_date=employee.last_working_date,
#             status="Resigned"
#         )
#         db.add(db_employee)
#         db.commit()
#         db.refresh(db_employee)
        
#         token = generate_unique_token()
#         form_link = create_form_link(token)
        
#         questions_json = json.dumps(employee.questions) if employee.questions else json.dumps([
#             "What was your primary reason for leaving?",
#             "How would you rate your overall experience with the company on a scale of 1 to 5?",
#             "How was your relationship with your manager?",
#             "Did you feel valued and recognized in your role?",
#             "Would you recommend our company to others? Why or why not?"
#         ])
        
#         db_interview = ExitInterview(
#             employee_id=db_employee.id,
#             form_token=token,
#             completed=False,
#             questions_json=questions_json
#         )
#         db.add(db_interview)
#         db.commit()
        
#         send_exit_interview_email(db_employee.email, db_employee.name, form_link)
        
#         return db_employee
#     except HTTPException:
#         raise
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=str(e))

# @app.get("/api/employees", response_model=List[EmployeeResponse])
# def list_employees(db: Session = Depends(get_db)):
#     return db.query(Employee).all()

# @app.get("/api/interviews/token/{token}")
# def get_interview_by_token(token: str, db: Session = Depends(get_db)):
#     interview = db.query(ExitInterview).filter(ExitInterview.form_token == token).first()
#     if not interview:
#         raise HTTPException(status_code=404, detail="Invalid token")
#     if interview.completed:
#         raise HTTPException(status_code=400, detail="Interview already completed")
    
#     questions = json.loads(interview.questions_json)
#     return {
#         "interview_id": interview.id,
#         "employee_name": interview.employee.name,
#         "employee_department": interview.employee.department,
#         "questions": questions,
#         "total_questions": len(questions),
#         "completed": interview.completed
#     }

# @app.websocket("/ws/interview/{token}")
# async def websocket_interview(websocket: WebSocket, token: str):
#     await websocket.accept()
    
#     db = SessionLocal()
#     session_id = str(uuid.uuid4())
#     nova_client = None
    
#     try:
#         interview = db.query(ExitInterview).filter(ExitInterview.form_token == token).first()
#         if not interview:
#             await websocket.send_json({"type": "error", "message": "Invalid token"})
#             return
        
#         questions = json.loads(interview.questions_json)
#         employee_name = interview.employee.name
        
#         print(f"\n{'='*80}")
#         print(f"🎙️ NEW INTERVIEW: {employee_name}")
#         print(f"📋 Questions: {len(questions)}")
#         print(f"{'='*80}\n")
        
#         await websocket.send_json({
#             "type": "session_start",
#             "session_id": session_id,
#             "employee_name": employee_name,
#             "total_questions": len(questions)
#         })
        
#         nova_client = NovaInterviewClient(
#             employee_name,
#             questions,
#             websocket,
#             db,
#             interview.id,
#             os.getenv("AWS_REGION", "us-east-1")
#         )
#         await nova_client.start_session()
        
#         await asyncio.sleep(2)
#         await nova_client.start_audio_input()
        
#         active_sessions[session_id] = nova_client
        
#         timeout_seconds = 900  # 15 minutes
#         start_time = datetime.now(timezone.utc)
        
#         while nova_client.is_active:
#             try:
#                 message = await asyncio.wait_for(websocket.receive_json(), timeout=0.5)
#                 start_time = datetime.now(timezone.utc)
                
#                 if message['type'] == 'audio_chunk':
#                     audio_data = base64.b64decode(message['data'])
#                     await nova_client.send_audio_chunk(audio_data)
                
#                 elif message['type'] == 'close':
#                     break
            
#             except asyncio.TimeoutError:
#                 elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
#                 if elapsed > timeout_seconds:
#                     print(f"⚠️ Interview timeout after {timeout_seconds}s")
#                     break
#                 continue
#             except WebSocketDisconnect:
#                 print("⚠️ Client disconnected")
#                 break
#             except Exception as e:
#                 print(f"⚠️ Error: {e}")
#                 break
    
#     except Exception as e:
#         print(f"❌ Error: {e}")
#         traceback.print_exc()
#         try:
#             await websocket.send_json({"type": "error", "message": str(e)})
#         except:
#             pass
#     finally:
#         if nova_client:
#             await nova_client.end_session()
#         if session_id in active_sessions:
#             del active_sessions[session_id]
#         db.close()

# @app.get("/api/interviews/{interview_id}/responses", response_model=List[InterviewResponseDetail])
# def get_interview_responses(interview_id: int, db: Session = Depends(get_db)):
#     """Get responses ordered by creation time"""
#     return db.query(InterviewResponse).filter(
#         InterviewResponse.interview_id == interview_id
#     ).order_by(InterviewResponse.created_at).all()

# @app.get("/api/stats")
# def get_statistics(db: Session = Depends(get_db)):
#     total = db.query(Employee).count()
#     completed = db.query(ExitInterview).filter(ExitInterview.completed == True).count()
#     return {
#         "total_resignations": total,
#         "completed_interviews": completed,
#         "pending_interviews": total - completed,
#         "completion_rate": (completed / total * 100) if total > 0 else 0
#     }

# def init_db():
#     Base.metadata.create_all(bind=engine)
#     print("✅ Database initialized!")

# if __name__ == "__main__":
#     init_db()
#     import uvicorn
#     print("\n🚀 Nova Sonic Exit Interview API v7.0.0")
#     print("📡 http://0.0.0.0:8000\n")
#     uvicorn.run(app, host="0.0.0.0", port=8000)





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
    
    # async def _process_responses(self):
    #     """Process responses from Nova"""
    #     try:
    #         while self.is_active:
    #             try:
    #                 output = await self.stream.await_output()
    #                 result = await output[1].receive()
                    
    #                 if not result.value or not result.value.bytes_:
    #                     continue
                    
    #                 response_data = result.value.bytes_.decode('utf-8')
    #                 json_data = json.loads(response_data)
                    
    #                 if 'event' not in json_data:
    #                     continue
                    
    #                 event = json_data['event']
                    
    #                 # ============ TEXT OUTPUT ============
    #                 if 'textOutput' in event:
    #                     text = event['textOutput'].get('content', '')
    #                     role = event['textOutput'].get('role', 'ASSISTANT')
                        
    #                     if role == "ASSISTANT" and text.strip():
    #                         print(f"🤖 Nova: {text[:120]}...")
                            
    #                         # Send to frontend
    #                         await self.websocket.send_json({
    #                             'type': 'text',
    #                             'content': text,
    #                             'role': 'ASSISTANT'
    #                         })
                            
    #                         # Check if Nova asked a question
    #                         if '?' in text:
    #                             # Match to question list
    #                             matched_idx = self._match_nova_question(text)
                                
    #                             # If we didn't get a match but we expect a specific question, try to use that
    #                             if matched_idx == -1 and self.expected_next_question < len(self.questions):
    #                                 print(f"⚠️ No match found, using expected question Q{self.expected_next_question + 1}")
    #                                 matched_idx = self.expected_next_question
                                
    #                             if matched_idx >= 0 and matched_idx not in self.saved_responses:
    #                                 # Save previous answer if we were waiting and have content
    #                                 if self.waiting_for_answer and self.user_answer_buffer.strip():
    #                                     # Check if the user was asking for repetition
    #                                     if self._is_repetition_request(self.user_answer_buffer):
    #                                         print(f"🔄 User requested repetition, not saving as answer")
    #                                         # Reset buffer and continue with the same question
    #                                         self.user_answer_buffer = ""
    #                                         self.last_user_text_time = None
    #                                         self.answer_complete = False
    #                                     elif self._is_technical_issue(self.user_answer_buffer):
    #                                         print(f"🔧 User reported technical issue, not saving as answer")
    #                                         # Reset buffer and continue with the same question
    #                                         self.user_answer_buffer = ""
    #                                         self.last_user_text_time = None
    #                                         self.answer_complete = False
    #                                     else:
    #                                         # Try to save as a normal answer
    #                                         if len(self.user_answer_buffer.strip()) >= 5 and len(self.user_answer_buffer.split()) >= 3:
    #                                             success = await self._save_response_to_db(
    #                                                 self.current_q_idx,
    #                                                 self.questions[self.current_q_idx],
    #                                                 self.user_answer_buffer.strip()
    #                                             )
    #                                             # If saving failed, just reset buffer and continue
    #                                             # Don't move to the next question
    #                                             if not success:
    #                                                 print(f"⚠️ Previous answer not valid, staying on Q{self.current_q_idx + 1}")
    #                                                 self.user_answer_buffer = ""
    #                                                 self.last_user_text_time = None
    #                                                 self.answer_complete = False
    #                                                 # Don't move to the next question
    #                                                 return
    #                                         else:
    #                                             print(f"⚠️ Answer too short to save: '{self.user_answer_buffer}'")
                                    
    #                                 # Only move to a new question if it's different from the current one
    #                                 # AND the current question has been answered
    #                                 if matched_idx != self.current_q_idx:
    #                                     # Check if the current question has been answered
    #                                     if self.current_q_idx in self.saved_responses or self.current_q_idx == -1:
    #                                         # Start new question
    #                                         self.current_q_idx = matched_idx
    #                                         self.waiting_for_answer = True
    #                                         self.user_answer_buffer = ""  # Clear buffer for new answer
    #                                         self.last_user_text_time = None
    #                                         self.answer_complete = False  # Reset answer complete flag
    #                                         self.last_question_time = datetime.now(timezone.utc)
                                            
    #                                         print(f"\n❓ QUESTION {self.current_q_idx + 1}: {self.questions[self.current_q_idx][:60]}...")
    #                                         print(f"   Waiting for answer...\n")
    #                                     else:
    #                                         print(f"⚠️ Current question Q{self.current_q_idx + 1} not answered, staying on it")
    #                                         # Don't move to the next question
    #                                         return
    #                                 else:
    #                                     print(f"🔄 Same question detected, continuing with Q{self.current_q_idx + 1}")
                            
    #                         # Check for goodbye
    #                         elif "goodbye" in text.lower() or "thank you for completing" in text.lower():
    #                             print(f"\n✅ GOODBYE DETECTED")
                                
    #                             # Save last answer if we have one and it hasn't been saved
    #                             if self.waiting_for_answer and self.user_answer_buffer.strip():
    #                                 if self.current_q_idx >= 0 and self.current_q_idx not in self.saved_responses:
    #                                     # Check if the user was asking for repetition
    #                                     if not self._is_repetition_request(self.user_answer_buffer) and not self._is_technical_issue(self.user_answer_buffer):
    #                                         # Only save if we have a substantial answer
    #                                         if len(self.user_answer_buffer.strip()) >= 5 and len(self.user_answer_buffer.split()) >= 3:
    #                                             success = await self._save_response_to_db(
    #                                                 self.current_q_idx,
    #                                                 self.questions[self.current_q_idx],
    #                                                 self.user_answer_buffer.strip()
    #                                             )
    #                                             if not success:
    #                                                 print(f"⚠️ Last answer not valid, not saving")
    #                                         else:
    #                                             print(f"⚠️ Last answer too short or incomplete: '{self.user_answer_buffer}'")
    #                                     else:
    #                                         print(f"🔄 User requested repetition or reported issue at the end, not saving as answer")
                                
    #                             await self._finalize_interview()
    #                             return
                            
    #                         self.last_nova_text = text
                        
    #                     elif role == "USER" and self.waiting_for_answer and text.strip():
    #                         # User speaking
    #                         print(f"👤 User: {text[:80]}...")
                            
    #                         # Only add to buffer if it's a new thought (not repetition)
    #                         if not self._is_repetition(text, self.user_answer_buffer):
    #                             if self.user_answer_buffer:
    #                                 self.user_answer_buffer += " "
    #                             self.user_answer_buffer += text
    #                             self.last_user_text_time = datetime.now(timezone.utc)
                            
    #                         print(f"   [Buffer: {len(self.user_answer_buffer)} chars]")
                            
    #                         # Send to frontend
    #                         await self.websocket.send_json({
    #                             'type': 'text',
    #                             'content': text,
    #                             'role': 'USER'
    #                         })
                    
    #                 # ============ AUDIO OUTPUT ============
    #                 elif 'audioOutput' in event:
    #                     audio_content = event['audioOutput'].get('content', '')
    #                     if audio_content:
    #                         await self.websocket.send_json({
    #                             'type': 'audio',
    #                             'data': audio_content
    #                         })
                    
    #                 # ============ COMPLETION ============
    #                 elif 'completionEnd' in event:
    #                     print("✅ Stream completion")
    #                     await self._finalize_interview()
    #                     return
                
    #             except asyncio.TimeoutError:
    #                 continue
    #             except Exception as e:
    #                 print(f"⚠️ Error in response processing: {e}")
    #                 traceback.print_exc()
    #                 continue
        
    #     except Exception as e:
    #         print(f"❌ Fatal error: {e}")
    #         traceback.print_exc()
    #         self.is_active = False



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

# @app.get("/api/employees", response_model=List[EmployeeResponse])
# def list_employees(db: Session = Depends(get_db)):
#     return db.query(Employee).all()



# Add this to your backend main.py

# Replace the existing /api/employees endpoint with this:

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