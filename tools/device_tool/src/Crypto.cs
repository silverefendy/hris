using System;
using System.Security.Cryptography;
using System.Text;

namespace HrisDeviceTool
{
    // Enkripsi rahasia dengan kata sandi aplikasi (portabel, tidak terikat akun Windows)
    public static class Crypto
    {
        const string Magic = "HDT1|";

        public static byte[] Encrypt(string plain, string password)
        {
            byte[] salt = new byte[16];
            byte[] iv = new byte[16];
            RandomNumberGenerator rng = RandomNumberGenerator.Create();
            rng.GetBytes(salt);
            rng.GetBytes(iv);
            byte[] key = new Rfc2898DeriveBytes(password, salt, 20000).GetBytes(32);
            Aes aes = Aes.Create();
            aes.Key = key;
            aes.IV = iv;
            aes.Mode = CipherMode.CBC;
            aes.Padding = PaddingMode.PKCS7;
            byte[] data = Encoding.UTF8.GetBytes(Magic + plain);
            byte[] enc = aes.CreateEncryptor().TransformFinalBlock(data, 0, data.Length);
            byte[] all = new byte[32 + enc.Length];
            Buffer.BlockCopy(salt, 0, all, 0, 16);
            Buffer.BlockCopy(iv, 0, all, 16, 16);
            Buffer.BlockCopy(enc, 0, all, 32, enc.Length);
            return all;
        }

        public static bool TryDecrypt(byte[] all, string password, out string plain)
        {
            plain = "";
            try
            {
                if (all == null || all.Length < 48) return false;
                byte[] salt = new byte[16];
                byte[] iv = new byte[16];
                Buffer.BlockCopy(all, 0, salt, 0, 16);
                Buffer.BlockCopy(all, 16, iv, 0, 16);
                byte[] enc = new byte[all.Length - 32];
                Buffer.BlockCopy(all, 32, enc, 0, enc.Length);
                byte[] key = new Rfc2898DeriveBytes(password, salt, 20000).GetBytes(32);
                Aes aes = Aes.Create();
                aes.Key = key;
                aes.IV = iv;
                aes.Mode = CipherMode.CBC;
                aes.Padding = PaddingMode.PKCS7;
                byte[] data = aes.CreateDecryptor().TransformFinalBlock(enc, 0, enc.Length);
                string s = Encoding.UTF8.GetString(data);
                if (!s.StartsWith(Magic, StringComparison.Ordinal)) return false;
                plain = s.Substring(Magic.Length);
                return true;
            }
            catch (CryptographicException)
            {
                return false;
            }
        }
    }
}
