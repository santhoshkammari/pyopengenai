import re
import sys
import json
import logging
import os

from langchain_core.messages import SystemMessage, HumanMessage

from .prompts import PROMPTS
from hugchat import hugchat
from hugchat.login import Login

os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QVBoxLayout, QTextEdit, QDesktopWidget, QHBoxLayout, \
    QComboBox
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, pyqtSignal, QObject
from PyQt5.QtGui import QPainter, QColor, QFont, QTextCursor

import threading
# Register QTextCursor for use in signals
from PyQt5.QtCore import QMetaType

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

QMetaType.type("QTextCursor")

DEFAULT_MODELS: list = ['Qwen/Qwen2.5-72B-Instruct', 'meta-llama/Meta-Llama-3.1-70B-Instruct',
                        'CohereForAI/c4ai-command-r-plus-08-2024', 'meta-llama/Llama-3.2-11B-Vision-Instruct',
                        'NousResearch/Hermes-3-Llama-3.1-8B', 'mistralai/Mistral-Nemo-Instruct-2407',
                        'microsoft/Phi-3.5-mini-instruct']


class StreamHandler(QObject):
    new_token_signal = pyqtSignal(str)

    def __init__(self, response_callback):
        super().__init__()
        self.response_callback = response_callback
        self.full_response = ""

    def on_llm_new_token(self, token: str, **kwargs):
        self.new_token_signal.emit(token)
        self.full_response += token

    def on_llm_end(self, response, **kwargs):
        self.response_callback(self.full_response)


class SpotlightLLM(QWidget):
    def __init__(self, email,password,models: list | str = None, execution_mode="Local"):
        super().__init__()
        self.email = email
        self.password = password  # NOTE: This should be kept securely. Use environment variables or secure vaults.
        self.models = models or DEFAULT_MODELS
        self.execution_mode = execution_mode  # Default to Local execution
        self.current_model = self.models[0]
        self.chatbot = self.initialize_chat()
        self.initUI()
        self.setup_data_directory()
        self.session_interactions = []
        self.response_complete = threading.Event()

        # Set up logging
        logging.basicConfig(filename='spotlight_llm.log', level=logging.DEBUG,
                            format='%(asctime)s - %(levelname)s - %(message)s')

    def initialize_chat(self):
        cookie_path_dir = "./cookies/"  # NOTE: trailing slash (/) is required to avoid errors
        sign = Login(self.email, self.password)
        cookies = sign.login(cookie_dir_path=cookie_path_dir, save_cookies=True)
        qwen_model = self.models[0] if isinstance(self.models, list) else self.models
        chatbot = hugchat.ChatBot(cookies=cookies.get_dict(),
                                  default_llm=qwen_model)
        return chatbot

    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)

        # Create a horizontal layout for search bar, model selection, and execution mode
        search_layout = QHBoxLayout()

        self.search_bar = QLineEdit(self)
        self.search_bar.setStyleSheet("""
            QLineEdit {
                background-color: rgba(60, 60, 60, 200);
                border: none;
                border-radius: 20px;
                padding: 10px;
                color: white;
                font-size: 18px;
            }
        """)
        self.search_bar.returnPressed.connect(self.on_submit)
        search_layout.addWidget(self.search_bar, 5)

        self.model_selector = QComboBox(self)
        self.model_selector.addItems(self.models)
        self.model_selector.setStyleSheet(self.get_combobox_style())
        self.model_selector.currentTextChanged.connect(self.on_model_change)
        search_layout.addWidget(self.model_selector, 2)

        self.execution_selector = QComboBox(self)
        self.execution_selector.addItems(["Local", "GPU"])
        self.execution_selector.setStyleSheet(self.get_combobox_style())
        self.execution_selector.currentTextChanged.connect(self.on_execution_mode_change)
        search_layout.addWidget(self.execution_selector, 2)

        layout.addLayout(search_layout)

        self.result_area = QTextEdit(self)
        self.result_area.setReadOnly(True)
        self.result_area.setStyleSheet("""
            QTextEdit {
                background-color: rgba(60, 60, 60, 200);
                border: none;
                border-radius: 10px;
                padding: 10px;
                color: white;
                font-size: 14px;
            }
        """)
        self.result_area.hide()
        layout.addWidget(self.result_area)

        self.setLayout(layout)

        screen = QDesktopWidget().screenNumber(QDesktopWidget().cursor().pos())
        screen_size = QDesktopWidget().screenGeometry(screen)
        window_width = 750
        window_height = 60
        x = (screen_size.width() - window_width) // 2
        y = screen_size.height() // 4
        self.setGeometry(x, y, window_width, window_height)

    def get_combobox_style(self):
        return """
            QComboBox {
                background-color: rgba(60, 60, 60, 200);
                border: none;
                border-radius: 20px;
                padding: 10px;
                color: white;
                font-size: 14px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: url(down_arrow.png);
                width: 12px;
                height: 12px;
            }
            QComboBox QAbstractItemView {
                background-color: rgba(60, 60, 60, 200);
                border: none;
                selection-background-color: rgba(80, 80, 80, 200);
                color: white;
            }
        """

    def setup_data_directory(self):
        self.data_dir = os.path.join(os.path.expanduser("~"), "spotlight_llm_data")
        os.makedirs(self.data_dir, exist_ok=True)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(30, 30, 30, 200))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 20, 20)

    def on_model_change(self, model):
        self.current_model = model
        logging.info(f"Model changed to: {model}")

    def on_execution_mode_change(self, mode):
        self.execution_mode = mode
        logging.info(f"Execution mode changed to: {mode}")

    def on_submit(self):
        query = self.search_bar.text()
        if query:
            self.result_area.clear()
            self.result_area.show()
            self.animate_expand()
            self.current_query = query
            self.current_timestamp = datetime.now().isoformat()
            self.response_complete.clear()
            threading.Thread(target=self.get_response, args=(query,), daemon=True).start()

    def update_result_area(self, token):
        cursor = self.result_area.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(token)
        self.result_area.setTextCursor(cursor)
        self.result_area.ensureCursorVisible()

    def add_universe_prompt(self, prompt):
        return PROMPTS.RAR_PROMPT + f"\n\n {prompt}"

    def add_messages_prompt(self, prompt):
        return [
            # {"role": "system","content": CLAUDE_SYSTEM_PROMPT},
            # SystemMessage(content=CLAUDE_SYSTEM_PROMPT),
            SystemMessage(content=PROMPTS.RAR_PROMPT),
            # {"role": "user","content": prompt}
            HumanMessage(content=prompt)
        ]

    def format_results_multi_agent(self, results):
        output = []

        # Add the final answer
        output.append("Final Answer:\n")
        output.append(results['final_answer'])
        output.append("")

        # Add subqueries and their results
        output.append("Subqueries and WebAnalysis:\n")
        for i, subquery in enumerate(results['subqueries']):
            output.append(f"{i + 1}. Subquery: {subquery}\n")

            # Get the corresponding result
            result = results['subquery_results'][i]

            # output.append("   Web Result:")
            # output.append(f"   {result['web_result']}")

            output.append("Relevant Information:")
            output.append(f"{result['relevant_info']}")
            output.append("")

        return "\n".join(output)

    def filter_prompts(self, prompt):
        # Add your prompt filtering logic here
        filtered_prompt = " ".join(prompt.split()[:-1])

        prompt = re.split("User Question : ", filtered_prompt)[-1]
        return prompt

    def get_response(self, user_query):
        # prompt = self.add_universe_prompt(user_query)
        prompt = user_query
        logging.debug(f"Starting response generation in {self.execution_mode} mode")
        stream_handler = StreamHandler(self.save_interaction)
        stream_handler.new_token_signal.connect(self.update_result_area)

        try:
            web_search_flag = False
            if prompt.lower().split()[-1] in ["google", "bing"]:
                prompt = self.filter_prompts(prompt)
                web_search_flag = True
            for resp in self.chatbot.chat(
                    prompt,
                    stream=True,
                    web_search=web_search_flag
            ):
                if resp:
                    stream_handler.on_llm_new_token(resp['token'])

            stream_handler.on_llm_end(None)
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            QApplication.instance().postEvent(self.result_area, QTextCursor(self.result_area.document()))
            self.result_area.setPlainText(error_message)
            self.save_interaction(error_message)
            logging.exception(f"Error in {self.execution_mode} mode")
        finally:
            if self.execution_mode == "GPU":
                # Add any necessary cleanup for GPU resources
                pass
            logging.debug(f"Finished response generation in {self.execution_mode} mode")
            self.response_complete.set()

    def save_interaction(self, response):
        interaction_data = {
            "timestamp": self.current_timestamp,
            "model": self.current_model,
            "execution_mode": self.execution_mode,
            "query": self.current_query,
            "response": response
        }
        self.session_interactions.append(interaction_data)
        logging.info(f"Interaction saved: {self.current_timestamp}")

    def animate_expand(self):
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(300)
        self.animation.setStartValue(self.geometry())
        new_height = 400
        new_geometry = QRect(self.x(), self.y(), self.width(), new_height)
        self.animation.setEndValue(new_geometry)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.animation.start()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
    def closeEvent(self, event):
        logging.info("Application closing")
        super().closeEvent(event)

def spotlight_llm_run(email,password):
    app = QApplication(sys.argv)
    ex = SpotlightLLM(email=email,password=password)
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    spotlight_llm_run(email="santhoshkammari1999@gmail.com",password="SK99@pass123")