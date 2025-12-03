# # # import streamlit as st
# # # import requests
# # # import json
# # # from datetime import datetime
# # # import os
# # # from dotenv import load_dotenv
# # # import asyncio
# # # import websockets
# # # import base64
# # # import pyaudio
# # # import threading
# # # import queue
# # # import time

# # # load_dotenv()

# # # API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000/api")
# # # WS_BASE = os.getenv("WS_BASE_URL", "ws://localhost:8000/ws")

# # # st.set_page_config(
# # #     page_title="Nova Voice Exit Interview",
# # #     page_icon="🎙️",
# # #     layout="wide"
# # # )

# # # # ----------------- (Your CSS unchanged) -----------------
# # # st.markdown("""
# # # <style>
# # #     .main-header {
# # #         font-size: 2.5rem;
# # #         font-weight: bold;
# # #         background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
# # #         -webkit-background-clip: text;
# # #         -webkit-text-fill-color: transparent;
# # #         text-align: center;
# # #         margin-bottom: 20px;
# # #     }
# # #     .voice-indicator {
# # #         width: 100px;
# # #         height: 100px;
# # #         border-radius: 50%;
# # #         background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
# # #         margin: 20px auto;
# # #         display: flex;
# # #         align-items: center;
# # #         justify-content: center;
# # #         animation: pulse 2s infinite;
# # #     }
# # #     @keyframes pulse {
# # #         0%, 100% { transform: scale(1); opacity: 1; }
# # #         50% { transform: scale(1.1); opacity: 0.8; }
# # #     }
# # #     .question-box {
# # #         background: #f0f2f6;
# # #         padding: 20px;
# # #         border-radius: 10px;
# # #         border-left: 5px solid #667eea;
# # #         margin: 20px 0;
# # #     }
# # #     .status-indicator {
# # #         display: inline-block;
# # #         width: 12px;
# # #         height: 12px;
# # #         border-radius: 50%;
# # #         margin-right: 8px;
# # #     }
# # #     .status-listening { background-color: #ff4444; animation: blink 1s infinite; }
# # #     .status-speaking { background-color: #4CAF50; }
# # #     .status-idle { background-color: #ffa500; }
# # #     @keyframes blink {
# # #         0%, 100% { opacity: 1; }
# # #         50% { opacity: 0.3; }
# # #     }
# # # </style>
# # # """, unsafe_allow_html=True)

# # # # ==================== AUDIO HANDLER (FIXED) ====================
# # # class AudioHandler:
# # #     def __init__(self):
# # #         # Audio configuration
# # #         self.FORMAT = pyaudio.paInt16
# # #         self.CHANNELS = 1

# # #         # Input (microphone) is 16k
# # #         self.INPUT_RATE = 16000
# # #         # Nova Sonic output is 24k PCM
# # #         self.OUTPUT_RATE = 24000

# # #         # CHUNK for recording (frames per buffer) -> use small chunk (~20ms)
# # #         self.CHUNK = 320  # 320 samples @16k = 20ms

# # #         # Playback frame alignment (samples)
# # #         # We'll write playback in blocks of 1024 samples (frames) — standard size
# # #         self.PLAY_FRAME_SAMPLES = 1024  # samples
# # #         self.PLAY_FRAME_BYTES = self.PLAY_FRAME_SAMPLES * 2  # 16-bit = 2 bytes per sample

# # #         # Queues: separate input & playback
# # #         self.input_queue = queue.Queue()    # mic -> to send to server
# # #         self.playback_queue = queue.Queue() # incoming server audio -> to play

# # #         # PyAudio
# # #         self.audio = pyaudio.PyAudio()
# # #         self.input_stream = None
# # #         self.output_stream = None

# # #         # control flags
# # #         self.recording = False
# # #         self.playing = False

# # #         # playback thread
# # #         self.playback_thread = None

# # #     # ---------- Recording ----------
# # #     def start_recording(self):
# # #         if self.recording:
# # #             return
# # #         self.recording = True
# # #         try:
# # #             self.input_stream = self.audio.open(
# # #                 format=self.FORMAT,
# # #                 channels=self.CHANNELS,
# # #                 rate=self.INPUT_RATE,
# # #                 input=True,
# # #                 frames_per_buffer=self.CHUNK,
# # #                 stream_callback=self._record_callback
# # #             )
# # #             self.input_stream.start_stream()
# # #         except Exception as e:
# # #             print(f"Failed to open input stream: {e}")
# # #             self.recording = False

# # #     def stop_recording(self):
# # #         self.recording = False
# # #         try:
# # #             if self.input_stream:
# # #                 try:
# # #                     self.input_stream.stop_stream()
# # #                 except Exception:
# # #                     pass
# # #                 try:
# # #                     self.input_stream.close()
# # #                 except Exception:
# # #                     pass
# # #                 self.input_stream = None
# # #         except Exception as e:
# # #             print(f"Error stopping input stream: {e}")

# # #     def _record_callback(self, in_data, frame_count, time_info, status):
# # #         # push microphone frames into input_queue only
# # #         if self.recording:
# # #             try:
# # #                 self.input_queue.put(in_data, block=False)
# # #             except queue.Full:
# # #                 # drop if full (shouldn't normally happen)
# # #                 pass
# # #         return (None, pyaudio.paContinue)

# # #     # ---------- Playback ----------
# # #     def start_playback(self, prebuffer_frames=3):
# # #         if self.playing:
# # #             return
# # #         self.playing = True

# # #         try:
# # #             self.output_stream = self.audio.open(
# # #                 format=self.FORMAT,
# # #                 channels=self.CHANNELS,
# # #                 rate=self.OUTPUT_RATE,
# # #                 output=True,
# # #                 frames_per_buffer=self.PLAY_FRAME_SAMPLES
# # #             )
# # #         except Exception as e:
# # #             print(f"Failed to open output stream: {e}")
# # #             self.playing = False
# # #             return

# # #         # start playback thread
# # #         self.playback_thread = threading.Thread(target=self._playback_loop, daemon=True)
# # #         self.playback_thread.start()

# # #         # optional: wait for a small prebuffer to reduce initial underflow
# # #         start_time = time.time()
# # #         while time.time() - start_time < 1.0:
# # #             if self.playback_queue.qsize() >= prebuffer_frames:
# # #                 break
# # #             time.sleep(0.01)

# # #     def _playback_loop(self):
# # #         # Loop that writes aligned frames to PyAudio.
# # #         while self.playing:
# # #             try:
# # #                 block = None
# # #                 try:
# # #                     # Wait for a block (2048 bytes). Use timeout so thread can exit quickly.
# # #                     block = self.playback_queue.get(timeout=0.2)
# # #                 except queue.Empty:
# # #                     # no data - write silence? we simply continue to wait
# # #                     continue

# # #                 if not block:
# # #                     continue

# # #                 # write to output. Use exception_on_underflow=False to avoid exceptions on underflow.
# # #                 try:
# # #                     self.output_stream.write(block, exception_on_underflow=False)
# # #                 except TypeError:
# # #                     # older pyaudio versions do not support exception_on_underflow param
# # #                     try:
# # #                         self.output_stream.write(block)
# # #                     except Exception as e:
# # #                         print(f"Playback write error: {e}")
# # #                         continue
# # #                 except Exception as e:
# # #                     print(f"Playback write error: {e}")
# # #                     continue

# # #             except Exception as e:
# # #                 print(f"Playback loop error (fatal): {e}")
# # #                 break

# # #     def play_audio(self, audio_base64):
# # #         """
# # #         Decode incoming base64 PCM data from server and enqueue aligned frames for playback.
# # #         We ensure we queue only full frames of PLAY_FRAME_BYTES so PyAudio receives consistent blocks.
# # #         """
# # #         try:
# # #             raw = base64.b64decode(audio_base64)

# # #             # Nova may return frames that are multiples or different sizes; slice them into fixed blocks.
# # #             for i in range(0, len(raw), self.PLAY_FRAME_BYTES):
# # #                 block = raw[i:i + self.PLAY_FRAME_BYTES]
# # #                 if len(block) == self.PLAY_FRAME_BYTES:
# # #                     try:
# # #                         self.playback_queue.put(block, block=False)
# # #                     except TypeError:
# # #                         # fallback if block param name mismatch (older Python)
# # #                         self.playback_queue.put(block)
# # #                     except queue.Full:
# # #                         # if queue is full, drop to avoid blocking
# # #                         pass
# # #                 else:
# # #                     # If block is partial, drop it (avoids under/overflow and artifacts).
# # #                     # Alternatively you could buffer partials until full frame assembled.
# # #                     pass
# # #         except Exception as e:
# # #             print(f"Error decoding/queuing playback audio: {e}")

# # #     def stop_playback(self):
# # #         self.playing = False
# # #         # join thread briefly
# # #         if self.playback_thread and self.playback_thread.is_alive():
# # #             self.playback_thread.join(timeout=1.0)
# # #         try:
# # #             if self.output_stream:
# # #                 try:
# # #                     self.output_stream.stop_stream()
# # #                 except Exception:
# # #                     pass
# # #                 try:
# # #                     self.output_stream.close()
# # #                 except Exception:
# # #                     pass
# # #                 self.output_stream = None
# # #         except Exception as e:
# # #             print(f"Error stopping output stream: {e}")

# # #     def cleanup(self):
# # #         self.stop_recording()
# # #         self.stop_playback()
# # #         try:
# # #             self.audio.terminate()
# # #         except Exception:
# # #             pass

# # # # ==================== WEBSOCKET HANDLER (FIXED) ====================
# # # async def handle_websocket(token, audio_handler, status_placeholder, transcript_placeholder):
# # #     """Handle WebSocket communication with backend"""
# # #     uri = f"{WS_BASE}/interview/{token}"

# # #     try:
# # #         async with websockets.connect(uri) as websocket:
# # #             st.session_state.ws = websocket
# # #             st.session_state.status = "connected"

# # #             # Start playback first (so the output stream is ready when audio arrives)
# # #             audio_handler.start_playback()

# # #             # Start recording (microphone)
# # #             audio_handler.start_recording()

# # #             # Create task for sending audio (consumes input_queue)
# # #             send_task = asyncio.create_task(send_audio_loop(websocket, audio_handler))

# # #             # Receive messages loop
# # #             while st.session_state.interview_active:
# # #                 try:
# # #                     # wait for incoming websocket message
# # #                     message = await asyncio.wait_for(websocket.recv(), timeout=0.1)

# # #                     # Defensive parsing
# # #                     if message is None:
# # #                         continue
# # #                     try:
# # #                         data = json.loads(message)
# # #                     except Exception as e:
# # #                         print(f"Invalid JSON from socket (ignored): {e}")
# # #                         continue

# # #                     # Defensive: ensure type exists
# # #                     msg_type = data.get('type')
# # #                     if not msg_type:
# # #                         continue

# # #                     # Handle message types
# # #                     if msg_type == 'session_start':
# # #                         st.session_state.session_id = data.get('session_id')
# # #                         st.session_state.total_questions = data.get('total_questions', 0)
# # #                         st.session_state.status = "speaking"
# # #                         try:
# # #                             status_placeholder.success("✅ Connected! Nova is starting...")
# # #                         except Exception:
# # #                             pass

# # #                     elif msg_type == 'text':
# # #                         # defensive extraction
# # #                         role = data.get('role', 'ASSISTANT')
# # #                         content = data.get('content', '') or ''
# # #                         if role == 'ASSISTANT':
# # #                             st.session_state.transcript.append(f"🤖 Nova: {content}")
# # #                             st.session_state.current_question = content
# # #                             st.session_state.status = "listening"
# # #                         else:
# # #                             st.session_state.transcript.append(f"👤 You: {content}")
# # #                             st.session_state.current_question_idx += 1

# # #                         # Update transcript display safely
# # #                         try:
# # #                             with transcript_placeholder.container():
# # #                                 for line in st.session_state.transcript[-5:]:
# # #                                     st.write(line)
# # #                         except Exception:
# # #                             pass

# # #                     elif msg_type == 'audio':
# # #                         audio_b64 = data.get('data')
# # #                         if audio_b64:
# # #                             # decode & queue aligned frames for playback
# # #                             audio_handler.play_audio(audio_b64)

# # #                     elif msg_type == 'content_end':
# # #                         st.session_state.status = "listening"

# # #                     elif msg_type == 'complete':
# # #                         st.session_state.interview_complete = True
# # #                         st.session_state.interview_active = False
# # #                         st.session_state.responses = data.get('responses', [])
# # #                         try:
# # #                             status_placeholder.success("✅ Interview completed!")
# # #                         except Exception:
# # #                             pass
# # #                         break

# # #                     elif msg_type == 'error':
# # #                         try:
# # #                             status_placeholder.error(f"❌ Error: {data.get('message', 'Unknown')}")
# # #                         except Exception:
# # #                             pass
# # #                         break

# # #                 except asyncio.TimeoutError:
# # #                     continue
# # #                 except websockets.ConnectionClosed:
# # #                     print("INFO: connection closed")
# # #                     break
# # #                 except Exception as e:
# # #                     print(f"Error receiving message: {e}")
# # #                     break

# # #             # Cleanup
# # #             send_task.cancel()
# # #             audio_handler.stop_recording()

# # #             # send close message if possible
# # #             try:
# # #                 await websocket.send(json.dumps({"type": "close"}))
# # #             except Exception:
# # #                 pass

# # #     except Exception as e:
# # #         try:
# # #             status_placeholder.error(f"❌ Connection error: {str(e)}")
# # #         except Exception:
# # #             pass
# # #         st.session_state.interview_active = False

# # # async def send_audio_loop(websocket, audio_handler):
# # #     """Send audio chunks to backend. Uses asyncio.to_thread to avoid blocking event loop."""
# # #     try:
# # #         while st.session_state.interview_active and audio_handler.recording:
# # #             try:
# # #                 # run blocking queue.get in thread pool so event loop isn't blocked
# # #                 audio_data = await asyncio.to_thread(audio_handler.input_queue.get, True, 0.1)
# # #                 if not audio_data:
# # #                     await asyncio.sleep(0.01)
# # #                     continue

# # #                 audio_base64 = base64.b64encode(audio_data).decode('utf-8')

# # #                 await websocket.send(json.dumps({
# # #                     'type': 'audio_chunk',
# # #                     'data': audio_base64
# # #                 }))

# # #             except queue.Empty:
# # #                 await asyncio.sleep(0.01)
# # #             except asyncio.CancelledError:
# # #                 break
# # #             except Exception as e:
# # #                 print(f"Error sending audio: {e}")
# # #                 break
# # #     except asyncio.CancelledError:
# # #         pass

# # # # ==================== MAIN APPLICATION (mostly unchanged) ====================
# # # params = st.query_params
# # # token = params.get("token", None)

# # # if not token:
# # #     st.error("❌ Invalid or missing interview token.")
# # #     st.info("Please use the link provided in your email.")
# # #     st.stop()

# # # # Initialize session state
# # # if "initialized" not in st.session_state:
# # #     st.session_state.initialized = False
# # #     st.session_state.interview_info = None
# # #     st.session_state.ws = None
# # #     st.session_state.session_id = None
# # #     st.session_state.status = "idle"
# # #     st.session_state.current_question_idx = 0
# # #     st.session_state.current_question = ""
# # #     st.session_state.total_questions = 0
# # #     st.session_state.responses = []
# # #     st.session_state.transcript = []
# # #     st.session_state.interview_complete = False
# # #     st.session_state.interview_active = False
# # #     st.session_state.audio_handler = None

# # # # Fetch interview info
# # # if not st.session_state.initialized:
# # #     try:
# # #         response = requests.get(f"{API_BASE}/interviews/token/{token}")
# # #         if response.status_code != 200:
# # #             error_data = response.json()
# # #             st.error(f"❌ {error_data.get('detail', 'Invalid token')}")
# # #             st.stop()

# # #         st.session_state.interview_info = response.json()
# # #         st.session_state.initialized = True
# # #     except Exception as e:
# # #         st.error(f"❌ Error connecting to server: {str(e)}")
# # #         st.info("Please make sure the backend server is running on http://localhost:8000")
# # #         st.stop()

# # # interview_info = st.session_state.interview_info

# # # # Header
# # # st.markdown('<p class="main-header">🎙️ Voice Exit Interview with Nova Sonic</p>', unsafe_allow_html=True)

# # # col1, col2, col3 = st.columns([1, 2, 1])
# # # with col2:
# # #     st.markdown(
# # #         '<div style="text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); '
# # #         'color: white; padding: 8px 16px; border-radius: 20px; display: inline-block;">'
# # #         '🔊 Powered by Amazon Nova Sonic</div>',
# # #         unsafe_allow_html=True
# # #     )

# # # st.markdown(f"### Welcome, **{interview_info['employee_name']}**!")
# # # st.markdown(f"**Department:** {interview_info['employee_department']}")
# # # st.markdown("---")

# # # # Show introduction if not started
# # # if not st.session_state.interview_active and not st.session_state.interview_complete:
# # #     st.info("### 🎙️ How this works:")
# # #     st.markdown("""
# # #     1. **Click Start** to begin your voice interview with Nova
# # #     2. **Nova speaks first** - Listen to the questions
# # #     3. **Speak your answers** - Your microphone will be active
# # #     4. **Nova responds** naturally and moves to the next question
# # #     5. **All responses are saved** automatically
# # #     """)

# # #     st.markdown("### 📋 Questions Nova will ask:")
# # #     for i, q in enumerate(interview_info['questions'], 1):
# # #         st.markdown(f"{i}. {q}")

# # #     st.markdown("---")

# # #     st.warning("⚠️ **Important:** Make sure your microphone is connected and working!")

# # #     if st.button("🎙️ Start Voice Interview", use_container_width=True, type="primary"):
# # #         # Initialize audio handler
# # #         st.session_state.audio_handler = AudioHandler()
# # #         st.session_state.interview_active = True
# # #         st.rerun()

# # # # Show interview interface
# # # elif st.session_state.interview_active and not st.session_state.interview_complete:

# # #     # Status indicator
# # #     status_colors = {
# # #         "idle": "status-idle",
# # #         "listening": "status-listening",
# # #         "speaking": "status-speaking",
# # #         "connected": "status-idle"
# # #     }
# # #     status_text = {
# # #         "idle": "Initializing...",
# # #         "listening": "🎤 Listening to you...",
# # #         "speaking": "🔊 Nova is speaking...",
# # #         "connected": "Connected"
# # #     }

# # #     col1, col2, col3 = st.columns([1, 2, 1])
# # #     with col2:
# # #         st.markdown(
# # #             f'<div style="text-align: center;">'
# # #             f'<span class="status-indicator {status_colors.get(st.session_state.status, "status-idle")}"></span>'
# # #             f'<strong>{status_text.get(st.session_state.status, "Ready")}</strong>'
# # #             f'</div>',
# # #             unsafe_allow_html=True
# # #         )

# # #     # Voice indicator
# # #     if st.session_state.status in ["listening", "speaking"]:
# # #         st.markdown('<div class="voice-indicator">🎙️</div>', unsafe_allow_html=True)

# # #     # Progress
# # #     if st.session_state.total_questions > 0:
# # #         progress = st.session_state.current_question_idx / st.session_state.total_questions
# # #         st.progress(progress)
# # #         st.caption(f"Question {st.session_state.current_question_idx + 1} of {st.session_state.total_questions}")

# # #     st.markdown("---")

# # #     # Current question
# # #     if st.session_state.current_question and st.session_state.status == "listening":
# # #         st.markdown(f'<div class="question-box"><strong>Current Question:</strong><br>{st.session_state.current_question}</div>', unsafe_allow_html=True)

# # #     # Status placeholder
# # #     status_placeholder = st.empty()
# # #     status_placeholder.info("🔄 Connecting to Nova Sonic...")

# # #     # Transcript
# # #     transcript_placeholder = st.expander("📝 Conversation Transcript", expanded=False)

# # #     # Stop button
# # #     if st.button("🛑 End Interview Early", use_container_width=True, type="secondary"):
# # #         st.session_state.interview_active = False
# # #         if st.session_state.audio_handler:
# # #             st.session_state.audio_handler.cleanup()
# # #         st.rerun()

# # #     # Run WebSocket connection
# # #     if st.session_state.audio_handler:
# # #         # Use asyncio.run since we are in top-level Streamlit flow
# # #         asyncio.run(handle_websocket(
# # #             token,
# # #             st.session_state.audio_handler,
# # #             status_placeholder,
# # #             transcript_placeholder
# # #         ))

# # #         # Cleanup
# # #         st.session_state.audio_handler.cleanup()
# # #         st.session_state.audio_handler = None

# # # # Show completion
# # # elif st.session_state.interview_complete:
# # #     st.success("### ✅ Interview Completed!")
# # #     st.balloons()

# # #     st.markdown("---")

# # #     st.markdown("### 📋 Your Responses")
# # #     if st.session_state.responses:
# # #         for i, resp in enumerate(st.session_state.responses, 1):
# # #             with st.expander(f"Question {i}", expanded=False):
# # #                 st.markdown(f"**Q:** {resp['question']}")
# # #                 st.markdown(f"**A:** {resp['answer']}")

# # #     st.markdown("---")

# # #     st.markdown("### 📝 Full Transcript")
# # #     for line in st.session_state.transcript:
# # #         st.write(line)

# # #     st.markdown("---")

# # #     st.markdown("""
# # #     ### Thank you for completing the exit interview!

# # #     Your feedback has been recorded and will help us improve.

# # #     You can now close this window.
# # #     """)

# # # # Sidebar
# # # with st.sidebar:
# # #     st.markdown("### 🎙️ About Nova Sonic")
# # #     st.markdown("""
# # #     Nova Sonic is Amazon's advanced voice AI:

# # #     - 🎤 Real-time speech recognition
# # #     - 🔊 Natural voice synthesis
# # #     - 💬 Bidirectional conversation
# # #     - ⚡ Low latency responses

# # #     **Tips:**
# # #     - Speak clearly and naturally
# # #     - Wait for Nova to finish speaking
# # #     - Be honest and open with your feedback
# # #     """)

# # #     st.markdown("---")

# # #     if st.session_state.interview_active:
# # #         st.markdown(f"**Status:** {st.session_state.status}")
# # #         if st.session_state.total_questions > 0:
# # #             st.markdown(f"**Progress:** {st.session_state.current_question_idx}/{st.session_state.total_questions}")

# # #     st.markdown("---")
# # #     st.caption("Powered by AWS Bedrock • Nova Sonic v1.0")



# # import streamlit as st
# # import requests
# # import json
# # from datetime import datetime
# # import os
# # from dotenv import load_dotenv
# # import asyncio
# # import websockets
# # import base64
# # import pyaudio
# # import threading
# # import queue
# # import time

# # load_dotenv()

# # API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000/api")
# # WS_BASE = os.getenv("WS_BASE_URL", "ws://localhost:8000/ws")

# # st.set_page_config(
# #     page_title="Nova Voice Exit Interview",
# #     page_icon="🎙️",
# #     layout="wide"
# # )

# # # CSS
# # st.markdown("""
# # <style>
# #     .main-header {
# #         font-size: 2.5rem;
# #         font-weight: bold;
# #         background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
# #         -webkit-background-clip: text;
# #         -webkit-text-fill-color: transparent;
# #         text-align: center;
# #         margin-bottom: 20px;
# #     }
# #     .voice-indicator {
# #         width: 100px;
# #         height: 100px;
# #         border-radius: 50%;
# #         background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
# #         margin: 20px auto;
# #         display: flex;
# #         align-items: center;
# #         justify-content: center;
# #         animation: pulse 2s infinite;
# #     }
# #     @keyframes pulse {
# #         0%, 100% { transform: scale(1); opacity: 1; }
# #         50% { transform: scale(1.1); opacity: 0.8; }
# #     }
# #     .question-box {
# #         background: #f0f2f6;
# #         padding: 20px;
# #         border-radius: 10px;
# #         border-left: 5px solid #667eea;
# #         margin: 20px 0;
# #     }
# #     .status-indicator {
# #         display: inline-block;
# #         width: 12px;
# #         height: 12px;
# #         border-radius: 50%;
# #         margin-right: 8px;
# #     }
# #     .status-listening { background-color: #ff4444; animation: blink 1s infinite; }
# #     .status-speaking { background-color: #4CAF50; }
# #     .status-idle { background-color: #ffa500; }
# #     @keyframes blink {
# #         0%, 100% { opacity: 1; }
# #         50% { opacity: 0.3; }
# #     }
# # </style>
# # """, unsafe_allow_html=True)

# # # ==================== FIXED AUDIO HANDLER ====================
# # class AudioHandler:
# #     def __init__(self):
# #         self.FORMAT = pyaudio.paInt16
# #         self.CHANNELS = 1
# #         self.INPUT_RATE = 16000
# #         self.OUTPUT_RATE = 24000
# #         self.INPUT_CHUNK = 320
        
# #         # FIXED: Larger frame size for stability
# #         self.OUTPUT_FRAME_SIZE = 16384
# #         self.FRAME_BYTES = self.OUTPUT_FRAME_SIZE * 2

# #         self.input_queue = queue.Queue(maxsize=20)
# #         self.playback_queue = queue.Queue(maxsize=200)

# #         self.audio = pyaudio.PyAudio()
# #         self.input_stream = None
# #         self.output_stream = None

# #         self.recording = False
# #         self.playing = False
# #         self.playback_thread = None

# #         # FIXED: Intermediate buffer for frame alignment
# #         self.playback_buffer = bytearray()
# #         self.buffer_lock = threading.Lock()

# #         print(f"✅ AudioHandler initialized:")
# #         print(f"   Input: {self.INPUT_RATE}Hz, Chunk: {self.INPUT_CHUNK}")
# #         print(f"   Output: {self.OUTPUT_RATE}Hz, Frame: {self.OUTPUT_FRAME_SIZE}")
# #         print(f"   Frame bytes: {self.FRAME_BYTES}")

# #     def start_recording(self):
# #         if self.recording:
# #             return
# #         self.recording = True
# #         try:
# #             # FIXED: Try with exception_on_overflow first, fallback if not supported
# #             try:
# #                 self.input_stream = self.audio.open(
# #                     format=self.FORMAT,
# #                     channels=self.CHANNELS,
# #                     rate=self.INPUT_RATE,
# #                     input=True,
# #                     frames_per_buffer=self.INPUT_CHUNK,
# #                     stream_callback=self._record_callback,
# #                     exception_on_overflow=False
# #                 )
# #             except TypeError:
# #                 # Fallback for older PyAudio versions
# #                 self.input_stream = self.audio.open(
# #                     format=self.FORMAT,
# #                     channels=self.CHANNELS,
# #                     rate=self.INPUT_RATE,
# #                     input=True,
# #                     frames_per_buffer=self.INPUT_CHUNK,
# #                     stream_callback=self._record_callback
# #                 )
# #             self.input_stream.start_stream()
# #             print("🎤 Recording started")
# #         except Exception as e:
# #             print(f"❌ Failed to open input stream: {e}")
# #             self.recording = False

# #     def stop_recording(self):
# #         self.recording = False
# #         try:
# #             if self.input_stream:
# #                 try:
# #                     self.input_stream.stop_stream()
# #                 except Exception:
# #                     pass
# #                 try:
# #                     self.input_stream.close()
# #                 except Exception:
# #                     pass
# #                 self.input_stream = None
# #         except Exception as e:
# #             print(f"Error stopping input stream: {e}")

# #     def _record_callback(self, in_data, frame_count, time_info, status):
# #         if status and status != pyaudio.paInputUnderflow:
# #             print(f"⚠️ Recording status: {status}")
        
# #         if self.recording:
# #             try:
# #                 self.input_queue.put(in_data, block=False)
# #             except queue.Full:
# #                 print("⚠️ Input queue full - dropping frame")
# #         return (None, pyaudio.paContinue)

# #     def start_playback(self, prebuffer_frames=15):
# #         if self.playing:
# #             return
        
# #         self.playing = True
# #         self.playback_buffer = bytearray()

# #         try:
# #             # FIXED: Try with exception_on_underflow first, fallback if not supported
# #             try:
# #                 self.output_stream = self.audio.open(
# #                     format=self.FORMAT,
# #                     channels=self.CHANNELS,
# #                     rate=self.OUTPUT_RATE,
# #                     output=True,
# #                     frames_per_buffer=self.OUTPUT_FRAME_SIZE,
# #                     exception_on_underflow=False
# #                 )
# #             except TypeError:
# #                 # Fallback for older PyAudio versions
# #                 self.output_stream = self.audio.open(
# #                     format=self.FORMAT,
# #                     channels=self.CHANNELS,
# #                     rate=self.OUTPUT_RATE,
# #                     output=True,
# #                     frames_per_buffer=self.OUTPUT_FRAME_SIZE
# #                 )
# #             print("🔊 Playback stream opened")
# #         except Exception as e:
# #             print(f"❌ Failed to open output stream: {e}")
# #             self.playing = False
# #             return

# #         self.playback_thread = threading.Thread(
# #             target=self._playback_loop,
# #             daemon=True,
# #             name="PlaybackThread"
# #         )
# #         self.playback_thread.start()

# #         print(f"⏳ Prebuffering {prebuffer_frames} frames...")
# #         start_time = time.time()
# #         while time.time() - start_time < 5.0:
# #             with self.buffer_lock:
# #                 if len(self.playback_buffer) >= (self.FRAME_BYTES * prebuffer_frames):
# #                     print(f"✅ Prebuffer ready ({len(self.playback_buffer)} bytes)")
# #                     return
# #             time.sleep(0.05)
        
# #         print("⚠️ Prebuffer timeout - starting anyway")

# #     def _playback_loop(self):
# #         """FIXED: Main playback loop with proper frame alignment"""
# #         print("▶️ Playback loop started")
        
# #         try:
# #             while self.playing:
# #                 # Try to get data from queue
# #                 try:
# #                     chunk = self.playback_queue.get(timeout=0.1)
# #                     if chunk:
# #                         with self.buffer_lock:
# #                             self.playback_buffer.extend(chunk)
# #                 except queue.Empty:
# #                     pass
                
# #                 # Extract one complete frame from buffer
# #                 with self.buffer_lock:
# #                     if len(self.playback_buffer) >= self.FRAME_BYTES:
# #                         frame = bytes(self.playback_buffer[:self.FRAME_BYTES])
# #                         del self.playback_buffer[:self.FRAME_BYTES]
# #                     else:
# #                         frame = None
                
# #                 # Write frame if available, otherwise write silence
# #                 if frame:
# #                     try:
# #                         self.output_stream.write(frame)
# #                     except Exception as e:
# #                         print(f"⚠️ Playback write error: {e}")
# #                 else:
# #                     # Write silence frame to prevent underflow
# #                     silence = b'\x00' * self.FRAME_BYTES
# #                     try:
# #                         self.output_stream.write(silence)
# #                     except Exception:
# #                         pass
        
# #         except Exception as e:
# #             print(f"❌ Playback loop fatal error: {e}")
# #         finally:
# #             print("⏹️ Playback loop stopped")

    

# #     def play_audio(self, audio_base64):
# #         """FIXED: Decode and queue for playback with proper frame handling"""
# #         try:
# #             raw = base64.b64decode(audio_base64)

# #             if not raw:
# #                 return
# #             with self.buffer_lock:
# #                 self.playback_buffer.extend(raw)

# #             # try:
# #             #     self.playback_queue.put(raw, block=False)
# #             # except queue.Full:
# #             #     print(f"⚠️ Playback queue full - dropping chunk ({len(raw)} bytes)")

# #         except Exception as e:
# #             print(f"❌ Error decoding/queuing playback audio: {e}")

# #     def stop_playback(self):
# #         self.playing = False
# #         if self.playback_thread and self.playback_thread.is_alive():
# #             self.playback_thread.join(timeout=1.0)
# #         try:
# #             if self.output_stream:
# #                 try:
# #                     self.output_stream.stop_stream()
# #                 except Exception:
# #                     pass
# #                 try:
# #                     self.output_stream.close()
# #                 except Exception:
# #                     pass
# #                 self.output_stream = None
# #         except Exception as e:
# #             print(f"Error stopping output stream: {e}")

# #     def cleanup(self):
# #         self.stop_recording()
# #         self.stop_playback()
# #         try:
# #             self.audio.terminate()
# #             print("✅ Audio cleanup complete")
# #         except Exception:
# #             pass

# #     def get_buffer_status(self):
# #         """Get current buffer status for debugging"""
# #         with self.buffer_lock:
# #             buffer_size = len(self.playback_buffer)
# #         queue_size = self.playback_queue.qsize()
# #         return {
# #             'buffer_bytes': buffer_size,
# #             'buffer_frames': buffer_size / self.FRAME_BYTES if self.FRAME_BYTES > 0 else 0,
# #             'queue_size': queue_size,
# #             'total_latency_ms': (buffer_size / 2 / self.OUTPUT_RATE * 1000) if self.OUTPUT_RATE > 0 else 0
# #         }

# # # ==================== WEBSOCKET HANDLER ====================
# # async def handle_websocket(token, audio_handler, status_placeholder, transcript_placeholder):
# #     """Handle WebSocket communication with backend"""
# #     uri = f"{WS_BASE}/interview/{token}"

# #     try:
# #         async with websockets.connect(uri) as websocket:
# #             st.session_state.ws = websocket
# #             st.session_state.status = "connected"

# #             audio_handler.start_playback(prebuffer_frames=20)
# #             audio_handler.start_recording()

# #             send_task = asyncio.create_task(send_audio_loop(websocket, audio_handler))

# #             while st.session_state.interview_active:
# #                 try:
# #                     message = await asyncio.wait_for(websocket.recv(), timeout=0.1)

# #                     if message is None:
# #                         continue
# #                     try:
# #                         data = json.loads(message)
# #                     except Exception as e:
# #                         print(f"Invalid JSON from socket (ignored): {e}")
# #                         continue

# #                     msg_type = data.get('type')
# #                     if not msg_type:
# #                         continue

# #                     if msg_type == 'session_start':
# #                         st.session_state.session_id = data.get('session_id')
# #                         st.session_state.total_questions = data.get('total_questions', 0)
# #                         st.session_state.status = "speaking"
# #                         try:
# #                             status_placeholder.success("✅ Connected! Nova is starting...")
# #                         except Exception:
# #                             pass

# #                     elif msg_type == 'text':
# #                         role = data.get('role', 'ASSISTANT')
# #                         content = data.get('content', '') or ''
# #                         if role == 'ASSISTANT':
# #                             st.session_state.transcript.append(f"🤖 Nova: {content}")
# #                             st.session_state.current_question = content
# #                             st.session_state.status = "listening"
# #                         else:
# #                             st.session_state.transcript.append(f"👤 You: {content}")
# #                             st.session_state.current_question_idx += 1

# #                         try:
# #                             with transcript_placeholder.container():
# #                                 for line in st.session_state.transcript[-5:]:
# #                                     st.write(line)
# #                         except Exception:
# #                             pass

# #                     elif msg_type == 'audio':
# #                         audio_b64 = data.get('data')
# #                         if audio_b64:
# #                             audio_handler.play_audio(audio_b64)

# #                     elif msg_type == 'content_end':
# #                         st.session_state.status = "listening"

# #                     elif msg_type == 'complete':
# #                         st.session_state.interview_complete = True
# #                         st.session_state.interview_active = False
# #                         st.session_state.responses = data.get('responses', [])
# #                         try:
# #                             status_placeholder.success("✅ Interview completed!")
# #                         except Exception:
# #                             pass
# #                         break

# #                     elif msg_type == 'error':
# #                         try:
# #                             status_placeholder.error(f"❌ Error: {data.get('message', 'Unknown')}")
# #                         except Exception:
# #                             pass
# #                         break

# #                 except asyncio.TimeoutError:
# #                     continue
# #                 except websockets.ConnectionClosed:
# #                     print("INFO: connection closed")
# #                     break
# #                 except Exception as e:
# #                     print(f"Error receiving message: {e}")
# #                     break

# #             send_task.cancel()
# #             audio_handler.stop_recording()

# #             try:
# #                 await websocket.send(json.dumps({"type": "close"}))
# #             except Exception:
# #                 pass

# #     except Exception as e:
# #         try:
# #             status_placeholder.error(f"❌ Connection error: {str(e)}")
# #         except Exception:
# #             pass
# #         st.session_state.interview_active = False

# # async def send_audio_loop(websocket, audio_handler):
# #     """Send audio chunks to backend"""
# #     try:
# #         while st.session_state.interview_active and audio_handler.recording:
# #             try:
# #                 audio_data = await asyncio.to_thread(audio_handler.input_queue.get, True, 0.1)
# #                 if not audio_data:
# #                     await asyncio.sleep(0.01)
# #                     continue

# #                 audio_base64 = base64.b64encode(audio_data).decode('utf-8')

# #                 await websocket.send(json.dumps({
# #                     'type': 'audio_chunk',
# #                     'data': audio_base64
# #                 }))

# #             except queue.Empty:
# #                 await asyncio.sleep(0.01)
# #             except asyncio.CancelledError:
# #                 break
# #             except Exception as e:
# #                 print(f"Error sending audio: {e}")
# #                 break
# #     except asyncio.CancelledError:
# #         pass

# # # ==================== MAIN APPLICATION ====================
# # params = st.query_params
# # token = params.get("token", None)

# # if not token:
# #     st.error("❌ Invalid or missing interview token.")
# #     st.info("Please use the link provided in your email.")
# #     st.stop()

# # # Initialize session state
# # if "initialized" not in st.session_state:
# #     st.session_state.initialized = False
# #     st.session_state.interview_info = None
# #     st.session_state.ws = None
# #     st.session_state.session_id = None
# #     st.session_state.status = "idle"
# #     st.session_state.current_question_idx = 0
# #     st.session_state.current_question = ""
# #     st.session_state.total_questions = 0
# #     st.session_state.responses = []
# #     st.session_state.transcript = []
# #     st.session_state.interview_complete = False
# #     st.session_state.interview_active = False
# #     st.session_state.audio_handler = None

# # # Fetch interview info
# # if not st.session_state.initialized:
# #     try:
# #         response = requests.get(f"{API_BASE}/interviews/token/{token}")
# #         if response.status_code != 200:
# #             error_data = response.json()
# #             st.error(f"❌ {error_data.get('detail', 'Invalid token')}")
# #             st.stop()

# #         st.session_state.interview_info = response.json()
# #         st.session_state.initialized = True
# #     except Exception as e:
# #         st.error(f"❌ Error connecting to server: {str(e)}")
# #         st.info("Please make sure the backend server is running on http://localhost:8000")
# #         st.stop()

# # interview_info = st.session_state.interview_info

# # # Header
# # st.markdown('<p class="main-header">🎙️ Voice Exit Interview with Nova Sonic</p>', unsafe_allow_html=True)

# # col1, col2, col3 = st.columns([1, 2, 1])
# # with col2:
# #     st.markdown(
# #         '<div style="text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); '
# #         'color: white; padding: 8px 16px; border-radius: 20px; display: inline-block;">'
# #         '🔊 Powered by Amazon Nova Sonic</div>',
# #         unsafe_allow_html=True
# #     )

# # st.markdown(f"### Welcome, **{interview_info['employee_name']}**!")
# # st.markdown(f"**Department:** {interview_info['employee_department']}")
# # st.markdown("---")

# # # Show introduction if not started
# # if not st.session_state.interview_active and not st.session_state.interview_complete:
# #     st.info("### 🎙️ How this works:")
# #     st.markdown("""
# #     1. **Click Start** to begin your voice interview with Nova
# #     2. **Nova speaks first** - Listen to the questions
# #     3. **Speak your answers** - Your microphone will be active
# #     4. **Nova responds** naturally and moves to the next question
# #     5. **All responses are saved** automatically
# #     """)

# #     st.markdown("### 📋 Questions Nova will ask:")
# #     for i, q in enumerate(interview_info['questions'], 1):
# #         st.markdown(f"{i}. {q}")

# #     st.markdown("---")

# #     st.warning("⚠️ **Important:** Make sure your microphone is connected and working!")

# #     if st.button("🎙️ Start Voice Interview", use_container_width=True, type="primary"):
# #         st.session_state.audio_handler = AudioHandler()
# #         st.session_state.interview_active = True
# #         st.rerun()

# # # Show interview interface
# # elif st.session_state.interview_active and not st.session_state.interview_complete:

# #     status_colors = {
# #         "idle": "status-idle",
# #         "listening": "status-listening",
# #         "speaking": "status-speaking",
# #         "connected": "status-idle"
# #     }
# #     status_text = {
# #         "idle": "Initializing...",
# #         "listening": "🎤 Listening to you...",
# #         "speaking": "🔊 Nova is speaking...",
# #         "connected": "Connected"
# #     }

# #     col1, col2, col3 = st.columns([1, 2, 1])
# #     with col2:
# #         st.markdown(
# #             f'<div style="text-align: center;">'
# #             f'<span class="status-indicator {status_colors.get(st.session_state.status, "status-idle")}"></span>'
# #             f'<strong>{status_text.get(st.session_state.status, "Ready")}</strong>'
# #             f'</div>',
# #             unsafe_allow_html=True
# #         )

# #     if st.session_state.status in ["listening", "speaking"]:
# #         st.markdown('<div class="voice-indicator">🎙️</div>', unsafe_allow_html=True)

# #     if st.session_state.total_questions > 0:
# #         progress = st.session_state.current_question_idx / st.session_state.total_questions
# #         st.progress(progress)
# #         st.caption(f"Question {st.session_state.current_question_idx + 1} of {st.session_state.total_questions}")

# #     st.markdown("---")

# #     if st.session_state.current_question and st.session_state.status == "listening":
# #         st.markdown(f'<div class="question-box"><strong>Current Question:</strong><br>{st.session_state.current_question}</div>', unsafe_allow_html=True)

# #     status_placeholder = st.empty()
# #     status_placeholder.info("🔄 Connecting to Nova Sonic...")

# #     transcript_placeholder = st.expander("📝 Conversation Transcript", expanded=False)

# #     if st.button("🛑 End Interview Early", use_container_width=True, type="secondary"):
# #         st.session_state.interview_active = False
# #         if st.session_state.audio_handler:
# #             st.session_state.audio_handler.cleanup()
# #         st.rerun()

# #     if st.session_state.audio_handler:
# #         asyncio.run(handle_websocket(
# #             token,
# #             st.session_state.audio_handler,
# #             status_placeholder,
# #             transcript_placeholder
# #         ))

# #         st.session_state.audio_handler.cleanup()
# #         st.session_state.audio_handler = None

# # # Show completion
# # elif st.session_state.interview_complete:
# #     st.success("### ✅ Interview Completed!")
# #     st.balloons()

# #     st.markdown("---")

# #     st.markdown("### 📋 Your Responses")
# #     if st.session_state.responses:
# #         for i, resp in enumerate(st.session_state.responses, 1):
# #             with st.expander(f"Question {i}", expanded=False):
# #                 st.markdown(f"**Q:** {resp['question']}")
# #                 st.markdown(f"**A:** {resp['answer']}")

# #     st.markdown("---")

# #     st.markdown("### 📝 Full Transcript")
# #     for line in st.session_state.transcript:
# #         st.write(line)

# #     st.markdown("---")

# #     st.markdown("""
# #     ### Thank you for completing the exit interview!

# #     Your feedback has been recorded and will help us improve.

# #     You can now close this window.
# #     """)

# # # Sidebar
# # with st.sidebar:
# #     st.markdown("### 🎙️ About Nova Sonic")
# #     st.markdown("""
# #     Nova Sonic is Amazon's advanced voice AI:

# #     - 🎤 Real-time speech recognition
# #     - 🔊 Natural voice synthesis
# #     - 💬 Bidirectional conversation
# #     - ⚡ Low latency responses

# #     **Tips:**
# #     - Speak clearly and naturally
# #     - Wait for Nova to finish speaking
# #     - Be honest and open with your feedback
# #     """)

# #     st.markdown("---")

# #     if st.session_state.interview_active and st.session_state.audio_handler:
# #         st.markdown(f"**Status:** {st.session_state.status}")
# #         if st.session_state.total_questions > 0:
# #             st.markdown(f"**Progress:** {st.session_state.current_question_idx}/{st.session_state.total_questions}")
        
# #         buffer_status = st.session_state.audio_handler.get_buffer_status()
# #         st.markdown(f"**Buffer:** {buffer_status['buffer_frames']:.1f} frames")
# #         st.markdown(f"**Latency:** {buffer_status['total_latency_ms']:.0f}ms")

# #     st.markdown("---")
# #     st.caption("Powered by AWS Bedrock • Nova Sonic v1.0")




# import streamlit as st
# import requests
# import json
# from datetime import datetime
# import os
# from dotenv import load_dotenv
# import asyncio
# import websockets
# import base64
# import pyaudio
# import threading
# import queue
# import time

# load_dotenv()

# API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000/api")
# WS_BASE = os.getenv("WS_BASE_URL", "ws://localhost:8000/ws")

# st.set_page_config(
#     page_title="Nova Voice Exit Interview",
#     page_icon="🎙️",
#     layout="wide"
# )

# st.markdown("""
# <style>
#     .main-header {
#         font-size: 2.5rem;
#         font-weight: bold;
#         background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#         -webkit-background-clip: text;
#         -webkit-text-fill-color: transparent;
#         text-align: center;
#         margin-bottom: 20px;
#     }
#     .voice-indicator {
#         width: 100px;
#         height: 100px;
#         border-radius: 50%;
#         background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#         margin: 20px auto;
#         display: flex;
#         align-items: center;
#         justify-content: center;
#         animation: pulse 2s infinite;
#     }
#     @keyframes pulse {
#         0%, 100% { transform: scale(1); opacity: 1; }
#         50% { transform: scale(1.1); opacity: 0.8; }
#     }
#     .question-box {
#         background: #f0f2f6;
#         padding: 20px;
#         border-radius: 10px;
#         border-left: 5px solid #667eea;
#         margin: 20px 0;
#     }
#     .status-indicator {
#         display: inline-block;
#         width: 12px;
#         height: 12px;
#         border-radius: 50%;
#         margin-right: 8px;
#     }
#     .status-listening { background-color: #ff4444; animation: blink 1s infinite; }
#     .status-speaking { background-color: #4CAF50; }
#     .status-idle { background-color: #ffa500; }
#     @keyframes blink {
#         0%, 100% { opacity: 1; }
#         50% { opacity: 0.3; }
#     }
#     .qa-pair {
#         background: #f8f9fa;
#         border-left: 4px solid #667eea;
#         padding: 15px;
#         margin: 10px 0;
#         border-radius: 5px;
#     }
#     .qa-question {
#         font-weight: bold;
#         color: #667eea;
#         margin-bottom: 8px;
#     }
#     .qa-answer {
#         color: #333;
#         font-style: italic;
#     }
# </style>
# """, unsafe_allow_html=True)

# # ==================== AUDIO HANDLER ====================
# class AudioHandler:
#     def __init__(self):
#         self.FORMAT = pyaudio.paInt16
#         self.CHANNELS = 1
#         self.INPUT_RATE = 16000
#         self.OUTPUT_RATE = 24000
#         self.INPUT_CHUNK = 320
#         self.OUTPUT_FRAME_SIZE = 4096
#         self.FRAME_BYTES = self.OUTPUT_FRAME_SIZE * 2

#         self.input_queue = queue.Queue(maxsize=20)
#         self.playback_queue = queue.Queue(maxsize=200)

#         self.audio = pyaudio.PyAudio()
#         self.input_stream = None
#         self.output_stream = None

#         self.recording = False
#         self.playing = False
#         self.playback_thread = None

#         self.playback_buffer = bytearray()
#         self.buffer_lock = threading.Lock()

#     def start_recording(self):
#         if self.recording:
#             return
#         self.recording = True
#         try:
#             try:
#                 self.input_stream = self.audio.open(
#                     format=self.FORMAT,
#                     channels=self.CHANNELS,
#                     rate=self.INPUT_RATE,
#                     input=True,
#                     frames_per_buffer=self.INPUT_CHUNK,
#                     stream_callback=self._record_callback,
#                     exception_on_overflow=False
#                 )
#             except TypeError:
#                 self.input_stream = self.audio.open(
#                     format=self.FORMAT,
#                     channels=self.CHANNELS,
#                     rate=self.INPUT_RATE,
#                     input=True,
#                     frames_per_buffer=self.INPUT_CHUNK,
#                     stream_callback=self._record_callback
#                 )
#             self.input_stream.start_stream()
#             print("🎤 Recording started")
#         except Exception as e:
#             print(f"❌ Failed to open input stream: {e}")
#             self.recording = False

#     def stop_recording(self):
#         self.recording = False
#         try:
#             if self.input_stream:
#                 try:
#                     self.input_stream.stop_stream()
#                 except Exception:
#                     pass
#                 try:
#                     self.input_stream.close()
#                 except Exception:
#                     pass
#                 self.input_stream = None
#         except Exception as e:
#             print(f"Error stopping input stream: {e}")

#     def _record_callback(self, in_data, frame_count, time_info, status):
#         if status and status != pyaudio.paInputUnderflow:
#             print(f"⚠️ Recording status: {status}")
        
#         if self.recording:
#             try:
#                 self.input_queue.put(in_data, block=False)
#             except queue.Full:
#                 print("⚠️ Input queue full")
#         return (None, pyaudio.paContinue)

#     def start_playback(self, prebuffer_frames=15):
#         if self.playing:
#             return
        
#         self.playing = True
#         self.playback_buffer = bytearray()

#         try:
#             try:
#                 self.output_stream = self.audio.open(
#                     format=self.FORMAT,
#                     channels=self.CHANNELS,
#                     rate=self.OUTPUT_RATE,
#                     output=True,
#                     frames_per_buffer=self.OUTPUT_FRAME_SIZE,
#                     exception_on_underflow=False
#                 )
#             except TypeError:
#                 self.output_stream = self.audio.open(
#                     format=self.FORMAT,
#                     channels=self.CHANNELS,
#                     rate=self.OUTPUT_RATE,
#                     output=True,
#                     frames_per_buffer=self.OUTPUT_FRAME_SIZE
#                 )
#             print("🔊 Playback stream opened")
#         except Exception as e:
#             print(f"❌ Failed to open output stream: {e}")
#             self.playing = False
#             return

#         self.playback_thread = threading.Thread(
#             target=self._playback_loop,
#             daemon=True,
#             name="PlaybackThread"
#         )
#         self.playback_thread.start()

#         print(f"⏳ Prebuffering {prebuffer_frames} frames...")
#         start_time = time.time()
#         while time.time() - start_time < 5.0:
#             with self.buffer_lock:
#                 if len(self.playback_buffer) >= (self.FRAME_BYTES * prebuffer_frames):
#                     print(f"✅ Prebuffer ready")
#                     return
#             time.sleep(0.05)
        
#         print("⚠️ Prebuffer timeout - starting anyway")

#     def _playback_loop(self):
#         print("▶️ Playback loop started")
        
#         try:
#             while self.playing:
#                 try:
#                     chunk = self.playback_queue.get(timeout=0.1)
#                     if chunk:
#                         with self.buffer_lock:
#                             self.playback_buffer.extend(chunk)
#                 except queue.Empty:
#                     pass
                
#                 with self.buffer_lock:
#                     if len(self.playback_buffer) >= self.FRAME_BYTES:
#                         frame = bytes(self.playback_buffer[:self.FRAME_BYTES])
#                         del self.playback_buffer[:self.FRAME_BYTES]
#                     else:
#                         frame = None
                
#                 if frame:
#                     try:
#                         self.output_stream.write(frame)
#                     except Exception as e:
#                         print(f"⚠️ Playback write error: {e}")
#                 else:
#                     silence = b'\x00' * self.FRAME_BYTES
#                     try:
#                         self.output_stream.write(silence)
#                     except Exception:
#                         pass
        
#         except Exception as e:
#             print(f"❌ Playback loop error: {e}")
#         finally:
#             print("⏹️ Playback loop stopped")

#     def play_audio(self, audio_base64):
#         try:
#             raw = base64.b64decode(audio_base64)
#             if not raw:
#                 return
#             with self.buffer_lock:
#                 self.playback_buffer.extend(raw)
#         except Exception as e:
#             print(f"❌ Error decoding audio: {e}")

#     def stop_playback(self):
#         self.playing = False
#         if self.playback_thread and self.playback_thread.is_alive():
#             self.playback_thread.join(timeout=1.0)
#         try:
#             if self.output_stream:
#                 try:
#                     self.output_stream.stop_stream()
#                 except Exception:
#                     pass
#                 try:
#                     self.output_stream.close()
#                 except Exception:
#                     pass
#                 self.output_stream = None
#         except Exception as e:
#             print(f"Error stopping output: {e}")

#     def cleanup(self):
#         self.stop_recording()
#         self.stop_playback()
#         try:
#             self.audio.terminate()
#             print("✅ Audio cleanup complete")
#         except Exception:
#             pass

#     def get_buffer_status(self):
#         with self.buffer_lock:
#             buffer_size = len(self.playback_buffer)
#         queue_size = self.playback_queue.qsize()
#         return {
#             'buffer_bytes': buffer_size,
#             'buffer_frames': buffer_size / self.FRAME_BYTES if self.FRAME_BYTES > 0 else 0,
#             'queue_size': queue_size,
#             'total_latency_ms': (buffer_size / 2 / self.OUTPUT_RATE * 1000) if self.OUTPUT_RATE > 0 else 0
#         }

# # ==================== WEBSOCKET HANDLER ====================
# async def handle_websocket(token, audio_handler, status_placeholder, transcript_placeholder):
#     """Handle WebSocket communication"""
#     uri = f"{WS_BASE}/interview/{token}"

#     try:
#         async with websockets.connect(uri) as websocket:
#             st.session_state.ws = websocket
#             st.session_state.status = "connected"

#             audio_handler.start_playback(prebuffer_frames=20)
#             audio_handler.start_recording()

#             send_task = asyncio.create_task(send_audio_loop(websocket, audio_handler))

#             while st.session_state.interview_active:
#                 try:
#                     message = await asyncio.wait_for(websocket.recv(), timeout=0.1)

#                     if message is None:
#                         continue
#                     try:
#                         data = json.loads(message)
#                     except Exception as e:
#                         print(f"Invalid JSON: {e}")
#                         continue

#                     msg_type = data.get('type')
#                     if not msg_type:
#                         continue

#                     if msg_type == 'session_start':
#                         st.session_state.session_id = data.get('session_id')
#                         st.session_state.total_questions = data.get('total_questions', 0)
#                         st.session_state.status = "speaking"
#                         try:
#                             status_placeholder.success("✅ Connected! Nova is starting...")
#                         except Exception:
#                             pass

#                     elif msg_type == 'text':
#                         role = data.get('role', 'ASSISTANT')
#                         content = data.get('content', '') or ''
#                         if role == 'ASSISTANT':
#                             st.session_state.transcript.append(f"🤖 Nova: {content}")
#                             st.session_state.status = "listening"
#                         else:
#                             st.session_state.transcript.append(f"👤 You: {content}")

#                         try:
#                             with transcript_placeholder.container():
#                                 for line in st.session_state.transcript[-3:]:
#                                     st.write(line)
#                         except Exception:
#                             pass

#                     elif msg_type == 'audio':
#                         audio_b64 = data.get('data')
#                         if audio_b64:
#                             audio_handler.play_audio(audio_b64)

#                     elif msg_type == 'response_saved':
#                         st.session_state.saved_responses.append({
#                             'question': data.get('question'),
#                             'answer': data.get('answer')
#                         })
#                         print(f"✅ Response saved: {data.get('question')[:50]}...")

#                     elif msg_type == 'interview_complete':
#                         st.session_state.interview_complete = True
#                         st.session_state.interview_active = False
#                         try:
#                             status_placeholder.success("✅ Interview completed successfully!")
#                         except Exception:
#                             pass
#                         print("✅ Interview marked as complete")
#                         break

#                     elif msg_type == 'error':
#                         try:
#                             status_placeholder.error(f"❌ Error: {data.get('message', 'Unknown')}")
#                         except Exception:
#                             pass
#                         break

#                 except asyncio.TimeoutError:
#                     continue
#                 except websockets.ConnectionClosed:
#                     print("⚠️ Connection closed")
#                     break
#                 except Exception as e:
#                     print(f"Error: {e}")
#                     break

#             send_task.cancel()
#             audio_handler.stop_recording()

#             try:
#                 await websocket.send(json.dumps({"type": "close"}))
#             except Exception:
#                 pass

#     except Exception as e:
#         try:
#             status_placeholder.error(f"❌ Connection error: {str(e)}")
#         except Exception:
#             pass
#         st.session_state.interview_active = False

# async def send_audio_loop(websocket, audio_handler):
#     """Send audio chunks"""
#     try:
#         while st.session_state.interview_active and audio_handler.recording:
#             try:
#                 audio_data = await asyncio.to_thread(audio_handler.input_queue.get, True, 0.1)
#                 if not audio_data:
#                     await asyncio.sleep(0.01)
#                     continue

#                 audio_base64 = base64.b64encode(audio_data).decode('utf-8')

#                 await websocket.send(json.dumps({
#                     'type': 'audio_chunk',
#                     'data': audio_base64
#                 }))

#             except queue.Empty:
#                 await asyncio.sleep(0.01)
#             except asyncio.CancelledError:
#                 break
#             except Exception as e:
#                 print(f"Error sending audio: {e}")
#                 break
#     except asyncio.CancelledError:
#         pass

# # ==================== MAIN APPLICATION ====================
# params = st.query_params
# token = params.get("token", None)

# if not token:
#     st.error("❌ Invalid or missing interview token.")
#     st.info("Please use the link provided in your email.")
#     st.stop()

# # Initialize session state
# if "initialized" not in st.session_state:
#     st.session_state.initialized = False
#     st.session_state.interview_info = None
#     st.session_state.ws = None
#     st.session_state.session_id = None
#     st.session_state.status = "idle"
#     st.session_state.total_questions = 0
#     st.session_state.transcript = []
#     st.session_state.saved_responses = []
#     st.session_state.interview_complete = False
#     st.session_state.interview_active = False
#     st.session_state.audio_handler = None

# # Fetch interview info
# if not st.session_state.initialized:
#     try:
#         response = requests.get(f"{API_BASE}/interviews/token/{token}")
#         if response.status_code != 200:
#             error_data = response.json()
#             st.error(f"❌ {error_data.get('detail', 'Invalid token')}")
#             st.stop()

#         st.session_state.interview_info = response.json()
#         st.session_state.initialized = True
#     except Exception as e:
#         st.error(f"❌ Error connecting to server: {str(e)}")
#         st.info("Make sure backend is running on http://localhost:8000")
#         st.stop()

# interview_info = st.session_state.interview_info

# # Header
# st.markdown('<p class="main-header">🎙️ Voice Exit Interview with Nova Sonic</p>', unsafe_allow_html=True)

# col1, col2, col3 = st.columns([1, 2, 1])
# with col2:
#     st.markdown(
#         '<div style="text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); '
#         'color: white; padding: 8px 16px; border-radius: 20px; display: inline-block;">'
#         '🔊 Powered by Amazon Nova Sonic</div>',
#         unsafe_allow_html=True
#     )

# st.markdown(f"### Welcome, **{interview_info['employee_name']}**!")
# st.markdown(f"**Department:** {interview_info['employee_department']}")
# st.markdown("---")

# # Show introduction if not started
# if not st.session_state.interview_active and not st.session_state.interview_complete:
#     st.info("### 🎙️ How this works:")
#     st.markdown("""
#     1. **Click Start** to begin your voice interview with Nova
#     2. **Nova speaks first** - Listen to the questions
#     3. **Speak your answers** - Your microphone will be active
#     4. **Nova responds** and moves to the next question
#     5. **All responses are saved** automatically
#     """)

#     st.markdown("### 📋 Questions Nova will ask:")
#     for i, q in enumerate(interview_info['questions'], 1):
#         st.markdown(f"**{i}.** {q}")

#     st.markdown("---")
#     st.warning("⚠️ Make sure your microphone is connected!")

#     if st.button("🎙️ Start Voice Interview", use_container_width=True, type="primary"):
#         st.session_state.audio_handler = AudioHandler()
#         st.session_state.interview_active = True
#         st.rerun()

# # Show interview interface
# elif st.session_state.interview_active and not st.session_state.interview_complete:

#     status_colors = {
#         "idle": "status-idle",
#         "listening": "status-listening",
#         "speaking": "status-speaking",
#         "connected": "status-idle"
#     }
#     status_text = {
#         "idle": "Initializing...",
#         "listening": "🎤 Listening to you...",
#         "speaking": "🔊 Nova is speaking...",
#         "connected": "Connected"
#     }

#     col1, col2, col3 = st.columns([1, 2, 1])
#     with col2:
#         st.markdown(
#             f'<div style="text-align: center;">'
#             f'<span class="status-indicator {status_colors.get(st.session_state.status, "status-idle")}"></span>'
#             f'<strong>{status_text.get(st.session_state.status, "Ready")}</strong>'
#             f'</div>',
#             unsafe_allow_html=True
#         )

#     if st.session_state.status in ["listening", "speaking"]:
#         st.markdown('<div class="voice-indicator">🎙️</div>', unsafe_allow_html=True)

#     if st.session_state.total_questions > 0:
#         progress = len(st.session_state.saved_responses) / st.session_state.total_questions
#         st.progress(progress)
#         st.caption(f"Answered {len(st.session_state.saved_responses)} of {st.session_state.total_questions} questions")

#     st.markdown("---")

#     status_placeholder = st.empty()
#     status_placeholder.info("🔄 Connecting to Nova Sonic...")

#     transcript_placeholder = st.expander("📝 Conversation Transcript", expanded=False)

#     if st.button("🛑 End Interview Early", use_container_width=True, type="secondary"):
#         st.session_state.interview_active = False
#         if st.session_state.audio_handler:
#             st.session_state.audio_handler.cleanup()
#         st.rerun()

#     if st.session_state.audio_handler:
#         asyncio.run(handle_websocket(
#             token,
#             st.session_state.audio_handler,
#             status_placeholder,
#             transcript_placeholder
#         ))

#         st.session_state.audio_handler.cleanup()
#         st.session_state.audio_handler = None

# # Show completion
# elif st.session_state.interview_complete:
#     st.success("### ✅ Interview Completed Successfully!")
#     st.balloons()

#     st.markdown("---")

#     st.markdown("### 📋 Your Responses")
#     if st.session_state.saved_responses:
#         for i, resp in enumerate(st.session_state.saved_responses, 1):
#             st.markdown(
#                 f'''<div class="qa-pair">
#                     <div class="qa-question">Q{i}: {resp['question']}</div>
#                     <div class="qa-answer">A: {resp['answer']}</div>
#                 </div>''',
#                 unsafe_allow_html=True
#             )
#     else:
#         st.warning("No responses were saved.")

#     st.markdown("---")

#     st.markdown("""
#     ### Thank you for completing the exit interview!

#     Your feedback has been recorded and will help us improve.

#     You can now close this window.
#     """)

# # Sidebar
# with st.sidebar:
#     st.markdown("### 🎙️ About Nova Sonic")
#     st.markdown("""
#     Nova Sonic is Amazon's advanced voice AI:

#     - 🎤 Real-time speech recognition
#     - 🔊 Natural voice synthesis
#     - 💬 Bidirectional conversation
#     - ⚡ Low latency responses

#     **Tips:**
#     - Speak clearly and naturally
#     - Wait for Nova to finish speaking
#     - Be honest with your feedback
#     """)

#     st.markdown("---")

#     if st.session_state.interview_active and st.session_state.audio_handler:
#         st.markdown(f"**Status:** {st.session_state.status}")
#         st.markdown(f"**Answered:** {len(st.session_state.saved_responses)}/{st.session_state.total_questions}")
        
#         buffer_status = st.session_state.audio_handler.get_buffer_status()
#         st.markdown(f"**Latency:** {buffer_status['total_latency_ms']:.0f}ms")

#     st.markdown("---")
#     st.caption("Powered by AWS Bedrock • Nova Sonic v1.0")



import streamlit as st
import requests
import json
from datetime import datetime
import os
from dotenv import load_dotenv
import asyncio
import websockets
import base64
import pyaudio
import threading
import queue
import time

load_dotenv()

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000/api")
WS_BASE = os.getenv("WS_BASE_URL", "ws://localhost:8000/ws")

st.set_page_config(
    page_title="Nova Voice Exit Interview",
    page_icon="🎙️",
    layout="wide"
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 20px;
    }
    .voice-indicator {
        width: 100px;
        height: 100px;
        border-radius: 50%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        margin: 20px auto;
        display: flex;
        align-items: center;
        justify-content: center;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0%, 100% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.1); opacity: 0.8; }
    }
    .question-box {
        background: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #667eea;
        margin: 20px 0;
    }
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
    }
    .status-listening { background-color: #ff4444; animation: blink 1s infinite; }
    .status-speaking { background-color: #4CAF50; }
    .status-idle { background-color: #ffa500; }
    @keyframes blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.3; }
    }
    .qa-pair {
        background: #f8f9fa;
        border-left: 4px solid #667eea;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    }
    .qa-question {
        font-weight: bold;
        color: #667eea;
        margin-bottom: 8px;
    }
    .qa-answer {
        color: #333;
        font-style: italic;
    }
    .timer-normal { color: green; font-size: 18px; font-weight: bold; }
    .timer-warning { color: orange; font-size: 18px; font-weight: bold; }
    .timer-error { color: red; font-size: 18px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ==================== AUDIO HANDLER ====================
class AudioHandler:
    def __init__(self):
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.INPUT_RATE = 16000
        self.OUTPUT_RATE = 24000
        self.INPUT_CHUNK = 320
        self.OUTPUT_FRAME_SIZE = 4096
        self.FRAME_BYTES = self.OUTPUT_FRAME_SIZE * 2

        self.input_queue = queue.Queue(maxsize=20)
        self.playback_queue = queue.Queue(maxsize=200)

        self.audio = pyaudio.PyAudio()
        self.input_stream = None
        self.output_stream = None

        self.recording = False
        self.playing = False
        self.playback_thread = None

        self.playback_buffer = bytearray()
        self.buffer_lock = threading.Lock()

    def start_recording(self):
        if self.recording:
            return
        self.recording = True
        try:
            try:
                self.input_stream = self.audio.open(
                    format=self.FORMAT,
                    channels=self.CHANNELS,
                    rate=self.INPUT_RATE,
                    input=True,
                    frames_per_buffer=self.INPUT_CHUNK,
                    stream_callback=self._record_callback,
                    exception_on_overflow=False
                )
            except TypeError:
                self.input_stream = self.audio.open(
                    format=self.FORMAT,
                    channels=self.CHANNELS,
                    rate=self.INPUT_RATE,
                    input=True,
                    frames_per_buffer=self.INPUT_CHUNK,
                    stream_callback=self._record_callback
                )
            self.input_stream.start_stream()
            print("🎤 Recording started")
        except Exception as e:
            print(f"❌ Failed to open input stream: {e}")
            self.recording = False

    def stop_recording(self):
        self.recording = False
        try:
            if self.input_stream:
                try:
                    self.input_stream.stop_stream()
                except Exception:
                    pass
                try:
                    self.input_stream.close()
                except Exception:
                    pass
                self.input_stream = None
        except Exception as e:
            print(f"Error stopping input stream: {e}")

    def _record_callback(self, in_data, frame_count, time_info, status):
        if status and status != pyaudio.paInputUnderflow:
            print(f"⚠️ Recording status: {status}")
        
        if self.recording:
            try:
                self.input_queue.put(in_data, block=False)
            except queue.Full:
                print("⚠️ Input queue full")
        return (None, pyaudio.paContinue)

    def start_playback(self, prebuffer_frames=15):
        if self.playing:
            return
        
        self.playing = True
        self.playback_buffer = bytearray()

        try:
            try:
                self.output_stream = self.audio.open(
                    format=self.FORMAT,
                    channels=self.CHANNELS,
                    rate=self.OUTPUT_RATE,
                    output=True,
                    frames_per_buffer=self.OUTPUT_FRAME_SIZE,
                    exception_on_underflow=False
                )
            except TypeError:
                self.output_stream = self.audio.open(
                    format=self.FORMAT,
                    channels=self.CHANNELS,
                    rate=self.OUTPUT_RATE,
                    output=True,
                    frames_per_buffer=self.OUTPUT_FRAME_SIZE
                )
            print("🔊 Playback stream opened")
        except Exception as e:
            print(f"❌ Failed to open output stream: {e}")
            self.playing = False
            return

        self.playback_thread = threading.Thread(
            target=self._playback_loop,
            daemon=True,
            name="PlaybackThread"
        )
        self.playback_thread.start()

        print(f"⏳ Prebuffering {prebuffer_frames} frames...")
        start_time = time.time()
        while time.time() - start_time < 5.0:
            with self.buffer_lock:
                if len(self.playback_buffer) >= (self.FRAME_BYTES * prebuffer_frames):
                    print(f"✅ Prebuffer ready")
                    return
            time.sleep(0.05)
        
        print("⚠️ Prebuffer timeout - starting anyway")

    def _playback_loop(self):
        print("▶️ Playback loop started")
        
        try:
            while self.playing:
                try:
                    chunk = self.playback_queue.get(timeout=0.1)
                    if chunk:
                        with self.buffer_lock:
                            self.playback_buffer.extend(chunk)
                except queue.Empty:
                    pass
                
                with self.buffer_lock:
                    if len(self.playback_buffer) >= self.FRAME_BYTES:
                        frame = bytes(self.playback_buffer[:self.FRAME_BYTES])
                        del self.playback_buffer[:self.FRAME_BYTES]
                    else:
                        frame = None
                
                if frame:
                    try:
                        self.output_stream.write(frame)
                    except Exception as e:
                        print(f"⚠️ Playback write error: {e}")
                else:
                    silence = b'\x00' * self.FRAME_BYTES
                    try:
                        self.output_stream.write(silence)
                    except Exception:
                        pass
        
        except Exception as e:
            print(f"❌ Playback loop error: {e}")
        finally:
            print("⏹️ Playback loop stopped")

    def play_audio(self, audio_base64):
        try:
            raw = base64.b64decode(audio_base64)
            if not raw:
                return
            with self.buffer_lock:
                self.playback_buffer.extend(raw)
        except Exception as e:
            print(f"❌ Error decoding audio: {e}")

    def stop_playback(self):
        self.playing = False
        if self.playback_thread and self.playback_thread.is_alive():
            self.playback_thread.join(timeout=1.0)
        try:
            if self.output_stream:
                try:
                    self.output_stream.stop_stream()
                except Exception:
                    pass
                try:
                    self.output_stream.close()
                except Exception:
                    pass
                self.output_stream = None
        except Exception as e:
            print(f"Error stopping output: {e}")

    def cleanup(self):
        self.stop_recording()
        self.stop_playback()
        try:
            self.audio.terminate()
            print("✅ Audio cleanup complete")
        except Exception:
            pass

    def get_buffer_status(self):
        with self.buffer_lock:
            buffer_size = len(self.playback_buffer)
        queue_size = self.playback_queue.qsize()
        return {
            'buffer_bytes': buffer_size,
            'buffer_frames': buffer_size / self.FRAME_BYTES if self.FRAME_BYTES > 0 else 0,
            'queue_size': queue_size,
            'total_latency_ms': (buffer_size / 2 / self.OUTPUT_RATE * 1000) if self.OUTPUT_RATE > 0 else 0
        }

# ==================== WEBSOCKET HANDLER ====================
async def handle_websocket(token, audio_handler, status_placeholder, transcript_placeholder):
    """Handle WebSocket communication"""
    uri = f"{WS_BASE}/interview/{token}"

    try:
        async with websockets.connect(uri) as websocket:
            st.session_state.ws = websocket
            st.session_state.status = "connected"

            audio_handler.start_playback(prebuffer_frames=20)
            audio_handler.start_recording()

            send_task = asyncio.create_task(send_audio_loop(websocket, audio_handler))

            while st.session_state.interview_active:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=0.1)

                    if message is None:
                        continue
                    try:
                        data = json.loads(message)
                    except Exception as e:
                        print(f"Invalid JSON: {e}")
                        continue

                    msg_type = data.get('type')
                    if not msg_type:
                        continue

                    if msg_type == 'session_start':
                        st.session_state.session_id = data.get('session_id')
                        st.session_state.total_questions = data.get('total_questions', 0)
                        st.session_state.timeout_seconds = data.get('timeout_seconds', 900)
                        st.session_state.start_time = time.time()
                        st.session_state.status = "speaking"
                        try:
                            status_placeholder.success("✅ Connected! Nova is starting...")
                        except Exception:
                            pass

                    elif msg_type == 'text':
                        role = data.get('role', 'ASSISTANT')
                        content = data.get('content', '') or ''
                        if role == 'ASSISTANT':
                            st.session_state.transcript.append(f"🤖 Nova: {content}")
                            st.session_state.status = "listening"
                        else:
                            st.session_state.transcript.append(f"👤 You: {content}")

                        try:
                            with transcript_placeholder.container():
                                for line in st.session_state.transcript[-3:]:
                                    st.write(line)
                        except Exception:
                            pass

                    elif msg_type == 'audio':
                        audio_b64 = data.get('data')
                        if audio_b64:
                            audio_handler.play_audio(audio_b64)

                    elif msg_type == 'response_saved':
                        st.session_state.saved_responses.append({
                            'question': data.get('question'),
                            'answer': data.get('answer')
                        })
                        print(f"✅ Response saved: {data.get('question')[:50]}...")

                    elif msg_type == 'interview_complete':
                        st.session_state.interview_complete = True
                        st.session_state.interview_active = False
                        try:
                            status_placeholder.success("✅ Interview completed successfully!")
                        except Exception:
                            pass
                        print("✅ Interview marked as complete")
                        break

                    elif msg_type == 'timeout':
                        st.session_state.interview_complete = True
                        st.session_state.interview_active = False
                        try:
                            status_placeholder.error("⏱️ Interview time limit reached!")
                        except Exception:
                            pass
                        print("⏱️ Interview timeout")
                        break

                    elif msg_type == 'error':
                        try:
                            status_placeholder.error(f"❌ Error: {data.get('message', 'Unknown')}")
                        except Exception:
                            pass
                        break

                except asyncio.TimeoutError:
                    continue
                except websockets.ConnectionClosed:
                    print("⚠️ Connection closed")
                    break
                except Exception as e:
                    print(f"Error: {e}")
                    break

            send_task.cancel()
            audio_handler.stop_recording()

            try:
                await websocket.send(json.dumps({"type": "close"}))
            except Exception:
                pass

    except Exception as e:
        try:
            status_placeholder.error(f"❌ Connection error: {str(e)}")
        except Exception:
            pass
        st.session_state.interview_active = False

async def send_audio_loop(websocket, audio_handler):
    """Send audio chunks"""
    try:
        while st.session_state.interview_active and audio_handler.recording:
            try:
                audio_data = await asyncio.to_thread(audio_handler.input_queue.get, True, 0.1)
                if not audio_data:
                    await asyncio.sleep(0.01)
                    continue

                audio_base64 = base64.b64encode(audio_data).decode('utf-8')

                await websocket.send(json.dumps({
                    'type': 'audio_chunk',
                    'data': audio_base64
                }))

            except queue.Empty:
                await asyncio.sleep(0.01)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error sending audio: {e}")
                break
    except asyncio.CancelledError:
        pass

# ==================== MAIN APPLICATION ====================
params = st.query_params
token = params.get("token", None)

if not token:
    st.error("❌ Invalid or missing interview token.")
    st.info("Please use the link provided in your email.")
    st.stop()

# Initialize session state
if "initialized" not in st.session_state:
    st.session_state.initialized = False
    st.session_state.interview_info = None
    st.session_state.ws = None
    st.session_state.session_id = None
    st.session_state.status = "idle"
    st.session_state.total_questions = 0
    st.session_state.timeout_seconds = 900  # 15 minutes
    st.session_state.start_time = None
    st.session_state.transcript = []
    st.session_state.saved_responses = []
    st.session_state.interview_complete = False
    st.session_state.interview_active = False
    st.session_state.audio_handler = None

# Fetch interview info
if not st.session_state.initialized:
    try:
        response = requests.get(f"{API_BASE}/interviews/token/{token}")
        if response.status_code != 200:
            error_data = response.json()
            st.error(f"❌ {error_data.get('detail', 'Invalid token')}")
            st.stop()

        st.session_state.interview_info = response.json()
        st.session_state.initialized = True
    except Exception as e:
        st.error(f"❌ Error connecting to server: {str(e)}")
        st.info("Make sure backend is running on http://localhost:8000")
        st.stop()

interview_info = st.session_state.interview_info

# Header
st.markdown('<p class="main-header">🎙️ Voice Exit Interview with Nova Sonic</p>', unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown(
        '<div style="text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); '
        'color: white; padding: 8px 16px; border-radius: 20px; display: inline-block;">'
        '🔊 Powered by Amazon Nova Sonic</div>',
        unsafe_allow_html=True
    )

st.markdown(f"### Welcome, **{interview_info['employee_name']}**!")
st.markdown(f"**Department:** {interview_info['employee_department']}")
st.markdown("---")

# Show introduction if not started
if not st.session_state.interview_active and not st.session_state.interview_complete:
    st.info("### 🎙️ How this works:")
    st.markdown("""
    1. **Click Start** to begin your voice interview with Nova
    2. **Nova speaks first** - Listen to the questions
    3. **Speak your answers** - Your microphone will be active
    4. **Nova responds** and moves to the next question
    5. **All responses are saved** automatically
    6. **Interview will automatically end after 15 minutes**
    """)

    st.markdown("### 📋 Questions Nova will ask:")
    for i, q in enumerate(interview_info['questions'], 1):
        st.markdown(f"**{i}.** {q}")

    st.markdown("---")
    st.warning("⚠️ Make sure your microphone is connected!")

    if st.button("🎙️ Start Voice Interview", use_container_width=True, type="primary"):
        st.session_state.audio_handler = AudioHandler()
        st.session_state.interview_active = True
        st.rerun()

# Show interview interface
elif st.session_state.interview_active and not st.session_state.interview_complete:

    status_colors = {
        "idle": "status-idle",
        "listening": "status-listening",
        "speaking": "status-speaking",
        "connected": "status-idle"
    }
    status_text = {
        "idle": "Initializing...",
        "listening": "🎤 Listening to you...",
        "speaking": "🔊 Nova is speaking...",
        "connected": "Connected"
    }

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(
            f'<div style="text-align: center;">'
            f'<span class="status-indicator {status_colors.get(st.session_state.status, "status-idle")}"></span>'
            f'<strong>{status_text.get(st.session_state.status, "Ready")}</strong>'
            f'</div>',
            unsafe_allow_html=True
        )

    # Add timer display
    if hasattr(st.session_state, 'start_time') and st.session_state.start_time:
        elapsed = time.time() - st.session_state.start_time
        remaining = max(0, st.session_state.timeout_seconds - elapsed)
        minutes, seconds = divmod(int(remaining), 60)
        
        if remaining > 60:
            timer_html = f'<div style="text-align: center;" class="timer-normal">⏱️ Time remaining: {minutes:02d}:{seconds:02d}</div>'
        elif remaining > 30:
            timer_html = f'<div style="text-align: center;" class="timer-warning">⚠️ Time remaining: {minutes:02d}:{seconds:02d}</div>'
        else:
            timer_html = f'<div style="text-align: center;" class="timer-error">🚨 Time remaining: {minutes:02d}:{seconds:02d}</div>'
        
        st.markdown(timer_html, unsafe_allow_html=True)

    if st.session_state.status in ["listening", "speaking"]:
        st.markdown('<div class="voice-indicator">🎙️</div>', unsafe_allow_html=True)

    if st.session_state.total_questions > 0:
        progress = len(st.session_state.saved_responses) / st.session_state.total_questions
        st.progress(progress)
        st.caption(f"Answered {len(st.session_state.saved_responses)} of {st.session_state.total_questions} questions")

    st.markdown("---")

    status_placeholder = st.empty()
    status_placeholder.info("🔄 Connecting to Nova Sonic...")

    transcript_placeholder = st.expander("📝 Conversation Transcript", expanded=False)

    if st.button("🛑 End Interview Early", use_container_width=True, type="secondary"):
        st.session_state.interview_active = False
        if st.session_state.audio_handler:
            st.session_state.audio_handler.cleanup()
        st.rerun()

    if st.session_state.audio_handler:
        asyncio.run(handle_websocket(
            token,
            st.session_state.audio_handler,
            status_placeholder,
            transcript_placeholder
        ))

        st.session_state.audio_handler.cleanup()
        st.session_state.audio_handler = None

# Show completion
elif st.session_state.interview_complete:
    if hasattr(st.session_state, 'timeout_reached') and st.session_state.timeout_reached:
        st.error("### ⏱️ Interview Time Limit Reached")
        st.markdown("The interview has been automatically ended after 15 minutes.")
    else:
        st.success("### ✅ Interview Completed Successfully!")
        st.balloons()

    st.markdown("---")

    st.markdown("### 📋 Your Responses")
    if st.session_state.saved_responses:
        for i, resp in enumerate(st.session_state.saved_responses, 1):
            st.markdown(
                f'''<div class="qa-pair">
                    <div class="qa-question">Q{i}: {resp['question']}</div>
                    <div class="qa-answer">A: {resp['answer']}</div>
                </div>''',
                unsafe_allow_html=True
            )
    else:
        st.warning("No responses were saved.")

    st.markdown("---")

    st.markdown("""
    ### Thank you for completing the exit interview!

    Your feedback has been recorded and will help us improve.

    You can now close this window.
    """)

# Sidebar
with st.sidebar:
    st.markdown("### 🎙️ About Nova Sonic")
    st.markdown("""
    Nova Sonic is Amazon's advanced voice AI:

    - 🎤 Real-time speech recognition
    - 🔊 Natural voice synthesis
    - 💬 Bidirectional conversation
    - ⚡ Low latency responses

    **Tips:**
    - Speak clearly and naturally
    - Wait for Nova to finish speaking
    - Be honest with your feedback
    - Interview will end after 15 minutes
    """)

    st.markdown("---")

    if st.session_state.interview_active and st.session_state.audio_handler:
        st.markdown(f"**Status:** {st.session_state.status}")
        st.markdown(f"**Answered:** {len(st.session_state.saved_responses)}/{st.session_state.total_questions}")
        
        buffer_status = st.session_state.audio_handler.get_buffer_status()
        st.markdown(f"**Latency:** {buffer_status['total_latency_ms']:.0f}ms")

    st.markdown("---")
    st.caption("Powered by AWS Bedrock • Nova Sonic v1.0")