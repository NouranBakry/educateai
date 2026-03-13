import streamlit as st

st.set_page_config(page_title="EducateAI", page_icon="🎓", layout="wide")

st.title("🎓 EducateAI")
st.caption("Turn any curriculum into engaging learning content for children.")

st.divider()

st.info("Upload a curriculum PDF or paste a subject below to get started.")

uploaded = st.file_uploader("Upload curriculum (PDF or DOCX)", type=["pdf", "docx"])
st.write("— or —")
subject = st.text_area("Describe a subject / paste curriculum text")

if st.button("Generate Content", disabled=not (uploaded or subject)):
    st.warning("API backend not connected yet — coming soon.")
