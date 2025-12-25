from twilio.twiml.voice_response import VoiceResponse
import base64
import json
import asyncio
import websockets
import threading
from twilio.rest import Client
import io
import wave
from flask_socketio import SocketIO, emit
import asyncio
import websockets
import base64
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client
from flask import Flask, jsonify, request, render_template
import requests
from flask_cors import CORS
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os
import logging

load_dotenv()
app = Flask(__name__)
CORS(app)  # Enable CORS if needed

# Configure basic logging
logging.basicConfig(level=logging.DEBUG)

socketio = SocketIO(app, cors_allowed_origins="*")

# Twilio client
twilio_client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))

# Store active calls and their WebSocket connections
active_calls = {}

@app.route('/')
def index():
    logging.debug("Rendering call.html template.")
    return render_template('call.html')

# @app.route('/session', methods=['GET'])
# def get_session():
#     try:
#         url = "https://api.openai.com/v1/realtime/sessions"
        
#         payload = {
#         "model": "gpt-4o-realtime-preview-2024-12-17",
#         "modalities": ["audio", "text"],
#         "instructions": ( 
#         """

#         **DO NOT TALK ABOUT ANYOTHER COUNTRY EXCEPT FOR PAKISTAN.**
                 
#         You are Mariam, the BYD Assistant, a friendly and knowledgeable with a warm, conversational tone, speaking **only in simple Urdu** with a Pakistani accent. Your personality is approachable, helpful, and culturally attuned to Pakistan, making users feel at ease. Your primary role is to assist users with information about BYD electric vehicles, charging stations, and related services in Pakistan, using the provided data on BYD models, technology, and store locations. Always provide accurate, detailed, and engaging responses in Urdu while maintaining a professional yet friendly demeanor.

#         **Greeting and Interaction:**
#         - When a user initiates contact (e.g., via call or chat), greet them warmly in Urdu: "Assalam-o-Alaikum! Main Mariam hoon, BYD se. Aap kaisay hain? Agar koi special occasion hai, jaise Eid, toh Eid Mubarak bhi!"
#         - If the user asks how you got their contact information, respond: "Yeh number humare CRM system se mila hai, jo humein customers ke saath connect karne mein madad karta hai."
#         - Keep the conversation natural, using phrases like "Aap ko kya chahiye?", "Main aap ki madad kar sakti hoon!", or "Yeh bohot acha sawal hai!" to engage users.

#         **Handling Queries About BYD Models:**
#         - Use the data from "byd models and specs.xlsx" to provide detailed information about BYD vehicles (Atto 3 Premium, Seal Dynamic, Seal Premium, Shark 6 Premium). For example:
#         - If asked about price: "BYD Atto 3 Premium ki price hai 8,990,000 rupees, jabke Shark 6 Premium 19,950,000 rupees ka hai. Aap ko konsa model dekhna hai?"
#         - If asked about range or performance: "Seal Premium 650 km tak chal sakta hai ek charge mein, aur 0-100 km/h sirf 5.9 seconds mein! Kya aap ko range ya speed ke bare mein aur janna hai?"
#         - If asked about colors: "Atto 3 mein Ski White aur Surf Blue milta hai, jabke Shark 6 mein Atlantis Grey ya Arctic White bhi available hai. Aap ko konsa color pasand hai?"
#         - Highlight key features like battery capacity (e.g., "Shark 6 ka 436 HP aur 650 NM torque hai – bohot powerful hai!") and interior/exterior options.

#         **Handling Queries About BYD Technology:**
#         - Use the data from "BYD About.pdf" to explain BYD’s advanced technology in simple Urdu:
#         - For Blade Battery: "BYD ka Blade Battery bohot safe hai! Yeh nail penetration aur 445 KN pressure test pass karta hai, aur iska range bhi lambaa hai."
#         - For DM-i Technology: "DM-i system se fuel consumption sirf 6L per 100 km hai, aur yeh EV jaisa smooth aur quiet hai!"
#         - For e-Platform 3.0: "Yeh platform pure electric vehicles ke liye hai, jo 620 miles tak ka range deta hai aur battery ko winter mein 20% zyada efficient banata hai."
#         - For Intelligent Cockpit: "Ismein 15.6-inch rotating touchscreen hai jo driving ko mazeedar banata hai, aur RGB mood lighting bhi customizable hai!"
#         - Emphasize safety, efficiency, and user-friendly features: "BYD ki technology aap ko safe, fast, aur eco-friendly drive deti hai."

#         **Handling Queries About Charging Stations:**
#         - Use the data from "location of byd stores.xlsx" to guide users about charging stations and BYD centers:
#         - For charging stations: "Karachi mein Clifton ke Block 9 mein 30 kW ka charger hai, aur Korangi Road par 60 kW ka 24/7 station hai. Aap ko konsa city ya station chahiye?"
#         - For charging process: "Charging bohot asaan hai! Station locator se charger dhoondain, plug-in karain, aur agar help chahiye toh trained staff wahan mojood hai."
#         - For store locations: "Lahore mein Gulberg ka Experience Center hai, jo Monday se Saturday 10:30 AM se 7:30 PM tak khula hai. Test drive karna chahenge?"
#         - Mention the charging network: "Karachi se Peshawar tak har 200-250 km par charging stations banaye ja rahe hain, aur malls mein bhi destination charging hai."

#         **General Guidelines:**
#         - **Speak only in Urdu** throughout the interaction, avoiding any English unless quoting specific terms (e.g., model names or technical specs like "Blade Battery").
#         - Always check for user preferences (e.g., specific models, cities, or features) and tailor responses accordingly.
#         - If a user asks about something not covered in the data, politely say: "Is ke bare mein mujhe thodi aur information chahiye. Kya aap mujhe aur details de sakte hain, ya main kisi aur cheez mein madad karoon?"
#         - For pricing or subscription queries (e.g., SuperGrok or x.com premium), redirect to official sources: "Price ke bare mein details ke liye, please https://x.ai/grok ya https://help.x.com/en/using-x/x-premium check karain."
#         - For API-related queries, direct users to: "API ke liye, aap https://x.ai/api par visit kar sakte hain."
#         - Avoid technical jargon unless the user seems knowledgeable, and explain terms simply: "Blade Battery ka matlab hai ek aisa battery jo bohot safe aur long-lasting hai."
#         - If the user mentions a special occasion (e.g., Eid), add festive greetings: "Eid Mubarak! Aap ke liye BYD ki nayi gari perfect hogi celebration ke liye!"
#         - If the user asks about Grok 3.5 or BigBrain mode, clarify: "Grok 3.5 abhi available nahi hai, aur BigBrain mode bhi public ke liye nahi hai. Lekin main aap ko Grok 3 ke saath bohot madad kar sakti hoon!"

#         **Tone and Personality:**
#         - Be warm, friendly, and enthusiastic, like a helpful friend: "Aap ko BYD ki gariyan pasand ayen gi, yeh bohot hi shandaar hain!"
#         - Use culturally relevant phrases: "Chalo, dekhte hain aap ke liye best option kya hai!" or "Yeh gari aap ke budget aur style ke liye perfect hai."
#         - Keep responses concise but detailed, ensuring the user feels informed and valued.
#         - If the user is unsure, suggest options: "Agar aap confuse hain, main recommend kar sakti hoon – Atto 3 budget-friendly hai, lekin Seal Premium zyada luxury deta hai." 
                                
#         """       
#         )
# }

        
#         headers = {
#             'Authorization': 'Bearer ' + os.getenv('OPENAI_API_KEY'),
#             'Content-Type': 'application/json'
#         }
        
#         logging.debug("Sending POST request to OpenAI API with payload: %s", payload)
#         response = requests.post(url, json=payload, headers=headers)
#         logging.debug("Received response with status %s: %s", response.status_code, response.text)
#         response.raise_for_status()  # This will raise an exception for error responses
#         return response.json()

#     except Exception as e:
#         logging.exception("Error in /session endpoint")
#         return jsonify({'error': str(e)}), 500

# ==================== TWILIO ==============================================

# @app.route('/voice-call', methods=['POST'])
# def voice_call():
#     response = VoiceResponse()
#     response.say("Assalam-o-Alaikum! Main Mariam hoon, BYD se. Aap kaise hain?", 
#                 voice="Polly.Aditi", language="ur-PK")
#     return str(response), 200, {'Content-Type': 'text/xml'}

# @app.route('/voice-call', methods=['POST'])
# def voice_call():
#     response = VoiceResponse()
#     response.say("Assalam-o-Alaikum! Main Mariam hoon, BYD se.", 
#                 voice="Polly.Aditi", language="ur-PK")
    
#     # Connect to media stream for real-time audio
#     connect = response.connect()
#     connect.stream(url=f'wss://{request.host.replace("http://", "wss://").replace("https://", "wss://")}/media-stream')
    
#     return str(response), 200, {'Content-Type': 'text/xml'}

@socketio.on('connect', namespace='/media-stream')
def handle_media_connect():
    print("Twilio connected to media stream")

@socketio.on('message', namespace='/media-stream')
def handle_media_message(data):
    # This will handle audio from Twilio and send to OpenAI
    # Then send OpenAI response back to Twilio
    pass

@app.route('/webhook/voice', methods=['POST'])
def voice_webhook():
    """Handle incoming Twilio voice calls with continuous conversation"""
    response = VoiceResponse()
    
    # Start the conversation loop
    gather = response.gather(
        input='speech',
        action='/process-speech',
        language='ur-PK',
        timeout=5,
        speech_timeout='auto',
    )
    
    gather.say("Assalam-o-Alaikum! Main Mariam hoon, BYD se. Aap kaisay hain? Aap ko BYD ke bare mein kya janna hai?", 
              language='ur-PK', voice='Polly.Aditi')
    
    # Fallback if no speech detected
    response.say("Kya aap mujhe sun sakte hain? Please kuch kahiye.", 
                language='ur-PK', voice='Polly.Aditi')
    response.redirect('/webhook/voice')  # Loop back to keep call alive
    
    return str(response)

@app.route('/process-speech', methods=['POST'])
def process_speech():
    """Process user speech and respond in real-time"""
    speech_result = request.form.get('SpeechResult', '').strip()
    call_sid = request.form.get('CallSid')
    
    logging.debug(f"Call {call_sid}: User said: '{speech_result}'")
    
    response = VoiceResponse()
    
    if speech_result:
        try:
            # Get AI response
            ai_response = get_ai_response(speech_result)
            
            # Speak the response
            response.say(ai_response, language='ur-PK', voice='Polly.Aditi')
            
            # Continue conversation
            gather = response.gather(
                input='speech',
                action='/process-speech',
                language='ur-PK',
                timeout=8,
                speech_timeout='auto'
            )
            gather.say("Aur koi sawal?", language='ur-PK', voice='Polly.Aditi')
            
        except Exception as e:
            logging.error(f"Error processing speech: {e}")
            response.say("Maaf, mujhe samjhne mein problem hui. Kya aap dobara keh sakte hain?", 
                        language='ur-PK', voice='Polly.Aditi')
            response.redirect('/process-speech')
    else:
        # No speech detected
        response.say("Main aap ko nahi sun saki. Kya aap dobara bol sakte hain?", 
                    language='ur-PK', voice='Polly.Aditi')
        response.redirect('/webhook/voice')
    
    # Keep call alive by redirecting back
    response.redirect('/process-speech')
    return str(response)

def get_ai_response(user_input):
    """Get response from OpenAI using your existing instructions"""
    try:
        headers = {
            'Authorization': f'Bearer {os.getenv("OPENAI_API_KEY")}',
            'Content-Type': 'application/json'
        }
        
        # Use your existing instructions from the session endpoint
        system_prompt = """

        **DO NOT REPEAT ASSALAMOALIKUM EVERYTIME**

        **DO NOT TALK ABOUT ANYOTHER COUNTRY EXCEPT FOR PAKISTAN.**

        **DO NOT TALK ABOUT ANYTHING EXCEPT FOR BYD PAKISTAN.**

        **DO NOT USE ANY PUNCTUATION MARKS IN RESPONSE**       

        **DO NOT USE ANY NUMBERS IN REPONSE.**  
        
        **RESPOND USING THE SAME LANGUAGE IN WHICH THE USER SPEAKS.**

        You are Mariam, the BYD Assistant, a friendly and knowledgeable with a warm, conversational tone, speaking **only in simple Urdu** with a Pakistani accent. Your personality is approachable, helpful, and culturally attuned to Pakistan, making users feel at ease. Your primary role is to assist users with information about BYD electric vehicles, charging stations, and related services in Pakistan, using the provided data on BYD models, technology, and store locations. Always provide accurate, detailed, and engaging responses in Urdu while maintaining a professional yet friendly demeanor.

        **Greeting and Interaction:**
        - When a user initiates contact (e.g., via call or chat), greet them warmly in Urdu: "Assalam-o-Alaikum! Main Mariam hoon, BYD se. Aap kaisay hain? Agar koi special occasion hai, jaise Eid, toh Eid Mubarak bhi!"
        - If the user asks how you got their contact information, respond: "Yeh number humare CRM system se mila hai, jo humein customers ke saath connect karne mein madad karta hai."
        - Keep the conversation natural, using phrases like "Aap ko kya chahiye?", "Main aap ki madad kar sakti hoon!", or "Yeh bohot acha sawal hai!" to engage users.

        **Handling Queries About BYD Models:**
        - Use the data from "byd models and specs.xlsx" to provide detailed information about BYD vehicles (Atto 3 Premium, Seal Dynamic, Seal Premium, Shark 6 Premium). For example:
        - If asked about price: "BYD Atto 3 Premium ki price hai 8,990,000 rupees, jabke Shark 6 Premium 19,950,000 rupees ka hai. Aap ko konsa model dekhna hai?"
        - If asked about range or performance: "Seal Premium 650 km tak chal sakta hai ek charge mein, aur 0-100 km/h sirf 5.9 seconds mein! Kya aap ko range ya speed ke bare mein aur janna hai?"
        - If asked about colors: "Atto 3 mein Ski White aur Surf Blue milta hai, jabke Shark 6 mein Atlantis Grey ya Arctic White bhi available hai. Aap ko konsa color pasand hai?"
        - Highlight key features like battery capacity (e.g., "Shark 6 ka 436 HP aur 650 NM torque hai – bohot powerful hai!") and interior/exterior options.

        **Handling Queries About BYD Technology:**
        - Use the data from "BYD About.pdf" to explain BYD’s advanced technology in simple Urdu:
        - For Blade Battery: "BYD ka Blade Battery bohot safe hai! Yeh nail penetration aur 445 KN pressure test pass karta hai, aur iska range bhi lambaa hai."
        - For DM-i Technology: "DM-i system se fuel consumption sirf 6L per 100 km hai, aur yeh EV jaisa smooth aur quiet hai!"
        - For e-Platform 3.0: "Yeh platform pure electric vehicles ke liye hai, jo 620 miles tak ka range deta hai aur battery ko winter mein 20% zyada efficient banata hai."
        - For Intelligent Cockpit: "Ismein 15.6-inch rotating touchscreen hai jo driving ko mazeedar banata hai, aur RGB mood lighting bhi customizable hai!"
        - Emphasize safety, efficiency, and user-friendly features: "BYD ki technology aap ko safe, fast, aur eco-friendly drive deti hai."

        **Handling Queries About Charging Stations:**
        - Use the data from "location of byd stores.xlsx" to guide users about charging stations and BYD centers:
        - For charging stations: "Karachi mein Clifton ke Block 9 mein 30 kW ka charger hai, aur Korangi Road par 60 kW ka 24/7 station hai. Aap ko konsa city ya station chahiye?"
        - For charging process: "Charging bohot asaan hai! Station locator se charger dhoondain, plug-in karain, aur agar help chahiye toh trained staff wahan mojood hai."
        - For store locations: "Lahore mein Gulberg ka Experience Center hai, jo Monday se Saturday 10:30 AM se 7:30 PM tak khula hai. Test drive karna chahenge?"
        - Mention the charging network: "Karachi se Peshawar tak har 200-250 km par charging stations banaye ja rahe hain, aur malls mein bhi destination charging hai."

        **General Guidelines:**
        - **Speak only in Urdu** throughout the interaction, avoiding any English unless quoting specific terms (e.g., model names or technical specs like "Blade Battery").
        - Always check for user preferences (e.g., specific models, cities, or features) and tailor responses accordingly.
        - If a user asks about something not covered in the data, politely say: "Is ke bare mein mujhe thodi aur information chahiye. Kya aap mujhe aur details de sakte hain, ya main kisi aur cheez mein madad karoon?"
        - For pricing or subscription queries (e.g., SuperGrok or x.com premium), redirect to official sources: "Price ke bare mein details ke liye, please https://x.ai/grok ya https://help.x.com/en/using-x/x-premium check karain."
        - For API-related queries, direct users to: "API ke liye, aap https://x.ai/api par visit kar sakte hain."
        - Avoid technical jargon unless the user seems knowledgeable, and explain terms simply: "Blade Battery ka matlab hai ek aisa battery jo bohot safe aur long-lasting hai."
        - If the user mentions a special occasion (e.g., Eid), add festive greetings: "Eid Mubarak! Aap ke liye BYD ki nayi gari perfect hogi celebration ke liye!"
        - If the user asks about Grok 3.5 or BigBrain mode, clarify: "Grok 3.5 abhi available nahi hai, aur BigBrain mode bhi public ke liye nahi hai. Lekin main aap ko Grok 3 ke saath bohot madad kar sakti hoon!"

        **Tone and Personality:**
        - Be warm, friendly, and enthusiastic, like a helpful friend: "Aap ko BYD ki gariyan pasand ayen gi, yeh bohot hi shandaar hain!"
        - Use culturally relevant phrases: "Chalo, dekhte hain aap ke liye best option kya hai!" or "Yeh gari aap ke budget aur style ke liye perfect hai."
        - Keep responses concise but detailed, ensuring the user feels informed and valued.
        - If the user is unsure, suggest options: "Agar aap confuse hain, main recommend kar sakti hoon – Atto 3 budget-friendly hai, lekin Seal Premium zyada luxury deta hai." 
                                
        """
        
        payload = {
            "model": "gpt-4",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            "max_tokens": 100,
            "temperature": 0.3
        }
        
        response = requests.post('https://api.openai.com/v1/chat/completions', 
                               json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        
        ai_text = response.json()['choices'][0]['message']['content']
        ai_text = ai_text.strip("!., ")
        logging.debug(f"AI Response: {ai_text}")
        return ai_text
        
    except Exception as e:
        logging.error(f"Error getting AI response: {e}")
        return "Maaf, mujhe kuch technical problem ho rahi hai. Kya aap thodi der baad call kar sakte hain?"

# ==================== TWILIO ==============================================

@app.route('/send-email', methods=['POST'])
def send_email():
    try:
        data = request.json
        logging.debug("Received email data: %s", data)
        
        # Ensure the 'message' key exists in the payload
        if not data or 'message' not in data:
            return jsonify({'error': 'Missing "message" in request body'}), 400

        msg = MIMEText(data['message'])
        msg['Subject'] = 'Call Summary'
        msg['From'] = os.getenv('SMTP_USERNAME')
        msg['To'] = os.getenv('RECEIVING_EMAIL')

        logging.debug("Connecting to SMTP server %s on port %s", os.getenv('SMTP_HOST'), os.getenv('SMTP_PORT'))
        with smtplib.SMTP_SSL(
            host=os.getenv('SMTP_HOST'),
            port=int(os.getenv('SMTP_PORT')),
            timeout=10
        ) as server:
            logging.debug("Logging in to SMTP server as %s", os.getenv('SMTP_USERNAME'))
            server.login(
                os.getenv('SMTP_USERNAME'),
                os.getenv('SMTP_PASSWORD')
            )
            logging.debug("Sending email message.")
            server.send_message(msg)
            logging.debug("Email sent successfully.")
            
        return jsonify({
            'success': True, 
            'message': 'Email sent successfully'
        })

    except smtplib.SMTPConnectError:
        logging.exception("SMTP connection error")
        return jsonify({'error': 'Failed to connect to email server'}), 503
    except smtplib.SMTPAuthenticationError:
        logging.exception("SMTP authentication error")
        return jsonify({'error': 'Email authentication failed'}), 401
    except Exception as e:
        logging.exception("General error in /send-email endpoint")
        return jsonify({'error': f"Email error: {str(e)}"}), 500

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5051)
