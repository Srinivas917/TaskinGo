import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager
import requests
from src.constants.properties import COOKIE_SECRET_KEY

BASE_URL = "http://localhost:9000"

st.set_page_config(page_title="TaskinGo AI", layout="wide")

cookies = EncryptedCookieManager(
    prefix="taskingo_",
    password=COOKIE_SECRET_KEY
)

if not cookies.ready():
    st.stop()

# ---------------- SESSION ----------------
if "access_token" not in st.session_state:
    st.session_state.access_token = cookies.get("access_token")
if "selected_goal" not in st.session_state:
    st.session_state.selected_goal = None
if "insight_data" not in st.session_state:
    st.session_state.insight_data = None


def headers():
    return {"Authorization": f"Bearer {st.session_state.access_token}"}


# ---------------- AUTH ----------------
def auth_page():
    st.title("TaskinGo AI")

    tab1, tab2 = st.tabs(["Login", "Register"])

    # ---------------- LOGIN ----------------
    with tab1:
        st.subheader("Login to your account")

        login_username = st.text_input("Username", key="login_username")
        login_password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login", key="login_btn"):
            if not login_username or not login_password:
                st.warning("Please enter both username and password.")
                return

            with st.spinner("Authenticating..."):
                res = requests.post(
                    f"{BASE_URL}/auth/login",
                    json={
                        "username": login_username,
                        "password": login_password
                    },
                )

            if res.status_code == 200:
                token = res.json()["access_token"]
                st.session_state.access_token = token
                cookies["access_token"] = token
                cookies.save()
                st.rerun()
            else:
                st.error(res.json().get("detail", "Invalid credentials"))

    # ---------------- REGISTER ----------------
    with tab2:
        st.subheader("Create a new account")

        reg_username = st.text_input("Username", key="reg_username")
        reg_email = st.text_input("Email", key="reg_email")
        reg_password = st.text_input("Password", type="password", key="reg_password")

        if st.button("Register", key="register_btn"):
            if not reg_username or not reg_email or not reg_password:
                st.warning("All fields are required.")
                return

            with st.spinner("Creating account..."):
                res = requests.post(
                    f"{BASE_URL}/auth/register",
                    json={
                        "username": reg_username,
                        "email": reg_email,
                        "password": reg_password,
                    },
                )

            if res.status_code == 200:
                st.success("Account created successfully. You can now login.")

            else:
                st.error(res.json().get("detail", "Registration failed"))

def create_goal_section():
    st.header("Create New Goal")

    title = st.text_input("Goal Title", key="goal_title")
    description = st.text_area("Goal Description", key="goal_desc")

    priority = st.selectbox(
        "Priority",
        ["High", "Medium", "Low"],
        key="goal_priority"
    )

    deadline = st.date_input("Deadline", key="goal_deadline")
    deadline_str = deadline.isoformat() if deadline else None

    if st.button("Create Goal"):
        if not title.strip():
            st.warning("Goal title cannot be empty")
            return

        res = requests.post(
            f"{BASE_URL}/goal/create-goal",
            json={
                "title": title,
                "description": description,
                "priority": priority,
                "deadline": deadline_str,
            },
            headers=headers(),
        )

        if res.status_code == 200:
            st.success("Goal created successfully")
            st.session_state.selected_goal = None
            st.rerun()
        else:
            st.error("Failed to create goal")
# ---------------- SIDEBAR ----------------
def sidebar():

    st.sidebar.title("Your Goals")
    if st.sidebar.button("Create New Goal"):
        st.session_state.selected_goal = None
        st.session_state.editing_goal = None
        st.rerun()

    # Fetch goals
    res = requests.get(f"{BASE_URL}/goal/get-goals", headers=headers())
    goals = res.json().get("goals", []) if res.status_code == 200 else []

    if "goal_menu_open" not in st.session_state:
        st.session_state.goal_menu_open = None

    if "editing_goal" not in st.session_state:
        st.session_state.editing_goal = None

    for goal in goals:

        goal_id = goal["goal_id"]

        col1, col2 = st.sidebar.columns([6, 2])

        # Goal Select Button
        if col1.button(goal["title"], key=f"goal_select_{goal_id}"):
            st.session_state.selected_goal = goal_id
            st.session_state.insight_data = None
            st.rerun()

        # 3 DOT BUTTON
        if col2.button("...", key=f"goal_menu_btn_{goal_id}"):
            if st.session_state.goal_menu_open == goal_id:
                st.session_state.goal_menu_open = None
            else:
                st.session_state.goal_menu_open = goal_id
            st.rerun()

        # ---------------- ACTION MENU ----------------
        if st.session_state.goal_menu_open == goal_id:

            st.sidebar.markdown("—")

            # COMPLETE
            if st.sidebar.button("Complete", key=f"goal_complete_{goal_id}"):
                requests.patch(
                    f"{BASE_URL}/goal/{goal_id}/complete-goal",
                    headers=headers(),
                )
                st.sidebar.success("Goal marked complete")
                st.session_state.goal_menu_open = None
                st.rerun()

            # UNCOMPLETE
            if st.sidebar.button("Uncomplete", key=f"goal_uncomplete_{goal_id}"):
                requests.patch(
                    f"{BASE_URL}/goal/{goal_id}/uncomplete-goal",
                    headers=headers(),
                )
                st.sidebar.success("Goal marked incomplete")
                st.session_state.goal_menu_open = None
                st.rerun()

            # EDIT
            if st.sidebar.button("Update", key=f"goal_edit_{goal_id}"):
                st.session_state.editing_goal = goal
                st.session_state.goal_menu_open = None
                st.rerun()

            # DELETE
            if st.sidebar.button("Delete", key=f"goal_delete_{goal_id}"):
                requests.delete(
                    f"{BASE_URL}/goal/{goal_id}/delete-goal",
                    headers=headers(),
                )
                st.sidebar.success("Goal deleted successfully")
                st.session_state.goal_menu_open = None
                st.rerun()


    st.sidebar.markdown("---")

    if st.sidebar.button("Logout"):
        cookies["access_token"] = ""
        cookies.save()
        st.session_state.clear()
        st.rerun()

    # ---------------- UPDATE GOAL DIALOG ----------------
    if st.session_state.editing_goal:

        goal = st.session_state.editing_goal

        @st.dialog("Update Goal", width="medium")
        def edit_goal_dialog():

            updated_title = st.text_input(
                "Title",
                value=goal.get("title", "")
            )

            updated_description = st.text_area(
                "Description",
                value=goal.get("description", "")
            )

            updated_priority = st.selectbox(
                "Priority",
                ["High", "Medium", "Low"],
                index=["High", "Medium", "Low"].index(goal.get("priority", "Medium"))
            )

            col1, col2 = st.columns(2)

            if col1.button("Save Changes", use_container_width=True):
                res = requests.put(
                    f"{BASE_URL}/goal/update-goal",
                    json={
                        "goal_id": goal["goal_id"],
                        "title": updated_title,
                        "description": updated_description,
                        "priority": updated_priority,
                    },
                    headers=headers(),
                )

                if res.status_code == 200:
                    st.success("Goal updated successfully")
                else:
                    st.error("Update failed")

                st.session_state.editing_goal = None
                st.rerun()

        edit_goal_dialog()


# ---------------- TASKS ----------------
def tasks_section(goal_id):
    st.header("Tasks")

    # ---------------- AI GENERATE BUTTON ----------------
    col1, col2 = st.columns([4, 1])

    with col2:
        if st.button("Generate Tasks", use_container_width=True):
            with st.spinner("AI is analyzing your goal and progress..."):
                res = requests.post(
                    f"{BASE_URL}/task/generate-tasks",
                    json={"goal_id": goal_id},
                    headers=headers(),
                )

            if res.status_code == 200:
                st.session_state.generated_tasks = res.json()
            else:
                st.error("Failed to generate tasks")

    # ---------------- AI SUGGESTED TASKS DISPLAY ----------------
    if "generated_tasks" in st.session_state and st.session_state.generated_tasks:

        gen = st.session_state.generated_tasks

        st.markdown("---")
        st.subheader("AI Suggested Tasks")

        st.info(gen.get("message", ""))

        tasks_list = gen.get("tasks", [])

        if tasks_list:
            selected_tasks = []

            for i, task in enumerate(tasks_list):
                with st.container():
                    st.markdown(
                        f"""
                        <div style="
                            padding:15px;
                            border-radius:10px;
                            background-color:#1f2937;
                            margin-bottom:10px;
                            border:1px solid #374151;
                        ">
                            <b>Task {i+1}</b><br>
                            {task}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    if st.checkbox("Select", key=f"select_ai_{i}"):
                        selected_tasks.append(task)

            if selected_tasks:
                if st.button("Add Selected Tasks to Goal"):
                    for task in selected_tasks:
                        requests.post(
                            f"{BASE_URL}/task/create-task",
                            json={
                                "goal_id": goal_id,
                                "title": task,
                                "description": "",
                                "priority": "Medium",
                            },
                            headers=headers(),
                        )

                    st.success("Selected tasks added successfully!")
                    st.session_state.generated_tasks = None
                    st.rerun()

        else:
            st.success("Goal Achieved. No additional tasks required.")

        st.markdown("---")

    # ---------------- EXISTING TASKS ----------------
    st.subheader("Your Current Tasks")

    res = requests.get(
        f"{BASE_URL}/task/{goal_id}/get-tasks",
        headers=headers(),
    )

    tasks = res.json().get("tasks", []) if res.status_code == 200 else []

    for task in tasks:
        task_id = task["task_id"]

        with st.expander(task["title"]):

            st.write("**Description:**", task.get("description", "N/A"))
            st.write("**Priority:**", task.get("priority", "N/A"))

            action_col1, action_col2, action_col3, action_col4 = st.columns(4)

            # COMPLETE
            if action_col1.button("Complete", key=f"complete_{task_id}"):
                requests.patch(
                    f"{BASE_URL}/task/{goal_id}/{task_id}/complete-task",
                    headers=headers(),
                )
                st.success("Task marked complete")
                st.rerun()

            # UNCOMPLETE
            if action_col2.button("Uncomplete", key=f"uncomplete_{task_id}"):
                requests.patch(
                    f"{BASE_URL}/task/{goal_id}/{task_id}/uncomplete-task",
                    headers=headers(),
                )
                st.success("Task marked incomplete")
                st.rerun()

            # DELETE
            if action_col3.button("Delete", key=f"delete_{task_id}"):
                requests.delete(
                    f"{BASE_URL}/task/{goal_id}/{task_id}/delete-task",
                    headers=headers(),
                )
                st.success("Task deleted successfully")
                st.rerun()

            # EDIT TOGGLE
            if action_col4.button("Edit", key=f"edit_toggle_{task_id}"):
                st.session_state[f"editing_{task_id}"] = True

            # ---------------- EDIT FORM ----------------
            if st.session_state.get(f"editing_{task_id}"):

                st.markdown("### Update Task")

                new_title = st.text_input(
                    "Title",
                    value=task["title"],
                    key=f"edit_title_{task_id}",
                )

                new_desc = st.text_area(
                    "Description",
                    value=task.get("description", ""),
                    key=f"edit_desc_{task_id}",
                )

                new_priority = st.selectbox(
                    "Priority",
                    ["High", "Medium", "Low"],
                    index=["High", "Medium", "Low"].index(task.get("priority", "Medium")),
                    key=f"edit_priority_{task_id}",
                )

                save_col, cancel_col = st.columns(2)

                if save_col.button("Save Changes", key=f"save_{task_id}"):
                    requests.put(
                        f"{BASE_URL}/task/update-task",
                        json={
                            "id": task_id,
                            "goal_id": goal_id,
                            "title": new_title,
                            "description": new_desc,
                            "priority": new_priority,
                        },
                        headers=headers(),
                    )

                    st.session_state[f"editing_{task_id}"] = False
                    st.success("Task updated successfully!")
                    st.rerun()

                if cancel_col.button("Cancel", key=f"cancel_{task_id}"):
                    st.session_state[f"editing_{task_id}"] = False
                    st.rerun()

    st.markdown("---")

    # ---------------- CREATE TASK FLOAT BUTTON ----------------

    if "show_task_form" not in st.session_state:
        st.session_state.show_task_form = False

    # Right aligned button
    col_left, col_right = st.columns([5, 1])

    with col_right:
        if st.button("New Task", use_container_width=True):
            st.session_state.show_task_form = not st.session_state.show_task_form


    # ---------------- TASK CREATION FORM ----------------
    if st.session_state.show_task_form:

        st.markdown("---")
        st.subheader("Create New Task")

        new_title = st.text_input("Task Title", key="new_task_title")
        new_desc = st.text_area("Task Description", key="new_task_desc")
        new_priority = st.selectbox(
            "Priority",
            ["High", "Medium", "Low"],
            key="new_task_priority"
        )

        col_save, col_cancel = st.columns(2)

        if col_save.button("Create Task", use_container_width=True):
            if not new_title:
                st.warning("Task title is required.")
            else:
                requests.post(
                    f"{BASE_URL}/task/{goal_id}/create-task",
                    json={
                        "goal_id": goal_id,
                        "title": new_title,
                        "description": new_desc,
                        "priority": new_priority,
                    },
                    headers=headers(),
                )
                st.success("Task created successfully!")
                st.session_state.show_task_form = False
                st.rerun()

        if col_cancel.button("Cancel", use_container_width=True):
            st.session_state.show_task_form = False
            st.rerun()


# ---------------- INSIGHTS ----------------
def insight_section(goal_id):
    st.header("AI Insights")

    if st.button("Generate Insights", use_container_width=True):
        res = requests.post(
            f"{BASE_URL}/insight/analyze-goal",
            json={"goal_id": goal_id},
            headers=headers(),
        )
        if res.status_code == 200:
            st.session_state.insight_data = res.json()

    if "insight_data" in st.session_state and st.session_state.insight_data:

        insight = st.session_state.insight_data
        st.write("RESPONSE:", insight)


# ---------------- NOTES ----------------

def notes_section(goal_id):

    st.header("Notes")

    # ---------------- FETCH NOTES ----------------
    res = requests.get(
        f"{BASE_URL}/notes/{goal_id}/get-notes",
        headers=headers(),
    )
    notes = res.json().get("notes", []) if res.status_code == 200 else []

    # ---------------- NOTE LIST ----------------
    for note in notes:

        if st.button(note["title"], key=f"note_btn_{note['_id']}"):

            @st.dialog("Note", width="medium")
            def view_note_dialog():

                with st.container():
                    st.markdown(f"### {note['title']}")
                    st.markdown("---")

                    st.markdown(
                        f"""
                        <div style="
                            font-size:15px;
                            line-height:1.6;
                            padding:10px 0px;
                            color:#E5E7EB;
                        ">
                            {note.get("content", "")}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    st.markdown("---")

                    col1, col2 = st.columns([1,1])

                    # EDIT
                    if col1.button("Edit", key=f"edit_btn_{note['_id']}", use_container_width=True):
                        st.session_state.editing_note = note
                        st.rerun()

                    # DELETE
                    if col2.button("Delete", key=f"delete_btn_{note['_id']}", use_container_width=True):
                        requests.delete(
                            f"{BASE_URL}/notes/{goal_id}/{note['_id']}/delete-note",
                            headers=headers(),
                        )
                        st.success("Note deleted successfully!")
                        st.rerun()


            view_note_dialog()

    st.markdown("---")

    # ---------------- NEW NOTE TOGGLE ----------------
    if "show_note_form" not in st.session_state:
        st.session_state.show_note_form = False

    col_left, col_right = st.columns([5, 1])

    with col_right:
        if st.button("New Note", use_container_width=True):
            st.session_state.show_note_form = not st.session_state.show_note_form

    # ---------------- CREATE NOTE FORM ----------------
    if st.session_state.show_note_form:

        st.subheader("Create New Note")

        new_title = st.text_input("Note Title", key="new_note_title")
        new_content = st.text_area("Write your thoughts here...", key="new_note_content")

        col1, col2 = st.columns(2)

        if col1.button("Save Note", use_container_width=True):
            if not new_title.strip():
                st.warning("Title is required")
            else:
                requests.post(
                    f"{BASE_URL}/notes/create-note",
                    json={
                        "goal_id": goal_id,
                        "title": new_title,
                        "content": new_content,
                    },
                    headers=headers(),
                )
                st.session_state.show_note_form = False
                st.success("Note created successfully!")
                st.rerun()

        if col2.button("Cancel", use_container_width=True):
            st.session_state.show_note_form = False
            st.rerun()

    # ---------------- EDIT NOTE DIALOG ----------------
    if "editing_note" in st.session_state and st.session_state.editing_note:

        note = st.session_state.editing_note

        @st.dialog("Edit Note", width="large")
        def edit_note_dialog():

            st.markdown("##Edit Note")
            st.markdown("---")

            updated_title = st.text_input(
                "Title",
                value=note.get("title", ""),
                key=f"edit_title_{note['_id']}"
            )

            updated_content = st.text_area(
                "Content",
                value=note.get("content", ""),
                key=f"edit_content_{note['_id']}",
                height=300
            )

            st.markdown("---")
            col1, col2 = st.columns(2)

            if col1.button("Save Changes", use_container_width=True):
                res = requests.put(
                    f"{BASE_URL}/notes/update-note",
                    json={
                        "note_id": note["_id"],
                        "goal_id": goal_id,
                        "title": updated_title,
                        "content": updated_content,
                    },
                    headers=headers(),
                )

                if res.status_code == 200:
                    st.success("Note updated successfully!")
                else:
                    st.error("Update failed")

                st.session_state.editing_note = None
                st.rerun()

            if col2.button("Cancel", use_container_width=True):
                st.session_state.editing_note = None
                st.rerun()

        edit_note_dialog()


# ---------------- MAIN ----------------
if not st.session_state.access_token:
    auth_page()
else:
    sidebar()

    if st.session_state.selected_goal:
        tasks_section(st.session_state.selected_goal)
        insight_section(st.session_state.selected_goal)
        notes_section(st.session_state.selected_goal)
    else:
        st.title("Welcome to Taskingo AI")
        st.write("Select a goal from sidebar to begin.")
        create_goal_section()