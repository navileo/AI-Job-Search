import os
import sys
import streamlit.web.cli as stcli

if __name__ == "__main__":
    # Set environment variables to avoid permission issues
    os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
    
    # Use current directory for config to avoid writing to system/user folders
    os.environ["STREAMLIT_CONFIG_DIR"] = os.path.join(os.getcwd(), ".streamlit")
    
    # Use port 8504 to avoid conflicts with previous runs
    sys.argv = ["streamlit", "run", "app.py", "--server.port", "8504"]
    print(f"Starting Streamlit with args: {sys.argv}")
    sys.exit(stcli.main())
