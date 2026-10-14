using System;
using System.Drawing;
using System.Windows.Forms;
using System.Runtime.InteropServices;

public class TestPicker {
    [DllImport("user32.dll")]
    private static extern bool SetForegroundWindow(IntPtr hWnd);

    [DllImport("user32.dll")]
    private static extern bool BringWindowToTop(IntPtr hWnd);

    private static Form CreateTopMostOwnerForm() {
        Form f = new Form();
        f.Size = new Size(1, 1);
        f.StartPosition = FormStartPosition.Manual;
        f.Location = new Point(-2000, -2000);
        f.ShowInTaskbar = false;
        f.FormBorderStyle = FormBorderStyle.None;
        f.Opacity = 0;
        f.Show();
        f.TopMost = true;
        f.BringToFront();
        f.Activate();
        SetForegroundWindow(f.Handle);
        BringWindowToTop(f.Handle);
        return f;
    }

    [STAThread]
    public static void Main() {
        Console.WriteLine("Creating TopMost Owner Form...");
        using (Form owner = CreateTopMostOwnerForm()) {
            Console.WriteLine("Owner HWND: " + owner.Handle + " TopMost: " + owner.TopMost);
        }
        Console.WriteLine("Success!");
    }
}
