# 🥗 NutriGen AI – Intelligent Meal & Grocery Generation System

NutriGen AI is an AI-powered full-stack web application that generates personalized weekly meal plans and smart grocery lists for families based on their health conditions, dietary preferences, and nutritional requirements.

The system leverages Artificial Intelligence to recommend balanced Indian meals while automatically creating a consolidated grocery list, helping families maintain healthier lifestyles and simplify meal planning.

---

## 📌 Features

- 👨‍👩‍👧‍👦 Family Profile Management
- ➕ Add Multiple Family Members
- 🩺 Health Condition Based Meal Planning
- 🥦 Vegetarian & Non-Vegetarian Support
- 🤖 AI Generated Weekly Meal Plans
- 🛒 Automatic Grocery List Generation
- 📅 7-Day Meal Schedule
- 📄 Grocery List PDF Export
- ⚡ FastAPI Backend
- 💻 React Frontend
- 🗄 SQLite Database
- 🔥 Groq LLM Integration

---

## 🛠 Tech Stack

### Frontend
- React.js
- HTML5
- CSS3
- JavaScript
- Axios

### Backend
- Python
- FastAPI
- SQLAlchemy
- SQLite

### AI
- Groq API
- Llama 3 Model

### Tools
- Git
- GitHub
- VS Code
- Postman

---

## 📂 Project Structure

```
NutriGen-AI/
│
├── frontend/
│   ├── src/
│   ├── public/
│   └── package.json
│
├── backend/
│   ├── app/
│   ├── routers/
│   ├── models/
│   ├── database.py
│   ├── ai.py
│   ├── main.py
│   └── requirements.txt
│
└── README.md
```

---

## ⚙ Installation

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/NutriGen-AI.git

cd NutriGen-AI
```

---

## Backend Setup

Create Virtual Environment

```bash
python -m venv venv
```

Activate Virtual Environment

Windows

```bash
venv\Scripts\activate
```

Linux / Mac

```bash
source venv/bin/activate
```

Install Dependencies

```bash
pip install -r requirements.txt
```

Run Backend

```bash
uvicorn app.main:app --reload
```

Backend URL

```
http://localhost:8000
```

API Documentation

```
http://localhost:8000/docs
```

---

## Frontend Setup

Move to frontend

```bash
cd frontend
```

Install Packages

```bash
npm install
```

Run React App

```bash
npm start
```

Frontend URL

```
http://localhost:3000
```

---

## 🤖 AI Workflow

1. User creates a family.
2. Add family members.
3. Enter:
   - Age
   - Height
   - Weight
   - Gender
   - Health Conditions
   - Dietary Preference
4. Click **Generate Meal Plan**.
5. Groq AI generates a personalized 7-day meal plan.
6. Grocery list is extracted automatically.
7. User can export grocery list as PDF.

---

## 📸 Screenshots

Add screenshots here.

Example

```
screenshots/
    home.png
    mealplan.png
    grocery.png
```

---

## Future Enhancements

- User Authentication
- Cloud Database
- Mobile App
- Nutrition Charts
- Voice Assistant
- Barcode Scanner
- Food Image Recognition
- Calorie Tracking
- Fitness Integration

---

## Learning Outcomes

- Full Stack Development
- REST API Development
- FastAPI
- React
- Database Design
- AI API Integration
- Prompt Engineering
- Git & GitHub

---

## Contributors

**Adithya A N**

Computer Science & Engineering

AMC Engineering College

---

## License

This project is developed for educational and academic purposes.

---

## ⭐ If you like this project

Give this repository a ⭐ on GitHub!
