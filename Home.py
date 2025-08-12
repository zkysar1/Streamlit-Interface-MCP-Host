import psutil
import streamlit as st
 
st.write("""# Zak Home Start""")
 
 
st.write("""## Computer Stats""")

hdd = psutil.disk_usage('/')
st.write("Total Storage: {}gbs".format(hdd.total / (2**30)))
st.write("Total free Storage: {}gbs".format(hdd.free / (2**30)))

cpuCount=psutil.cpu_count(logical=True)
ramUsagePercent=psutil.virtual_memory().percent
totalMemory=psutil.virtual_memory().total/1000000000
st.write("Total memory: {}gbs".format(totalMemory))
st.write("Percent Memory Used: {}%".format(ramUsagePercent))
st.write("Count of CPU Cores: {}".format(cpuCount))