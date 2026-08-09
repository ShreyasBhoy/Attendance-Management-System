import pandas as pd
from app import app
from models import db, Student, Attendance, Marks
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.preprocessing import StandardScaler
import pickle

# Models
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier


def load_data():
    with app.app_context():
        students = Student.query.all()
        attendance = Attendance.query.all()
        marks = Marks.query.all()

    # Convert to DataFrames
    att_df = pd.DataFrame([{
       "student_id": str(a.student_id).strip(),
       "status": a.status
    } for a in attendance])

    marks_df = pd.DataFrame([{
        "student_id": str(m.student_id).strip(),
        "internal": m.internal,
        "external": m.external,
        "submission": m.submission 
    } for m in marks])

    print(att_df.head())
    print(marks_df.head())
    return att_df, marks_df

    


def preprocess(att_df, marks_df):

    # Convert attendance to numeric
    att_df["present"] = att_df["status"].apply(
        lambda x: 1 if x.lower() == "present" else 0
    )

    # Attendance %
    attendance_percent = att_df.groupby("student_id")["present"].mean().reset_index()
    attendance_percent.rename(columns={"present": "attendance_percent"}, inplace=True)

    # Aggregate marks per student (IMPORTANT)
    marks_df = marks_df.groupby("student_id").mean().reset_index()

    # Merge attendance + marks
    df = pd.merge(attendance_percent, marks_df, on="student_id")

    # Total marks
    df["total_marks"] = df["internal"] + df["external"] + df["submission"]

    # Label (Pass / Risk)
    df["label"] = (
        (df["attendance_percent"] >= 0.75) &
        (df["internal"] >= 8) &
        (df["external"] >= 24) &
        (df["submission"] >= 8) &
        (df["total_marks"] >= 40)
    ).astype(int)

    return df

    
def train_model(df):
    # ✅ Use label from preprocess (DO NOT redefine)

    print("Label Distribution:\n", df["label"].value_counts())

    if df["label"].nunique() < 2:
        raise ValueError("❌ Still only one class in dataset. Fix labeling.")

    # Features & target
    X = df[["attendance_percent", "internal", "external", "submission"]]
    y = df["label"]

    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.4, stratify=y) 

    # Scaling
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    # Model
    model = LogisticRegression()
    model.fit(X_train, y_train)

    # Evaluation
    preds = model.predict(X_test)
    print("Accuracy:", accuracy_score(y_test, preds))
    print("Confusion Matrix:\n", confusion_matrix(y_test, preds, labels=[0, 1]))

    return model, scaler


def save_model(model, scaler):
    with open("model.pkl", "wb") as f:
        pickle.dump(model, f)

    with open("scaler.pkl", "wb") as f:
        pickle.dump(scaler, f)


if __name__ == "__main__":
    att_df, marks_df = load_data()
    df = preprocess(att_df, marks_df)

    model, scaler = train_model(df)
    save_model(model, scaler)

    print("✅ Model trained and saved!")