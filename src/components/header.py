import streamlit as st
import base64


def get_base64_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def header_home():
    logo = get_base64_image("assets/logo.jpeg")

    st.markdown(
        f"""
        <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;margin-top:20px;margin-bottom:35px;">
            <img src="data:image/jpeg;base64,{logo}" style="height:120px;border-radius:20px;" />
            <h1>SNAP<br/>CLASS</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

def header_dashboard():
    logo = get_base64_image("assets/logo.jpeg")

    st.markdown(
        f"""
        <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;margin-top:20px;margin-bottom:35px;">
            <img src="data:image/jpeg;base64,{logo}" style="height:120px;border-radius:20px;" />
            <h2>SNAP<br/>CLASS</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )
       