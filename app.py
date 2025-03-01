import streamlit as st

import legal_assistant

# Set Streamlit page configuration
st.set_page_config(page_title="Animal Welfare Legal Assistant", layout="wide")

# Create LangGraph agent
agent = legal_assistant.get_agent()

# Streamlit app setup
st.title("Animal Welfare Legal Assistant")

# Sidebar for user input
st.sidebar.header("Case Information")
case_purpose = st.sidebar.text_area(
    "Describe the purpose of your legal action:",
    placeholder="Provide a brief description of the action you want to take...",
)

uploaded_files = st.sidebar.file_uploader(
    "Upload Case Text Files (optional):",
    type=["txt"],
    accept_multiple_files=True,
)

if st.sidebar.button("Generate Recommendations"):
    if not case_purpose:
        st.error("Please provide a description of your case in the sidebar.")
    else:
        st.info("Processing your input...")

        # Process uploaded files (if any)
        case_texts = []
        if uploaded_files:
            for uploaded_file in uploaded_files:
                case_text = uploaded_file.read().decode("utf-8")
                case_texts.append(case_text)

        # Invoke the agent
        with st.spinner("Generating legal recommendations..."):
            try:
                response = legal_assistant.run_script(agent, case_purpose, case_texts)

                st.success("Recommendations generated!")

                st.subheader("Strategy")
                st.write(response["strategy"])

                st.subheader("Draft Complaint")
                st.write(response["complaint"])

                st.subheader("TODOs for you")
                st.write(response["todo"])

                st.subheader("Resources consulted")
                st.write("\n".join(response["urls"]))

            except Exception as e:
                st.error(f"An error occurred: {e}")

# Footer
st.markdown("---")
st.markdown(
    """This app assists in researching and structuring legal cases related to animal welfare, especially around formulating a complaint.

    Obviously don't file the output of this without consulting a lawyer!  This is just supposed to get you started and hopefully make your case look attractive to people who may want to work pro bono.
    """
)
