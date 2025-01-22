import streamlit as st
from streamlit_pills import pills
import json

# Example usage
if __name__ == "__main__":
    # Define the list of interests
    # Load interests_with_icons from a JSON file
    with open('./ekko/ekko_prototype/tools/interests.json') as file:
        interests_with_icons = json.load(file)
    interests_with_icons = interests_with_icons['interests_with_icons']

    st.header("Please select your interests:")
    selected = pills("", list(interests_with_icons.keys()), icons=list(interests_with_icons.values()),
                      key="interests", multiselect=True, index=[0])
    # TODO:
    # - gotta have a clear all button, come on
    # also, needing to pass in an index for default selection makes no sense; having to unclick it first is ugly
    st.button('Clear all', on_click=st.rerun)