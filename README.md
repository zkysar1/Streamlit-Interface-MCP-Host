# Streamlit-Interface-MCP-Host: One interface to connect to a MCP Host.  

## Directory Location
```bash
# Windows (WSL)
win_home=$(wslpath -u "$(wslvar USERPROFILE)")
cd $win_home/OneDrive/Zak/SmartNPCs/MCPThink/Streamlit-Interface-MCP-Host/

# Linux/Mac
cd ~/ZAK-Agent/
```

## OpenAi API Key
This chat uses OpenAi, and requires a key.  The key is stored as a windows environment variable called `OPENAI_API_KEY`, and it should be available when launching streaming from the windows shell.  

## Launch Streamlit from command line/powershell
python -m streamlit run "C:\Users\zkysa\OneDrive\Zak\SmartNPCs\MCPThink\Streamlit-Interface-MCP-Host\Home.py"
- old way: streamlit run "C:\Users\zkysa\OneDrive\Zak\SmartNPCs\MCPThink\Streamlit-Interface-MCP-Host\Home.py"
py -3.12 -m pip install --user -r "C:\Users\zkysa\OneDrive\Zak\SmartNPCs\MCPThink\Streamlit-Interface-MCP-Host\requirements.txt"
- old way: pip install -r "C:\Users\zkysa\OneDrive\Zak\SmartNPCs\MCPThink\Streamlit-Interface-MCP-Host\requirements.txt"