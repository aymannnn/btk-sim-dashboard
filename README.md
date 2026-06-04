# 📈 BTK Admin Dashboard

Welcome to the BTK Admin Dashboard for the Oral Board Simulator! This tool allows you to visualize and explore all of the data exported from Designli.

Because this dashboard processes massive datasets, it runs directly on your own computer rather than a remote cloud server. In other words, it's very hard to allow for 4 GB+ uploads on websites without much hassle. You do not need to be a software engineer to run this, just follow the exact steps below. Please contact me if you need any help.

---

## 🛠️ Setup Instructions (You only do this once!)

### Step 1: Install Python
Your computer needs a program called Python to run the dashboard.
1. Go to [python.org/downloads](https://www.python.org/downloads/)
2. Click the big yellow button to download the latest version for your computer (Windows or Mac).
3. **🚨 CRITICAL FOR WINDOWS USERS 🚨**: When you open the Python installer, look at the very bottom of the window and **CHECK THE BOX** that says `"Add Python to PATH"` before clicking Install. If you forget this, nothing will work!
4. Complete the installation.

### Step 2: Download the Dashboard
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
   python -m pip install -r requirements.txt
   ```
   *Wait 1-2 minutes for it to finish installing.*

**For Mac Users:**
1. Open the **Terminal** app (Press `Command + Space`, type `Terminal`, and hit Enter).
2. Type `cd ` (make sure there is a space after cd), then drag and drop the unzipped `BTK_admin_dashboard` folder from your Desktop directly into the Terminal window, and hit **Enter**.
3. Copy and paste this exact command and hit Enter:
   ```bash
   python3 -m pip install -r requirements.txt
   ```
   *Wait 1-2 minutes for it to finish installing.*

---

## 🚀 How to Run the Dashboard
You only ever have to do the setup above once. From now on, whenever you want to open the dashboard, just do this:

1. Open your terminal inside the dashboard folder (just like you did in Step 3).
2. Type the following command and hit Enter:
   * **Windows:** `python -m streamlit run app.py`
   * **Mac:** `python3 -m streamlit run app.py`
3. A web browser window will automatically pop open with your dashboard!

---

## 📂 How to Load Your Data

1. Once the dashboard opens in your browser, look at the sidebar on the left.
2. Click **"Browse files"** (or drag and drop your `snapshot.zip` file into the box).
3. The dashboard will automatically extract and process the data. *Note: If your file is extremely large (e.g., 4GB), please be patient and allow the progress bar to finish without clicking away!*
