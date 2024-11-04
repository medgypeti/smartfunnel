from smartfunnel.crew_youtube import YoutubeCrew

def replay():
    task_id = ""
    # inputs = {"instagram_username": "clubvipfinance"}  # Add any inputs if needed
    try:
        YoutubeCrew().crew().replay(task_id=task_id)
    except Exception as e:
        print(f"An error occurred while replaying the crew: {e}")

if __name__ == "__main__":
    replay()

#   def replay():
#   """
#   Replay the crew execution from a specific task.
#   """
#   task_id = '356844b9-990e-44fa-bb76-4eb0bfc82896'
# #   inputs = {"topic": "CrewAI Training"}  # This is optional; you can pass in the inputs you want to replay; otherwise, it uses the previous kickoff's inputs.
#   try:
#       YourCrewName_Crew().crew().replay(task_id=task_id, inputs=inputs)

#   except subprocess.CalledProcessError as e:
#       raise Exception(f"An error occurred while replaying the crew: {e}")

#   except Exception as e:
#       raise Exception(f"An unexpected error occurred: {e}")

# if __name__ == "__main__":
#     replay()
