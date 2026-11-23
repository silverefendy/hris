using System;
using System.ComponentModel;
using System.Runtime.InteropServices;
using System.Text;

namespace HrisDeviceTool
{
    // Enkripsi Windows (DPAPI), terikat ke akun Windows di PC ini.
    // Berkas hasilnya hanya bisa dibuka oleh akun Windows yang sama di PC yang sama.
    public static class Dpapi
    {
        static readonly byte[] Magic = new byte[] { (byte)'H', (byte)'D', (byte)'T', (byte)'2' };
        static readonly byte[] Entropy = Encoding.UTF8.GetBytes("HrisDeviceTool.rahasia.v2");
        const int UiForbidden = 1;

        [StructLayout(LayoutKind.Sequential)]
        struct DataBlob
        {
            public int cbData;
            public IntPtr pbData;
        }

        [DllImport("crypt32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        static extern bool CryptProtectData(ref DataBlob pDataIn, string szDataDescr, ref DataBlob pOptionalEntropy,
            IntPtr pvReserved, IntPtr pPromptStruct, int dwFlags, out DataBlob pDataOut);

        [DllImport("crypt32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        static extern bool CryptUnprotectData(ref DataBlob pDataIn, IntPtr ppszDataDescr, ref DataBlob pOptionalEntropy,
            IntPtr pvReserved, IntPtr pPromptStruct, int dwFlags, out DataBlob pDataOut);

        [DllImport("kernel32.dll")]
        static extern IntPtr LocalFree(IntPtr hMem);

        static DataBlob Blob(byte[] d)
        {
            DataBlob b = new DataBlob();
            b.cbData = d.Length;
            b.pbData = Marshal.AllocHGlobal(d.Length == 0 ? 1 : d.Length);
            Marshal.Copy(d, 0, b.pbData, d.Length);
            return b;
        }

        static byte[] Ambil(DataBlob b)
        {
            byte[] r = new byte[b.cbData];
            Marshal.Copy(b.pbData, r, 0, b.cbData);
            LocalFree(b.pbData);
            return r;
        }

        // true bila berkas berformat DPAPI (diawali HDT2)
        public static bool Ada(byte[] all)
        {
            if (all == null || all.Length <= Magic.Length) return false;
            for (int i = 0; i < Magic.Length; i++)
                if (all[i] != Magic[i]) return false;
            return true;
        }

        public static byte[] Lindungi(string plain)
        {
            DataBlob din = Blob(Encoding.UTF8.GetBytes(plain));
            DataBlob ent = Blob(Entropy);
            DataBlob dout = new DataBlob();
            bool ok = false;
            int err = 0;
            try
            {
                ok = CryptProtectData(ref din, "HRIS Device Tool", ref ent, IntPtr.Zero, IntPtr.Zero, UiForbidden, out dout);
                if (!ok) err = Marshal.GetLastWin32Error();
            }
            finally
            {
                Marshal.FreeHGlobal(din.pbData);
                Marshal.FreeHGlobal(ent.pbData);
            }
            if (!ok) throw new Win32Exception(err);
            byte[] enc = Ambil(dout);
            byte[] all = new byte[Magic.Length + enc.Length];
            Buffer.BlockCopy(Magic, 0, all, 0, Magic.Length);
            Buffer.BlockCopy(enc, 0, all, Magic.Length, enc.Length);
            return all;
        }

        // false bila bukan format DPAPI, atau tidak bisa dibuka (PC/akun Windows lain)
        public static bool TryBuka(byte[] all, out string plain)
        {
            plain = "";
            try
            {
                if (!Ada(all)) return false;
                byte[] enc = new byte[all.Length - Magic.Length];
                Buffer.BlockCopy(all, Magic.Length, enc, 0, enc.Length);
                DataBlob din = Blob(enc);
                DataBlob ent = Blob(Entropy);
                DataBlob dout = new DataBlob();
                bool ok = false;
                try
                {
                    ok = CryptUnprotectData(ref din, IntPtr.Zero, ref ent, IntPtr.Zero, IntPtr.Zero, UiForbidden, out dout);
                }
                finally
                {
                    Marshal.FreeHGlobal(din.pbData);
                    Marshal.FreeHGlobal(ent.pbData);
                }
                if (!ok) return false;
                plain = Encoding.UTF8.GetString(Ambil(dout));
                return true;
            }
            catch (Exception)
            {
                return false;
            }
        }
    }
}