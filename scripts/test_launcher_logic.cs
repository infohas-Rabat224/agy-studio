using System;
using System.Diagnostics;
using System.IO;
using System.Net;

class TestLogic {
    static void Main() {
        Console.WriteLine("1. Testing CheckBridgeHealth(8001)...");
        try {
            var req = (HttpWebRequest)WebRequest.Create("http://127.0.0.1:8001/api/bridge/status");
            req.Proxy = null;
            req.Timeout = 800;
            req.ReadWriteTimeout = 800;
            req.Method = "GET";
            Console.WriteLine("2. Calling GetResponse...");
            using (var resp = (HttpWebResponse)req.GetResponse()) {
                Console.WriteLine("3. Status: " + resp.StatusCode);
            }
        } catch (Exception ex) {
            Console.WriteLine("Caught expected: " + ex.Message);
        }
        Console.WriteLine("4. Done CheckBridgeHealth test.");
    }
}
