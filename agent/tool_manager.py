class ToolManager:

    def __init__(self):

        self.tools = {}

    def register_tool(self, name, tool):

        self.tools[name] = tool

    def execute(self, name, **kwargs):

        if name not in self.tools:

            return {

                "success": False,

                "message": f"{name} tool not found."
            }

        return self.tools[name].execute(**kwargs)