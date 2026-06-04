import os
import sys
import streamlit.web.cli as stcli

def resolve_path(path):
    """
    Resolve paths depending on whether the code is running normally or bundled as a PyInstaller executable.
    PyInstaller unpacks files into a temporary directory accessed via sys._MEIPASS.
    """
    if getattr(sys, "frozen", False):
        resolved_path = os.path.abspath(os.path.join(sys._MEIPASS, path))
    else:
        resolved_path = os.path.abspath(os.path.join(os.getcwd(), path))
    return resolved_path

if __name__ == "__main__":
    # The following block is never executed but forces PyInstaller to find and bundle these local modules
    if False:
        import app
        import data_processor
        import components.charts

    app_path = resolve_path("app.py")
    
    # Simulate the command line arguments passed to the streamlit runner
    sys.argv = [
        "streamlit", 
        "run", 
        app_path, 
        "--global.developmentMode=false"
    ]
    
    # Execute Streamlit
    sys.exit(stcli.main())
