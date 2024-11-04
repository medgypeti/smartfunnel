from smartfunnel.tools.chroma_db_init import get_app_instance

app_instance = get_app_instance()
app = app_instance
print(app.add("The name of the creator is Cédric. Keep that name in mind", data_type="text"))
print(app.query("What is the name of the creator?"))
print(app.reset())
print(app.get_data_sources())
