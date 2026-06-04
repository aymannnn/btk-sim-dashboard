# 📈 BTK Admin Dashboard

Welcome to the BTK Admin Dashboard! This tool allows you to instantly process, analyze, and visualize massive 4GB+ data snapshots completely securely on your local machine.

Because this dashboard processes massive datasets, it runs directly on your own computer rather than a remote cloud server. You do not need to be a software engineer to run this, just follow the exact steps below!

---

## 🛠️ Setup Instructions (You only do this once!)

### Step 1: Install Python
Your computer needs a program called Python to run the dashboard.
1. Go to [python.org/downloads](https://www.python.org/downloads/)
2. Click the big yellow button to download the latest version for your computer (Windows or Mac).
3. **🚨 CRITICAL FOR WINDOWS USERS 🚨**: When you open the Python installer, look at the very bottom of the window and **CHECK THE BOX** that says `"Add Python to PATH"` before clicking Install. If you forget this, nothing will work!
4. Complete the installation.

### Step 2: Download the Dashboard
You don't need any fancy developer tools to download this code:
1. Go to the top of this GitHub repository page.
2. Click the green **"<> Code"** button.
3. Click **"Download ZIP"**.
4. Unzip the downloaded folder somewhere easy to find (like your Desktop).

### Step 3: Install the Background Libraries
We need to download the required math and graphing libraries for the dashboard.

**For Windows Users:**
1. Open the unzipped `BTK_admin_dashboard` folder on your Desktop.
2. Click on the file explorer address bar at the very top of the window, type `cmd`, and hit **Enter**. (This opens a black terminal window exactly inside your folder).
3. Copy and paste this exact command into the black window and hit Enter:
   ```cmd
   pip install -r requirements.txt
   ```
   *Wait 1-2 minutes for it to finish installing.*

**For Mac Users:**
1. Open the **Terminal** app (Press `Command + Space`, type `Terminal`, and hit Enter).
2. Type `cd ` (make sure there is a space after cd), then drag and drop the unzipped `BTK_admin_dashboard` folder from your Desktop directly into the Terminal window, and hit **Enter**.
3. Copy and paste this exact command and hit Enter:
   ```bash
   pip3 install -r requirements.txt
   ```
   *Wait 1-2 minutes for it to finish installing.*

---

## 🚀 How to Run the Dashboard
You only ever have to do the setup above once. From now on, whenever you want to open the dashboard, just do this:

1. Open your terminal inside the dashboard folder (just like you did in Step 3).
2. Type the following command and hit Enter:
   * **Windows:** `streamlit run app.py`
   * **Mac:** `python3 -m streamlit run app.py`
3. A web browser window will automatically pop open with your dashboard!

---

## 📂 How to Load Massive 4GB Datasets

Do NOT use the "Web Upload" button for massive files (your web browser will run out of memory and crash). 
Because this dashboard is running locally on your computer, it can read files straight off your hard drive natively!

1. In the dashboard sidebar, change the Upload Method to **"Local Path (Fastest)"**.
2. Type the path to your dataset (e.g. `./snapshot/` or `C:\Users\Name\Desktop\snapshot.zip`).

**⚡ Pro-Tip for Instant Loading:** 
You do *not* have to unzip your 4GB `snapshot.zip` file—the dashboard is smart enough to process the raw `.zip` file for you. **HOWEVER**, if you manually unzip the folder yourself and type the path to the *unzipped folder*, the dashboard will load the 4GB of data almost instantly because it skips the heavy decompression phase!
