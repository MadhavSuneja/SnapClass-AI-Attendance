import streamlit as st
import time

from src.database.db import enroll_student_to_subject
from src.database.config import supabase


@st.dialog("Quick Enrollment")
def auto_enroll_dialog(subject_code):

    if "student_data" not in st.session_state:
        st.warning("Please login first to continue.")
        return

    student_id = st.session_state.student_data["student_id"]

    res = (
        supabase.table("subjects")
        .select("subject_id,name,subject_code")
        .eq("subject_code", subject_code)
        .execute()
    )

    if not res.data:
        st.error("Subject not found.")
        if st.button("Close", key="close_invalid_subject"):
            st.query_params.clear()
            st.rerun()
        return

    subject = res.data[0]

    check = (
        supabase.table("subject_students")
        .select("*")
        .eq("student_id", student_id)
        .eq("subject_id", subject["subject_id"])
        .execute()
    )

    if check.data:
        st.info("You are already enrolled in this subject.")

        if st.button("OK", key="already_enrolled"):
            st.query_params.clear()
            st.rerun()

        return

    st.markdown(
        f"### 📘 Would you like to enroll in **{subject['name']}**?"
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Cancel", key="cancel_auto"):
            st.query_params.clear()
            st.rerun()

    with col2:
        if st.button(
            "Enroll Now",
            type="primary",
            use_container_width=True,
            key="confirm_auto",
        ):
            enroll_student_to_subject(
                student_id,
                subject["subject_id"],
            )

            st.success("Successfully enrolled!")

            st.query_params.clear()

            time.sleep(1)

            st.rerun()