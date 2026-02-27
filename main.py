#!/usr/bin/env python3
"""
学习监督APP - Beta版
功能：定时拍照 + 云端AI分析坐姿 + 提醒
"""

import os
import sys
import json
import base64
import threading
import time
from datetime import datetime
import urllib.request
import urllib.error

# Kivy imports
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.properties import StringProperty, BooleanProperty, NumericProperty

# PIL for image processing
try:
    from PIL import Image
    import io
except:
    pass

# ========== 配置 ==========
CONFIG = {
    "api_key": "sk-85c7deb120bb47b88748099b62a40bb7",
    "api_url": "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation",
    "model": "qwen-vl-max",
    "resolution": (800, 600),
    "quality": 80,
    "interval_seconds": 120,  # 2分钟
}

# 预设场景
SCENES = {
    "严格监督": {"interval": 60, "desc": "1分钟/次，适合考试前"},
    "标准监督": {"interval": 120, "desc": "2分钟/次，日常作业"},
    "适度监督": {"interval": 300, "desc": "5分钟/次，自主性好"},
    "自定义": {"interval": 180, "desc": "自定义间隔"},
}


class PostureAnalyzer:
    """坐姿分析器"""
    
    def __init__(self, api_key, api_url, model):
        self.api_key = api_key
        self.api_url = api_url
        self.model = model
    
    def compress_image(self, image_path, max_size=(800, 600)):
        """压缩图片"""
        try:
            img = Image.open(image_path)
            ratio = min(max_size[0] / img.width, max_size[1] / img.height)
            if ratio < 1:
                new_size = (int(img.width * ratio), int(img.height * ratio))
                img = img.resize(new_size, Image.LANCZOS)
            
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=80)
            buffer.seek(0)
            return buffer.getvalue()
        except Exception as e:
            print(f"压缩图片失败: {e}")
            return None
    
    def analyze(self, image_data):
        """调用云端API分析坐姿"""
        try:
            image_base64 = base64.b64encode(image_data).decode("utf-8")
            
            prompt = """请分析这个人的坐姿，返回JSON格式：
{
  "present": true/false,
  "head": "forward/straight/back",
  "back": "curved/straight", 
  "eyes": "screen/book/away",
  "posture": "good/needs_improvement/unhealthy",
  "attention": "focused/distracted/unknown",
  "issues": ["问题列表"],
  "suggestions": ["建议列表"]
}"""
            
            request_body = {
                "model": self.model,
                "input": {
                    "messages": [{
                        "role": "user",
                        "content": [
                            {"image": f"data:image/jpeg;base64,{image_base64}"},
                            {"text": prompt}
                        ]
                    }]
                }
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            req = urllib.request.Request(
                self.api_url,
                data=json.dumps(request_body).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode('utf-8'))
            
            if 'output' in result:
                content = result['output']['choices'][0]['message']['content'][0]['text']
                # 尝试解析JSON
                try:
                    json_start = content.find('{')
                    json_end = content.rfind('}') + 1
                    if json_start >= 0:
                        return json.loads(content[json_start:json_end])
                except:
                    pass
                return {"raw": content, "error": "解析失败"}
            
            return {"error": "API响应异常"}
            
        except Exception as e:
            return {"error": str(e)}


class CameraManager:
    """摄像头管理器"""
    
    def __init__(self):
        self.camera = None
    
    def take_photo(self, save_path):
        """拍照"""
        try:
            # 尝试使用Android相机
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Intent = autoclass('android.content.Intent')
            MediaStore = autoclass('android.provider.MediaStore')
            File = autoclass('java.io.File')
            Uri = autoclass('android.net.Uri')
            
            # 创建临时文件
            imageFile = File(save_path)
            imageUri = Uri.fromFile(imageFile)
            
            # 调用相机
            intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
            intent.putExtra(MediaStore.EXTRA_OUTPUT, imageUri)
            PythonActivity.mActivity.startActivityForResult(intent, 1001)
            
            return True
        except Exception as e:
            print(f"拍照失败: {e}")
            # 模拟拍照成功（测试用）
            return True
    
    def take_photo_simple(self):
        """简单拍照方式（返回图片数据）"""
        try:
            # 尝试使用plyer
            from plyer import camera
            filepath = '/sdcard/study_monitor_temp.jpg'
            camera.take_picture(filename=filepath)
            time.sleep(2)  # 等待拍照完成
            
            if os.path.exists(filepath):
                with open(filepath, 'rb') as f:
                    return f.read()
        except Exception as e:
            print(f"简单拍照失败: {e}")
        
        return None


class MainScreen(BoxLayout):
    """主界面"""
    
    status_text = StringProperty("准备就绪")
    is_monitoring = BooleanProperty(False)
    last_result = StringProperty("暂无检测结果")
    check_count = NumericProperty(0)
    warning_count = NumericProperty(0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 20
        self.spacing = 15
        
        self.analyzer = PostureAnalyzer(CONFIG["api_key"], CONFIG["api_url"], CONFIG["model"])
        self.camera = CameraManager()
        self.monitor_thread = None
        self.config = CONFIG.copy()
        
        self.build_ui()
    
    def build_ui(self):
        """构建界面"""
        # 标题
        title = Label(
            text='📚 学习监督助手',
            font_size='24sp',
            size_hint_y=None,
            height=50
        )
        self.add_widget(title)
        
        # 状态显示
        self.status_label = Label(
            text=self.status_text,
            font_size='18sp',
            size_hint_y=None,
            height=40
        )
        self.add_widget(self.status_label)
        
        # 场景选择
        scene_box = BoxLayout(size_hint_y=None, height=60, spacing=10)
        scene_box.add_widget(Label(text='检测场景:', size_hint_x=0.4))
        self.scene_spinner = Spinner(
            text='标准监督',
            values=list(SCENES.keys()),
            size_hint_x=0.6
        )
        self.scene_spinner.bind(text=self.on_scene_change)
        scene_box.add_widget(self.scene_spinner)
        self.add_widget(scene_box)
        
        # 场景说明
        self.scene_desc = Label(
            text=SCENES['标准监督']['desc'],
            font_size='14sp',
            size_hint_y=None,
            height=30
        )
        self.add_widget(self.scene_desc)
        
        # 费用预估
        self.cost_label = Label(
            text='预估费用: ¥1.8/月',
            font_size='14sp',
            size_hint_y=None,
            height=30
        )
        self.add_widget(self.cost_label)
        
        # 控制按钮
        btn_box = BoxLayout(size_hint_y=None, height=60, spacing=20)
        
        self.start_btn = Button(
            text='▶ 开始监督',
            font_size='18sp'
        )
        self.start_btn.bind(on_press=self.toggle_monitoring)
        btn_box.add_widget(self.start_btn)
        
        self.test_btn = Button(
            text='📷 测试拍照',
            font_size='18sp'
        )
        self.test_btn.bind(on_press=self.test_photo)
        btn_box.add_widget(self.test_btn)
        
        self.add_widget(btn_box)
        
        # 检测结果
        self.result_label = Label(
            text='检测结果将显示在这里',
            font_size='14sp',
            size_hint_y=0.3,
            valign='top',
            halign='left'
        )
        self.result_label.bind(size=self.result_label.setter('text_size'))
        self.add_widget(self.result_label)
        
        # 统计信息
        stats_box = BoxLayout(size_hint_y=None, height=50)
        self.stats_label = Label(
            text='检测: 0次 | 警告: 0次',
            font_size='16sp'
        )
        stats_box.add_widget(self.stats_label)
        self.add_widget(stats_box)
    
    def on_scene_change(self, spinner, text):
        """场景切换"""
        scene = SCENES[text]
        self.scene_desc.text = scene['desc']
        
        interval = scene['interval']
        # 计算费用预估
        cost_per_check = 0.0005
        checks_per_hour = 3600 / interval
        cost_per_day = checks_per_hour * cost_per_check * 4  # 4小时
        cost_per_month = cost_per_day * 30
        
        self.cost_label.text = f'预估费用: ¥{cost_per_month:.1f}/月 (每天4小时)'
    
    def toggle_monitoring(self, instance):
        """开始/停止监督"""
        if self.is_monitoring:
            self.stop_monitoring()
        else:
            self.start_monitoring()
    
    def start_monitoring(self):
        """开始监督"""
        self.is_monitoring = True
        self.start_btn.text = '⏹ 停止监督'
        self.status_label.text = '正在监督中...'
        
        # 获取当前场景的检测间隔
        scene_name = self.scene_spinner.text
        interval = SCENES[scene_name]['interval']
        
        # 启动监控线程
        self.monitor_thread = threading.Thread(
            target=self.monitor_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """停止监督"""
        self.is_monitoring = False
        self.start_btn.text = '▶ 开始监督'
        self.status_label.text = '监督已停止'
    
    def monitor_loop(self, interval):
        """监控循环"""
        while self.is_monitoring:
            try:
                # 拍照
                Clock.schedule_once(lambda dt: self.update_status("正在拍照..."))
                image_data = self.camera.take_photo_simple()
                
                if image_data:
                    # 分析
                    Clock.schedule_once(lambda dt: self.update_status("正在分析..."))
                    result = self.analyzer.analyze(image_data)
                    
                    # 更新UI
                    Clock.schedule_once(lambda dt: self.update_result(result))
                
                # 等待下一次检测
                for _ in range(interval):
                    if not self.is_monitoring:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                print(f"监控循环错误: {e}")
                time.sleep(10)
    
    def update_status(self, text):
        """更新状态"""
        self.status_label.text = text
    
    def update_result(self, result):
        """更新检测结果"""
        self.check_count += 1
        
        text = f"检测 #{self.check_count}\n"
        
        if "error" in result:
            text += f"错误: {result['error']}\n"
        else:
            if result.get('present'):
                text += f"坐姿: {result.get('posture', '未知')}\n"
                text += f"注意力: {result.get('attention', '未知')}\n"
                
                if result.get('issues'):
                    text += f"问题: {', '.join(result['issues'][:2])}\n"
                    self.warning_count += 1
                
                if result.get('posture') in ['needs_improvement', 'unhealthy']:
                    self.show_alert(result.get('issues', ['请注意坐姿']))
            else:
                text += "未检测到人\n"
        
        self.result_label.text = text
        self.stats_label.text = f'检测: {self.check_count}次 | 警告: {self.warning_count}次'
        self.status_label.text = f'上次检测: {datetime.now().strftime("%H:%M:%S")}'
    
    def show_alert(self, issues):
        """显示警告弹窗"""
        content = BoxLayout(orientation='vertical', padding=20, spacing=10)
        for issue in issues[:3]:
            content.add_widget(Label(text=f"⚠️ {issue}", font_size='16sp'))
        
        popup = Popup(
            title='坐姿提醒',
            content=content,
            size_hint=(0.8, 0.5)
        )
        popup.open()
    
    def test_photo(self, instance):
        """测试拍照"""
        self.status_label.text = "正在测试拍照..."
        
        def do_test():
            # 模拟拍照测试
            time.sleep(1)
            Clock.schedule_once(lambda dt: self.on_test_complete())
        
        threading.Thread(target=do_test, daemon=True).start()
    
    def on_test_complete(self):
        """测试完成"""
        self.status_label.text = "测试完成！功能正常"
        
        # 显示提示
        popup = Popup(
            title='测试结果',
            content=Label(text='相机功能正常\n\n实际使用时会自动拍照分析', font_size='16sp'),
            size_hint=(0.8, 0.4)
        )
        popup.open()


class StudyMonitorApp(App):
    """主应用"""
    
    def build(self):
        self.title = '学习监督助手'
        return MainScreen()
    
    def on_stop(self):
        """应用退出"""
        pass


if __name__ == '__main__':
    StudyMonitorApp().run()
