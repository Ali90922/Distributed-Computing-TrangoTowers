
# Running Distributed Computing Project

## Setup and Running the Programs

### Step 1: Open Three Terminal Tabs
Navigate to the project directory in each tab:
```bash
cd /Users/Ali_Nawaz/music/Distributed-Computing-TrangoTowers
```

### Step 2: Start the Server
In the first terminal tab, start the server:
```bash
python server.py
```

### Step 3: Start the Web Server
In the second terminal tab, start the web server:
```bash
python WebServer.py
```

### Step 4: Run the Client for Debugging
In the third terminal tab, run the client:
```bash
python client.py 127.0.0.1
```
Replace `127.0.0.1` with the appropriate IP if running on a different machine.

---

## Accessing the Web Interface

- **On Your Local Machine**:  
  Open a web browser and go to:
  ```
  http://localhost:8548/
  ```

- **On the Aviary Network**:  
  If running this in the Aviary environment, access it through:
  ```
  http://hawk.cs.umanitoba.ca:8548/
  ```

---

## Running the Screen Scraper Program

### Step 1: Compile the Program
In the project directory, compile with:
```bash
make
```

### Step 2: Execute the Screen Scraper
Run the screen scraper with the following syntax:
```bash
./screen_scraper [host] [port] [username] [message]
```

#### Example (on your local machine):
```bash
./screen_scraper 127.0.0.1 8000 Ali "Very Sunny Day today!"
```

---

## Summary of Commands

```bash
# Terminal Tab 1
cd /Users/Ali_Nawaz/music/Distributed-Computing-TrangoTowers
python server.py

# Terminal Tab 2
cd /Users/Ali_Nawaz/music/Distributed-Computing-TrangoTowers
python WebServer.py

# Terminal Tab 3
cd /Users/Ali_Nawaz/music/Distributed-Computing-TrangoTowers
python client.py 127.0.0.1

# Screen Scraper Compilation
cd /Users/Ali_Nawaz/music/Distributed-Computing-TrangoTowers
make

# Screen Scraper Execution Example
./screen_scraper 127.0.0.1 8000 Ali "Very Sunny Day today!"
```
