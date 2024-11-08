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

### Running Curl HTTP Commands to test API Routes :


2. GET /api/messages fetches messages, has query string to limit how many messages are fetched

4. GET/POST /api/messages return appropriate error message when not logged in

5. POST /api/login sets cookie, DELETE removes cookie

   For a user that's not logged in :
   curl -X GET "http://130.179.28.113:8548/api/messages"
   [nawaza1@eagle Assignment 2]> curl -X GET "http://130.179.28.113:8548/api/messages"
{"error": "Not logged in"}[nawaza1@eagle Assignment 2]>

Logging in and sending messages

[nawaza1@eagle Assignment 2]> curl -X POST "http://130.179.28.113:8548/api/login" -d '{"username": "your_username", "password": "your_password"}' -c cookies.txt -H "Content-Type: application/json"
[nawaza1@eagle Assignment 2]> curl -X GET "http://130.179.28.113:8548/api/messages" -b cookies.txt
{"messages": ["NICK", "614 | Mirha: Hi", "615 | Mirha: this is Mirha", "616 | Mirha: what is up ?", "617 | Mirha: yeah looks good", "618 | Ali: Very Sunny Day today", "619 | Mirha: Hi - this is Mirha", "620 | Mirha: and looks like it's working perfectly fine on Aviary", "621 | Mirha: yeah good stuff", "622 | Mirha: brilliant", "623 | Mirha: need to test the ScreenScraper program now  !", "624 | Jihan: Hope this works on Aviary", "625 | Jihan: Hope this works on Aviary - I just updated the makefile", "626 | Mirha: good stuff G", "627 | Max: hi", "628 | Max: hello", "629 | Max: what is up", "630 | Max: Hiiii", "631 | Max: this is Max", "632 | Jihan: Good day to u Ali", "633 | Jihan: Good day to u Ali"]}[nawaza1@eagle Assignment 2]> 



[nawaza1@eagle Assignment 2]> curl -X GET "http://130.179.28.113:8548/api/messages" -b cookies.txt
{"messages": ["NICK", "614 | Mirha: Hi", "615 | Mirha: this is Mirha", "616 | Mirha: what is up ?", "617 | Mirha: yeah looks good", "618 | Ali: Very Sunny Day today", "619 | Mirha: Hi - this is Mirha", "620 | Mirha: and looks like it's working perfectly fine on Aviary", "621 | Mirha: yeah good stuff", "622 | Mirha: brilliant", "623 | Mirha: need to test the ScreenScraper program now  !", "624 | Jihan: Hope this works on Aviary", "625 | Jihan: Hope this works on Aviary - I just updated the makefile", "626 | Mirha: good stuff G", "627 | Max: hi", "628 | Max: hello", "629 | Max: what is up", "630 | Max: Hiiii", "631 | Max: this is Max", "632 | Jihan: Good day to u Ali", "633 | Jihan: Good day to u Ali"]}[nawaza1@eagle Assignment 2]> curl -X POST "http://130.179.28.113:8548/api/messages" -d '{"message": "Your message here"}' -H "Content-Type: application/json" -b cookies.txt
Message sent[nawaza1@eagle Assignment 2]> 

Working as expected ^^^^^

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
