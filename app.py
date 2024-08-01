import streamlit as st
from PyPDF2 import PdfReader
import re
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import os

# Global variable to store the concatenated text
global_text = ""

def extract_and_concatenate_text(pdf_file):
    # Create a PDF reader object from the uploaded file
    reader = PdfReader(pdf_file)

    # Initialize a list to store all extracted text
    all_text = []

    # Iterate through all pages and extract text
    for page in reader.pages:
        text = page.extract_text()
        if text:
            # Split the text into words and concatenate with a space
            words = text.split()
            concatenated_text = ' '.join(words)
            all_text.append(concatenated_text)

    # Join text from all pages
    return '\n'.join(all_text)

# Allow only PDF files to be uploaded
uploaded_files = st.file_uploader("Choose a PDF file", accept_multiple_files=True, type=["pdf"])

# Loop through the uploaded files
for uploaded_file in uploaded_files:
    # Extract and concatenate text from the PDF file
    text = extract_and_concatenate_text(uploaded_file)
    
    # Update the global variable
    global_text = text

    # Display the filename and extracted text
    st.write("Filename:", uploaded_file.name)
    st.write(text)

def enumerate_words(text):
    words = text.split()
    enumerated_dict = {i + 1: word for i, word in enumerate(words)}
    return enumerated_dict

def find_phone_numbers(enumerated_dict):
    phone_number_index = []
    phone_number_pattern = re.compile(r'^(\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}$')  # Adjust the regex pattern as needed

    for key, value in enumerated_dict.items():
        if phone_number_pattern.search(value):
            phone_number_index.append(key)

    return phone_number_index

def find_emails(enumerated_dict):
    email_index = []
    email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')

    for key, value in enumerated_dict.items():
        if email_pattern.search(value):
            email_index.append(key)

    return email_index

def find_number_sequences(enumerated_dict):
    number_index = []
    
    # Patterns to match the sequences
    sequence_pattern = re.compile(r'\b\d{4} \d{4} \d{4}\b')  # For sequences like 6744 7057 2494
    phone_pattern = re.compile(r'\b\d{10}\b')                # For phone numbers like 8626931738
    
    for key, value in enumerated_dict.items():
        if sequence_pattern.search(value) or phone_pattern.search(value):
            number_index.append(key)
    
    return number_index

def redact_words_with_numbers(enumerated_dict):
    # Pattern to match words containing any digits
    number_pattern = re.compile(r'\d')
    
    # List to hold the indices of words containing numbers
    redacted_indices = []
    
    for key, value in enumerated_dict.items():
        if number_pattern.search(value):
            redacted_indices.append(key)
    
    return redacted_indices


def redacted(text, indices):
    words = text.split()
    for index in indices:
        words[index - 1] = "[REDACTED]"
    return ' '.join(words)

# Use the global variable text for further processing
input_text = global_text
enumerated = enumerate_words(input_text)
phone_numbers = find_phone_numbers(enumerated)
found_sequences = find_number_sequences(enumerated)
words_and_numbers=redact_words_with_numbers(enumerated)
emails = find_emails(enumerated)
redacted_text = redacted(input_text, phone_numbers + emails +found_sequences + words_and_numbers)

pdf_dir = "pdf_files"
os.makedirs(pdf_dir, exist_ok=True)
file_name = os.path.join(pdf_dir, "output.pdf")

def create_pdf(text_to_insert, file_name):
    doc = SimpleDocTemplate(file_name, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Create a Paragraph object and add it to the story
    story.append(Paragraph(text_to_insert, styles["Normal"]))

    # Build the PDF
    doc.build(story)

# The string to be inserted into the PDF
text_to_insert = redacted_text

# Streamlit app
st.title("sensitive information has been redacted")

# Automatically create the PDF when the page loads
if global_text:
    create_pdf(text_to_insert, file_name)
    st.success("PDF created successfully!")

    with open(file_name, "rb") as f:
        st.download_button(
            label="Download PDF",
            data=f,
            file_name="output.pdf",
            mime="application/pdf"
        )
