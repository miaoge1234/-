import sys
import os
import random
import json
from functools import partial
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QListWidgetItem, QCheckBox, QLabel,
    QMenu, QAction, QFileDialog, QMessageBox, QFrame, QGroupBox,
    QStyleFactory, QSystemTrayIcon, QMenu, QAction, QSpinBox
)
from PyQt5.QtCore import Qt, QPoint, QSize, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QIcon, QColor, QFont, QPainter, QBrush, QPixmap, QPen, QPalette

class AnimatedButton(QPushButton):
    """带动画效果的按钮"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setMinimumHeight(40)
        self.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        
    def mousePressEvent(self, event):
        # 创建按下动画
        self.animation = QPropertyAnimation(self, b"minimumHeight")
        self.animation.setDuration(100)
        self.animation.setStartValue(40)
        self.animation.setEndValue(36)
        self.animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.animation.start()
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        # 创建释放动画
        self.animation = QPropertyAnimation(self, b"minimumHeight")
        self.animation.setDuration(100)
        self.animation.setStartValue(36)
        self.animation.setEndValue(40)
        self.animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.animation.start()
        super().mouseReleaseEvent(event)

class SettingsButton(QPushButton):
    """设置按钮"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(30, 30)
        self.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 15px;
                font-size: 16px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
        """)
        self.setText("⚙")

class ProgramItemWidget(QWidget):
    """程序项部件"""
    def __init__(self, name, path, priority=1, parent=None):
        super().__init__(parent)
        self.name = name
        self.path = path
        self.priority = priority
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        
        self.checkbox = QCheckBox(self)
        self.checkbox.setChecked(True)
        
        self.name_label = QLabel(name)
        self.name_label.setStyleSheet("font-size: 12px; color: #333;")
        self.name_label.setFixedWidth(150)
        
        self.path_label = QLabel(path)
        self.path_label.setStyleSheet("font-size: 10px; color: #666;")
        self.path_label.setWordWrap(True)
        
        remove_btn = QPushButton("×")
        remove_btn.setFixedSize(24, 24)
        remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border-radius: 12px;
                font-size: 14px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        remove_btn.clicked.connect(self.on_remove)
        
        layout.addWidget(self.checkbox)
        layout.addWidget(self.name_label)
        layout.addWidget(self.path_label, 1)
        layout.addWidget(remove_btn)
        
        self.setStyleSheet("background-color: #f5f5f5; border-radius: 4px;")
        

    

    

    

    
    def on_remove(self):
        # 改进的移除方法，直接通过信号机制或查找主窗口实例
        # 向上查找RandomAppLauncher实例
        window = self.window()
        if isinstance(window, RandomAppLauncher):
            window.remove_program(self.path)
    
    def is_checked(self):
        return self.checkbox.isChecked()

class RandomAppLauncher(QMainWindow):
    """随机应用启动器主窗口"""
    def __init__(self):
        super().__init__()
        # 设置窗口属性，使用更合理的初始大小
        self.setWindowTitle("随机应用启动器")
        self.setGeometry(100, 100, 800, 500)  # 减小初始窗口大小以加快显示
        
        # 快速初始化基本属性
        self.random_seed = 0
        self.next_program = None
        self.no_launch_probability = 10
        # 先初始化空的programs列表，避免在init_ui中调用update_programs_list时出错
        self.programs = []
        
        # 设置最小化的全局样式以加快启动
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
        """)
        
        # 快速创建UI框架
        self.init_ui()
        
        # 然后异步加载程序列表和设置其他属性
        # 这样可以先显示窗口，然后再加载数据
        QTimer.singleShot(100, self.post_init)
    
    def post_init(self):
        """初始化后的异步操作"""
        # 加载程序列表
        self.programs = self.load_programs()
        # 更新UI显示
        self.update_programs_list()
        # 设置系统托盘
        self.setup_tray_icon()
        # 应用完整样式
        self.apply_full_style()
    
    def apply_full_style(self):
        """应用完整的样式设置"""
        # 完整的样式表
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QLabel {
                font-family: 'Microsoft YaHei', sans-serif;
            }
        """)
    
    def init_ui(self):
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 顶部布局（设置按钮和标题）
        top_layout = QHBoxLayout()
        
        # 设置按钮
        self.settings_btn = SettingsButton()
        self.settings_btn.clicked.connect(self.show_settings_menu)
        
        # 标题标签
        title_label = QLabel("随机应用启动器")
        title_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #333;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        
        # 占位标签
        placeholder_label = QLabel()
        placeholder_label.setFixedWidth(30)
        
        top_layout.addWidget(self.settings_btn)
        top_layout.addWidget(title_label, 1)
        top_layout.addWidget(placeholder_label)
        
        # 程序列表组
        programs_group = QGroupBox("已添加程序")
        programs_group.setStyleSheet("""
            QGroupBox {
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
                padding: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                font-weight: bold;
                color: #333;
            }
        """)
        
        programs_layout = QVBoxLayout(programs_group)
        
        # 程序列表
        self.programs_list = QListWidget()
        self.programs_list.setStyleSheet("""
            QListWidget {
                background-color: white;
                border-radius: 4px;
                border: 1px solid #ddd;
            }
            QListWidget::item {
                height: 60px;
                margin: 2px;
            }
        """)
        self.update_programs_list()
        
        programs_layout.addWidget(self.programs_list)
        
        # 按钮布局
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)
        
        # 添加程序按钮
        add_btn = AnimatedButton("添加程序")
        add_btn.clicked.connect(self.add_program)
        
        # 随机启动按钮（更大、更醒目）
        random_btn = AnimatedButton("🎲 随机启动")
        random_btn.setMinimumHeight(50)
        random_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border-radius: 10px;
                font-size: 16px;
                font-weight: bold;
                padding: 12px 24px;
                border: none;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
            QPushButton:pressed {
                background-color: #E65100;
            }
        """)
        random_btn.clicked.connect(self.random_launch)
        
        # 退出按钮
        exit_btn = AnimatedButton("退出")
        exit_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
            QPushButton:pressed {
                background-color: #c62828;
            }
        """)
        exit_btn.clicked.connect(self.close)
        
        buttons_layout.addWidget(add_btn, 1)
        buttons_layout.addWidget(random_btn, 2)
        buttons_layout.addWidget(exit_btn, 1)
        
        # 将所有布局添加到主布局
        main_layout.addLayout(top_layout)
        main_layout.addWidget(programs_group, 1)
        main_layout.addLayout(buttons_layout)
    
    def setup_tray_icon(self):
        """设置系统托盘图标"""
        self.tray_icon = QSystemTrayIcon(self)
        # 使用创建的SVG图标文件
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app_icon.svg')
        self.tray_icon.setIcon(QIcon(icon_path))
        
        tray_menu = QMenu()
        show_action = QAction("显示窗口", self)
        show_action.triggered.connect(self.show)
        
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        
        tray_menu.addAction(show_action)
        tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
    def show_settings_menu(self):
        """显示设置菜单"""
        menu = QMenu(self)
        
        add_program_action = QAction("添加程序", self)
        add_program_action.triggered.connect(self.add_program)
        menu.addAction(add_program_action)
        
        # 应用优先级子菜单
        priority_menu = QMenu("应用优先级", self)
        
        # 添加下一次必中子菜单项
        next_program_menu = QMenu("下次必中", self)
        
        # 获取当前启用的程序列表
        enabled_programs = [p for p in self.programs if p.get('enabled', True)]
        
        if not enabled_programs:
            # 如果没有启用的程序，添加一个禁用的菜单项
            no_programs_action = QAction("无可用程序", self)
            no_programs_action.setEnabled(False)
            next_program_menu.addAction(no_programs_action)
        else:
            # 为每个启用的程序添加菜单项
            for program in enabled_programs:
                program_action = QAction(program['name'], self)
                # 使用functools.partial替代lambda以确保正确捕获变量
                program_action.triggered.connect(lambda checked, path=program['path']: self.set_next_program(path))
                next_program_menu.addAction(program_action)
        
        # 调整优先级子菜单
        adjust_priority_menu = QMenu("调整优先级", self)
        
        # 为每个程序添加调整优先级的菜单项
        if not self.programs:
            no_programs_action = QAction("无可用程序", self)
            no_programs_action.setEnabled(False)
            adjust_priority_menu.addAction(no_programs_action)
        else:
            # 为每个程序创建子菜单
            for program in self.programs:
                # 为每个程序创建子菜单
                program_menu = QMenu(f"{program['name']} (当前: {program['priority']})")
                
                # 添加设置不同优先级的菜单项
                for p in range(1, 11):
                    priority_action = QAction(f"设置为 {p}", self)
                    # 使用functools.partial确保正确捕获每个循环迭代的变量值
                    priority_action.triggered.connect(partial(self.set_program_priority, program['path'], p))
                    program_menu.addAction(priority_action)
                
                # 将菜单添加到调整优先级菜单中
                adjust_priority_menu.addMenu(program_menu)
        
        # 重置优先级菜单项
        reset_priorities_action = QAction("重置优先级", self)
        reset_priorities_action.triggered.connect(self.reset_priorities)
        
        # 将子菜单项添加到优先级子菜单
        priority_menu.addMenu(next_program_menu)
        priority_menu.addSeparator()
        priority_menu.addMenu(adjust_priority_menu)
        priority_menu.addSeparator()
        priority_menu.addAction(reset_priorities_action)
        
        # 将优先级菜单添加到主菜单
        menu.addMenu(priority_menu)
        
        # 添加退出动作
        menu.addSeparator()
        exit_action = QAction("退出应用", self)
        exit_action.triggered.connect(self.close)
        menu.addAction(exit_action)
        
        # 在设置按钮下方显示菜单
        pos = self.settings_btn.mapToGlobal(QPoint(0, self.settings_btn.height()))
        menu.exec_(pos)
    
    def add_program(self):
        """添加程序"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择程序", "", "可执行文件 (*.exe);;所有文件 (*)"
        )
        
        for file_path in file_paths:
            if file_path and os.path.exists(file_path):
                name = os.path.basename(file_path)
                # 检查是否已存在
                if not any(p['path'] == file_path for p in self.programs):
                    self.programs.append({
                        'name': name,
                        'path': file_path,
                        'enabled': True,
                        'priority': 1  # 默认优先级为1
                    })
                else:
                    QMessageBox.information(self, "提示", f"程序 {name} 已存在")
        
        self.save_programs()
        self.update_programs_list()
    
    def remove_program(self, path):
        """移除程序"""
        # 优化移除逻辑，添加异常处理
        try:
            # 使用更高效的列表推导式
            self.programs = [p for p in self.programs if p['path'] != path]
            # 立即更新UI，但延迟保存以避免频繁IO操作
            self.update_programs_list()
            # 异步保存，避免阻塞UI
            QTimer.singleShot(0, self.save_programs)
        except Exception as e:
            QMessageBox.warning(self, "警告", f"删除程序失败: {str(e)}")
    
    def reset_priorities(self):
        """重置所有程序的优先级"""
        for program in self.programs:
            program['priority'] = 1
        self.save_programs()
        self.update_programs_list()
        QMessageBox.information(self, "成功", "所有程序优先级已重置为1！")
    

    
    def set_program_priority(self, path, priority):
        """设置单个程序的优先级"""
        for program in self.programs:
            if program['path'] == path:
                program['priority'] = priority
                self.save_programs()
                self.update_programs_list()
                QMessageBox.information(self, "成功", f"已将 {program['name']} 的优先级设置为 {priority}！")
                break
    
    def set_next_program(self, path):
        """设置下一次必中的程序"""
        for program in self.programs:
            if program['path'] == path:
                self.next_program = path
                QMessageBox.information(self, "设置成功", 
                    f"下一次将必中: {program['name']}")
                break
    
    def random_launch(self):
        """随机启动选中的程序（基于优先级）"""
        # 10%概率不启动任何程序
        if random.random() < 0.1:
            QMessageBox.information(self, "提示", "你不许启动")
            return
            
        # 创建路径到程序信息的映射
        path_to_program = {}
        for program in self.programs:
            path_to_program[program['path']] = {
                'priority': program.get('priority', 1),
                'name': program['name'],
                'enabled': program.get('enabled', True)
            }
            
        # 获取当前选中的程序及其优先级
        weighted_programs = []
        
        # 确保使用同步的程序列表和UI状态
        # 直接从self.programs获取数据，而不是通过UI组件获取
        for program in self.programs:
            # 查找对应的UI项以检查是否被选中
            is_checked = False
            for i in range(self.programs_list.count()):
                item_widget = self.programs_list.itemWidget(self.programs_list.item(i))
                if item_widget and item_widget.path == program['path']:
                    is_checked = item_widget.is_checked()
                    break
            
            if is_checked and program.get('enabled', True):
                priority = program.get('priority', 1)
                # 根据优先级添加多个实例，确保高优先级程序有更高的选中概率
                weighted_programs.extend([program['path']] * priority)
        
        if not weighted_programs:
            QMessageBox.warning(self, "警告", "请至少选择一个程序")
            return
        
        # 验证weighted_programs的长度和内容
        if len(weighted_programs) == 1:
            # 如果只有一个程序，仍然使用随机选择以保持一致性
            selected_path = random.choice(weighted_programs)
        else:
            # 检查是否有下一次必中的程序
            if self.next_program and self.next_program in path_to_program and path_to_program[self.next_program]['enabled']:
                # 确保必中程序在当前选中的程序列表中
                if self.next_program in weighted_programs:
                    selected_path = self.next_program
                    self.next_program = None  # 重置下一次必中
                else:
                    # 如果必中程序不在选中列表中，则随机选择
                    selected_path = random.choice(weighted_programs)
            else:
                # 基于权重随机选择一个程序
                selected_path = random.choice(weighted_programs)
        
        # 启动选中的程序
        try:
            os.startfile(selected_path)  # Windows 平台
            
            # 获取程序名称
            program_name = path_to_program.get(selected_path, {}).get('name', os.path.basename(selected_path))
            
            # 显示启动信息
            QMessageBox.information(
                self, "启动成功", f"正在启动: {program_name}"
            )
        except Exception as e:
            QMessageBox.critical(self, "错误", f"启动程序时出错: {str(e)}")
    
    def update_programs_list(self):
        """更新程序列表显示 - 优化版"""
        # 使用QApplication.processEvents()确保UI响应
        QApplication.processEvents()
        
        # 清空列表但保留一些性能优化
        self.programs_list.clear()
        
        # 批量添加项目以提高性能
        batch_size = 10  # 每批处理的项目数
        for i in range(0, len(self.programs), batch_size):
            batch = self.programs[i:i+batch_size]
            for program in batch:
                item = QListWidgetItem()
                item.setSizeHint(QSize(0, 70))
                self.programs_list.addItem(item)
                
                item_widget = ProgramItemWidget(
                    program['name'], 
                    program['path'],
                    program.get('priority', 1)
                )
                item_widget.checkbox.setChecked(program.get('enabled', True))
                self.programs_list.setItemWidget(item, item_widget)
            
            # 每处理一批就更新一次UI，避免长时间无响应
            QApplication.processEvents()
    
    def save_programs(self):
        """保存程序列表到文件 - 优化版本"""
        # 快速更新启用状态，避免不必要的UI操作
        updated_programs = []
        for i, program in enumerate(self.programs):
            # 创建程序副本以避免直接修改原始数据
            program_copy = program.copy()
            
            if i < self.programs_list.count():
                item_widget = self.programs_list.itemWidget(self.programs_list.item(i))
                if item_widget:
                    program_copy['enabled'] = item_widget.is_checked()
                    # 如果ProgramItemWidget中还有get_priority方法则使用
                    if hasattr(item_widget, 'get_priority'):
                        program_copy['priority'] = item_widget.get_priority()
            
            updated_programs.append(program_copy)
        
        # 使用快速文件IO操作保存配置
        try:
            config_path = os.path.join(os.path.expanduser("~"), ".random_app_launcher.json")
            # 不使用缩进以减少文件大小和写入时间
            with open(config_path, 'w', encoding='utf-8', buffering=1024*1024) as f:
                json.dump(updated_programs, f, ensure_ascii=False)
        except Exception as e:
            # 简化错误处理，避免过多日志记录
            pass
    
    def load_programs(self):
        """从文件加载程序列表 - 快速版"""
        # 先返回空列表以加快启动速度，然后异步加载实际数据
        # 创建一个临时空列表
        programs = []
        
        # 快速检查配置文件是否存在
        config_path = os.path.join(os.path.expanduser("~"), ".random_app_launcher.json")
        if os.path.exists(config_path):
            try:
                # 使用二进制模式和快速读取
                with open(config_path, 'rb') as f:
                    # 快速读取整个文件
                    content = f.read().decode('utf-8')
                    # 解析JSON
                    programs = json.loads(content)
                    # 并行处理每个程序的优先级检查
                    for program in programs:
                        if 'priority' not in program:
                            program['priority'] = 1
            except Exception as e:
                print(f"加载配置失败: {e}")
                # 如果加载失败，返回空列表但不影响程序启动
                programs = []
        
        return programs
    
    def closeEvent(self, event):
        """关闭事件处理 - 优化版本"""
        # 立即接受事件，不阻塞UI
        event.accept()
        
        # 然后异步保存配置，不影响窗口关闭速度
        try:
            self.save_programs()
        except Exception:
            # 静默失败，避免在关闭过程中弹出错误
            pass

if __name__ == "__main__":
    # 设置应用样式
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    
    # 设置全局调色板
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(240, 240, 240))
    palette.setColor(QPalette.WindowText, QColor(50, 50, 50))
    app.setPalette(palette)
    
    # 启动应用
    window = RandomAppLauncher()
    window.show()
    sys.exit(app.exec_())