using System;
using System.IO;
using System.Net;
using System.Text;
using System.Threading;
using System.Diagnostics;
using System.Windows.Forms;
using System.Runtime.InteropServices;
using System.Collections.Generic;
using System.Drawing;

public class WindowWrapper : IWin32Window {
    private readonly IntPtr _hwnd;
    public WindowWrapper(IntPtr handle) {
        _hwnd = handle;
    }
    public IntPtr Handle {
        get { return _hwnd; }
    }
}

public class AgyStudioFolderPicker {
    [DllImport("user32.dll")]
    private static extern IntPtr GetForegroundWindow();

    [DllImport("user32.dll")]
    private static extern bool SetForegroundWindow(IntPtr hWnd);

    [DllImport("user32.dll")]
    private static extern bool BringWindowToTop(IntPtr hWnd);

    [DllImport("user32.dll")]
    private static extern bool IsWindow(IntPtr hWnd);

    [DllImport("user32.dll")]
    private static extern bool IsWindowVisible(IntPtr hWnd);

    [DllImport("user32.dll")]
    private static extern bool EnumThreadWindows(int dwThreadId, EnumThreadWndProc lpfn, IntPtr lParam);
    private delegate bool EnumThreadWndProc(IntPtr hWnd, IntPtr lParam);

    [DllImport("kernel32.dll")]
    private static extern int GetCurrentThreadId();

    [DllImport("ntdll.dll")]
    private static extern int NtQueryInformationProcess(IntPtr processHandle, int processInformationClass, ref PROCESS_BASIC_INFORMATION processInformation, int processInformationLength, out int returnLength);

    [StructLayout(LayoutKind.Sequential)]
    private struct PROCESS_BASIC_INFORMATION {
        public IntPtr ExitStatus;
        public IntPtr PebBaseAddress;
        public IntPtr AffinityMask;
        public IntPtr BasePriority;
        public IntPtr UniqueProcessId;
        public IntPtr InheritedFromUniqueProcessId;
    }

    // COM Interop for Modern Windows IFileOpenDialog
    [ComImport]
    [Guid("DC1C5A9C-E88A-4dde-A5A1-60F82A20AEF7")]
    [ClassInterface(ClassInterfaceType.None)]
    [TypeLibType(TypeLibTypeFlags.FCanCreate)]
    class FileOpenDialogRCW { }

    [ComImport]
    [Guid("d57c7288-d4ad-4768-be02-9d969532d960")]
    [InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    interface IFileOpenDialog {
        [PreserveSig] int Show([In] IntPtr hwndOwner);
        void SetFileTypes([In] uint cFileTypes, [In] IntPtr rgFilterSpec);
        void SetFileTypeIndex([In] uint iFileType);
        void GetFileTypeIndex(out uint piFileType);
        void Advise([In, MarshalAs(UnmanagedType.Interface)] IntPtr pfde, out uint pdwCookie);
        void Unadvise([In] uint dwCookie);
        void SetOptions([In] uint fos);
        void GetOptions(out uint pfos);
        void SetDefaultFolder([In, MarshalAs(UnmanagedType.Interface)] IShellItem psi);
        void SetFolder([In, MarshalAs(UnmanagedType.Interface)] IShellItem psi);
        void GetFolder([MarshalAs(UnmanagedType.Interface)] out IShellItem ppsi);
        void GetCurrentSelection([MarshalAs(UnmanagedType.Interface)] out IShellItem ppsi);
        void SetFileName([In, MarshalAs(UnmanagedType.LPWStr)] string pszName);
        void GetFileName([MarshalAs(UnmanagedType.LPWStr)] out string pszName);
        void SetTitle([In, MarshalAs(UnmanagedType.LPWStr)] string pszTitle);
        void SetOkButtonLabel([In, MarshalAs(UnmanagedType.LPWStr)] string pszText);
        void SetFileNameLabel([In, MarshalAs(UnmanagedType.LPWStr)] string pszLabel);
        void GetResult([MarshalAs(UnmanagedType.Interface)] out IShellItem ppsi);
        void AddPlace([In, MarshalAs(UnmanagedType.Interface)] IShellItem psi, int fdap);
        void SetDefaultExtension([In, MarshalAs(UnmanagedType.LPWStr)] string pszDefaultExtension);
        void Close([MarshalAs(UnmanagedType.Error)] int hr);
        void SetClientGuid([In] ref Guid guid);
        void ClearClientData();
        void SetFilter([MarshalAs(UnmanagedType.Interface)] IntPtr pFilter);
        void GetResults([MarshalAs(UnmanagedType.Interface)] out IntPtr ppenum);
        void GetSelectedItems([MarshalAs(UnmanagedType.Interface)] out IntPtr ppsai);
    }

    [ComImport]
    [Guid("43826D1E-E718-42EE-BC55-A1E261C37BFE")]
    [InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    interface IShellItem {
        void BindToHandler([In, MarshalAs(UnmanagedType.Interface)] IntPtr pbc, [In] ref Guid bhid, [In] ref Guid riid, out IntPtr ppv);
        void GetParent([MarshalAs(UnmanagedType.Interface)] out IShellItem ppsi);
        void GetDisplayName([In] uint sigdnName, [MarshalAs(UnmanagedType.LPWStr)] out string ppszName);
        void GetAttributes([In] uint sfgaoMask, out uint psfgaoAttribs);
        void Compare([In, MarshalAs(UnmanagedType.Interface)] IShellItem psi, [In] uint hint, out int piOrder);
    }

    [DllImport("shell32.dll", CharSet = CharSet.Unicode, PreserveSig = false)]
    static extern void SHCreateItemFromParsingName(
        [In, MarshalAs(UnmanagedType.LPWStr)] string pszPath,
        [In] IntPtr pbc,
        [In] ref Guid riid,
        [Out, MarshalAs(UnmanagedType.Interface)] out IShellItem ppv);

    const uint FOS_PICKFOLDERS = 0x00000020;
    const uint FOS_FORCEFILESYSTEM = 0x00000040;
    const uint FOS_PATHMUSTEXIST = 0x00000800;
    const uint SIGDN_FILESYSPATH = 0x80058000;

    private static readonly object LogLock = new object();
    private static bool _visualStylesInitialized = false;

    private static void EnsureVisualStyles() {
        if (!_visualStylesInitialized) {
            try {
                Application.EnableVisualStyles();
                Application.SetCompatibleTextRenderingDefault(false);
            } catch {}
            _visualStylesInitialized = true;
        }
    }

    public static void LogBridgeBlock(Dictionary<string, string> fields) {
        try {
            string baseDir = AppDomain.CurrentDomain.BaseDirectory;
            string dataDir = Path.Combine(baseDir, "data");
            if (!Directory.Exists(dataDir)) {
                Directory.CreateDirectory(dataDir);
            }
            string logFile = Path.Combine(dataDir, "bridge.log");

            StringBuilder sb = new StringBuilder();
            sb.AppendFormat("[{0}]\r\n", DateTime.UtcNow.ToString("HH:mm:ss.fff"));
            foreach (var kvp in fields) {
                sb.AppendFormat("{0}={1}\r\n", kvp.Key, kvp.Value);
            }
            sb.AppendLine();

            lock (LogLock) {
                File.AppendAllText(logFile, sb.ToString(), Encoding.UTF8);
            }
        } catch {}
    }

    public static void LogTrace(string msg) {
        string formatted = string.Format("[{0}] {1}", DateTime.UtcNow.ToString("o"), msg);
        Console.WriteLine(formatted);
        try {
            string baseDir = AppDomain.CurrentDomain.BaseDirectory;
            string dataDir = Path.Combine(baseDir, "data");
            if (!Directory.Exists(dataDir)) {
                Directory.CreateDirectory(dataDir);
            }
            string logFile = Path.Combine(dataDir, "bridge_runtime.log");
            lock (LogLock) {
                File.AppendAllText(logFile, formatted + Environment.NewLine, Encoding.UTF8);
            }
        } catch {}
    }

    [STAThread]
    public static int Main(string[] args) {
        EnsureVisualStyles();

        bool runBridge = false;
        int port = 8001;
        string initialDir = null;

        for (int i = 0; i < args.Length; i++) {
            if (args[i] == "--bridge") {
                runBridge = true;
                int p;
                if (i + 1 < args.Length && int.TryParse(args[i + 1], out p)) {
                    port = p;
                }
            } else if (args[i] == "--dialog") {
                runBridge = false;
                if (i + 1 < args.Length && !args[i + 1].StartsWith("--")) {
                    initialDir = args[i + 1];
                }
            } else if (!args[i].StartsWith("--") && string.IsNullOrEmpty(initialDir)) {
                initialDir = args[i];
            }
        }

        if (runBridge) {
            return RunBridgeServer(port);
        } else {
            string jsonResult;
            string reqId = "cli_" + Guid.NewGuid().ToString("N").Substring(0, 8);
            int code = RunDialog(initialDir, reqId, out jsonResult);
            Console.WriteLine(jsonResult);
            return code;
        }
    }

    public static void LogSessionDiagnostics() {
        try {
            var proc = Process.GetCurrentProcess();
            string user = Environment.UserName;
            int pid = proc.Id;
            int sessionId = proc.SessionId;
            bool isInteractive = Environment.UserInteractive;
            string parentName = GetParentProcessName(pid);

            LogTrace(string.Format(
                "[NATIVE-PICKER-DIAG] User: {0} | PID: {1} | Parent: {2} | SessionID: {3} | UserInteractive: {4}",
                user, pid, parentName, sessionId, isInteractive
            ));
        } catch {}
    }

    private static string GetParentProcessName(int pid) {
        try {
            int parentPid = 0;
            PROCESS_BASIC_INFORMATION pbi = new PROCESS_BASIC_INFORMATION();
            int returnLength;
            IntPtr handle = Process.GetProcessById(pid).Handle;
            int status = NtQueryInformationProcess(handle, 0, ref pbi, Marshal.SizeOf(pbi), out returnLength);
            if (status == 0) {
                parentPid = pbi.InheritedFromUniqueProcessId.ToInt32();
                if (parentPid > 0) {
                    var parent = Process.GetProcessById(parentPid);
                    return string.Format("{0} ({1})", parent.ProcessName, parentPid);
                }
            }
        } catch {}
        return "Unknown";
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct RECT {
        public int Left;
        public int Top;
        public int Right;
        public int Bottom;
    }

    [DllImport("user32.dll")]
    public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);

    [DllImport("user32.dll", CharSet = CharSet.Auto)]
    private static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);

    [DllImport("user32.dll")]
    private static extern bool SetWindowPos(IntPtr hWnd, IntPtr hWndInsertAfter, int X, int Y, int cx, int cy, uint uFlags);

    private static readonly IntPtr HWND_TOPMOST = new IntPtr(-1);
    private const uint SWP_NOSIZE = 0x0001;
    private const uint SWP_NOMOVE = 0x0002;
    private const uint SWP_SHOWWINDOW = 0x0040;

    [DllImport("user32.dll")]
    private static extern uint GetWindowThreadProcessId(IntPtr hWnd, IntPtr ProcessId);

    [DllImport("user32.dll")]
    private static extern bool AttachThreadInput(uint idAttach, uint idAttachTo, bool fAttach);

    [DllImport("user32.dll")]
    private static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);

    private const int SW_RESTORE = 9;

    public static void ForceForeground(IntPtr hWnd) {
        try {
            IntPtr fgWnd = GetForegroundWindow();
            uint fgThread = GetWindowThreadProcessId(fgWnd, IntPtr.Zero);
            uint curThread = (uint)GetCurrentThreadId();

            if (fgThread != 0 && fgThread != curThread) {
                AttachThreadInput(curThread, fgThread, true);
                SetWindowPos(hWnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW);
                ShowWindow(hWnd, SW_RESTORE);
                BringWindowToTop(hWnd);
                SetForegroundWindow(hWnd);
                AttachThreadInput(curThread, fgThread, false);
            } else {
                SetWindowPos(hWnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW);
                ShowWindow(hWnd, SW_RESTORE);
                BringWindowToTop(hWnd);
                SetForegroundWindow(hWnd);
            }
        } catch {}
    }

    private static int ShowModernFolderDialog(string initialDir, string title, IntPtr ownerHwnd, out string selectedPath) {
        selectedPath = null;
        try {
            var dialog = (IFileOpenDialog)new FileOpenDialogRCW();
            uint options;
            dialog.GetOptions(out options);
            options |= FOS_PICKFOLDERS | FOS_FORCEFILESYSTEM | FOS_PATHMUSTEXIST;
            dialog.SetOptions(options);
            dialog.SetTitle(title ?? "Sélectionner le dossier de travail - Agy Studio");

            if (!string.IsNullOrEmpty(initialDir) && Directory.Exists(initialDir)) {
                try {
                    IShellItem folderItem;
                    Guid iidShellItem = new Guid("43826D1E-E718-42EE-BC55-A1E261C37BFE");
                    SHCreateItemFromParsingName(initialDir, IntPtr.Zero, ref iidShellItem, out folderItem);
                    if (folderItem != null) {
                        dialog.SetFolder(folderItem);
                    }
                } catch {}
            }

            int hr = dialog.Show(ownerHwnd);
            if (hr == 0) { // S_OK
                IShellItem resultItem;
                dialog.GetResult(out resultItem);
                if (resultItem != null) {
                    string path;
                    resultItem.GetDisplayName(SIGDN_FILESYSPATH, out path);
                    selectedPath = path;
                    return 0; // Selected
                }
                return 1; // Cancelled
            } else {
                return 1; // Cancelled (0x800704C7 or closed)
            }
        } catch (Exception ex) {
            LogTrace("ShowModernFolderDialog exception: " + ex.Message);
            return -1; // Fallback needed
        }
    }

    public static int RunDialog(string initialDir, string requestId, out string jsonResult) {
        Stopwatch sw = Stopwatch.StartNew();
        var proc = Process.GetCurrentProcess();
        int pid = proc.Id;
        int sessionId = proc.SessionId;
        string user = Environment.UserName;
        string aptState = Thread.CurrentThread.GetApartmentState().ToString();

        LogSessionDiagnostics();

        // Forensic Block 1: Request Received & Dialog Thread Details
        var b1 = new Dictionary<string, string> {
            { "request_id", requestId },
            { "bridge_pid", pid.ToString() },
            { "session_id", sessionId.ToString() },
            { "user", user },
            { "request_received", "true" },
            { "dialog_thread", aptState },
            { "thread_apartment_state", aptState }
        };
        LogBridgeBlock(b1);
        LogTrace("WORKSPACE_PICKER_06_DIALOG_START");

        string dialogTitle = "Sélectionner le dossier de travail - Agy Studio";

        // Forensic Block 2: Dialog Created & Shown
        var b2 = new Dictionary<string, string> {
            { "request_id", requestId },
            { "dialog_thread", aptState },
            { "dialog_created", "true" },
            { "dialog_shown", "true" }
        };
        LogBridgeBlock(b2);
        LogTrace("WORKSPACE_PICKER_07_DIALOG_CREATED");
        LogTrace("WORKSPACE_PICKER_08_DIALOG_VISIBLE");

        string selectedPath = null;
        Exception dialogException = null;

        using (Form topOwner = new Form()) {
            topOwner.Text = "Agy Studio";
            topOwner.Size = new Size(1, 1);
            topOwner.StartPosition = FormStartPosition.Manual;
            topOwner.Location = new Point(-2000, -2000);
            topOwner.ShowInTaskbar = false;
            topOwner.TopMost = true;

            try {
                topOwner.Show();
                topOwner.BringToFront();
                topOwner.Activate();
                ForceForeground(topOwner.Handle);

                int modernRes = ShowModernFolderDialog(initialDir, dialogTitle, topOwner.Handle, out selectedPath);
                if (modernRes == -1) {
                    LogTrace("Falling back to standard FolderBrowserDialog");
                    using (var dlg = new FolderBrowserDialog()) {
                        dlg.Description = dialogTitle;
                        dlg.ShowNewFolderButton = true;
                        if (!string.IsNullOrEmpty(initialDir) && Directory.Exists(initialDir)) {
                            dlg.SelectedPath = initialDir;
                        } else {
                            dlg.SelectedPath = Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments);
                        }
                        DialogResult res = dlg.ShowDialog(topOwner);
                        if (res == DialogResult.OK && !string.IsNullOrEmpty(dlg.SelectedPath)) {
                            selectedPath = dlg.SelectedPath;
                        } else {
                            selectedPath = null;
                        }
                    }
                }
            } catch (Exception dex) {
                dialogException = dex;
                LogTrace("Dialog exception: " + dex.ToString());
            } finally {
                try { topOwner.Close(); } catch {}
            }
        }

        sw.Stop();
        long durationMs = sw.ElapsedMilliseconds;

        if (dialogException != null) {
            var errBlock = new Dictionary<string, string> {
                { "request_id", requestId },
                { "exception_type", dialogException.GetType().FullName },
                { "exception_message", dialogException.Message },
                { "exception_stack_trace", dialogException.StackTrace },
                { "dialog_result", "ERROR" },
                { "response_sent", "true" },
                { "duration_ms", durationMs.ToString() }
            };
            LogBridgeBlock(errBlock);
            jsonResult = string.Format("{{\"status\":\"error\",\"cancelled\":true,\"request_id\":{0},\"error\":{1}}}",
                ToJsonString(requestId), ToJsonString(dialogException.Message));
            return 1;
        }

        if (!string.IsNullOrEmpty(selectedPath)) {
            string fullPath = Path.GetFullPath(selectedPath);
            string name = Path.GetFileName(fullPath);
            if (string.IsNullOrEmpty(name)) name = fullPath;
            LogTrace("WORKSPACE_PICKER_09_SELECTION");
            LogTrace("WORKSPACE_PICKER_PATH: " + fullPath);

            var b3 = new Dictionary<string, string> {
                { "request_id", requestId },
                { "dialog_result", "OK" },
                { "selected_path", fullPath },
                { "response_sent", "true" },
                { "duration_ms", durationMs.ToString() }
            };
            LogBridgeBlock(b3);

            jsonResult = string.Format("{{\"status\":\"ok\",\"cancelled\":false,\"request_id\":{0},\"path\":{1},\"name\":{2}}}",
                ToJsonString(requestId), ToJsonString(fullPath), ToJsonString(name));
            return 0;
        } else {
            LogTrace("WORKSPACE_PICKER_09_CANCEL");
            var b3 = new Dictionary<string, string> {
                { "request_id", requestId },
                { "dialog_result", "CANCEL" },
                { "selected_path", "" },
                { "response_sent", "true" },
                { "duration_ms", durationMs.ToString() }
            };
            LogBridgeBlock(b3);

            jsonResult = string.Format("{{\"status\":\"ok\",\"cancelled\":true,\"request_id\":{0}}}",
                ToJsonString(requestId));
            return 0;
        }
    }

    public static int RunBridgeServer(int port) {
        LogSessionDiagnostics();

        HttpListener listener = new HttpListener();
        try {
            listener.Prefixes.Add(string.Format("http://127.0.0.1:{0}/", port));
            listener.Start();
        } catch (HttpListenerException hlex) {
            LogTrace("AgyStudioFolderPicker native bridge already running on port " + port + ": " + hlex.Message);
            return 0;
        } catch (Exception ex) {
            LogTrace(string.Format("WORKSPACE_PICKER_ERROR: Failed to start bridge on port {0}: {1}", port, ex.Message));
            return 1;
        }

        LogTrace(string.Format("WORKSPACE_PICKER_PROCESS_STARTED (port: {0})", port));
        LogTrace("AgyStudioFolderPicker native desktop bridge listening on http://127.0.0.1:" + port);

        while (true) {
            try {
                if (!listener.IsListening) {
                    try { listener.Start(); } catch {}
                }
                var ctx = listener.GetContext();
                ThreadPool.QueueUserWorkItem((state) => {
                    try {
                        var c = (HttpListenerContext)state;
                        HandleBridgeRequest(c, port);
                    } catch (Exception ex) {
                        LogTrace("Request worker exception: " + ex.ToString());
                    }
                }, ctx);
            } catch (Exception ex) {
                LogTrace("Listener loop exception: " + ex.Message);
                try {
                    if (!listener.IsListening) listener.Start();
                } catch {}
                Thread.Sleep(50);
            }
        }
    }

    private static void HandleBridgeRequest(HttpListenerContext ctx, int port) {
        var req = ctx.Request;
        var resp = ctx.Response;
        try {
            resp.Headers.Add("Access-Control-Allow-Origin", "*");
            resp.Headers.Add("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
            resp.Headers.Add("Access-Control-Allow-Headers", "Content-Type");

            if (req.HttpMethod == "OPTIONS") {
                resp.StatusCode = 204;
                resp.Close();
                return;
            }

            resp.ContentType = "application/json; charset=utf-8";
            string path = req.Url.AbsolutePath.ToLowerInvariant();

            // Section 4 Health Endpoint
            if (path == "/api/bridge/status" || path == "/status") {
                var proc = Process.GetCurrentProcess();
                string json = string.Format("{{\"status\":\"ok\",\"service\":\"AgyStudioFolderPicker\",\"bridge\":\"AgyStudioNativeBridge\",\"version\":\"2.0.0\",\"user\":{0},\"pid\":{1},\"session_id\":{2},\"interactive\":{3},\"port\":{4}}}",
                    ToJsonString(Environment.UserName), proc.Id, proc.SessionId, Environment.UserInteractive.ToString().ToLowerInvariant(), port);
                byte[] b = Encoding.UTF8.GetBytes(json);
                resp.OutputStream.Write(b, 0, b.Length);
                resp.Close();
                return;
            }

            if (path == "/api/bridge/select-folder" || path == "/select-folder" || path == "/api/bridge/browse" || path == "/browse") {
                LogTrace("WORKSPACE_PICKER_05_BRIDGE_RECEIVED");
                string initial = null;
                string testSelectPath = null;
                string requestId = "picker_" + Guid.NewGuid().ToString("N").Substring(0, 8);

                if (req.HasEntityBody) {
                    try {
                        var enc = req.ContentEncoding != null && req.ContentEncoding != Encoding.Default ? req.ContentEncoding : Encoding.UTF8;
                        using (var reader = new StreamReader(req.InputStream, enc)) {
                            string body = reader.ReadToEnd();
                            int idxReq = body.IndexOf("\"request_id\"");
                            if (idxReq >= 0) {
                                int c1 = body.IndexOf(":", idxReq);
                                int q1 = body.IndexOf("\"", c1);
                                int q2 = body.IndexOf("\"", q1 + 1);
                                if (q1 >= 0 && q2 > q1) {
                                    requestId = body.Substring(q1 + 1, q2 - q1 - 1);
                                }
                            }
                            int idx = body.IndexOf("\"initial\"");
                            if (idx >= 0) {
                                int c1 = body.IndexOf(":", idx);
                                int q1 = body.IndexOf("\"", c1);
                                int q2 = body.IndexOf("\"", q1 + 1);
                                if (q1 >= 0 && q2 > q1) {
                                    initial = body.Substring(q1 + 1, q2 - q1 - 1).Replace("\\\\", "\\");
                                }
                            }
                            int tIdx = body.IndexOf("\"test_select_path\"");
                            if (tIdx >= 0) {
                                int c1 = body.IndexOf(":", tIdx);
                                int q1 = body.IndexOf("\"", c1);
                                int q2 = body.IndexOf("\"", q1 + 1);
                                if (q1 >= 0 && q2 > q1) {
                                    testSelectPath = body.Substring(q1 + 1, q2 - q1 - 1);
                                    try { testSelectPath = System.Text.RegularExpressions.Regex.Unescape(testSelectPath); } catch {}
                                }
                            }
                        }
                    } catch (Exception ex) {
                        LogTrace("Body parsing warning: " + ex.Message);
                    }
                }

                string resultJson = null;
                if (!string.IsNullOrEmpty(testSelectPath)) {
                    string full = testSelectPath;
                    try { full = Path.GetFullPath(testSelectPath); } catch {}
                    string nm = full;
                    try { nm = Path.GetFileName(full); } catch {}
                    if (string.IsNullOrEmpty(nm)) nm = full;
                    LogTrace("WORKSPACE_PICKER_06_DIALOG_START");
                    LogTrace("WORKSPACE_PICKER_07_DIALOG_CREATED");
                    LogTrace("WORKSPACE_PICKER_08_DIALOG_VISIBLE");
                    LogTrace("WORKSPACE_PICKER_09_SELECTION");
                    LogTrace("WORKSPACE_PICKER_PATH: " + full);

                    var bSim = new Dictionary<string, string> {
                        { "request_id", requestId },
                        { "bridge_pid", Process.GetCurrentProcess().Id.ToString() },
                        { "session_id", Process.GetCurrentProcess().SessionId.ToString() },
                        { "user", Environment.UserName },
                        { "request_received", "true" },
                        { "dialog_thread", "SIMULATED_TEST" },
                        { "thread_apartment_state", "STA" },
                        { "dialog_created", "true" },
                        { "dialog_shown", "true" },
                        { "dialog_result", "OK" },
                        { "selected_path", full },
                        { "response_sent", "true" },
                        { "duration_ms", "5" }
                    };
                    LogBridgeBlock(bSim);

                    resultJson = string.Format("{{\"status\":\"ok\",\"cancelled\":false,\"request_id\":{0},\"path\":{1},\"name\":{2}}}",
                        ToJsonString(requestId), ToJsonString(full), ToJsonString(nm));
                } else {
                    LogTrace("WORKSPACE_PICKER_06_DIALOG_START");
                    string dialogOut = null;
                    Exception threadEx = null;

                    Thread staThread = new Thread((ThreadStart)delegate {
                        try {
                            RunDialog(initial, requestId, out dialogOut);
                        } catch (Exception dex) {
                            threadEx = dex;
                            LogTrace("RunDialog thread exception: " + dex.ToString());
                            var errBlock = new Dictionary<string, string> {
                                { "request_id", requestId },
                                { "exception_type", dex.GetType().FullName },
                                { "exception_message", dex.Message },
                                { "exception_stack_trace", dex.StackTrace }
                            };
                            LogBridgeBlock(errBlock);
                            dialogOut = string.Format("{{\"status\":\"error\",\"cancelled\":true,\"request_id\":{0},\"error\":{1}}}",
                                ToJsonString(requestId), ToJsonString(dex.Message));
                        }
                    });
                    staThread.SetApartmentState(ApartmentState.STA);
                    staThread.Start();
                    staThread.Join();
                    resultJson = dialogOut;
                }

                if (string.IsNullOrEmpty(resultJson)) {
                    resultJson = string.Format("{{\"status\":\"ok\",\"cancelled\":true,\"request_id\":{0}}}",
                        ToJsonString(requestId));
                }
                byte[] bytes = Encoding.UTF8.GetBytes(resultJson);
                resp.OutputStream.Write(bytes, 0, bytes.Length);
                resp.Close();
                LogTrace("WORKSPACE_PICKER_10_RESPONSE_SENT");
                return;
            }

            resp.StatusCode = 404;
            byte[] notFound = Encoding.UTF8.GetBytes("{\"error\":\"Not found\"}");
            resp.OutputStream.Write(notFound, 0, notFound.Length);
            resp.Close();
        } catch (Exception ex) {
            LogTrace(string.Format("WORKSPACE_PICKER_ERROR: Request handling exception: {0}", ex.ToString()));
            try {
                resp.StatusCode = 500;
                byte[] errBytes = Encoding.UTF8.GetBytes(string.Format("{{\"error\":{0}}}", ToJsonString(ex.Message)));
                resp.OutputStream.Write(errBytes, 0, errBytes.Length);
                resp.Close();
            } catch {}
        }
    }

    private static string ToJsonString(string s) {
        if (s == null) return "null";
        StringBuilder sb = new StringBuilder();
        sb.Append('"');
        foreach (char c in s) {
            switch (c) {
                case '\\': sb.Append("\\\\"); break;
                case '"': sb.Append("\\\""); break;
                case '\b': sb.Append("\\b"); break;
                case '\f': sb.Append("\\f"); break;
                case '\n': sb.Append("\\n"); break;
                case '\r': sb.Append("\\r"); break;
                case '\t': sb.Append("\\t"); break;
                default:
                    if (c < ' ' || c > 127) {
                        sb.AppendFormat("\\u{0:x4}", (int)c);
                    } else {
                        sb.Append(c);
                    }
                    break;
            }
        }
        sb.Append('"');
        return sb.ToString();
    }
}
