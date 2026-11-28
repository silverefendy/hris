using System;
using System.Collections.Generic;

namespace HrisDeviceTool.Data
{
    // Penyaring baris log menurut tanggal. Murni, tidak menyentuh mesin atau database.
    public static class SaringLog
    {
        // dari: termasuk. sampaiEksklusif: tidak termasuk. null berarti tanpa batas.
        public static List<BarisLog> Tanggal(IList<BarisLog> baris, DateTime? dari, DateTime? sampaiEksklusif)
        {
            List<BarisLog> h = new List<BarisLog>();
            foreach (BarisLog b in baris)
            {
                if (dari.HasValue && b.Waktu < dari.Value) { continue; }
                if (sampaiEksklusif.HasValue && b.Waktu >= sampaiEksklusif.Value) { continue; }
                h.Add(b);
            }
            return h;
        }
    }
}