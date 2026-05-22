# Women2Women

A cycle-tracking web app with personalized daily recommendations based on the user's menstrual phase, period prediction, and a cycle companion chatbot (Vera). Built with Flask and React.

## Requirements

- Python 3.10+
- XAMPP (MariaDB running on port 3306)
- A `women2women` database created in phpMyAdmin

Install dependencies:
```bash
pip install flask flask-cors flask-login werkzeug pymysql sentence-transformers
```

## How to Run

```bash
python app.py
```

- App: `http://localhost:5000`
- Admin panel: `http://localhost:5000/admin` (password: `admin123`)
