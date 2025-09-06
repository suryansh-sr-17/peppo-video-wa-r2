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
> ![Application Workflow](src/workflow.png)

---

## 🌐 Demo Video:

👉 Live App URL: [https://peppo-video-app-new.vercel.app/](https://peppo-video-app-new.vercel.app/)

---

## 📲 Phone Demo Screenshots

> ![](src/1wa.jpg)
>
> ![](src/2wa.jpg)
>
> ![](src/3wa.jpg)
>
> ![](src/4wa.jpg)
>
> ![](src/5wa.jpg)

---

## 🌐 Demo Website:

👉 Live App URL: [https://peppo-video-app-new.vercel.app/](https://peppo-video-app-new.vercel.app/)

---

## ⚓ Twilio Account SetUp

> **Guidelines**
>
> ![Create a Twilio account with your email id and verify it with your phone number](src/1.png)
>
> ![Copy your Account SID and Auth Token from the Dashboard and add it to your .env file](src/2.png)
>
> ![Scan the QR code and then use your code to gain access to your Twilio Whatsapp Sandbox](src/3.png)
>
> ![Expose your FAST API port using **ngrok** and use it's "/webhook/whatsapp" endpoint for POST operations](src/4.png)

---
