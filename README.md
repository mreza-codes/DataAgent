# DataAgent

**AI-powered data cleaning agent with automatic type detection, semantic cleaning, and clean CSV export.**  
DataAgent analyzes raw datasets, detects column types using LLM reasoning, applies safe preprocessing steps, fixes missing values, encodes categorical features, and exports a fully cleaned dataset ready for analysis or machine learning.

---

## 📸 Screenshot

Below is a preview of the DataAgent UI:

![DataAgent Screenshot](./sc.png)

---

## 🚀 Features

- **LLM-powered column type detection**  
  Automatically identifies numeric, categorical, text, and datetime columns using dataset preview + model reasoning.

- **Semantic cleaning engine**  
  Applies intelligent rules based on column names (e.g., duration parsing, long-text handling, ticket/cabin patterns).

- **Safe missing-value handling**  
  - Numeric → median  
  - Categorical → mode  
  - Datetime → forward-fill  
  - Text → empty string  

- **Automatic categorical encoding**  
  Lightweight encoder without sklearn/scipy dependencies.

- **Skewness correction**  
  Log-transform applied to highly skewed numeric columns (except population/area/density/rank fields).

- **Automatic datetime conversion**

- **Exports clean CSV**  
  Output saved in `/outputs/cleaned_data.csv`.

- **PyQt desktop interface**  
  Simple UI for loading datasets, previewing structure, cleaning, and exporting results.

---

## 📁 Project Structure

```
DataAgent/
│ main.py
│ agent.py
│ deepseek_model.py
│ ui_main.py
│ icon.ico
│ sc.png
│ README.md
│ requirements.txt
│
├── Tests/
│   ├── titanic_cleaned.csv
│   ├── world_population_cleaned.csv
│   ├── iris_cleaned.csv
│   └── Netflix_Titles_Cleaned.csv 
│
└── outputs/   (auto-created on runtime, ignored in Git)
```

---

## 🧠 How It Works

1. **Preview Phase**  
   The agent loads the dataset and generates a structured preview (dtypes, null counts, head, etc.).

2. **Reasoning Phase**  
   A lightweight LLM receives the preview and returns a JSON plan describing:
   - column types  
   - missing-value ratios  
   - high-cardinality columns  
   - datetime detection  

3. **Cleaning Phase**  
   The agent applies:
   - type corrections  
   - datetime parsing  
   - semantic rules  
   - missing-value handling  
   - categorical encoding  
   - skewness correction  
   - removal of fully-empty columns  

4. **Export Phase**  
   Cleaned dataset is saved to `/outputs/cleaned_data.csv`.

---

## 🖥️ Running the Application

### **Method 1 — Run with Python**
```
python main.py
```

### **Method 2 — Run without console (pythonw)**
```
pythonw main.py
```

---

## 📦 Requirements

```
pandas
numpy
requests
PyQt6
```

> No sklearn or scipy required.

---

## 🧪 Sample Datasets

The `Tests/` folder contains cleaned versions of common public datasets:

- Titanic  
- World Population  
- Iris  

These are included for demonstration and testing purposes.

---

## 📝 License

This project uses public datasets and is intended for educational and research use.

---

# معرفی

این برنامه یک دستیار هوشمند برای پاک‌سازی و آماده‌سازی داده‌هاست.  
سامانه با تحلیل اولیه‌ی جدول، نوع ستون‌ها را تشخیص می‌دهد، مقادیر خالی را به‌صورت ایمن اصلاح می‌کند، ستون‌های متنی و عددی را سامان‌دهی می‌کند و در پایان یک نسخه‌ی تمیز از داده را ذخیره می‌کند.

---

## امکانات

- تشخیص خودکار نوع ستون‌ها با کمک مدل هوشمند  
- پاک‌سازی معنایی بر اساس نام ستون‌ها  
- اصلاح مقادیر خالی با روش‌های ایمن  
- سامان‌دهی ستون‌های دسته‌ای  
- اصلاح کجی داده‌های عددی  
- تبدیل خودکار ستون‌های زمانی  
- ذخیره‌ی نسخه‌ی تمیز در پوشه‌ی خروجی  
- دارای رابط کاربری ساده و روان

---

## شیوه‌ی کار

۱. بررسی اولیه‌ی جدول و استخراج اطلاعات پایه  
۲. تشخیص نوع ستون‌ها با کمک مدل هوشمند  
۳. پاک‌سازی معنایی و اصلاح مقادیر خالی  
۴. سامان‌دهی ستون‌های دسته‌ای و عددی  
۵. ذخیره‌ی نسخه‌ی تمیز در پوشه‌ی خروجی

---

## اجرا

```
اجرای معمول:
python main.py




