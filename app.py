import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager
import html
import requests
from datetime import datetime
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
    token = cookies.get("access_token")

    if token:
        # Verify token by calling profile endpoint
        try:
            res = requests.get(
                f"{BASE_URL}/auth/user-profile",
                headers={"Authorization": f"Bearer {token}"}
            )

            if res.status_code == 200:
                st.session_state.access_token = token
            else:
                st.session_state.access_token = None
                cookies["access_token"] = ""
                cookies.save()

        except:
            st.session_state.access_token = None
    else:
        st.session_state.access_token = None

if "selected_goal" not in st.session_state:
    st.session_state.selected_goal = None
if "insight_data" not in st.session_state:
    st.session_state.insight_data = None


def headers():
    return {"Authorization": f"Bearer {st.session_state.access_token}"}


# ---------------- AUTH ----------------
def auth_page():

    # Reduce top spacing
    st.markdown(
    """
    <style>
        /* Control overall container spacing */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 500px;
        }

        /* Reduce space below main title */
        h1 {
            margin-bottom: 0.4rem !important;
        }

        /* Reduce space around horizontal line */
        hr {
            margin-top: 0.2rem !important;
            margin-bottom: 1rem !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)

    st.title("TaskinGo AI")
    st.markdown("---")

    tab1, tab2 = st.tabs(["Login", "Register"])

    # ---------------- LOGIN ----------------
    with tab1:

        login_username = st.text_input("Username", key="login_username")
        login_password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login", use_container_width=True):
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

        reg_username = st.text_input("Username", key="reg_username")
        reg_email = st.text_input("Email", key="reg_email")
        reg_password = st.text_input("Password", type="password", key="reg_password")

        if st.button("Register", use_container_width=True):
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

@st.dialog("Update Goal", width="medium")
def edit_goal_dialog():
    goal = st.session_state.get("goal_to_edit")
    existing_deadline = goal.get("deadline")

    if existing_deadline:
        try:
            existing_deadline = datetime.fromisoformat(existing_deadline).date()
        except:
            existing_deadline = None
    else:
        existing_deadline = None

    updated_title = st.text_input(
        "Title",
        value=goal.get("title", "")
    )

    updated_description = st.text_area(
        "Description",
        value=goal.get("description", "")
    )

    updated_category = st.text_input(
        "Category",
        value=goal.get("category","")
    )

    priority_options = ["High", "Medium", "Low"]

    current_priority = goal.get("priority")

    if current_priority in priority_options:
        default_index = priority_options.index(current_priority)
    else:
        default_index = 1  # fallback to Medium

    updated_priority = st.selectbox(
        "Priority",
        priority_options,
        index=default_index
    )

    updated_deadline = st.date_input(
        "Deadline",
        value=existing_deadline
    )
    
    col1, col2 = st.columns(2)
    if col1.button("Save Changes", use_container_width=True):
        deadline_str = updated_deadline.isoformat() if updated_deadline else None

        res = requests.put(
            f"{BASE_URL}/goal/update-goal",
            json={
                "goal_id": goal["goal_id"],
                "title": updated_title,
                "description": updated_description,
                "category": updated_category,
                "priority": updated_priority,
                "deadline": deadline_str
            },
            headers=headers(),
        )

        if res.status_code == 200:
            st.success("Goal updated successfully")
        else:
            st.error("Update failed")

        st.session_state.goal_to_edit = None
        st.rerun()

    if col2.button("Cancel", use_container_width=True):
        st.session_state.goal_to_edit = None
        st.rerun()
def fetch_user_profile():
    try:
        res = requests.get(
            f"{BASE_URL}/auth/user-profile",
            headers=headers(),
        )
        if res.status_code == 200:
            return res.json()
        return None
    except:
        return None

def create_goal_section():
    st.header("Create New Goal")

    title = st.text_input("Goal Title", key="goal_title")
    description = st.text_area("Goal Description", key="goal_desc")
    category = st.text_input("Goal Category", key="goal_cat")
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
                "category": category,
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
    profile = fetch_user_profile()

    if profile:
        if st.sidebar.button(f"Hi {profile['username']}", use_container_width=True):
            st.session_state.open_profile_dialog = True

    st.sidebar.markdown("---")

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

            # COMPLETE
            if st.sidebar.button("Complete", key=f"goal_complete_{goal_id}"):
                requests.patch(
                    f"{BASE_URL}/goal/{goal_id}/complete-goal",
                    headers=headers(),
                )
                st.sidebar.success("Goal marked complete")
                st.session_state.goal_menu_open = None
                st.rerun()

            # INCOMPLETE
            if st.sidebar.button("Incomplete", key=f"goal_Incomplete_{goal_id}"):
                requests.patch(
                    f"{BASE_URL}/goal/{goal_id}/uncomplete-goal",
                    headers=headers(),
                )
                st.sidebar.success("Goal marked incomplete")
                st.session_state.goal_menu_open = None
                st.rerun()

            # EDIT
            if st.sidebar.button("Update", key=f"goal_edit_{goal_id}"):
                st.session_state.goal_to_edit = goal
                st.session_state.open_goal_dialog = True
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

    if st.sidebar.button("Logout"):
        cookies["access_token"] = ""
        cookies.save()

        st.session_state.access_token = None
        st.session_state.selected_goal = None
        st.session_state.insight_data = None

        st.rerun()

    # ---------------- PROFILE DIALOG ----------------
    if st.session_state.get("open_profile_dialog", False):

        # Reset trigger immediately to prevent reopen
        st.session_state.open_profile_dialog = False

        @st.dialog("User Profile", width="medium")
        def profile_dialog():

            st.markdown("### Account Information")
            st.markdown("---")

            st.write("**User ID:**", profile["user_id"])
            st.write("**Username:**", profile["username"])
            st.write("**Email:**", profile["email"])

            st.markdown("---")
            st.markdown("### Goals Overview")

            st.write("**Total Goals:**", profile["total_goals"])
            st.write("**Completed Goals:**", profile["completed_goals"])
            st.write("**Pending Goals:**", profile["pending_goals"])

            st.markdown("---")
            st.markdown("### Tasks Overview")

            st.write("**Completed Tasks:**", profile["completed_tasks"])
            st.write("**Pending Tasks:**", profile["pending_tasks"])

            if st.button("Close", use_container_width=True):
                st.rerun()

        profile_dialog()

    # ---------------- UPDATE GOAL DIALOG ----------------
    if st.session_state.get("open_goal_dialog", False):

        goal = st.session_state.get("goal_to_edit")

        # reset flag immediately
        st.session_state.open_goal_dialog = False
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
                st.session_state.open_ai_task_dialog = True
                st.rerun()
            else:
                st.error("Failed to generate tasks")

    # ---------------- AI TASK DIALOG ----------------
    if st.session_state.get("open_ai_task_dialog", False):

        ai_data = st.session_state.get("generated_tasks", {})

        # Reset trigger immediately
        st.session_state.open_ai_task_dialog = False

        @st.dialog("AI Suggested Tasks", width="medium")
        def ai_task_dialog():

            st.markdown("### AI Analysis")
            st.info(ai_data.get("message", ""))

            tasks_list = ai_data.get("tasks", [])

            if not tasks_list:
                st.success("Goal Achieved. No additional tasks required.")
                if st.button("Close", use_container_width=True):
                    st.session_state.generated_tasks = None
                    st.rerun()
                return

            st.markdown("---")
            st.markdown("### Select Tasks to Add")

            selected_tasks = []

            for i, task in enumerate(tasks_list):

                st.markdown(
                    f"""
                    <div style="
                        padding:12px;
                        border-radius:8px;
                        background-color:#1f2937;
                        margin-bottom:8px;
                        border:1px solid #374151;
                    ">
                        <b>Task {i+1}</b><br>
                        {task}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                if st.checkbox("Select", key=f"ai_select_{i}"):
                    selected_tasks.append(task)

            st.markdown("---")

            col_add, col_cancel = st.columns(2)

            if col_add.button("Add Selected Tasks", use_container_width=True):

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

                st.success("Tasks added successfully!")
                st.session_state.generated_tasks = None
                st.rerun()

            if col_cancel.button("Cancel", use_container_width=True):
                st.session_state.generated_tasks = None
                st.rerun()

        ai_task_dialog()

    # ---------------- EXISTING TASKS ----------------
    st.subheader("Your Current Tasks")

    res = requests.get(
        f"{BASE_URL}/task/{goal_id}/get-tasks",
        headers=headers(),
    )

    tasks = res.json().get("tasks", []) if res.status_code == 200 else []

    for task in tasks:
        task_id = task["task_id"]

        is_completed = task.get("is_completed", False)

        # ---------- HEADER ROW ----------
        col1, col2 = st.columns([8, 1])  # Expander wide, checkbox small

        with col1:
            expander = st.expander(task["title"])

        with col2:
            checkbox_value = st.checkbox(
                label=f"Mark task {task_id} as complete",
                key=f"task_checkbox_{task_id}",
                value=is_completed,
                label_visibility="collapsed"
            )

        # ---------- HANDLE CHECKBOX ----------
        if checkbox_value != is_completed:
            if checkbox_value:
                requests.patch(
                    f"{BASE_URL}/task/{goal_id}/{task_id}/complete-task",
                    headers=headers(),
                )
            else:
                requests.patch(
                    f"{BASE_URL}/task/{goal_id}/{task_id}/uncomplete-task",
                    headers=headers(),
                )
            st.rerun()

        # ---------- EXPANDER CONTENT ----------
        with expander:
            st.write("**Description:**", task.get("description", "N/A"))
            st.write("**Priority:**", task.get("priority", "N/A"))

            col_edit, col_delete = st.columns(2)

            if col_edit.button("Edit", key=f"edit_toggle_{task_id}", use_container_width=True):
                st.session_state[f"editing_{task_id}"] = True

            if col_delete.button("Delete", key=f"delete_{task_id}", use_container_width=True):
                requests.delete(
                    f"{BASE_URL}/task/{goal_id}/{task_id}/delete-task",
                    headers=headers(),
                )
                st.rerun()

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

    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks if t.get("is_completed", False))

    if total_tasks > 0:
        st.markdown("### Goal Progress")

        progress_ratio = completed_tasks / total_tasks
        progress_percent = int(progress_ratio * 100)

        # Styled progress bar
        st.markdown(
            f"""
            <div style="
                background-color:#1f2937;
                border-radius:12px;
                height:22px;
                width:100%;
                overflow:hidden;
                margin-top:10px;
                border:1px solid #374151;
            ">
                <div style="
                    width:{progress_percent}%;
                    background-color:#22c55e;
                    height:100%;
                    transition: width 0.3s ease-in-out;
                "></div>
            </div>
            <div style="
                text-align:right;
                margin-top:6px;
                font-weight:500;
            ">
                {completed_tasks} / {total_tasks} Completed
            </div>
            """,
            unsafe_allow_html=True
        )

    else:
        st.info("No tasks yet. Add tasks to start tracking progress.")

    st.markdown("---")

    # ---------------- CREATE TASK FLOAT BUTTON ----------------

    col_left, col_right = st.columns([5, 1])

    with col_right:
        if st.button("New Task", use_container_width=True):
            st.session_state.open_task_dialog = True



    # ---------------- TASK CREATION FORM ----------------
    if "open_task_dialog" in st.session_state and st.session_state.open_task_dialog:

        st.session_state.open_task_dialog = False

        @st.dialog("Create New Task", width="medium")
        def create_task_dialog():

            new_title = st.text_input("Task Title")
            new_desc = st.text_area("Task Description")
            new_priority = st.selectbox(
                "Priority",
                ["High", "Medium", "Low"]
            )

            col_save, col_cancel = st.columns(2)

            if col_save.button("Create Task", use_container_width=True):

                if not new_title.strip():
                    st.warning("Task title is required.")
                    return

                res = requests.post(
                    f"{BASE_URL}/task/create-task",
                    json={
                        "goal_id": goal_id,
                        "title": new_title,
                        "description": new_desc,
                        "priority": new_priority,
                    },
                    headers=headers(),
                )

                if res.status_code == 200:
                    st.success("Task created successfully!")
                    st.rerun()

                else:
                    st.error("Failed to create task")


            if col_cancel.button("Cancel", use_container_width=True):
                st.session_state.open_task_dialog = False
                st.rerun()

        create_task_dialog()

# ---------------- INSIGHTS ----------------
def insight_section(goal_id):
    st.header("AI Insights")
    st.markdown("""
            <style>
            /* Metric label (heading) */
            [data-testid="stMetricLabel"] {
                font-size: 18px !important;
                font-weight: 600 !important;
            }

            /* Metric value */
            [data-testid="stMetricValue"] {
                font-size: 28px !important;
            }
            </style>
            """, unsafe_allow_html=True)

    if st.button("Generate Insights", use_container_width=True):
        with st.spinner("Analyzing goal performance..."):
            res = requests.post(
                f"{BASE_URL}/insight/analyze-goal",
                json={"goal_id": goal_id},
                headers=headers(),
            )
            if res.status_code == 200:
                st.session_state.insight_data = res.json()

    if "insight_data" in st.session_state and st.session_state.insight_data:

        insight = st.session_state.insight_data

        st.markdown("---")

        # ---------------- SCORE CARDS ----------------
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Completion Score", f"{insight['completion_score']}%")

        with col2:
            st.metric("Priority", insight["priority"])

        with col3:
            days = insight.get("days_remaining")
            st.metric("Days Remaining", days if days else "No Deadline")

        # ---------------- STRATEGY ----------------
        st.subheader("Execution Strategy")

        st.info(insight["strategy_plan"]["execution_strategy"])

        # ---------------- INSIGHTS ----------------
        st.subheader("Performance Insights")

        insights_data = insight.get("insights", {})

        st.success(insights_data.get("appreciation", ""))

        st.warning(insights_data.get("focus_area", ""))

        tips = insights_data.get("improvement_tip", [])
        if tips:
            st.markdown("### Improvement Tips")
            for tip in tips:
                st.markdown(f"- {tip}")

        suggestions = insights_data.get("task_suggestions", [])
        if suggestions:
            st.markdown("### AI Suggested New Tasks")
            for suggestion in suggestions:
                st.markdown(f"• {suggestion}")

        # ---------------- IRRELEVANT TASKS ----------------
        irrelevant = insight.get("irrelevant_tasks", [])

        if irrelevant:
            st.subheader("Irrelevant Tasks Detected")

            for task in irrelevant:
                with st.expander(task["title"]):
                    st.write("Reason:", task["reason"])

        # ---------------- OBSERVATIONS ----------------
        obs = insight.get("observations", {})

        st.subheader("Overall Observations")

        st.markdown(f"**Progress Status:** {obs.get('progress_status')}")
        st.markdown(f"**Risk Level:** {obs.get('risk_level')}")
        st.markdown(f"**Task Alignment:** {obs.get('task_alignment')}")
        st.markdown(f"**Deadline Status:** {obs.get('deadline_status')}")

    st.markdown("---")
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
    if notes:

        # 3 cards per row
        cols = st.columns(3)

        for index, note in enumerate(notes):

            with cols[index % 3]:

                st.markdown(
                    f"""
                    <div style="
                        background-color:#1f2937;
                        padding:18px;
                        border-radius:12px;
                        border:1px solid #374151;
                        margin-bottom:15px;
                        cursor:pointer;
                        transition:0.2s ease-in-out;
                    ">
                        <div style="font-size:16px;font-weight:600;">
                            {note['title']}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                if st.button("Open", key=f"note_open_{note['_id']}", use_container_width=True):
                    st.session_state.editing_note = note
                    st.rerun()

    else:
        st.info("No notes yet. Create your first note")

    st.markdown("---")

    # ---------------- NEW NOTE TOGGLE ----------------
    col_left, col_right = st.columns([5, 1])

    with col_right:
        if st.button("New Note", use_container_width=True):
            st.session_state.open_note_dialog = True

    # ---------------- CREATE NOTE DIALOG ----------------
    if st.session_state.get("open_note_dialog", False):

        # Reset trigger immediately (prevents reopen)
        st.session_state.open_note_dialog = False

        @st.dialog("Create New Note", width="medium")
        def create_note_dialog():

            new_title = st.text_input("Note Title")
            new_content = st.text_area(
                "Write your thoughts here...",
                height=250
            )

            col1, col2 = st.columns(2)

            if col1.button("Save Note", use_container_width=True):

                if not new_title.strip():
                    st.warning("Title is required")
                    return

                res = requests.post(
                    f"{BASE_URL}/notes/create-note",
                    json={
                        "goal_id": goal_id,
                        "title": new_title,
                        "content": new_content,
                    },
                    headers=headers(),
                )

                if res.status_code == 200:
                    st.success("Note created successfully!")
                    st.rerun()
                else:
                    st.error("Failed to create note")

            if col2.button("Cancel", use_container_width=True):
                st.rerun()

        create_note_dialog()

    # ---------------- EDIT NOTE DIALOG ----------------
    if "editing_note" in st.session_state and st.session_state.editing_note:

        note = st.session_state.editing_note
        original_content = note.get("content", "")
        fixed_content = original_content.replace("\\n", "\n")

        @st.dialog("Edit Note", width="medium")
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
                value=fixed_content,
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

            if col2.button("Delete", key=f"delete_btn_{note['_id']}", use_container_width=True):
                requests.delete(
                    f"{BASE_URL}/notes/{goal_id}/{note['_id']}/delete-note",
                    headers=headers(),
                )
                st.success("Note deleted successfully!")
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
        create_goal_section()