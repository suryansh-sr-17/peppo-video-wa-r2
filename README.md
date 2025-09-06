# 🎥 Peppo – AI-Powered Text to Video Generator Whatsapp Bot Integration

Round 2 Technical Challenge: A simple, provider-agnostic web app that helps generate **videos** from **text ideas** and **optimized prompts** using AI which is integrated into a **Whatsapp Bot** using **Twilio**  

- ⚡ **FastAPI** backend
- 🌐 **Twilio** integration framework
- ✨ **Creative idea generation** and **prompt optimization**  
- 🗂️ Clear project structure with providers & services  
- 🔑 **API key configurable** via `.env.example` (for api key configuration reference)  
- 🌍 Accessible via twilio whatsapp sandbox  

---

## ✨ Features  

- 👋 **Warm Welcome**: The bot sends an **introductory message** on startup to avoid cold starts for new (and especially kid) users.  
- ⌨️ **Kid-Friendly Commands**: Simple and easy command lines designed for children to **learn & explore** without confusion.  
- 💬 **Conversational Flow**: An interactive, chat-like mechanism that makes generating videos feel like talking to a friend.  
- 🧑‍🏫 **Friendly Prompt Optimizer**: Gently guides kids to improve their prompts while ensuring video quality stays top-notch.  
- 🔔 **Periodic Notifications**: Timely reminders encourage kids to **come back daily**, boosting engagement & retention.  
- ❤️ **Simple Feedback Loop**: Kids can share opinions 👍👎 easily, and their feedback gets fed back into improvements.  
- 🎬 **WhatsApp-Ready Videos**: Automatic **video compression with FFmpeg** keeps files under WhatsApp’s 16 MB limit.  
- ⚡ **Smart Performance**: Built-in **queueing, cache retrieval, and error handling** ensure a smooth, lag-free experience.  

---

## 📂 Project Structure

```bash
.
|   .env.example            # Sample API Key and other configurations
|   jobs.db                 # Video ID records database
|   requests.db             # User requests queue database
|   
+---api/                    # API endpoint
|       
+---app/                    # Core application logic
|   |   
|   +---integrations/       # Twilio integration endpoint
|   |           
|   +---providers/          # External provider integrations 
|   |           
|   +---services/           # Business logic and services
|   |           
|   +---static/             # Static files
|   |   |   
|   |   \---compressed/     # Compressed file from ffmpeg operation   
|   |           
|   +---templates/          # HTML templates
|   |       
|   +---workers/            # Whatsapp bot actions endpoints
|           
\---scripts/                # Operation scripts
```

---

## 🧭 Application Workflow

> **Workflow Diagram**
>
> ![Application Workflow](https://github.com/user-attachments/assets/9cf80355-e685-4544-bfad-8f9a86f9c707)

---

## 🌐 Demo Video:

[![Watch the demo](https://github.com/user-attachments/assets/bc62e253-9acc-4e4d-8f62-8746351c563d)]([https://www.youtube.com/watch?v=YOUR_VIDEO_ID](https://drive.google.com/file/d/1BOKV2pV-Y-rX3z3js2JW9vnbQHO1PPpg/view?usp=sharing))

---

## 📲 Phone Demo Screenshots  

<p align="center">
  <img src="https://github.com/user-attachments/assets/e25fecb5-5662-4f68-a477-f0323881d28c" alt="Screenshot 1" width="45%" />
  <img src="https://github.com/user-attachments/assets/f645e07d-46fe-4d12-8797-d404a503c340" alt="Screenshot 2" width="45%" />
</p>

<p align="center">
  <img src="https://github.com/user-attachments/assets/d4311c45-05be-40df-94fd-e64ca507d53e" alt="Screenshot 3" width="45%" />
  <img src="https://github.com/user-attachments/assets/c7b4aa71-796d-4eae-a2ad-a02492a573d5" alt="Screenshot 4" width="45%" />
</p>

<p align="center">
  <img src="https://github.com/user-attachments/assets/a3e8cf52-546d-4910-b447-c55a01de8532" alt="Screenshot 5" width="45%" />
</p>

---

## 🌐 Demo Website:

👉 Live App URL: [https://peppo-video-app-new.vercel.app/](https://peppo-video-app-new.vercel.app/)

---

## ⚓ Twilio Account SetUp

> **Guidelines**
>
> ![Create a Twilio account with your email id and verify it with your phone number](https://github.com/user-attachments/assets/11e9e4ea-91d3-4040-b6aa-b477ba736381)
>
> ![Copy your Account SID and Auth Token from the Dashboard and add it to your .env file](https://github.com/user-attachments/assets/a8c4e106-db56-4979-8739-c61aaf383c6e)
>
> ![Scan the QR code and then use your code to gain access to your Twilio Whatsapp Sandbox](https://github.com/user-attachments/assets/98f3b4ba-1d7c-43ee-86c0-a8e5118b098b)
>
> ![Expose your FAST API port using **ngrok** and use it's "/webhook/whatsapp" endpoint for POST operations](https://github.com/user-attachments/assets/5e296e92-bf2d-4689-9659-3494ab543b19)

---
