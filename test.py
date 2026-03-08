"""
优化版 HTTP 文件服务器，用于提供 powercat.ps1 等文件。
支持自定义监听IP和端口。
"""

import http.server
import socketserver
import argparse
import os
import sys

def main():
    parser = argparse.ArgumentParser(description="简易HTTP文件服务器")
    parser.add_argument('--ip', type=str, default='0.0.0.0',
                        help='绑定的IP地址，默认为0.0.0.0（所有接口）')
    parser.add_argument('--port', '-p', type=int, default=8000,
                        help='监听的端口，默认为8000')
    parser.add_argument('--dir', '-d', type=str, default='.',
                        help='要共享的目录，默认为当前目录')
    args = parser.parse_args()

    # 切换到指定目录
    try:
        os.chdir(args.dir)
    except FileNotFoundError:
        print(f"错误：目录 '{args.dir}' 不存在")
        sys.exit(1)
    except PermissionError:
        print(f"错误：没有权限访问目录 '{args.dir}'")
        sys.exit(1)

    handler = http.server.SimpleHTTPRequestHandler
    server_address = (args.ip, args.port)

    try:
        with socketserver.TCPServer(server_address, handler) as httpd:
            print(f"[*] HTTP服务器启动成功")
            print(f"[*] 监听地址: {args.ip}:{args.port}")
            print(f"[*] 服务目录: {os.path.abspath(args.dir)}")
            print(f"[*] 可用文件: {os.listdir('.')}")
            print("[*] 按 Ctrl+C 停止服务")
            httpd.serve_forever()
    except OSError as e:
        if e.errno == 10048:  # Windows下端口被占用
            print(f"错误：端口 {args.port} 已被占用，请更换端口或关闭占用程序")
        elif e.errno == 10049:  # 地址不可用
            print(f"错误：IP地址 {args.ip} 无效或本机没有此IP")
        else:
            print(f"错误：无法启动服务器 - {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[*] 收到中断，服务器已停止")
        sys.exit(0)

if __name__ == '__main__':
    main()