import streamlit as st

st.set_page_config(page_title="EducateAI", page_icon="🎓", layout="wide")

st.title("🎓 EducateAI")
st.caption("Turn any curriculum into engaging learning content for children.")

st.divider()

st.info("Upload a curriculum PDF or paste a subject below to get started.")

uploaded = st.file_uploader("Upload curriculum (PDF or DOCX)", type=["pdf", "docx"])
st.write("— or —")
subject = st.text_area("Describe a subject / paste curriculum text")

import requests

if st.button("Generate Content", disabled=not uploaded):
    with st.spinner("Processing..."):
        response = requests.post(
            "http://localhost:8000/api/upload",
            files={"file": (uploaded.name, uploaded.getvalue(), uploaded.type)}
        )
    if response.status_code == 200:
        data = response.json()
        st.success(f"Uploaded {data['chunk_count']} chunks from {data['filename']}")
    else:
        st.error(response.json().get("detail", "Upload failed"))
