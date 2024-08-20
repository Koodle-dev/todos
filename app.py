import streamlit as st
from supabase import create_client, Client
from datetime import datetime

st.set_page_config(layout='wide', page_title='koodle to-do')

# Supabase setup
url = st.secrets["supabase"]["supabase_url"]
key = st.secrets["supabase"]["supabase_key"]
supabase: Client = create_client(url, key)

# User authentication (sign-up, sign-in, etc.)
def authenticate_user():
    auth_option = st.radio("what you want to do?", ("sign up", "sign in"))

    if auth_option == "sign up":
        st.subheader("create a new account")
        email = st.text_input("email")
        password = st.text_input("password", type="password")
        confirm_password = st.text_input("confirm password", type="password")
        
        if st.button("sign up"):
            if password != confirm_password:
                st.error("passwords do not match...")
            else:
                try:
                    response = supabase.auth.sign_up({
                        "email": email,
                        "password": password
                    })
                    st.session_state.user_id = response.user.id
                    st.session_state.user_email = email
                    st.success("account created successfully...")
                    st.rerun()
                except Exception as e:
                    st.error(f"error creating account: {str(e)}")

    elif auth_option == "sign in":
        st.subheader("log in to your account")
        email = st.text_input("email")
        password = st.text_input("password", type="password")

        if st.button("sign in"):
            try:
                response = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
                st.session_state.user_id = response.user.id  # This id corresponds to auth.users.id
                st.session_state.user_email = email
                st.success("logged in successfully...")
                st.rerun()
            except Exception as e:
                st.error(f"error logging in: {str(e)}")

# Add task
def add_task(user_id, task_name):
    # Convert the date to a string in 'YYYY-MM-DD' format
    task_date = datetime.now().date().strftime('%Y-%m-%d')
    
    supabase.table("tasks").insert({
        "user_id": user_id,
        "task_name": task_name,
        "completed": False,
        "date": task_date  # Use the string format for the date
    }).execute()

# Complete task
def complete_task(task_id):
    # Update the task as completed
    supabase.table("tasks").update({"completed": True}).eq("task_id", task_id).execute()
    
    # Get the user ID associated with the task
    task = supabase.table("tasks").select("user_id").eq("task_id", task_id).execute()
    if task.data:
        user_id = task.data[0]['user_id']
        today = datetime.now().date().strftime('%Y-%m-%d')
        
        # Check if the task was already completed (to prevent duplicate points addition)
        completed_task = supabase.table("tasks").select("completed").eq("task_id", task_id).execute()
        if completed_task.data and not completed_task.data[0]['completed']:
            # Add points only if the task was not previously completed
            # Check if points entry already exists for today
            points_entry = supabase.table("points").select("points").eq("user_id", user_id).eq("date", today).execute()
            if points_entry.data:
                # Update the existing points entry
                current_points = points_entry.data[0]['points']
                new_points = current_points + 10
                supabase.table("points").update({"points": new_points}).eq("user_id", user_id).eq("date", today).execute()
            else:
                # Insert a new points entry
                supabase.table("points").insert({
                    "user_id": user_id,
                    "date": today,
                    "points": 10
                }).execute()



# Calculate points
def calculate_points(user_id):
    tasks = supabase.table("tasks").select("*").eq("user_id", user_id).eq("date", datetime.now().date()).execute()
    completed_tasks = [task for task in tasks.data if task["completed"]]
    return len(completed_tasks) * 10

# Reset tasks and points daily
def reset_tasks_and_points():
    # Logic to reset tasks and points daily
    pass

# Streamlit UI
def app():
    st.title("koodle to-do")
    
    if 'user_id' not in st.session_state:
        authenticate_user()
    else:
        st.write(f"welcome, {st.session_state['user_email']}!")

        # Calculate and display points
        points = calculate_points(st.session_state['user_id'])
        st.write(f"you have currently got {points} points")

        # Add new task
        with st.form("task_form"):
            task_name = st.text_input("New Task")
            submit_task = st.form_submit_button("Add Task")
            if submit_task and task_name:
                add_task(st.session_state['user_id'], task_name)
        
        # Display tasks and points
        tasks = supabase.table("tasks").select("*").eq("user_id", st.session_state['user_id']).eq("date", datetime.now().date().strftime('%Y-%m-%d')).execute()
        if tasks.data:
            for task in tasks.data:
                # Use the task_id as the unique key for each checkbox
                checkbox_key = f"checkbox_{task['task_id']}"
                if st.checkbox(task["task_name"], value=task["completed"], key=checkbox_key):
                    complete_task(task["task_id"])
        
        # Log out
        if st.button("log out"):
            st.session_state.clear()
            st.rerun()

if __name__ == "__main__":
    app()
