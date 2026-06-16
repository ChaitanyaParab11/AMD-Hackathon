import streamlit as st
import pandas as pd
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import os

st.set_page_config(
    page_title="Secure Java",
    layout="wide"
)


def main() :
    st.title("Lets Secure JAVA code ! ",text_alignment="left",anchor=False)

    MODEL_PATH = "../qwen_security_merged"
     
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
     
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        torch_dtype=torch.bfloat16,
        device_map="auto"
    )
    
    col1 , col2 = st.columns(spec=[1,1],gap="medium")
    codeText = ""
    with col1:
        codeText = col_1_Method()

    with col2:
        st.subheader("Secure Result : ",anchor=False)
        if st.button("Secure") and codeText : 
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
    prompt = f"""
    ### Task
    Analyze the Java code and fix the vulnerability
     
    ### Java Code
     
    {codeText}
     
    ### Vulnerability
    """
     
    inputs = tokenizer(
        prompt,
        return_tensors="pt"
    ).to(model.device)
     
    outputs = model.generate(
        **inputs,
        max_new_tokens=1024,
        do_sample=False
    )
    
    result = tokenizer.decode(
            outputs[0],
            skip_special_tokens=True
        )
    codeText = result.split("### Vulnerability")[-1].strip()
    
    st.code(codeText,language="java")

if __name__ == "__main__" :
    main()