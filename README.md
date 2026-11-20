# PCIe Modeler – Bandwidth & Latency

Phiên bản web Streamlit chuyển từ ứng dụng Tkinter `pcie_modeler.pyw`.
Giữ nguyên các công thức PCIe Gen 1–5, băng thông theo x1/x2/x4/x8/x16,
ước lượng latency, 2 biểu đồ và khả năng tải CSV/PNG.

## Chạy trên máy

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Tạo đường link để nộp

1. Tạo repository mới trên https://github.com và tải **app.py** cùng **requirements.txt** lên thư mục gốc (có thể thêm README.md).
2. Vào https://share.streamlit.io/ rồi đăng nhập bằng GitHub.
3. Chọn **Create app / Deploy an app**, chọn repository vừa tạo, nhánh `main`, file chính `app.py`.
4. Nhấn **Deploy**, chờ trang chạy, sao chép URL dạng `https://ten-app.streamlit.app/` để nộp.

Lưu ý: Các giá trị hiệu suất payload, trễ T0 và trễ switch là giả định mô hình, không phải các giá trị bất biến của chuẩn PCIe.
