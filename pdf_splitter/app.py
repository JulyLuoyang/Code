from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
from PyPDF2 import PdfReader, PdfWriter
import time

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'

# 全局变量，用于存储分割进度
progress = 0

# 确保上传和输出目录存在
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
if not os.path.exists(app.config['OUTPUT_FOLDER']):
    os.makedirs(app.config['OUTPUT_FOLDER'])

def split_pdf(input_pdf_path, num_parts, output_dir, part1_pages=None, part2_pages=None):
    global progress
    progress = 0  # 重置进度

    # 打开 PDF 文件
    reader = PdfReader(input_pdf_path)
    total_pages = len(reader.pages)

    if num_parts == 2 and part1_pages and part2_pages:
        pages_per_part = [part1_pages, part2_pages]
    else:
        pages_per_part = [total_pages // num_parts] * num_parts
        remainder = total_pages % num_parts  # 剩余的页数
        for i in range(remainder):
            pages_per_part[i] += 1

    # 动态分割 PDF
    start_page = 0
    for part in range(1, num_parts + 1):
        writer = PdfWriter()
        end_page = start_page + pages_per_part[part - 1]

        # 添加当前部分的页面
        for i in range(start_page, end_page):
            writer.add_page(reader.pages[i])

        # 保存当前部分
        output_path = os.path.join(output_dir, f"part_{part}.pdf")
        with open(output_path, "wb") as output_pdf:
            writer.write(output_pdf)

        # 更新进度
        progress = int((part / num_parts) * 100)
        time.sleep(1)  # 模拟耗时操作

        start_page = end_page

    progress = 100  # 分割完成

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/split', methods=['POST'])
def split():
    global progress
    progress = 0  # 重置进度

    # 获取用户输入
    file = request.files['file']
    num_parts = int(request.form['num_parts'])
    output_dir = os.path.join(app.config['OUTPUT_FOLDER'], request.form['output_dir'])
    part1_pages = request.form.get('part1_pages')
    part2_pages = request.form.get('part2_pages')

    # 保存上传的文件
    if file and file.filename.endswith('.pdf'):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        # 确保输出目录存在
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 启动分割任务
        if num_parts == 2 and part1_pages and part2_pages:
            split_pdf(file_path, num_parts, output_dir, int(part1_pages), int(part2_pages))
        else:
            split_pdf(file_path, num_parts, output_dir)

    return jsonify({"status": "success"})

@app.route('/progress')
def get_progress():
    global progress
    return jsonify({"progress": progress})

if __name__ == '__main__':
    app.run(debug=True)