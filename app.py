import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Debugg Java",
    layout="wide"
)


def main() :
    st.title("Lets Debug JAVA code ! ",text_alignment="left",anchor=False)

    col1 , col2 = st.columns(spec=[1,1],gap="medium")
    codeText = ""
    with col1:
        codeText = col_1_Method()

    with col2:
        st.subheader("Debugging Result : ",anchor=False)
        if st.button("Debugg") and codeText : 
            col_2_Method(codeText)
        


# st.cache_data
def col_1_Method():
    codeText = ""
    st.subheader("Input code :",anchor=False)
    code_file = st.file_uploader("Upload code ",type=["java"],max_upload_size=2,accept_multiple_files=False)

    if code_file is not None :
        codeText = code_file.read().decode("utf-8")
    else :
        st.subheader("OR",text_alignment="center",anchor=False)
        codeText = st.text_area("Enter JAVA code",height=300)

    previewCode = st.toggle("Preview code")
    if previewCode and codeText :
        st.code(codeText,language="java")
    else : 
        st.write("Preview Block")

    return codeText

def col_2_Method(codeText):
    # Process codeText 
    # get dubug output
    # put in a variable debugOP
    # and st.code(debugOP,language="java")
    st.code(codeText,language="java")

if __name__ == "__main__" :
    main()