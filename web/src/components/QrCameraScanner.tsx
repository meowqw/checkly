import { useEffect, useId, useRef, useState } from "react";
import { Html5Qrcode } from "html5-qrcode";
import { X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { isFiscalReceiptQr, normalizeQrPayload } from "@/lib/qr-payload";

type Props = {
  open: boolean;
  onClose: () => void;
  onScan: (payload: string) => void;
};

export function QrCameraScanner({ open, onClose, onScan }: Props) {
  const regionId = useId().replace(/:/g, "");
  const scannerRef = useRef<Html5Qrcode | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!open) return;

    let cancelled = false;
    const scanner = new Html5Qrcode(regionId, { verbose: false });
    scannerRef.current = scanner;
    setError("");

    const onDecoded = (text: string) => {
      const payload = normalizeQrPayload(text);
      if (!isFiscalReceiptQr(payload)) return;
      void scanner.stop().then(() => {
        scannerRef.current = null;
        onScan(payload);
        onClose();
      });
    };

    scanner
      .start(
        { facingMode: "environment" },
        { fps: 10, qrbox: { width: 260, height: 260 }, aspectRatio: 1 },
        onDecoded,
        () => {}
      )
      .catch((err: unknown) => {
        if (!cancelled) {
          const msg = err instanceof Error ? err.message : "Не удалось открыть камеру";
          setError(msg);
        }
      });

    return () => {
      cancelled = true;
      const active = scannerRef.current;
      if (active) {
        void active.stop().catch(() => {});
      }
      scannerRef.current = null;
    };
  }, [open, regionId, onClose, onScan]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-black/90 p-4">
      <div className="mb-3 flex items-center justify-between text-white">
        <span className="text-sm font-medium">Наведите на QR чека</span>
        <button
          type="button"
          onClick={onClose}
          className="rounded-full p-2 hover:bg-white/10"
          aria-label="Закрыть"
        >
          <X size={20} />
        </button>
      </div>
      <div className="relative mx-auto w-full max-w-sm flex-1 overflow-hidden rounded-2xl bg-black">
        <div id={regionId} className="min-h-[280px] w-full [&_video]:rounded-2xl" />
      </div>
      {error && <p className="mt-3 text-center text-sm text-red-300">{error}</p>}
      <Button type="button" variant="outline" className="mt-4 w-full" onClick={onClose}>
        Отмена
      </Button>
    </div>
  );
}