from collections import defaultdict

import pandas as pd
import streamlit as st


class QuestionManager:
    """Manages the questions and scoring of the personality test.

    :param session_state: Streamlit's session state to hold the state of the app.
    :type session_state: streamlit.state.SessionState
    :param questions: A list of questions and associated personality traits.
    :type questions: list
    """

    def __init__(self, session_state, questions):
        """Initializes the QuestionManager with questions and sets up scoring.

        :param session_state: Streamlit's session state to hold the state of the app.
        :type session_state: streamlit.state.SessionState
        :param questions: A list of questions and associated personality traits.
        :type questions: list
        """
        self.session_state = session_state
        self.questions = questions

    def display_current_question(self):
        """Displays the current question and options, allowing the user to respond."""
        if 'current_index' not in self.session_state:
            self.session_state.current_index = 0

        if self.session_state.current_index < len(self.questions):
            question = self.questions[self.session_state.current_index]
            # TODO:
            # - find a better way to control the layout
            st.write('\n')
            st.write('\n')
            st.write('\n')
            col1, col2, col3, = st.columns([.2,.1,.7])

            with col1:
                if st.button(label=list(question.keys())[1], 
                             key=f"option1_{self.session_state.current_index}", 
                             on_click=self._update_scores, args=(1,)):
                    pass

            with col3:
                if st.button(label=list(question.keys())[2], 
                             key=f"option2_{self.session_state.current_index}", 
                             on_click=self._update_scores, args=(2,)):
                    pass
            with col2:
                st.write('or')
        else:
            st.success("Thank you for the introduction :)", icon='✅')

    def _update_scores(self, option_number):
        """Updates the scores based on the selected option.

        :param option_number: The selected option number (1 or 2).
        :type option_number: int
        """
        question = self.questions[self.session_state.current_index]
        option_key = list(question.keys())[option_number]
        for trait in question[option_key]:
            if 'scores' not in self.session_state:
                self.session_state.scores = defaultdict(int)
            self.session_state.scores[trait] += 1
        self.session_state.current_index += 1

def display_scores(scores):
    """Displays the scores as a normalized histogram.

    :param scores: A dictionary with personality traits and their scores.
    :type scores: dict
    """
    df = pd.DataFrame(list(scores.items()), columns=['Personality', 'Score'])
    df['Score'] = df['Score'] / df['Score'].sum()  # Normalizing the scores
    st.bar_chart(df.set_index('Personality'))

def main(questions):
    """Main function to run the personality test.

    :param questions: A list of questions for the personality test.
    :type questions: list
    """
    st.title("Personality Test")

    qm = QuestionManager(st.session_state, questions)

    # Display questions and handle user interaction
    qm.display_current_question()

    # If all questions have been answered, display the scores
    if 'current_index' in st.session_state and st.session_state.current_index >= len(questions):
        display_scores(st.session_state.scores)

if __name__ == "__main__":
    import json
    with open("questions.json") as f:
        questions = json.load(f)
    main(questions)