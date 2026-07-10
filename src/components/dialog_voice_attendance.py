import streamlit as st
import pandas as pd
from datetime import datetime
from src.pipelines.voice_pipeline import process_bulk_audio
from src.database.config import supabase
from src.components.dialog_attendance_results import show_attendance_result


@st.dialog("Voice Attendance")
def voice_attendance_dialog(selected_subject_id):

    # Initialize once
    if "voice_attendance_results" not in st.session_state:
        st.session_state.voice_attendance_results = None

    st.write(
        "Record classroom audio of students saying 'I am present'. "
        "AI will identify registered students."
    )

    audio_data = st.audio_input("Record classroom audio")

    if st.button(
        "Analyze Audio",
        type="primary",
        width="stretch"
    ):

        if audio_data is None:
            st.warning("Please record classroom audio first.")
            return

        with st.spinner("Processing audio..."):

            enrolled_res = (
                supabase.table("subject_students")
                .select("*, students(*)")
                .eq("subject_id", selected_subject_id)
                .execute()
            )

            enrolled_students = enrolled_res.data or []

            if len(enrolled_students) == 0:
                st.warning("No students enrolled in this subject.")
                return

            candidates_dict = {}

            for node in enrolled_students:

                student = node["students"]

                if student.get("voice_embedding") is not None:
                    candidates_dict[
                        student["student_id"]
                    ] = student["voice_embedding"]

            if len(candidates_dict) == 0:
                st.warning(
                    "No enrolled student has a registered voice profile."
                )
                return

            try:
                audio_bytes = audio_data.read()

                detected_scores = process_bulk_audio(
                    audio_bytes,
                    candidates_dict
                )

            except Exception as e:
                st.error(f"Voice processing failed:\n{e}")
                return

            results = []
            attendance_to_log = []

            current_timestamp = datetime.now().strftime(
                "%Y-%m-%dT%H:%M:%S"
            )

            for node in enrolled_students:

                student = node["students"]

                score = float(
                    detected_scores.get(
                        student["student_id"],
                        0.0
                    )
                )

                present = score > 0

                results.append({

                    "Name": str(student["name"]),

                    "ID": int(student["student_id"]),

                    "Source": (
                        f"{score:.3f}"
                        if present
                        else "Not Detected"
                    ),

                    "Status": (
                        "✅ Present"
                        if present
                        else "❌ Absent"
                    )

                })

                attendance_to_log.append({

                    "student_id": student["student_id"],

                    "subject_id": selected_subject_id,

                    "timestamp": current_timestamp,

                    "is_present": present

                })

            st.session_state.voice_attendance_results = (
                pd.DataFrame(results),
                attendance_to_log
            )

            st.rerun()

    # Safe display
    result = st.session_state.get("voice_attendance_results")

    if (
        result is not None
        and isinstance(result, tuple)
        and len(result) == 2
    ):

        df_results, logs = result

        st.divider()

        show_attendance_result(df_results, logs)