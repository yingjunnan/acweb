#!/bin/bash

# 交互式 CLI 工具测试脚本
# 用于验证终端是否正确支持交互式应用

echo "=========================================="
echo "交互式 CLI 工具测试"
echo "=========================================="
echo ""

# 测试 1: 检查终端类型
echo "1. 检查终端类型和环境变量"
echo "   TERM: $TERM"
echo "   COLORTERM: $COLORTERM"
echo "   TERM_PROGRAM: $TERM_PROGRAM"
echo ""

# 测试 2: 检查终端尺寸
echo "2. 检查终端尺寸"
if command -v tput &> /dev/null; then
    echo "   列数: $(tput cols)"
    echo "   行数: $(tput lines)"
else
    echo "   tput 命令不可用"
fi
echo ""

# 测试 3: 测试颜色支持
echo "3. 测试颜色支持"
echo -e "   \033[31m红色\033[0m \033[32m绿色\033[0m \033[33m黄色\033[0m \033[34m蓝色\033[0m \033[35m品红\033[0m \033[36m青色\033[0m"
echo -e "   \033[1;31m亮红\033[0m \033[1;32m亮绿\033[0m \033[1;33m亮黄\033[0m \033[1;34m亮蓝\033[0m \033[1;35m亮品红\033[0m \033[1;36m亮青\033[0m"
echo ""

# 测试 4: 测试光标移动
echo "4. 测试光标移动和定位"
echo -n "   测试光标移动: "
echo -ne "\033[5C→\033[5D←"  # 向右移动5格，向左移动5格
echo ""
echo ""

# 测试 5: 测试清屏功能
echo "5. 测试清屏功能（按回车继续）"
read -r
clear
echo "清屏成功！"
echo ""

# 测试 6: 简单的交互式菜单测试
echo "6. 简单的交互式菜单测试"
echo "   请使用方向键选择选项（按 q 退出）："
echo ""

# 创建一个简单的菜单
PS3="请选择: "
options=("选项 1" "选项 2" "选项 3" "退出")
select opt in "${options[@]}"
do
    case $opt in
        "选项 1")
            echo "你选择了选项 1"
            ;;
        "选项 2")
            echo "你选择了选项 2"
            ;;
        "选项 3")
            echo "你选择了选项 3"
            ;;
        "退出")
            break
            ;;
        *) 
            echo "无效选项 $REPLY"
            ;;
    esac
done

echo ""
echo "=========================================="
echo "测试完成！"
echo "=========================================="
echo ""
echo "如果以上所有测试都正常显示，说明终端配置正确。"
echo "现在可以测试更复杂的交互式工具，如："
echo "  - vim 或 nano (文本编辑器)"
echo "  - less 或 more (分页查看器)"
echo "  - top 或 htop (系统监控)"
echo "  - claude (Claude Code CLI)"
echo ""
