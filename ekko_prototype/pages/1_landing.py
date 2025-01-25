import glob

import streamlit as st

ekko_icon = glob.glob("./**/ekko.png", recursive=True)[0]
st.set_page_config(page_title="ekko v0.1", page_icon=ekko_icon)


# TODO:
# make nicer, add a bit more content
def welcome():
    st.markdown("""
            ## Introducing ekko: Your digital self, amplified.

            **Discover ekko,** where your digital chaos finds calm. In a world racing with content, ekko is not just a tool—it's a revolution in how you interact with information. This dynamic content, discovery, curation and summarization tool is your gateway to becoming effortlessly knowledgeable.

            ### Why Choose ekko?
            **Our vision:**
            - **Tailored Summaries:** Get the gist of podcasts and YouTube channels you love. Our AI cuts through the noise to deliver what matters to you.
            - **Save Time:** No more endless scrolling or battling FOMO. ekko brings you up to speed in minutes, not hours.
            - **Your Content, Organized:** Integrate previously scattered libraries of notes, content, and endless 'watch later' lists into one cohesive platform.
            - **Access and Act**: Your digital brain is always within reach. ekko not only allows unlimited information recall, but also lets you leverage the knowledge to take action, all through your digital assistant.
            - **Smart Content Delivery:** Receive concise, insightful summaries right where and when you want them — be it your inbox or directly within the app.
            - **Stay Ahead:** Subscribe to the sources and media you want, and let ekko take care of it. Receive updates immediately or as often as you like.

            **Join the Revolution**
            Embrace a smarter, more efficient way to consume content. With ekko, knowledge isn't just power—it's easy, it's quick, and it's tailored just for you. Say goodbye to content overload and hello to clarity.

            **Be part of shaping the future of content consumption.** Experience the power of ekko and take the first step towards a more informed, organized digital life.
            """)

    st.markdown("""
                ### But first, let's start with some feedback 🤓!
                
                - We would like to get to know you, and to understand if ekko (and what it aims to become), could be of value to you and others like you.
                - The feedback form will take about 3 minutes to complete, we highly appreciate your time and participation! 🙏🏽
                - _Note_: 
                    - For the best experience, please use a computer for testing out the protoype.
                    - If you are using a mobile device, try not letting it go to sleep while you are interacting with the prototype.
                """)

    st.session_state["feedback_round"] = "general"
    # st.page_link(page="./pages/feedback_record.py", label="Click here to get started 🚀")


if __name__ == "__main__":
    welcome()
