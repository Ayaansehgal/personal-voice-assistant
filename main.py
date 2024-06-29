import speech_recognition as sr
import pyttsx3
import webbrowser
import requests
import cv2
from fer import FER
import google.generativeai as genai
import os
import json

engine = pyttsx3.init()
recognizer = sr.Recognizer()
newsapi = "caceb7f1bfa146888b1f28efb4f60552"
emotion_detector = FER()
os.environ["GOOGLE_API_KEY"] = "AIzaSyBv9UyDqx5Klo6KOOPozrlOdVXP1YEoOac"
# Configure the Google Gemini AI
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
)
chat_session = model.start_chat(history=[])


def speak(text):
    engine.say(text)
    engine.runAndWait()


def recognize_emotion():
    cap = cv2.VideoCapture(0)
    emotion_response = {
        'angry': "Whoa, take it easy! Maybe some deep breaths?",
        'disgust': "Yikes! Something smells fishy?",
        'fear': "Don't worry, everything will be okay!",
        'happy': "Yay! Keep smiling!",
        'sad': "Oh no! How about a virtual hug?",
        'surprise': "Surprise! What's the big news?",
        'neutral': "Just chilling, I see."
    }
    emoji_dict = {
        'angry': "😡",
        'disgust': "🤢",
        'fear': "😱",
        'happy': "😊",
        'sad': "😢",
        'surprise': "😲",
        'neutral': "😐"
    }
    
    while True:
        ret, frame = cap.read()
        if ret:
            emotions = emotion_detector.detect_emotions(frame)
            if emotions:
                prominent_emotion = max(emotions[0]['emotions'], key=emotions[0]['emotions'].get)
                bounding_box = emotions[0]['box']
                x, y, w, h = bounding_box

                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                emotion_text = f"{prominent_emotion}: {emotions[0]['emotions'][prominent_emotion]:.2f}"
                cv2.putText(frame, emotion_text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2, cv2.LINE_AA)
                cv2.putText(frame, f"Detected Emotion: {prominent_emotion} {emoji_dict[prominent_emotion]}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)

                if prominent_emotion in emotion_response:
                    speak(emotion_response[prominent_emotion])

            cv2.imshow('Emotion Detector', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        else:
            break

    cap.release()
    cv2.destroyAllWindows()
    return prominent_emotion if emotions else None


def generate_gemini_response(input_text):
    response = chat_session.send_message(input_text)
    return response.text


def process_command(command):
    if "open google" in command.lower():
        webbrowser.open("https://google.com")
    elif "open youtube" in command.lower():
        webbrowser.open("https://youtube.com")
    elif command.lower().startswith("play"):
        song = command.lower().split(" ")[1]
        # Example mapping, ensure `musiclib` is defined
        musiclib = {
            "songname": "http://link.to/song"
        }
        link = musiclib.get(song)
        if link:
            webbrowser.open(link)
        else:
            speak("Sorry, I don't know that song.")
    elif "news" in command.lower():
        r = requests.get(f"https://newsapi.org/v2/top-headlines?country=in&apiKey={newsapi}")
        if r.status_code == 200:
            data = r.json()
            headlines = [article['title'] for article in data['articles']]
            for i, headline in enumerate(headlines, 1):
                speak(f"{i}. {headline}")
        else:
            speak(f"Failed to fetch headlines. Status code: {r.status_code}")
    elif "weather" in command.lower():
        speak("Sure, which city's weather would you like to know?")
        try:
            with sr.Microphone() as source:
                audio = recognizer.listen(source, timeout=5)
            city = recognizer.recognize_google(audio)
            weather_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid=00a90661361a47ed45eddf8861b5f840&units=metric"
            r = requests.get(weather_url)
            if r.status_code == 200:
                weather_data = r.json()
                description = weather_data['weather'][0]['description']
                temperature = weather_data['main']['temp']
                speak(f"The weather in {city} is {description}. The temperature is {temperature} degrees Celsius.")
            else:
                speak("Sorry, I couldn't fetch the weather information.")
        except sr.UnknownValueError:
            speak("Sorry, I didn't catch that. Please try again.")
        except sr.RequestError as e:
            speak(f"Sorry, there was an issue with the speech recognition service; {e}")
        except Exception as ex:
            speak(f"Error occurred: {ex}")
    elif "emotion" in command.lower():
        speak("Let me check your emotion.")
        emotion = recognize_emotion()
        if emotion:
            speak(f"You seem to be feeling {emotion}.")
        else:
            speak("Sorry, I couldn't recognize your emotion.")
    else:
        # Use Gemini AI for other commands
        response = generate_gemini_response(command)
        speak(response)


if __name__ == "__main__":
    speak("hi im cyrus")
    
    running = True
    r = sr.Recognizer()
    
    while running:
        try:
            with sr.Microphone() as source:
                print("Listening for wake word...")
                audio = r.listen(source, timeout=5)
                word = r.recognize_google(audio)
                if word.lower() == "cyrus":
                    speak("Hi, I'm your assistant. How can I help you today?...")
                    with sr.Microphone() as source:
                        print("Listening for command...")
                        audio = r.listen(source, timeout=5)
                        command = r.recognize_google(audio)
                        print(f"Command recognized: {command}")
                        if command.lower() == "stop":
                            speak("Goodbye!")
                            running = False
                        else:
                            process_command(command)
        except sr.UnknownValueError:
            print("Sorry, I couldn't understand what you said.")
        except sr.RequestError as e:
            print(f"Error occurred in recognizing speech; {e}")
        except Exception as ex:
            print(f"Error occurred: {ex}")
