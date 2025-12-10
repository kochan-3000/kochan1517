import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import easyocr
import datetime
from pathlib import Path
import numpy as np
import os

reader = easyocr.Reader(['ja', 'en'], gpu=False)


class OCRApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OCRアプリ（日本語パス対応）")

        self.image = None
        self.image_path: Path | None = None

        # 注意文
        notice = tk.Label(root, text="日本語パスの画像にも対応しています。", fg="green")
        notice.pack(pady=5)

        # ボタン群
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=5)

        tk.Button(btn_frame, text="画像を開く", command=self.open_image).pack(side="left", padx=5)
        tk.Button(btn_frame, text="OCR実行", command=self.run_ocr).pack(side="left", padx=5)
        tk.Button(btn_frame, text="PDF保存", command=self.save_as_pdf).pack(side="left", padx=5)

        # 画像表示用
        self.canvas = tk.Canvas(root, width=600, height=400, bg="gray")
        self.canvas.pack()

        # OCR結果表示
        self.text_box = tk.Text(root, height=15, width=80)
        self.text_box.pack(pady=10)

    # ------------------------
    # 画像読込
    # ------------------------
    def open_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("画像ファイル", "*.png;*.jpg;*.jpeg;*.bmp;*.tif;*.tiff")]
        )
        if not file_path:
            return

        try:
            self.image_path = Path(file_path)
            self.image = Image.open(self.image_path)

            img = self.image.copy()
            img.thumbnail((600, 400))
            self.photo = ImageTk.PhotoImage(img)
            self.canvas.create_image(300, 200, image=self.photo)

        except Exception as e:
            messagebox.showerror("エラー", f"画像を開けませんでした:\n{e}")

    # ------------------------
    # OCR実行
    # ------------------------
    def run_ocr(self):
        if self.image is None:
            messagebox.showwarning("警告", "画像を選択してください。")
            return

        try:
            img_array = np.array(self.image)
            results = reader.readtext(img_array)

            self.text_box.delete(1.0, tk.END)

            if not results:
                self.text_box.insert(tk.END, "OCR結果は空です。\n")
                return

            for (_, text, prob) in results:
                self.text_box.insert(tk.END, f"{text}（信頼度: {prob:.2f}）\n")

        except Exception as e:
            self.text_box.insert(tk.END, f"[OCRエラー]\n{e}")

    # ------------------------
    # PDF保存
    # ------------------------
    def save_as_pdf(self):
        if self.image is None:
            messagebox.showwarning("警告", "画像を選択してください。")
            return

        try:
            today = datetime.date.today().strftime("%Y-%m-%d")
            default_name = f"{today}.pdf"

            save_path = filedialog.asksaveasfilename(
                initialfile=default_name,
                defaultextension=".pdf",
                filetypes=[("PDFファイル", "*.pdf")]
            )
            if not save_path:
                return

            save_path = Path(save_path)
            rgb_img = self.image.convert("RGB")
            rgb_img.save(save_path, "PDF")

            messagebox.showinfo("完了", f"PDFを保存しました:\n{save_path}")

        except Exception as e:
            messagebox.showerror("エラー", f"PDF保存に失敗しました:\n{e}")


if __name__ == "__main__":
    root = tk.Tk()
    OCRApp(root)
    root.mainloop()
