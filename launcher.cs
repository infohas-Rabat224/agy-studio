using System;
using System.Diagnostics;
using System.IO;
using System.Net;
using System.Net.NetworkInformation;
using System.Threading;

class Program {
    static void Log(string msg) {
        string formatted = string.Format("[{0}] {1}", DateTime.UtcNow.ToString("o"), msg);
        try { Console.WriteLine(formatted); } catch {}
        try {
            string baseDir = AppDomain.CurrentDomain.BaseDirectory;
            string dataDir = Path.Combine(baseDir, "data");
            if (!Directory.Exists(dataDir)) Directory.CreateDirectory(dataDir);
            string logFile = Path.Combine(dataDir, "launcher.log");
            for (int r = 0; r < 10; r++) {
                try {
                    using (var fs = new FileStream(logFile, FileMode.Append, FileAccess.Write, FileShare.ReadWrite))
                    using (var sw = new StreamWriter(fs)) {
                        sw.WriteLine(formatted);
                    }
                    break;
                } catch {
                    Thread.Sleep(30);
                }
            }
        } catch {}
    }

    static string SafeGetId(Process p) {
        if (p == null) return "null";
        try {
            return p.Id.ToString();
        } catch {
            return "running";
        }
    }

    [STAThread]
    static void Main() {
        try {
            Log("=================================================");
            Log("Launcher starting (Agy Studio Production Launcher v2.0)...");
            string baseDir = AppDomain.CurrentDomain.BaseDirectory;
            if (baseDir.EndsWith("\\") || baseDir.EndsWith("/")) {
                baseDir = baseDir.Substring(0, baseDir.Length - 1);
            }
            Log("BaseDir: " + baseDir);

            int bridgePort = 8001;

            // 1. Recover stale picker processes if bridge is not healthy (Section 7 & 18)
            bool isBridgeHealthy = CheckBridgeHealth(bridgePort);
            Log("Initial isBridgeHealthy(8001): " + isBridgeHealthy);
            if (!isBridgeHealthy) {
                CleanupStalePickerProcesses();
            }

            // 2. Start backend server (port 8000) if not running (Section 22)
            bool isServerRunning = CheckPort(8000);
            Log("isServerRunning: " + isServerRunning);

            Process srvProc = null;
            if (!isServerRunning) {
                string uvExe = DiscoverUv(baseDir);
                string serverPy = Path.Combine(baseDir, "backend", "server.py");
                Log("uvExe: " + uvExe + " (exists: " + File.Exists(uvExe) + ")");
                Log("serverPy: " + serverPy + " (exists: " + File.Exists(serverPy) + ")");

                ProcessStartInfo srv = new ProcessStartInfo();
                srv.FileName = uvExe;
                srv.Arguments = "run --with fastapi --with uvicorn --with websockets --with pydantic --with python-docx --with python-multipart --with pypdf --with openpyxl --with python-pptx --with pillow --with playwright python \"" + serverPy + "\"";
                srv.WorkingDirectory = baseDir;
                srv.WindowStyle = ProcessWindowStyle.Hidden;
                srv.UseShellExecute = true;
                try {
                    srvProc = Process.Start(srv);
                    Log("Started server PID: " + SafeGetId(srvProc));
                } catch (Exception ex) {
                    Log("Error starting server: " + ex.ToString());
                }

                // Wait for port 8000 (up to 40 seconds for agent discovery)
                for (int i = 0; i < 80; i++) {
                    if (CheckPort(8000)) {
                        Log("Port 8000 is ready after " + (i * 500) + "ms");
                        break;
                    }
                    Thread.Sleep(500);
                }
            }

            // 3. Start native picker bridge (port 8001) if not healthy (Section 22)
            isBridgeHealthy = CheckBridgeHealth(bridgePort);
            string pickerExe = Path.Combine(baseDir, "AgyStudioFolderPicker.exe");
            Log("pickerExe: " + pickerExe + " (exists: " + File.Exists(pickerExe) + ")");

            if (isBridgeHealthy) {
                Log("Bridge port " + bridgePort + " is already healthy and verified.");
            } else if (File.Exists(pickerExe)) {
                try {
                    ProcessStartInfo br = new ProcessStartInfo();
                    br.FileName = pickerExe;
                    br.Arguments = "--bridge " + bridgePort;
                    br.WorkingDirectory = baseDir;
                    br.WindowStyle = ProcessWindowStyle.Hidden;
                    br.UseShellExecute = true;
                    var proc = Process.Start(br);
                    Log("Started picker PID: " + SafeGetId(proc));
                } catch (Exception ex) {
                    Log("Error starting picker: " + ex.ToString());
                }

                // Wait for bridge health endpoint (Section 4 & 22)
                for (int i = 0; i < 20; i++) {
                    if (CheckBridgeHealth(bridgePort)) {
                        Log("Bridge port " + bridgePort + " health verified after " + (i * 250) + "ms");
                        isBridgeHealthy = true;
                        break;
                    }
                    Thread.Sleep(250);
                }
            }

            // 4. Start Chrome or Edge in app mode (Section 22)
            string chrome = DiscoverChrome();
            Log("Chrome: " + chrome);
            if (!string.IsNullOrEmpty(chrome) && File.Exists(chrome)) {
                ProcessStartInfo appInfo = new ProcessStartInfo();
                appInfo.FileName = chrome;
                appInfo.Arguments = "--app=http://127.0.0.1:8000";
                appInfo.UseShellExecute = true;
                try {
                    Process.Start(appInfo);
                    Log("Started Chrome in app mode");
                } catch (Exception ex) {
                    Log("Error starting Chrome: " + ex.ToString());
                }
            } else {
                string edge = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86), "Microsoft", "Edge", "Application", "msedge.exe");
                if (!File.Exists(edge)) {
                    edge = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles), "Microsoft", "Edge", "Application", "msedge.exe");
                }
                if (File.Exists(edge)) {
                    ProcessStartInfo edgeInfo = new ProcessStartInfo();
                    edgeInfo.FileName = edge;
                    edgeInfo.Arguments = "--app=http://127.0.0.1:8000";
                    edgeInfo.UseShellExecute = true;
                    Process.Start(edgeInfo);
                    Log("Started Edge in app mode");
                } else {
                    Process.Start("http://127.0.0.1:8000");
                    Log("Started default browser");
                }
            }
            Log("Launcher entering session monitoring loop...");
            while (CheckPort(8000)) {
                Thread.Sleep(1000);
            }
            Log("AgyStudio.exe exiting gracefully.");
        } catch (Exception fatal) {
            Log("FATAL LAUNCHER ERROR: " + fatal.ToString());
        }
    }

    static bool CheckBridgeHealth(int port) {
        if (!CheckPort(port)) return false;
        try {
            var req = (HttpWebRequest)WebRequest.Create("http://127.0.0.1:" + port + "/api/bridge/status");
            req.Proxy = null;
            req.Timeout = 800;
            req.ReadWriteTimeout = 800;
            req.Method = "GET";
            using (var resp = (HttpWebResponse)req.GetResponse()) {
                if (resp.StatusCode == HttpStatusCode.OK) {
                    using (var sr = new StreamReader(resp.GetResponseStream())) {
                        string txt = sr.ReadToEnd();
                        return txt.Contains("\"status\":\"ok\"") && txt.Contains("AgyStudioFolderPicker");
                    }
                }
            }
        } catch {}
        return false;
    }

    static void CleanupStalePickerProcesses() {
        try {
            foreach (var p in Process.GetProcessesByName("AgyStudioFolderPicker")) {
                try {
                    Log("Terminating stale picker PID: " + p.Id);
                    p.Kill();
                    p.WaitForExit(1000);
                } catch {}
            }
        } catch {}
    }

    static bool CheckPort(int port) {
        try {
            var ipGlobal = IPGlobalProperties.GetIPGlobalProperties();
            var endpoints = ipGlobal.GetActiveTcpListeners();
            for (int i = 0; i < endpoints.Length; i++) {
                if (endpoints[i].Port == port) return true;
            }
        } catch {}
        return false;
    }

    static string DiscoverUv(string baseDir) {
        string localAppData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
        string[] candidates = new string[] {
            Path.Combine(baseDir, "runtime", "uv.exe"),
            Path.Combine(localAppData, "hermes", "bin", "uv.exe"),
            Path.Combine(localAppData, "uv", "uv.exe"),
            Path.Combine(localAppData, "Programs", "astral", "uv", "uv.exe")
        };
        foreach (var c in candidates) {
            if (File.Exists(c)) return c;
        }
        return "uv.exe";
    }

    static string DiscoverChrome() {
        string[] candidates = new string[] {
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles), "Google", "Chrome", "Application", "chrome.exe"),
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86), "Google", "Chrome", "Application", "chrome.exe"),
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Google", "Chrome", "Application", "chrome.exe")
        };
        foreach (var c in candidates) {
            if (File.Exists(c)) return c;
        }
        return null;
    }
}
