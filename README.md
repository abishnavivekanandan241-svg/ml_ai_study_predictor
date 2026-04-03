# 🎓 AI Student Predictor

## 🚀 Overview

AI Student Predictor is a web application that predicts student performance based on inputs such as study hours, attendance, and other academic metrics. It helps students and educators analyze learning patterns and make data-driven decisions.

---

## 🧠 How It Works

* User inputs student details (study hours, attendance, etc.)
* A **Random Forest Machine Learning model** processes the data
* The model predicts the student's performance score
* (Optional) SHAP is used to explain predictions

---

## 🛠 Tech Stack

* **Backend:** Flask (Python)
* **Machine Learning:** scikit-learn (Random Forest)
* **Data Handling:** pandas
* **Frontend:** HTML, CSS
* **Explainability (Optional):** SHAP

---

## 📁 Project Structure

```
ml_ai_study_predictor/
│
├── app.py              # Main Flask application
├── models.py           # Machine Learning logic
├── student_data.csv    # Dataset
├── templates/
│   ├── index.html
│   ├── history.html
│   └── base.html
├── requirements.txt
└── README.md
```

---

## ▶️ Run Locally

### 1. Clone the Repository

```bash
git clone https://github.com/abishnavivekanandan241-svg/ml_ai_study_predictor.git
cd ml_ai_study_predictor
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Application

```bash
python app.py
```

### 4. Open in Browser

Go to: [http://127.0.0.1:5000](http://127.0.0.1:5000)

---



## 🔐 Notes

* Store API keys in a `.env` file
* Add sensitive files to `.gitignore`

---

## 🚀 Future Improvements

* 🤖 Add AI chatbot for guidance
* 🔐 User authentication system
* ☁️ Deploy using Render / Railway / AWS
* 📊 Improve model accuracy with more data

---

## ⭐ Contributing

Pull requests are welcome. For major changes, please open an issue first.

---

## 📄 License

This project is open-source and available under the MIT License.
