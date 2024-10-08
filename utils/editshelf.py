import streamlit as st
import shelve
import os
import pandas as pd
from rich.console import Console

def open_shelve_db(file_path):
    """Open a shelve database, removing the .db extension if necessary."""
    if file_path.endswith('.db'):
        file_path = file_path[:-3]
    return shelve.open(file_path)

def display_shelve_contents(shelf):
    """Display and edit shelve contents, excluding 'history' key."""
    data = {"Key": [], "Value": []}
    for key in list(shelf.keys()):
        if key == 'history':
            continue
        value = shelf[key]
        data["Key"].append(key)
        data["Value"].append(value)
    
    # Display the contents as a table
    df = pd.DataFrame(data)
    st.dataframe(df)

def add_new_entry_to_shelve(shelf):
    """Add a new key-value pair to the shelve."""
    with st.expander("Add New Entry"):
        new_key = st.text_input("New Key")
        new_value = st.text_area("New Value")
        if st.button("Add to Shelve"):
            if new_key and new_value:
                shelf[new_key] = new_value
                st.success(f"Added {new_key} to the shelve.")
            else:
                st.error("Both key and value are required.")

def view_history(shelf):
    """View a range of the history key."""
    if 'history' not in shelf:
        st.error("No history found in the shelve database.")
        return
    history = shelf['history']
    start_index = st.number_input("Start Index", min_value=0, max_value=len(history)-1, value=0)
    end_index = st.number_input("End Index", min_value=start_index+1, max_value=len(history), value=min(start_index+10, len(history)))

    if st.button("View History"):
        for i in range(start_index, end_index):
            st.write(f"History Item {i}:")
            st.text(history[i].parts[0].text)

# Streamlit app layout
st.title("Shelve Database Editor")

uploaded_file = st.file_uploader("Choose a shelve .db file", type="db")

if uploaded_file is not None:
    # Save the uploaded file temporarily
    temp_file_path = f"./temp_{uploaded_file.name}"
    with open(temp_file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # Open the shelve database
    with open_shelve_db(temp_file_path) as shelf:
        st.write("Opened shelve database successfully.")

        # Display and edit shelve contents
        display_shelve_contents(shelf)
        
        # Option to add a new entry
        add_new_entry_to_shelve(shelf)

        # Option to view a range of history
        with st.expander("History View"):
            view_history(shelf)

    # Remove temporary file after closing shelve
    os.remove(temp_file_path)
