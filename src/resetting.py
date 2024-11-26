from smartfunnel.tools.ResettingTool import ResetDatabaseTool
from smartfunnel.tools.chroma_db_init import app_instance

app = app_instance
app.add("blablabla", data_type="text")
print(app.get_data_sources())

reset_database_tool = ResetDatabaseTool(app=app)
reset_database_tool._run()
# app.get_sources()
print(app.get_data_sources())