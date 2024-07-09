import os
from dotenv import load_dotenv
import openai
import requests
import json
import time
import logging
from datetime import datetime
import streamlit as st
from io import StringIO
# thread_7O9OLEY6h8RLhnNtiUDNghRx
load_dotenv()

client = openai.OpenAI()

model = "gpt-4o"  # "gpt-3.5-turbo-16k"


# == Run it
class StudyBuddy:
    assis_id="asst_Lh7niJpzDi69snEo9Gr0kOgV"
    thread_id =None
    # thread_id="thread_5WtanbVPeinJWk24dXTyAwhw"

    def __init__(self,model:str=model):
        self.client=client
        self.model=model
        self.assistant=None
        self.thread=None
        self.run=None
        self.summary=None



        if StudyBuddy.assis_id:
            self.assistant=self.client.beta.assistants.retrieve(
                assistant_id=StudyBuddy.assis_id
            )
        if StudyBuddy.thread_id:
            self.thread=self.client.beta.threads.retrieve(
                thread_id=StudyBuddy.thread_id
            )

    def create_assistant(self, name, instructions):
        if not self.assistant:
            assis_obj=self.client.beta.assistants.create(
                name=name,instructions=instructions,model=self.model
            )
            StudyBuddy.assis_id=assis_obj.id
            self.assistant=assis_obj

            print(f"AssisID :: {self.assistant.id}")
    
    def create_thread(self):
        if not self.thread:
            thread_obj=self.client.beta.threads.create()
            StudyBuddy.thread_id=thread_obj.id
            self.thread=thread_obj
            print(f"ThreadID :: {self.thread.id}")

    def add_message_to_thread(self,role,content):
        if self.thread:
            self.client.beta.threads.messages.create(
                thread_id=self.thread.id,role=role,content=content
            )
                  
    def run_assistant(self,instructions):
        if self.thread and self.assistant:
            self.run=self.client.beta.threads.runs.create(
                thread_id=self.thread.id,
                assistant_id=self.assistant.id,
                instructions=instructions,
                max_prompt_tokens=500,
                max_completion_tokens=700
            )
    def process_message(self):
        if self.thread:
            messages=self.client.beta.threads.messages.list(thread_id=self.thread.id)
            summary=[]

            last_message=messages.data[0]
            role=last_message.role
            response=last_message.content[0].text.value
            summary.append(response)

            self.summary="\n".join(summary)
            print(f"Response :{role.capitalize()} ====>> {response}")            

    def wait_for_completion(self):
        if self.thread and self.run:
            i = 0
            while True:
                i+=1
                run_status=self.client.beta.threads.runs.retrieve(
                    thread_id=self.thread.id, run_id=self.run.id
                )
                print(f"Run Status {i}, {run_status.status}")

                if run_status.status== "completed":
                    self.process_message()
                    break
            
    
    def run_steps(self):
        run_steps = self.client.beta.threads.runs.steps.list(
            thread_id=self.thread.id, run_id=self.run.id
        )
        print(f"Run-Steps::: {run_steps}")
        return run_steps.data
    def create_files(self,filedata):
        
        with open(filedata.name,"wb") as f:
            f.write(filedata.getvalue())
        

        file_obj=self.client.files.create(
            file=open(filedata.name,"rb"),
            purpose="vision"
        )

        return file_obj.id
    
    def run_process(self,content):
        self.create_assistant(
            name="Studdy Buddy",
            instructions="""You are a Math study assistant specializing in Mathematics education in Pakistan. Your primary role is to provide customized questions that are either more challenging or simpler to enhance students' understanding and skills. Analyze the student's input—whether a picture, file, or text—to gauge their skill level and comprehension. Based on this analysis, create personalized math problems that cater to their specific learning needs."""
        )
        self.create_thread()

        self.add_message_to_thread(
            role="user",content=content
        )
        self.run_assistant(
            instructions="Address the user as buddy.Provide the student with either more challenging or simple question based on the analysis of the input—whether a picture, file, or text— provided by the student")
        
        self.wait_for_completion()

        return self.summary

def main():
    studybuddy = StudyBuddy()

    st.title("Taleemabad's Math Tutor")

    with st.form(key="user_input_form"):
        st.subheader("Upload or Capture an Image")
        file_input = st.file_uploader(label="Upload your images", type=['jpg', 'jpeg', 'png'])
        camera_input = st.camera_input(label="Take a picture")

        st.subheader("Or Enter Text")
        text_input = st.text_input("Hey Buddy, how can I help you:")

        submit_button = st.form_submit_button(label="Run Assistant")

    if submit_button:
        content = []

        if file_input:
            file_id = studybuddy.create_files(file_input)
            content.append({"type": "image_file", "image_file": {"file_id": file_id}})
        if camera_input:
            file_id = studybuddy.create_files(camera_input)
            content.append({"type": "image_file", "image_file": {"file_id": file_id}})
        if text_input:
            content.append({"type": "text", "text": text_input})

        if content:
            with st.spinner("Processing..."):
                summary = studybuddy.run_process(content)
                st.success("Processing complete!")
                st.write(summary)
        else:
            st.error("Please provide input in any of the fields.")

        if file_input:
            try:
                os.remove(file_input.name)
            except Exception as e:
                st.error(f"Error removing file: {e}")

        if camera_input:
            try:
                os.remove(camera_input.name)
            except Exception as e:
                st.error(f"Error removing file: {e}")

if __name__ == "__main__":
    main()