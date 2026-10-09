"""Generate the MyRedis In-Memory Database Technical Deep Dive PDF."""
from fpdf import FPDF, XPos, YPos


class PDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        if self.page_no() > 1:
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(120, 120, 120)
            self.cell(0, 8, "MyRedis - In-Memory Database | Complete Technical Deep Dive", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
            self.set_draw_color(220, 60, 60)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def ch(self, t):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(26, 34, 54)
        self.ln(4)
        self.cell(0, 10, t, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_draw_color(220, 60, 60)
        self.set_line_width(0.8)
        self.line(10, self.get_y(), 80, self.get_y())
        self.ln(6)

    def sec(self, t):
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(40, 50, 70)
        self.ln(3)
        self.cell(0, 8, t, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(2)

    def sub(self, t):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(60, 70, 90)
        self.ln(2)
        self.cell(0, 6, t, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1)

    def p(self, t):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 5, t)
        self.ln(2)

    def q(self, t):
        self.set_font("Helvetica", "I", 9)
        self.set_text_color(50, 60, 80)
        y0 = self.get_y()
        self.set_x(15)
        self.multi_cell(180, 5, t)
        self.set_draw_color(220, 60, 60)
        self.set_line_width(0.4)
        self.line(14, y0, 14, self.get_y())
        self.ln(3)

    def code(self, t):
        self.set_font("Courier", "", 7.5)
        self.set_text_color(40, 40, 40)
        self.set_fill_color(240, 241, 243)
        for line in t.split("\n"):
            self.cell(0, 4, "  " + line, new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True)
        self.ln(3)

    def tr(self, cells, hdr=False):
        self.set_font("Helvetica", "B" if hdr else "", 7.5)
        if hdr:
            self.set_fill_color(26, 34, 54)
            self.set_text_color(255, 255, 255)
        else:
            self.set_fill_color(248, 249, 250)
            self.set_text_color(30, 30, 30)
        w = 190 / len(cells)
        for c in cells:
            self.cell(w, 5.5, str(c), border=1, fill=True)
        self.ln()

    def tr_w(self, cells, widths, hdr=False):
        """Table row with custom column widths."""
        self.set_font("Helvetica", "B" if hdr else "", 7.5)
        if hdr:
            self.set_fill_color(26, 34, 54)
            self.set_text_color(255, 255, 255)
        else:
            self.set_fill_color(248, 249, 250)
            self.set_text_color(30, 30, 30)
        for c, w in zip(cells, widths):
            self.cell(w, 5.5, str(c), border=1, fill=True)
        self.ln()

    def b(self, t, indent=0):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(30, 30, 30)
        self.set_x(15 + indent)
        self.cell(4, 5, "-")
        self.multi_cell(175 - indent, 5, t)
        self.ln(1)

    def red(self, label, text):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(220, 60, 60)
        self.cell(40, 5, label)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(30, 30, 30)
        self.multi_cell(150, 5, text)
        self.ln(1)


def build():
    pdf = PDF()
    pdf.alias_nb_pages()

    # ===== COVER =====
    pdf.add_page()
    pdf.ln(30)
    pdf.set_font("Helvetica", "B", 36)
    pdf.set_text_color(26, 34, 54)
    pdf.cell(0, 15, "MyRedis", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.set_font("Helvetica", "", 14)
    pdf.set_text_color(220, 60, 60)
    pdf.cell(0, 10, "In-Memory Database Server", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(40, 50, 70)
    pdf.cell(0, 12, "Complete Technical Deep Dive", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.ln(8)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, "Architecture | Implementation | Networking | Concurrency", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(60, 60, 60)
    for line in [
        "Language: C++17 | ~1,573 Lines of Code | 27 Commands Supported",
        "Networking: POSIX TCP Sockets | RESP Wire Protocol",
        "Concurrency: Thread-per-Client | std::mutex Synchronization",
        "Data Structures: unordered_map (O(1) lookup) | vector | nested maps",
        "Persistence: Custom text-based dump format (dump.my_rdb)",
        "Compatible with official redis-cli",
        "",
        "3 Classes | 26 Database Methods | 38 Automated Tests",
    ]:
        pdf.cell(0, 6, line, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.ln(12)
    pdf.set_font("Helvetica", "I", 9)
    pdf.cell(0, 6, "Author: Mandar", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")

    # ===== CHAPTER 1: PROJECT OVERVIEW =====
    pdf.add_page()
    pdf.ch("1. What Is This Project?")

    pdf.q("A Redis-compatible in-memory database server built entirely from scratch in C++17. It listens on a TCP port, accepts multiple client connections simultaneously, parses the Redis RESP wire protocol, stores data in memory using hash maps and vectors, supports 27 Redis commands across strings, lists, and hashes, persists data to disk periodically and on shutdown, and handles graceful shutdown via Unix signals. You can connect to it using the official redis-cli tool -- it speaks the same protocol as real Redis.")

    pdf.sec("What Is Redis and Why Clone It?")
    pdf.p("Redis (Remote Dictionary Server) is the world's most popular in-memory data store, used as a cache, message broker, and session store.")
    pdf.p("Building a Redis clone teaches core systems programming skills:")
    pdf.b("How network servers work at the lowest level (sockets, TCP)")
    pdf.b("How to handle multiple clients simultaneously (threads, mutexes)")
    pdf.b("How to design an efficient in-memory data store")
    pdf.b("How protocols work (parsing binary wire formats)")
    pdf.b("How persistence works (serializing memory to disk)")

    # ===== CHAPTER 2: ARCHITECTURE =====
    pdf.add_page()
    pdf.ch("2. Architecture Overview")

    pdf.code(
        "                  +------------------+\n"
        "                  |    main.cpp      |\n"
        "                  |  (Entry Point)   |\n"
        "                  +--------+---------+\n"
        "                           |\n"
        "            +--------------+--------------+\n"
        "            |                             |\n"
        " +----------v----------+     +------------v-----------+\n"
        " |    RedisServer       |     | Persistence Thread     |\n"
        " | (TCP Socket Server)  |     | (dumps every 300s)     |\n"
        " +----------+-----------+     +------------------------+\n"
        "            |\n"
        "            | accept() -> spawn thread per client\n"
        "            |\n"
        " +----------v-----------+\n"
        " | RedisCommandHandler   |\n"
        " | (RESP Parser +        |\n"
        " |  Command Dispatch)    |\n"
        " +----------+------------+\n"
        "            |\n"
        " +----------v-----------+\n"
        " |   RedisDatabase       |\n"
        " |   (Singleton)         |\n"
        " |  kv_store    unordered_map<string, string>           |\n"
        " |  list_store  unordered_map<string, vector<string>>   |\n"
        " |  hash_store  unordered_map<string, umap<str,str>>    |\n"
        " |  expire_map  unordered_map<string, time_point>       |\n"
        " |  db_mutex    std::mutex                              |\n"
        " +-----------------------+"
    )

    pdf.sec("Three Classes, Clean Separation")
    pdf.tr(["Class", "Responsibility"], hdr=True)
    pdf.tr(["RedisServer", "Owns TCP socket, accepts clients, spawns threads"])
    pdf.tr(["RedisCommandHandler", "Parses RESP protocol, dispatches to handler functions"])
    pdf.tr(["RedisDatabase", "Stores all data, thread-safe via mutex, handles persistence"])

    pdf.sec("Entry Point (main.cpp) - 27 Lines")
    pdf.code(
        "main()\n"
        "  |\n"
        "  +-- Parse port from argv (default 6379)\n"
        "  +-- Load database from dump.my_rdb (if exists)\n"
        "  +-- Create RedisServer(port)\n"
        "  +-- Spawn persistence thread (dumps every 300s, detached)\n"
        "  +-- server.run()  <-- blocks here until shutdown"
    )

    # ===== CHAPTER 3: CORE CONCEPTS =====
    pdf.add_page()
    pdf.ch("3. TCP/IP and Socket Programming")

    pdf.sec("The Server Socket Lifecycle")
    pdf.code(
        "1. socket()    -- Create a socket (get a phone)\n"
        "2. bind()      -- Assign address + port (get a phone number)\n"
        "3. listen()    -- Start accepting calls (turn the ringer on)\n"
        "4. accept()    -- Wait for a client to connect (pick up the phone)\n"
        "5. recv/send   -- Exchange data with the client (talk)\n"
        "6. close()     -- Hang up"
    )

    pdf.sec("Implementation Details")
    pdf.code(
        "// Create socket\n"
        "server_socket = socket(AF_INET, SOCK_STREAM, 0);\n"
        "// AF_INET = IPv4, SOCK_STREAM = TCP\n"
        "\n"
        "// Allow port reuse (avoid 'Address already in use')\n"
        "int opt = 1;\n"
        "setsockopt(server_socket, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));\n"
        "\n"
        "// Bind to all interfaces on our port\n"
        "sockaddr_in serverAddr{};\n"
        "serverAddr.sin_family = AF_INET;\n"
        "serverAddr.sin_addr.s_addr = INADDR_ANY;\n"
        "serverAddr.sin_port = htons(port);  // host-to-network byte order\n"
        "bind(server_socket, (struct sockaddr*)&serverAddr, sizeof(serverAddr));\n"
        "\n"
        "// Start listening (backlog of 5 pending connections)\n"
        "listen(server_socket, 5);\n"
        "\n"
        "// Accept loop\n"
        "while (running) {\n"
        "    int client_socket = accept(server_socket, nullptr, nullptr);\n"
        "    // spawn a thread to handle this client...\n"
        "}"
    )

    pdf.sec("Key Networking Concepts")
    pdf.red("htons():", "Converts port from host byte order to network byte order (big-endian). Ensures both sides agree on the byte layout.")
    pdf.red("SO_REUSEADDR:", "When you kill a server, the OS keeps the port in TIME_WAIT for ~60s. This option lets us rebind immediately on restart.")
    pdf.red("Backlog:", "Number of pending connections the OS queues before refusing new ones.")

    # ===== CHAPTER 4: RESP PROTOCOL =====
    pdf.add_page()
    pdf.ch("4. RESP Protocol")

    pdf.p("RESP (REdis Serialization Protocol) is how redis-cli talks to the server. It's a text-based, binary-safe protocol.")

    pdf.sec("Data Types")
    w = [15, 40, 65, 70]
    pdf.tr_w(["Prefix", "Type", "Example", "Meaning"], w, hdr=True)
    pdf.tr_w(["+", "Simple String", "+OK\\r\\n", "Success message"], w)
    pdf.tr_w(["-", "Error", "-Error: key not found\\r\\n", "Error message"], w)
    pdf.tr_w([":", "Integer", ":42\\r\\n", "Numeric result"], w)
    pdf.tr_w(["$", "Bulk String", "$5\\r\\nhello\\r\\n", "Length-prefixed string"], w)
    pdf.tr_w(["$-1", "Null", "$-1\\r\\n", "Key doesn't exist (nil)"], w)
    pdf.tr_w(["*", "Array", "*2\\r\\n$3\\r\\nfoo\\r\\n...", "List of elements"], w)

    pdf.sec("How 'SET mykey myvalue' Is Encoded")
    pdf.code(
        "*3\\r\\n        <-- array of 3 elements\n"
        "$3\\r\\n        <-- first element is 3 bytes\n"
        "SET\\r\\n       <-- \"SET\"\n"
        "$5\\r\\n        <-- second element is 5 bytes\n"
        "mykey\\r\\n     <-- \"mykey\"\n"
        "$7\\r\\n        <-- third element is 7 bytes\n"
        "myvalue\\r\\n   <-- \"myvalue\""
    )

    pdf.sec("Parser Logic")
    pdf.code(
        "std::vector<std::string> parseRespCommand(const std::string &input) {\n"
        "    // If input starts with '*', parse as RESP:\n"
        "    //   1. Read '*N' -> number of elements\n"
        "    //   2. For each element:\n"
        "    //      a. Read '$N' -> length of next string\n"
        "    //      b. Read exactly N bytes -> that's the token\n"
        "    //   3. Return vector of tokens\n"
        "    // Otherwise: fall back to whitespace splitting\n"
        "}"
    )

    # ===== CHAPTER 5: CONCURRENCY =====
    pdf.add_page()
    pdf.ch("5. Concurrency & Thread Safety")

    pdf.sec("Thread-per-Client Model")
    pdf.code(
        "Main Thread\n"
        "    |\n"
        "    +-- accept() -> Client 1 Thread -> recv/process/send loop\n"
        "    +-- accept() -> Client 2 Thread -> recv/process/send loop\n"
        "    +-- accept() -> Client 3 Thread -> recv/process/send loop\n"
        "    +-- ..."
    )

    pdf.sec("Thread Spawning Code")
    pdf.code(
        "while (running) {\n"
        "    int client_socket = accept(server_socket, nullptr, nullptr);\n"
        "    clientThreads.emplace_back([client_socket, &cmdHandler]() {\n"
        "        char buffer[1024] = {0};\n"
        "        while (true) {\n"
        "            memset(buffer, 0, sizeof(buffer));\n"
        "            int bytes = recv(client_socket, buffer, sizeof(buffer)-1, 0);\n"
        "            if (bytes <= 0) break;  // client disconnected\n"
        "            std::string request(buffer, bytes);\n"
        "            std::string response = cmdHandler.processCommand(request);\n"
        "            send(client_socket, response.c_str(), response.size(), 0);\n"
        "        }\n"
        "        close(client_socket);\n"
        "    });\n"
        "}"
    )

    pdf.sec("Lambda Captures")
    pdf.red("client_socket:", "Captured by value -- each thread gets its own copy of the socket fd")
    pdf.red("&cmdHandler:", "Captured by reference -- all threads share the same handler (stateless, safe)")

    pdf.sec("Mutex and Synchronization")
    pdf.p("Multiple threads accessing the same data simultaneously causes race conditions. Solution: std::mutex + std::lock_guard (RAII pattern).")

    pdf.code(
        "bool RedisDatabase::set(const std::string& key, const std::string& value) {\n"
        "    std::lock_guard<std::mutex> lock(db_mutex);  // LOCK acquired\n"
        "    kv_store[key] = value;\n"
        "    return true;\n"
        "}   // lock_guard destructor -> UNLOCK (even if exception thrown)"
    )

    pdf.p("Every single database method starts with std::lock_guard<std::mutex> lock(db_mutex). This means: only one thread modifies the DB at a time, reads are also serialized, and no data corruption is possible.")

    pdf.sec("Thread Safety Matrix")
    w2 = [55, 45, 45, 45]
    pdf.tr_w(["", "Client Thread 1", "Client Thread 2", "Persistence Thread"], w2, hdr=True)
    pdf.tr_w(["Reads kv_store", "Must lock", "Must lock", "Must lock"], w2)
    pdf.tr_w(["Writes kv_store", "Must lock", "Must lock", "Never writes"], w2)
    pdf.tr_w(["Reads running flag", "Via atomic", "Via atomic", "N/A"], w2)

    # ===== CHAPTER 6: DESIGN PATTERNS =====
    pdf.add_page()
    pdf.ch("6. Design Patterns")

    pdf.sec("Singleton Pattern (RedisDatabase)")
    pdf.p("Ensures exactly ONE database instance shared across all threads and all client connections.")

    pdf.code(
        "class RedisDatabase {\n"
        "public:\n"
        "    static RedisDatabase& getInstance();  // only way to get instance\n"
        "private:\n"
        "    RedisDatabase() = default;            // private constructor\n"
        "    ~RedisDatabase() = default;\n"
        "    RedisDatabase(const RedisDatabase&) = delete;            // no copy\n"
        "    RedisDatabase& operator=(const RedisDatabase&) = delete; // no assign\n"
        "};\n"
        "\n"
        "RedisDatabase& RedisDatabase::getInstance() {\n"
        "    static RedisDatabase instance;  // created once, thread-safe in C++11+\n"
        "    return instance;\n"
        "}"
    )

    pdf.red("static local:", "In C++11+, function-local static initialization is guaranteed thread-safe. First thread creates, others wait.")
    pdf.red("delete copy:", "Prevents accidental second copy at compile time.")

    pdf.sec("Signal Handling (Graceful Shutdown)")
    pdf.code(
        "static RedisServer* globalServer = nullptr;\n"
        "\n"
        "void signalHandler(int signum) {\n"
        "    if (globalServer) {\n"
        "        globalServer->shutdown();  // sets running=false, closes socket\n"
        "    }\n"
        "    exit(signum);\n"
        "}\n"
        "\n"
        "// In constructor:\n"
        "signal(SIGINT, signalHandler);   // Ctrl+C\n"
        "signal(SIGTERM, signalHandler);  // kill command"
    )

    pdf.sec("Shutdown Flow")
    pdf.code(
        "1. OS delivers SIGINT (Ctrl+C)\n"
        "2. signalHandler() called\n"
        "3. shutdown() sets running=false, closes server_socket\n"
        "4. accept() returns -1 -> loop exits\n"
        "5. Server joins all client threads\n"
        "6. Server dumps database to disk\n"
        "7. Process exits"
    )

    pdf.red("Global pointer:", "Signal handlers are C-style function pointers -- can't be member functions or lambdas. Global pointer is the bridge.")
    pdf.red("std::atomic<bool>:", "The running flag is read by main thread and written by signal handler. atomic prevents compiler optimizations that could cache stale values.")

    # ===== CHAPTER 7: DATA STRUCTURES =====
    pdf.add_page()
    pdf.ch("7. Data Structures")

    pdf.sec("The Three Stores")
    pdf.code(
        "// KEY-VALUE: string -> string\n"
        "std::unordered_map<std::string, std::string> kv_store;\n"
        "// {\"session:123\" -> \"user_data\", \"config:timeout\" -> \"30\"}\n"
        "\n"
        "// LISTS: key -> ordered sequence of strings\n"
        "std::unordered_map<std::string, std::vector<std::string>> list_store;\n"
        "// {\"job_queue\" -> [\"task1\", \"task2\", \"task3\"]}\n"
        "\n"
        "// HASHES: key -> field/value map (nested hash map)\n"
        "std::unordered_map<std::string, std::unordered_map<std::string, std::string>> hash_store;\n"
        "// {\"user:1000\" -> {\"name\" -> \"Alice\", \"age\" -> \"30\"}}\n"
        "\n"
        "// EXPIRY: key -> deadline\n"
        "std::unordered_map<std::string, std::chrono::steady_clock::time_point> expire_map;"
    )

    pdf.sec("Why unordered_map?")
    pdf.tr(["Operation", "unordered_map", "std::map"], hdr=True)
    pdf.tr(["Lookup", "O(1) average", "O(log n)"])
    pdf.tr(["Insert", "O(1) average", "O(log n)"])
    pdf.tr(["Delete", "O(1) average", "O(log n)"])
    pdf.p("For a cache, O(1) lookup is critical. We don't need sorted keys, so unordered_map (hash table) is the right choice.")

    pdf.sec("Why vector for Lists? (Known Limitation)")
    pdf.p("std::vector gives O(1) access by index and O(1) push_back. However, LPUSH (insert at front) is O(n) because it shifts all elements. A std::deque would be O(1) for both ends.")

    pdf.sec("Expiry Mechanism (Passive)")
    pdf.code(
        "// Setting expiry:\n"
        "expire_map[key] = steady_clock::now() + chrono::seconds(seconds);\n"
        "\n"
        "// Checking (on GET):\n"
        "auto exp_it = expire_map.find(key);\n"
        "if (exp_it != expire_map.end()) {\n"
        "    if (steady_clock::now() > exp_it->second) {\n"
        "        kv_store.erase(key);\n"
        "        list_store.erase(key);\n"
        "        hash_store.erase(key);\n"
        "        expire_map.erase(exp_it);\n"
        "        return false;  // key expired\n"
        "    }\n"
        "}"
    )
    pdf.red("steady_clock:", "Monotonic clock -- never jumps backwards even if system time changes. Essential for reliable timeouts.")

    # ===== CHAPTER 8: CLASS BREAKDOWN =====
    pdf.add_page()
    pdf.ch("8. Class-by-Class Breakdown")

    pdf.sec("RedisServer (19 + 119 lines)")
    pdf.code(
        "class RedisServer {\n"
        "public:\n"
        "    RedisServer(int port);\n"
        "    void run();       // main server loop\n"
        "    void shutdown();  // graceful shutdown\n"
        "private:\n"
        "    int port;\n"
        "    int server_socket;\n"
        "    std::atomic<bool> running;\n"
        "    void setupSignalHandlers();\n"
        "};"
    )

    pdf.sec("RedisDatabase: 26 Methods (80 + 454 lines)")
    pdf.sub("Common (1)")
    w3 = [35, 25, 130]
    pdf.tr_w(["Method", "Return", "Description"], w3, hdr=True)
    pdf.tr_w(["flushAll()", "bool", "Clears ALL stores and expire_map"], w3)

    pdf.sub("Key-Value (7)")
    pdf.tr_w(["Method", "Return", "Description"], w3, hdr=True)
    pdf.tr_w(["set(key, value)", "bool", "Store string value"], w3)
    pdf.tr_w(["get(key, &value)", "bool", "Retrieve value (checks expiry first)"], w3)
    pdf.tr_w(["keys()", "vector", "All keys from all three stores"], w3)
    pdf.tr_w(["type(key)", "string", "\"string\", \"list\", \"hash\", or \"none\""], w3)
    pdf.tr_w(["del(key)", "bool", "Remove from all stores"], w3)
    pdf.tr_w(["expire(key, secs)", "bool", "Set TTL"], w3)
    pdf.tr_w(["rename(old, new)", "bool", "Rename key in whichever store it lives"], w3)

    pdf.sub("List (9)")
    pdf.tr_w(["Method", "Return", "Description"], w3, hdr=True)
    pdf.tr_w(["llen(key)", "int", "List length, -1 if not found"], w3)
    pdf.tr_w(["lpush(key, values)", "int", "Push to front, returns new length"], w3)
    pdf.tr_w(["rpush(key, values)", "int", "Push to back, returns new length"], w3)
    pdf.tr_w(["lpop(key, &value)", "bool", "Remove and return front element"], w3)
    pdf.tr_w(["rpop(key, &value)", "bool", "Remove and return back element"], w3)
    pdf.tr_w(["lrem(key, cnt, val)", "int", "Remove matching elements"], w3)
    pdf.tr_w(["lrange(key,s,e,&r)", "bool", "Get range (supports negative indices)"], w3)
    pdf.tr_w(["lindex(key, idx, &v)", "bool", "Get element by index"], w3)
    pdf.tr_w(["lset(key, idx, val)", "bool", "Set element at index"], w3)

    pdf.add_page()
    pdf.sub("Hash (8)")
    pdf.tr_w(["Method", "Return", "Description"], w3, hdr=True)
    pdf.tr_w(["hset(key, fld, val)", "int", "Set field (1=new, 0=updated, -1=wrong type)"], w3)
    pdf.tr_w(["hget(key, fld, &v)", "bool", "Get field value"], w3)
    pdf.tr_w(["hexists(key, fld)", "bool", "Check if field exists"], w3)
    pdf.tr_w(["hdel(key, fld)", "bool", "Delete field"], w3)
    pdf.tr_w(["hgetall(key)", "vec<pair>", "All field-value pairs"], w3)
    pdf.tr_w(["hkeys(key)", "vector", "All field names"], w3)
    pdf.tr_w(["hvals(key)", "vector", "All field values"], w3)
    pdf.tr_w(["hlen(key)", "int", "Number of fields"], w3)

    pdf.sub("Persistence (2)")
    pdf.tr_w(["Method", "Return", "Description"], w3, hdr=True)
    pdf.tr_w(["dump(filename)", "bool", "Serialize all data to file"], w3)
    pdf.tr_w(["load(filename)", "bool", "Deserialize from file, replacing all data"], w3)

    pdf.sec("Type Safety Across Stores")
    pdf.code(
        "int RedisDatabase::lpush(const std::string& key, ...) {\n"
        "    std::lock_guard<std::mutex> lock(db_mutex);\n"
        "    if (kv_store.count(key) || hash_store.count(key))\n"
        "        return -1;  // WRONGTYPE error\n"
        "    // ...\n"
        "}"
    )
    pdf.p("Prevents SET x \"hello\" then LPUSH x \"oops\" -- returns a type error, just like real Redis.")

    pdf.sec("RedisCommandHandler (12 + 510 lines)")
    pdf.code(
        "std::string processCommand(const std::string& commandLine) {\n"
        "    auto tokens = parseRespCommand(commandLine);\n"
        "    std::string cmd = tokens[0];\n"
        "    std::transform(cmd.begin(), cmd.end(), cmd.begin(), ::toupper);\n"
        "\n"
        "    RedisDatabase& db = RedisDatabase::getInstance();\n"
        "\n"
        "    if      (cmd == \"PING\")  return handlePing(tokens, db);\n"
        "    else if (cmd == \"SET\")   return handleSet(tokens, db);\n"
        "    else if (cmd == \"GET\")   return handleGet(tokens, db);\n"
        "    // ... 24 more commands ...\n"
        "    else return \"-Error: Unsupported command\\r\\n\";\n"
        "}"
    )

    # ===== CHAPTER 9: COMMAND REFERENCE =====
    pdf.add_page()
    pdf.ch("9. Complete Command Reference")

    pdf.sec("Common Commands")
    w4 = [35, 55, 50, 50]
    pdf.tr_w(["Command", "Example", "Response", "Purpose"], w4, hdr=True)
    pdf.tr_w(["PING", "PING", "PONG", "Test connectivity"], w4)
    pdf.tr_w(["ECHO", "ECHO \"hello\"", "\"hello\"", "Echo back message"], w4)
    pdf.tr_w(["FLUSHALL", "FLUSHALL", "OK", "Delete ALL data"], w4)

    pdf.sec("Key/Value Commands")
    pdf.tr_w(["Command", "Example", "Response", "Notes"], w4, hdr=True)
    pdf.tr_w(["SET", "SET k v", "OK", "Store string value"], w4)
    pdf.tr_w(["GET", "GET k", "\"v\" or (nil)", "Checks expiry first"], w4)
    pdf.tr_w(["KEYS", "KEYS *", "1) \"k\"", "Pattern arg accepted, not filtered"], w4)
    pdf.tr_w(["TYPE", "TYPE k", "string/list/hash/none", "Returns data type"], w4)
    pdf.tr_w(["DEL/UNLINK", "DEL k", "(integer) 1 or 0", "Remove from any store"], w4)
    pdf.tr_w(["EXPIRE", "EXPIRE k 10", "(integer) 1", "Set TTL in seconds"], w4)
    pdf.tr_w(["RENAME", "RENAME a b", "OK", "Rename without data loss"], w4)

    pdf.sec("List Commands")
    pdf.tr_w(["Command", "Example", "Response", "Notes"], w4, hdr=True)
    pdf.tr_w(["RPUSH", "RPUSH L a b c", "(integer) 3", "Append to end"], w4)
    pdf.tr_w(["LPUSH", "LPUSH L x", "(integer) 4", "Prepend to front"], w4)
    pdf.tr_w(["LGET", "LGET L", "1) x 2) a ...", "All elements (custom cmd)"], w4)
    pdf.tr_w(["LLEN", "LLEN L", "(integer) 4", "List length"], w4)
    pdf.tr_w(["LPOP", "LPOP L", "\"x\"", "Remove+return first"], w4)
    pdf.tr_w(["RPOP", "RPOP L", "\"c\"", "Remove+return last"], w4)
    pdf.tr_w(["LINDEX", "LINDEX L 0", "\"a\"", "Supports negative indices"], w4)
    pdf.tr_w(["LSET", "LSET L 1 new", "OK", "Replace at index"], w4)
    pdf.tr_w(["LREM", "LREM L 2 x", "(integer) 2", "Remove N occurrences"], w4)
    pdf.tr_w(["LRANGE", "LRANGE L 0 -1", "1) a 2) b", "Range with neg indices"], w4)

    pdf.sec("Hash Commands")
    pdf.tr_w(["Command", "Example", "Response", "Notes"], w4, hdr=True)
    pdf.tr_w(["HSET", "HSET u name A", "(integer) 1", "1=new, 0=updated"], w4)
    pdf.tr_w(["HGET", "HGET u name", "\"A\"", "Single field value"], w4)
    pdf.tr_w(["HEXISTS", "HEXISTS u name", "(integer) 1", "Check field exists"], w4)
    pdf.tr_w(["HDEL", "HDEL u age", "(integer) 1", "Remove field"], w4)
    pdf.tr_w(["HGETALL", "HGETALL u", "name A email ..", "Flat array output"], w4)
    pdf.tr_w(["HKEYS", "HKEYS u", "1) name 2) email", "All field names"], w4)
    pdf.tr_w(["HVALS", "HVALS u", "1) A 2) a@x.com", "All field values"], w4)
    pdf.tr_w(["HLEN", "HLEN u", "(integer) 2", "Field count"], w4)
    pdf.tr_w(["HMSET", "HMSET u k1 v1 k2 v2", "OK", "Multi-set (returns OK)"], w4)

    # ===== CHAPTER 10: PERSISTENCE =====
    pdf.add_page()
    pdf.ch("10. Persistence Format")

    pdf.sec("Dump File Format (dump.my_rdb)")
    pdf.code(
        "K session:123           <-- K = key-value type, then key name\n"
        "user_data               <-- value on next line\n"
        "\n"
        "L job_queue 3           <-- L = list type, key name, element count\n"
        "task1                   <-- 3 list items follow\n"
        "task2\n"
        "task3\n"
        "\n"
        "H user:1000 2           <-- H = hash type, key name, field count\n"
        "name Alice              <-- 2 field-value pairs follow (space-separated)\n"
        "email a@x.com"
    )

    pdf.sec("Dump Algorithm")
    pdf.b("Lock the mutex (no writes during dump)")
    pdf.b("Iterate kv_store -> write 'K <key>\\n<value>\\n'")
    pdf.b("Iterate list_store -> write 'L <key> <count>\\n' then each item")
    pdf.b("Iterate hash_store -> write 'H <key> <count>\\n' then each field-value pair")

    pdf.sec("Load Algorithm")
    pdf.b("Lock the mutex")
    pdf.b("Clear all stores")
    pdf.b("Read line by line")
    pdf.b("First character determines type (K/L/H)")
    pdf.b("Parse key, count, and elements accordingly")

    pdf.sec("When Persistence Happens")
    pdf.tr(["Trigger", "Mechanism"], hdr=True)
    pdf.tr(["Background thread", "Dumps every 300 seconds (5 minutes)"])
    pdf.tr(["On shutdown", "Dumps before process exits (via signal handler)"])
    pdf.tr(["On startup", "Loads from file if it exists"])

    # ===== CHAPTER 11: DATA FLOW =====
    pdf.add_page()
    pdf.ch("11. Complete Data Flow")

    pdf.sec("End-to-End: SET mykey myvalue")
    pdf.code(
        "redis-cli                    Network              Server\n"
        "----------                   -------              ------\n"
        "1. User types:\n"
        "   SET mykey myvalue\n"
        "\n"
        "2. redis-cli encodes         ---------->  3. recv() reads bytes\n"
        "   to RESP:                                  into buffer[1024]\n"
        "   *3\\r\\n$3\\r\\nSET\\r\\n\n"
        "   $5\\r\\nmykey\\r\\n                      4. processCommand()\n"
        "   $7\\r\\nmyvalue\\r\\n                       |\n"
        "                                             +- parseRespCommand()\n"
        "                                             |  -> [\"SET\",\"mykey\",\"myvalue\"]\n"
        "                                             +- cmd = \"SET\" (uppercased)\n"
        "                                             +- handleSet(tokens, db)\n"
        "                                             |  +- db.set(\"mykey\",\"myvalue\")\n"
        "                                             |  |  +- lock_guard locks\n"
        "                                             |  |  +- kv_store[\"mykey\"]=\"myvalue\"\n"
        "                                             |  |  +- lock_guard unlocks\n"
        "                                             |  +- return \"+OK\\r\\n\"\n"
        "                                          5. send() sends \"+OK\\r\\n\"\n"
        "6. redis-cli decodes         <----------\n"
        "   \"+OK\\r\\n\" -> prints OK"
    )

    # ===== CHAPTER 12: BUILD SYSTEM =====
    pdf.sec("Build System (Makefile)")
    pdf.tr(["Flag", "Purpose"], hdr=True)
    pdf.tr(["-std=c++17", "C++17 standard (structured bindings, if constexpr)"])
    pdf.tr(["-Wall", "Enable all compiler warnings"])
    pdf.tr(["-pthread", "Link POSIX threads library"])
    pdf.tr(["-MMD -MP", "Auto-generate dependency files for header changes"])
    pdf.tr(["-O2", "Optimization level 2 (faster executable)"])

    pdf.code(
        "make          # compile and link\n"
        "make clean    # remove build/ and executable\n"
        "make rebuild  # clean + build\n"
        "make run      # build then run"
    )

    # ===== CHAPTER 13: TESTING =====
    pdf.add_page()
    pdf.ch("12. Testing")

    pdf.sec("Automated Test Suite")
    pdf.code(
        "./my_redis_server 6399 &\n"
        "python3 test.py\n"
        "# Runs 38 tests covering all commands via raw TCP + RESP"
    )

    pdf.sec("Manual Testing")
    pdf.code(
        "make run                    # Terminal 1\n"
        "./redis-cli -p 6379        # Terminal 2"
    )

    pdf.sec("Edge Cases to Verify")
    w5 = [50, 60, 80]
    pdf.tr_w(["Test", "Command", "Expected"], w5, hdr=True)
    pdf.tr_w(["GET nonexistent", "GET ghost", "(nil)"], w5)
    pdf.tr_w(["DEL nonexistent", "DEL ghost", "(integer) 0"], w5)
    pdf.tr_w(["Wrong type", "SET x str; LPUSH x val", "Error"], w5)
    pdf.tr_w(["Out of range", "LINDEX L 9999", "(nil)"], w5)
    pdf.tr_w(["Expire then GET", "SET k v; EXPIRE k 1; wait; GET k", "(nil)"], w5)
    pdf.tr_w(["Persistence", "SET data; restart; GET data", "Original value"], w5)

    # ===== CHAPTER 14: LIMITATIONS =====
    pdf.ch("13. Limitations & Future Improvements")

    w6 = [45, 65, 80]
    pdf.tr_w(["Issue", "Impact", "Fix"], w6, hdr=True)
    pdf.tr_w(["Thread-per-client", "Dies at ~10K connections", "Use epoll event loop"], w6)
    pdf.tr_w(["Single global mutex", "All operations serialized", "Sharded/per-key locks or shared_mutex"], w6)
    pdf.tr_w(["LPUSH is O(n)", "Slow for large lists", "Replace vector with deque"], w6)
    pdf.tr_w(["1024-byte buffer", "Large commands truncated", "Dynamic buffer allocation"], w6)
    pdf.tr_w(["Passive expiry only", "Expired keys waste memory", "Background expiry sweep"], w6)
    pdf.tr_w(["No memory limit", "Grows until OOM", "maxmemory + LRU eviction"], w6)
    pdf.tr_w(["KEYS pattern ignored", "Always returns all keys", "Implement glob pattern matching"], w6)
    pdf.tr_w(["No SET EX support", "Can't set value + TTL atomically", "Parse EX/PX options in SET"], w6)

    pdf.sec("Recommended Next Steps")
    pdf.b("1. Replace std::vector with std::deque for lists")
    pdf.b("2. Fix DEL/EXPIRE/RENAME to return integer replies (: not +)")
    pdf.b("3. Add SET key value EX seconds support")
    pdf.b("4. Implement glob pattern matching for KEYS")
    pdf.b("5. Add background expiry thread")
    pdf.b("6. Replace thread-per-client with epoll")
    pdf.b("7. Add LRU eviction with memory cap")
    pdf.b("8. Add PUB/SUB support")

    # ===== CHAPTER 15: GLOSSARY =====
    pdf.add_page()
    pdf.ch("14. Glossary")

    terms = [
        ("TCP", "Transmission Control Protocol -- reliable, ordered byte stream over a network"),
        ("Socket", "OS-level endpoint for network communication"),
        ("RESP", "REdis Serialization Protocol -- the wire format Redis uses"),
        ("Mutex", "Mutual Exclusion -- a lock ensuring one thread accesses a resource at a time"),
        ("RAII", "Resource Acquisition Is Initialization -- cleanup tied to object lifetime"),
        ("Singleton", "Design pattern ensuring exactly one instance of a class exists"),
        ("Thread safety", "Code works correctly when accessed by multiple threads simultaneously"),
        ("TTL", "Time To Live -- seconds until a key expires"),
        ("Atomic", "Operation that completes entirely or not at all, no intermediate state"),
        ("epoll", "Linux kernel mechanism for efficiently monitoring many sockets"),
        ("LRU", "Least Recently Used -- eviction policy removing oldest-accessed items"),
        ("O(1)", "Constant time -- operation speed doesn't depend on data size"),
        ("Race condition", "Bug where behavior depends on unpredictable thread timing"),
        ("Serialization", "Converting in-memory data to a byte stream for storage/transfer"),
        ("Backlog", "Pending connections the OS queues before refusing new ones"),
        ("SIGINT", "Signal sent by OS when user presses Ctrl+C"),
        ("Detached thread", "Thread that runs independently -- parent doesn't wait for it"),
        ("Wire protocol", "Exact format of bytes exchanged between client and server"),
    ]
    for term, defn in terms:
        pdf.red(f"{term}:", defn)

    # Save
    out = "docs/MyRedis_Technical_Deep_Dive.pdf"
    pdf.output(out)
    print(f"Generated: {out} ({pdf.page_no()} pages)")


if __name__ == "__main__":
    build()
