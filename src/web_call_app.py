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

@app.route('/')
def index():
    logging.debug("Rendering call.html template.")
    return render_template('call.html')

@app.route('/session', methods=['GET'])
def get_session():
    try:
        url = "https://api.openai.com/v1/realtime/sessions"
        
        payload = {
        "model": "gpt-4o-realtime-preview-2024-12-17",
        "modalities": ["audio", "text"],
        "instructions": (
        """
        **DO NOT TALK ABOUT ANYOTHER COUNTRY EXCEPT FOR PAKISTAN.**
                 
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
        - Avoid technical jargon unless the user seems knowledgeable, and explain terms simply: "Blade Battery ka matlab hai ek aisa battery jo bohot safe aur long-lasting hai."
        - If the user mentions a special occasion (e.g., Eid), add festive greetings: "Eid Mubarak! Aap ke liye BYD ki nayi gari perfect hogi celebration ke liye!"
        - If the user asks about Grok 3.5 or BigBrain mode, clarify: "Grok 3.5 abhi available nahi hai, aur BigBrain mode bhi public ke liye nahi hai. Lekin main aap ko Grok 3 ke saath bohot madad kar sakti hoon!"

        **Tone and Personality:**
        - Be warm, friendly, and enthusiastic, like a helpful friend: "Aap ko BYD ki gariyan pasand ayen gi, yeh bohot hi shandaar hain!"
        - Use culturally relevant phrases: "Chalo, dekhte hain aap ke liye best option kya hai!" or "Yeh gari aap ke budget aur style ke liye perfect hai."
        - Keep responses concise but detailed, ensuring the user feels informed and valued.
        - If the user is unsure, suggest options: "Agar aap confuse hain, main recommend kar sakti hoon – Atto 3 budget-friendly hai, lekin Seal Premium zyada luxury deta hai." 
                                
        """       
        )
}

        
        headers = {
            'Authorization': 'Bearer ' + os.getenv('OPENAI_API_KEY'),
            'Content-Type': 'application/json'
        }
        
        logging.debug("Sending POST request to OpenAI API with payload: %s", payload)
        response = requests.post(url, json=payload, headers=headers)
        logging.debug("Received response with status %s: %s", response.status_code, response.text)
        response.raise_for_status()  # This will raise an exception for error responses
        return response.json()

    except Exception as e:
        logging.exception("Error in /session endpoint")
        return jsonify({'error': str(e)}), 500

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
    app.run(debug=True, port=5051)
