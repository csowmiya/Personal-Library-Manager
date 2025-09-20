import streamlit as st
import sqlite3
import pandas as pd
from fpdf import FPDF
import matplotlib.pyplot as plt
import re

# -------------------- Database Setup --------------------
def connect_db():
    return sqlite3.connect("library.db")

def init_db():
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            userid INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            email TEXT,
            password TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            bookid INTEGER PRIMARY KEY AUTOINCREMENT,
            userid INTEGER,
            title TEXT,
            author TEXT,
            genre TEXT,
            status TEXT,
            FOREIGN KEY(userid) REFERENCES users(userid)
        )
    """)
    db.commit()
    db.close()

init_db()

# -------------------- Helper Functions --------------------
def validate_email(email):
    return re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email) is not None

def validate_password(password):
    return len(password) > 0

def generate_pdf(rows, username):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"{username}'s Library", ln=True, align="C")
    pdf.ln(10)

    # Table header
    pdf.set_font("Arial", "B", 12)
    pdf.cell(50, 10, "Title", border=1)
    pdf.cell(50, 10, "Author", border=1)
    pdf.cell(40, 10, "Genre", border=1)
    pdf.cell(40, 10, "Status", border=1)
    pdf.ln()

    # Table rows
    pdf.set_font("Arial", "", 12)
    for row in rows:
        pdf.cell(50, 10, row[0], border=1)
        pdf.cell(50, 10, row[1], border=1)
        pdf.cell(40, 10, row[2], border=1)
        pdf.cell(40, 10, row[3], border=1)
        pdf.ln()
    filename = "library.pdf"
    pdf.output(filename)
    return filename

# -------------------- App Pages --------------------
def home_page():
    st.title("📚 Personal Library Manager")
    st.write("Manage your books, track reading progress, and see stats.")
    if st.button("Login"):
        st.session_state.page = "login"
        st.rerun()
    if st.button("Register"):
        st.session_state.page = "register"
        st.rerun()

def register_page():
    st.title("Register")
    with st.form("register_form"):
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Register")
        if submitted:
            if not username or not validate_email(email) or not validate_password(password):
                st.error("Invalid input")
                return
            db = connect_db()
            cursor = db.cursor()
            cursor.execute("INSERT INTO users (username,email,password) VALUES (?, ?, ?)",
                           (username, email, password))
            db.commit()
            db.close()
            st.success("Registration successful! Please login.")
            st.session_state.page = "login"
            st.rerun()
    if st.button("Back"):
        st.session_state.page = "home"
        st.rerun()

def login_page():
    st.title("Login")
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            db = connect_db()
            cursor = db.cursor()
            cursor.execute("SELECT userid, username FROM users WHERE email=? AND password=?", (email, password))
            user = cursor.fetchone()
            db.close()
            if user:
                st.session_state.userid, st.session_state.username = user
                st.success("Login successful!")
                st.session_state.page = "menu"
                st.rerun()
            else:
                st.error("Invalid email or password")
    if st.button("Back"):
        st.session_state.page = "home"
        st.rerun()

def menu_page():
    st.title(f"Welcome, {st.session_state.username}!")
    if st.button("Add Book"):
        st.session_state.page = "add_book"
        st.rerun()
    if st.button("View Books"):
        st.session_state.page = "view_books"
        st.rerun()
    if st.button("Logout"):
        st.session_state.userid = None
        st.session_state.username = None
        st.session_state.page = "home"
        st.rerun()

def add_book_page():
    st.title("Add a New Book")
    title = st.text_input("Title")
    author = st.text_input("Author")
    genre = st.text_input("Genre")
    status = st.selectbox("Status", ["Reading", "Read", "Wishlist"])
    if st.button("Add Book"):
        if not title or not author or not genre:
            st.error("All fields are required")
            return
        db = connect_db()
        cursor = db.cursor()
        cursor.execute("INSERT INTO books (userid,title,author,genre,status) VALUES (?, ?, ?, ?, ?)",
                       (st.session_state.userid, title, author, genre, status))
        db.commit()
        db.close()
        st.success("Book added successfully!")
    if st.button("Back"):
        st.session_state.page = "menu"
        st.rerun()

def view_books_page():
    st.title("Your Library")
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("SELECT title, author, genre, status FROM books WHERE userid=?", (st.session_state.userid,))
    rows = cursor.fetchall()
    db.close()
    
    if rows:
        df = pd.DataFrame(rows, columns=["Title", "Author", "Genre", "Status"])
        st.dataframe(df)
        
        # Export buttons
        col1, col2 = st.columns(2)
        with col1:
            csv = df.to_csv(index=False)
            st.download_button("Download CSV", csv, f"{st.session_state.username}_library.csv", "text/csv")
        with col2:
            pdf_file = generate_pdf(rows, st.session_state.username)
            with open(pdf_file, "rb") as file:
                st.download_button("Download PDF", file, "library.pdf", "application/pdf")
        
        # Charts
        st.subheader("Books by Genre")
        genre_counts = df['Genre'].value_counts()
        fig1, ax1 = plt.subplots()
        ax1.pie(genre_counts, labels=genre_counts.index, autopct='%1.1f%%', startangle=90)
        st.pyplot(fig1)
        
        st.subheader("Books by Status")
        status_counts = df['Status'].value_counts()
        fig2, ax2 = plt.subplots()
        ax2.bar(status_counts.index, status_counts.values, color=['blue','green','orange'])
        st.pyplot(fig2)
    else:
        st.info("No books found. Add some!")
    
    if st.button("Back"):
        st.session_state.page = "menu"
        st.rerun()

# -------------------- Main --------------------
def main():
    st.set_page_config(page_title="Library Manager", page_icon="📚", layout="wide")
    if 'page' not in st.session_state:
        st.session_state.page = "home"
    if 'userid' not in st.session_state:
        st.session_state.userid = None
    if 'username' not in st.session_state:
        st.session_state.username = None
    
    if st.session_state.page == "home":
        home_page()
    elif st.session_state.page == "register":
        register_page()
    elif st.session_state.page == "login":
        login_page()
    elif st.session_state.page == "menu":
        menu_page()
    elif st.session_state.page == "add_book":
        add_book_page()
    elif st.session_state.page == "view_books":
        view_books_page()

if __name__ == "__main__":
    main()
